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
        user_lang : Language = user.lang
        if not user_lang:
            user_lang = Language.EN
        dialog_nodes_roots : NodesRootIDs | None= self._dialog_nodes_rootIDs_lang.get(user_lang)
        if not dialog_nodes_roots:
            logger.error(LogZone.MESSAGE_PROCESS, f"no {user_lang} lang")
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
            await self._openNode(user, next_node_id, answer, dialog_nodes_roots)
        else:
            user.stackPopN(1)
            await self._openNode(user,current_node_id, answer, dialog_nodes_roots)
        await self._userManager.save_users_dirty(user)
        return answer

    async def _processInputHandlers(self, user: User, message: Message, current_node, dialog_nodes_roots: NodesRootIDs) -> int | None:
        message_preprocess_handler = current_node.get("message_preprocess_handler")
        if message_preprocess_handler:
            await message_preprocess_handler(user.to_dict(), MessageView(message, can_edit_text=True))
        triggers = current_node.get("triggers", {})
        nodes : dict[int,dict]= dialog_nodes_roots["nodes"]
        rootIDs : dict [Roles, int]= dialog_nodes_roots["roots"]
        global_root_id = rootIDs.get(Roles.GLOBAL)
        global_root = nodes[global_root_id]
        global_triggers = global_root.get("triggers", {})
        if global_triggers:
            for key, value in global_triggers.items():
                triggers.setdefault(key, value)
        if triggers:
            matched_trigger = triggers.get(message.text)
            if matched_trigger:
                return matched_trigger
        cmd_triggers = current_node.get("cmd_triggers")
        freeInput_handler = current_node.get("freeInput_handler")
        if freeInput_handler:
            user_new_data = await freeInput_handler(user, MessageView(message))
            if user_new_data:
                for key, value in user_new_data.items():
                    user.tmp[key] = value
        cmd_exit_handler = current_node.get("cmd_exit_handler")
        if cmd_exit_handler:
            ref_id = await cmd_exit_handler(user, self._userManager, cmd_triggers)
            if ref_id:
                return ref_id
        return None

    async def _openNode(self, user: User, new_node_id, answer: Answer, dialog_nodes_roots: NodesRootIDs):
        nodes: dict[int, dict] = dialog_nodes_roots["nodes"]
        rootIDs : dict [Roles, int] = dialog_nodes_roots["roots"]
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
        cmd_handler = new_node.get("cmd_handler")
        ref_id = None
        if cmd_handler:
            ref_id = await cmd_handler(user, self._userManager, new_node.get("cmd_triggers"))
        answer_handler = new_node.get("answer_handler")
        if answer_handler:
            new_node["text"] = await answer_handler(user.to_dict(), new_node.get("text", ""))
        triggers = new_node.get("triggers", {})
        global_root_id = rootIDs.get(Roles.GLOBAL)
        global_root = nodes[global_root_id]
        global_triggers = global_root.get("triggers", {})
        if global_triggers:
            for key, value in global_triggers.items():
                triggers.setdefault(key, value)
        answer.text.append(new_node.get("text", ""))  # текстов ответа может быть несколько
        answer.hints = list(triggers.keys())  # дальнейшие подсказки только от последнего
        if ref_id is None:
            ref_id = new_node.get("ref")
        if ref_id is not None:
            if ref_id > 0:
                await self._openNode(user, ref_id, answer, dialog_nodes_roots)
            else:
                if ref_id == 0:
                    user.stackClear()
                    back_to_node_id = rootIDs[user.role]
                else:
                    if -ref_id < user.stackLen():
                        back_to_node_id = user.stackPopN((-ref_id)+1)
                    else:
                        user.stackClear()
                        back_to_node_id = rootIDs[user.role]
                if not back_to_node_id:
                    logger.warning(LogZone.MESSAGE_PROCESS, f"no root for {user.role} or bad ref {ref_id}")
                await self._openNode(user, back_to_node_id, answer, dialog_nodes_roots)