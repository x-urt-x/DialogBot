from message import Message, MessageView
from roles import Roles
from user import User
from zonelogger import logger, LogZone
from answer import Answer
from user_manager import UserManager
from nodesDict import NodesRootIDs
from languages import Language
from messageAnswerQueue import MessageAnswerQueue

class MessageManager:
    def __init__(self, dialog_nodes_rootIDs_lang: dict[Language,NodesRootIDs], userManager: UserManager, messageAnswerQueue: MessageAnswerQueue):
        self._dialog_nodes_rootIDs_lang = dialog_nodes_rootIDs_lang
        self._userManager = userManager
        self._messageAnswerQueue = messageAnswerQueue

    async def process_queue(self):
        if self._messageAnswerQueue.incoming.empty():
            return
        user, message = await self._messageAnswerQueue.incoming.get()
        answer =  await self.process(user, message)
        if answer:
            await self._messageAnswerQueue.outgoing.put(answer)

    async def process(self, user: User, message: Message)->Answer | None:
        answer = Answer()
        answer.to_user_id = user.getId()
        user_lang : Language = user["lang"]
        if not user_lang:
            user_lang = Language.EN
        dialog_nodes_roots : NodesRootIDs | None= self._dialog_nodes_rootIDs_lang.get(user_lang)
        if not dialog_nodes_roots:
            logger.error(LogZone.MESSAGE_PROCESS, f"no {user_lang} lang")
            return None
        nodes: dict[int, dict] = dialog_nodes_roots["nodes"]
        #get node
        if not user["dialog_stack"]:
            await self._dialogStackToRoot(user, dialog_nodes_roots["roots"])
        current_node_id = user["dialog_stack"][-1]
        #load node
        current_node = nodes.get(current_node_id)
        if not current_node:
            logger.error(LogZone.MESSAGE_PROCESS, f"no node on {current_node_id} id")
            return None
        #check input
        #start handlers
        #get next node
        next_node_id = await MessageManager._processInputHandlers(user, message, current_node, dialog_nodes_roots)
        #move on dialogs
        if next_node_id != 0:
            await self._openNode(user, next_node_id, answer, dialog_nodes_roots)
        else:
            user["dialog_stack"].pop()
            await self._openNode(user,current_node_id, answer, dialog_nodes_roots)
        #output text
        #process ref check perm
        #move on dialogs if needed
        return answer

    @staticmethod
    async def _processInputHandlers(user: User, message: Message, current_node, dialog_nodes_roots: NodesRootIDs):
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
            freeInput_res = await freeInput_handler(user.to_dict(), MessageView(message), cmd_triggers)
            if freeInput_res != 0:
                return freeInput_res
        return 0

    async def _openNode(self, user: User, new_node_id, answer: Answer, dialog_nodes_roots: NodesRootIDs):
        nodes: dict[int, dict] = dialog_nodes_roots["nodes"]
        rootIDs : dict [Roles, int] = dialog_nodes_roots["roots"]
        new_node = nodes.get(new_node_id)
        if not new_node:
            logger.error(LogZone.MESSAGE_PROCESS, f"no node on {new_node_id} id")
            return
        node_role = new_node.get("role")
        if node_role is not None:
            user_role = user["role"]
            if node_role != user_role:
                user_roles : Roles = user["roles"]
                if user_roles & Roles(node_role):
                    if node_role != Roles.GLOBAL:
                        await self._userManager.setRole(user.getId(),node_role)
                        await self._dialogStackToRoot(user, rootIDs)
                else:
                    answer.text.append("u dont have permission")
                    logger.info(LogZone.MESSAGE_PROCESS, f"user {user.getId()} tres get access to {new_node_id} node")
                    return
        user["dialog_stack"].append(new_node_id)
        user.setDirty("dialog_stack")
        cmd_handler = new_node.get("cmd_handler")
        ref_id = None
        if cmd_handler:
            ref_id = await cmd_handler(user, self._userManager ,new_node.get("cmd_triggers"))
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
                    await self._dialogStackToRoot(user, rootIDs)
                else:
                    dialog_stack = user["dialog_stack"]
                    if -ref_id < len(dialog_stack):
                        del dialog_stack[ref_id:]
                    else:
                        await self._dialogStackToRoot(user, rootIDs)
                back_to_node_id = user["dialog_stack"].pop()
                await self._openNode(user, back_to_node_id, answer, dialog_nodes_roots)
        await self._userManager.save_users_dirty(user)

    async def _dialogStackToRoot(self, user: User, rootIDs : dict[Roles, int]):
        role : Roles = user["role"]
        root_node_id = rootIDs[role]
        user["dialog_stack"] = [root_node_id]
        user.setDirty("dialog_stack")
        await self._userManager.save_users_dirty(user)