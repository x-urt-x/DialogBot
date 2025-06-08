from models.message import Message
from models.user import User
from models.answer import Answer
from models.nodesDict import NodesRootIDs
from models.messageAnswerQueue import MessageAnswerQueue
from enums.roles import Roles
from enums.languages import Language
from core.userManager import UserManager
from core.bUserParser import BUserParser
from zonelogger import logger, LogZone
from core.handlerTypes import HandlerTypes as Ht
from core.templateProcessor import TemplateProcessor

class MessageManager:
    def __init__(self, dialog_nodes_rootIDs_lang: dict[Language,NodesRootIDs], userManager: UserManager, messageAnswerQueue: MessageAnswerQueue, bUserParser: BUserParser ):
        self._dialog_nodes_rootIDs_lang = dialog_nodes_rootIDs_lang
        self._userManager = userManager
        self._messageAnswerQueue = messageAnswerQueue
        self._bUserParser = bUserParser
        self._back = False

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
        self._back = False
        await self._userManager.trySaveUserDirty(user)
        answer.text = TemplateProcessor.render_all(answer.text, user, message)
        return answer

    async def _processInputHandlers(self, user: User, message: Message, current_node, dialog_nodes_roots: NodesRootIDs) -> int | None:
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
        switch_triggers = current_node.get("switch_triggers")

        #INPUT_MSG
        input_msg_handler = current_node.get(Ht.INPUT_MSG)
        if input_msg_handler:
            await input_msg_handler(message)

        #triggers
        if clean_combined_triggers:
            matched_trigger = clean_combined_triggers.get(message.text)
            if matched_trigger:
                return matched_trigger

        #INPUT_PARSE
        input_parse_handler = current_node.get(Ht.INPUT_PARSE.value)
        if input_parse_handler:
            res = await input_parse_handler(message)
            MessageManager._deep_merge(user.tmp, res)

        #INPUT_USER
        input_user_handler = current_node.get(Ht.INPUT_USER.value)
        if input_user_handler:
            await input_user_handler(user, self._userManager)

        #INPUT_SWITCH
        input_switch_handler = current_node.get(Ht.INPUT_SWITCH.value)
        if input_switch_handler:
            ref_id = await input_switch_handler(user.tmp, switch_triggers)
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
                if node_role != Roles.GLOBAL:
                    if user_roles & Roles(node_role):
                        user.role = node_role
                        res = user.stackToRoot(rootIDs)
                        if not res:
                            logger.warning(LogZone.MESSAGE_PROCESS, f"no root for {user.role}")
                    else:
                        answer.text.append("u dont have permission")
                        logger.info(LogZone.MESSAGE_PROCESS, f"user {user.api}:{user.ID} tres get access to {new_node_id} node")
                        return
        user.stackAppend(new_node_id)

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
        switch_triggers = new_node.get("switch_triggers")

        #OPEN_USER
        open_user_handler = new_node.get(Ht.OPEN_USER.value)
        if open_user_handler:
            await open_user_handler(user, self._userManager)

        #OPEN_TEXT
        text = new_node.get("text")
        open_text_handler = new_node.get(Ht.OPEN_TEXT.value)
        if open_text_handler:
            text = await open_text_handler(user.tmp, text)
        if text is None:
            text = ""

        #OPEN_SWITCH
        ref_id = None
        open_switch_handler = new_node.get(Ht.OPEN_SWITCH.value)
        if open_switch_handler:
            ref_id = await open_switch_handler(user.tmp, switch_triggers)

        no_back_stop = new_node.get("no_back_stop", None)
        if self._back and (no_back_stop is not None):
            ref_id = -1
        else:
            answer.text.append(text)
            answer.hints = list(clean_combined_triggers.keys())

        if ref_id is None:
            ref_id = new_node.get("ref")
        if ref_id is not None:
            if self._back:
                self._back = False
                ref_id = -1
            if ref_id > 0:
                await self._openNode(user, ref_id, answer)
            else:
                if ref_id == 0:
                    user.stackClear()
                    back_to_node_id = -1
                else:
                    if -ref_id < user.stackLen():
                        back_to_node_id = user.stackPopN((-ref_id)+1)
                        self._back = True
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

    @staticmethod
    def _deep_merge(old: dict, new: dict| None) -> dict:
        if new is None:
            return old
        for key, new_value in new.items():
            if key in old:
                old_value = old[key]
                if isinstance(old_value, dict) and isinstance(new_value, dict):
                    MessageManager._deep_merge(old_value, new_value)
                else:
                    old[key] = new_value
            else:
                old[key] = new_value
        return old