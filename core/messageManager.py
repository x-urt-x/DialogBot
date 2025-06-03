from models.message import Message, MessageView
from models.user import User
from models.answer import Answer
from models.nodesDict import NodesRootIDs
from models.messageAnswerQueue import MessageAnswerQueue
from enums.roles import Roles
from enums.languages import Language
from core.userManager import UserManager
from core.bUserParser import BUserParser
from zonelogger import logger, LogZone
from core.handlerTypes import HandlerTypes

class MessageManager:
    def __init__(self, dialog_nodes_rootIDs_lang: dict[Language,NodesRootIDs], userManager: UserManager, messageAnswerQueue: MessageAnswerQueue, bUserParser: BUserParser ):
        self._dialog_nodes_rootIDs_lang = dialog_nodes_rootIDs_lang
        self._userManager = userManager
        self._messageAnswerQueue = messageAnswerQueue
        self._bUserParser = bUserParser

    async def process_queue(self):
        if self._messageAnswerQueue.incoming.empty():
            return
        bUser, message = await self._messageAnswerQueue.incoming.get()
        user = await self._bUserParser.parse(bUser)
        if not user:
            return
        answer =  await self.process(user, message)
        if answer:
            await self._messageAnswerQueue.outgoing.put(answer)

    async def process(self, user: User, message: Message)->Answer | None:
        answer = Answer()
        answer.to_ID = user.ID
        answer.to_api = user.api
        dialog_nodes_roots : NodesRootIDs | None= self._dialog_nodes_rootIDs_lang.get(user.lang)
        if not dialog_nodes_roots:
            logger.error(LogZone.MESSAGE_PROCESS, f"no {user.lang} lang")
            return None
        nodes: dict[int, dict] = dialog_nodes_roots["nodes"]
        if user.stackLen() == 0:
            res = user.stackToRoot(dialog_nodes_roots["roots"])
            if not res:
                logger.warning(LogZone.MESSAGE_PROCESS, f"no root for {user.role}")
        current_node_id = user.stackPeek()
        current_node = nodes.get(current_node_id)
        if not current_node:
            logger.error(LogZone.MESSAGE_PROCESS, f"no node on {current_node_id} id")
            return None
        next_node_id = await self._processInputHandlers(user, message, current_node, dialog_nodes_roots)
        if next_node_id:
            await self._openNode(user, next_node_id, answer)
        else:
            user.stackPopN(1)
            await self._openNode(user,current_node_id, answer)
        await self._userManager.save_users_dirty(user)
        return answer

    async def _processInputHandlers(self, user: User, message: Message, current_node, dialog_nodes_roots: NodesRootIDs) -> int | None:
        message_preprocess_handler = current_node.get("message_preprocess_handler")
        if message_preprocess_handler:
            await message_preprocess_handler(user.to_dict(), MessageView(message, can_edit_text=True))
        nodes : dict[int,dict]= dialog_nodes_roots["nodes"]
        rootIDs : dict [Roles, int]= dialog_nodes_roots["roots"]

        triggers = current_node.get("triggers", {})
        global_root_id = rootIDs.get(Roles.GLOBAL)
        global_root = nodes[global_root_id]
        global_triggers = global_root.get("triggers", {})
        combined_triggers  = MessageManager._combineTriggers(triggers, global_triggers)
        clean_combined_triggers = {
            key: node_id
            for key, (node_id, visibility) in combined_triggers.items()
            if visibility != -1
        }
        if clean_combined_triggers:
            matched_trigger = clean_combined_triggers.get(message.text)
            if matched_trigger:
                return matched_trigger

        cmd_triggers = current_node.get("cmd_triggers")
        freeInput_handler = current_node.get(HandlerTypes.FREE_INPUT.value)
        if freeInput_handler:
            user_new_data = await freeInput_handler(user, MessageView(message))
            if user_new_data:
                for key, value in user_new_data.items():
                    user.tmp[key] = value
        cmd_exit_handler = current_node.get(HandlerTypes.CMD_EXIT.value)
        if cmd_exit_handler:
            ref_id = await cmd_exit_handler(user, self._userManager, cmd_triggers)
            if ref_id:
                return ref_id
        return None

    async def _openNode(self, user: User, new_node_id, answer: Answer):
        dialog_nodes_roots = self._dialog_nodes_rootIDs_lang.get(user.lang)
        nodes: dict[int, dict] = dialog_nodes_roots["nodes"]
        rootIDs : dict [Roles, int] = dialog_nodes_roots["roots"]
        if new_node_id == -1:
            new_node_id = rootIDs[user.role]
        new_node = nodes.get(new_node_id)
        if not new_node:
            logger.error(LogZone.MESSAGE_PROCESS, f"no node on {new_node_id} id")
            return
        node_role = new_node.get("role")
        if node_role is not None:
            user_role = user.role
            if node_role != user_role:
                user_roles : Roles = user.roles
                if user_roles & Roles(node_role):
                    if node_role != Roles.GLOBAL:
                        user.role = node_role
                        res = user.stackToRoot(rootIDs)
                        if not res:
                            logger.warning(LogZone.MESSAGE_PROCESS, f"no root for {user.role}")
                else:
                    answer.text.append("u dont have permission")
                    logger.info(LogZone.MESSAGE_PROCESS, f"user {user.api}:{user.ID} tres get access to {new_node_id} node")
                    return
        user.stackAppend(new_node_id)
        cmd_handler = new_node.get(HandlerTypes.CMD.value)
        ref_id = None
        if cmd_handler:
            ref_id = await cmd_handler(user, self._userManager, new_node.get("cmd_triggers"))
        answer_handler = new_node.get(HandlerTypes.ANSWER.value)
        if answer_handler:
            new_node["text"] = await answer_handler(user.to_dict(), new_node.get("text", ""))
        triggers = new_node.get("triggers", {})
        global_root_id = rootIDs.get(Roles.GLOBAL)
        global_root = nodes[global_root_id]
        global_triggers = global_root.get("triggers", {})
        combined_triggers = MessageManager._combineTriggers(triggers, global_triggers)
        clean_combined_triggers = {
            key: node_id
            for key, (node_id, visibility) in combined_triggers.items()
            if visibility == 1
        }
        answer.text.append(new_node.get("text", ""))  # текстов ответа может быть несколько
        answer.hints = list(clean_combined_triggers.keys())  # дальнейшие подсказки только от последнего
        if ref_id is None:
            ref_id = new_node.get("ref")
        if ref_id is not None:
            if ref_id > 0:
                await self._openNode(user, ref_id, answer)
            else:
                if ref_id == 0:
                    user.stackClear()
                    back_to_node_id = -1
                else:
                    if -ref_id < user.stackLen():
                        back_to_node_id = user.stackPopN((-ref_id)+1)
                    else:
                        user.stackClear()
                        back_to_node_id = -1
                if not back_to_node_id:
                    logger.warning(LogZone.MESSAGE_PROCESS, f"no root for {user.role} or bad ref {ref_id}")
                await self._openNode(user, back_to_node_id, answer)

    @staticmethod
    def _combineTriggers(
            local_triggers: dict[str, tuple[int | None, int]],
            global_triggers: dict[str, tuple[int, int]]
    ) -> dict[str, tuple[int, int]]:
        merged = {}

        # Start with global triggers
        for key, (g_node_id, g_vis) in global_triggers.items():
            merged[key] = (g_node_id, g_vis)

        # Override or extend with local triggers
        for key, (l_node_id, l_vis) in local_triggers.items():
            if l_node_id is None:
                g_node_id = global_triggers.get(key, (None,))[0]
                merged[key] = (g_node_id, l_vis)
            else:
                merged[key] = (l_node_id, l_vis)

        return merged