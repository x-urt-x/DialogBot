from message import Message, MessageView
from user import User
from IDialogLoader import IDialogLoader
from zonelogger import logger, LogZone
from answer import Answer
from user_manager import UserManager

class MessageManager:
    def __init__(self, dialogLoader: IDialogLoader, userManager: UserManager):
        self._dialogLoader = dialogLoader
        self._userManager = userManager

    async def process(self, user: User, message: Message, answer: Answer):
        #get node
        current_node_id = user["dialog_stack"][-1]
        #load node
        nodes = self._dialogLoader.getNodes()
        current_node = nodes.get(current_node_id)
        if not current_node:
            logger.error(LogZone.MESSAGE_PROCESS, f"no node on {current_node_id} id")
            return
        #check input
        #start handlers
        #get next node
        next_node_id = await self._processInputHandlers(user, message, current_node)
        #move on dialogs
        if next_node_id != 0:
            await self._openNode(user, next_node_id, answer)
        #output text
        #process ref check perm
        #move on dialogs if needed

    @staticmethod
    async def _processInputHandlers(user: User, message: Message, current_node):
        message_preprocess_handler = current_node.get("message_preprocess_handler")
        if message_preprocess_handler:
            await message_preprocess_handler(user.to_dict(), MessageView(message, can_edit_text=True))
        triggers = current_node.get("triggers")
        cmd_triggers = current_node.get("cmd_triggers")
        if triggers:
            matched_trigger = triggers.get(message.text)
            if matched_trigger:
                return matched_trigger
        freeInput_handler = current_node.get("freeInput_handler")
        if freeInput_handler:
            freeInput_res = await freeInput_handler(user.to_dict(), MessageView(message), cmd_triggers)
            if freeInput_res != 0:
                return freeInput_res

        return 0

    async def _openNode(self, user: User, new_node_id, answer: Answer):
        nodes = self._dialogLoader.getNodes()
        new_node = nodes.get(new_node_id)
        if not new_node:
            logger.error(LogZone.MESSAGE_PROCESS, f"no node on {new_node_id} id")
            return
        node_role = new_node.get("role")
        if node_role is not None:
            user_role = user["role"]
            if node_role != user_role:
                user_roles = user["roles"]
                if node_role in user_roles:
                    await self._userManager.setRole(user.getId(),node_role)
                    user["dialog_stack"] = [1]
                else:
                    answer.text.append("u dont have permission")
                    logger.info(LogZone.MESSAGE_PROCESS, f"user {user.getId()} tres get access to {new_node_id} node")
                    return
        user["dialog_stack"].append(new_node_id)
        user.setDirty("dialog_stack")
        cmd_handler = new_node.get("cmd_handler")
        if cmd_handler:
            await cmd_handler(user)
        answer_handler = new_node.get("answer_handler")
        if answer_handler:
            new_node["text"] = await answer_handler(user.to_dict(), new_node.get("text", ""))
        answer.text.append(new_node.get("text", ""))  # текстов ответа может быть несколько
        answer.hints = list(new_node.get("triggers", {}).keys())  # дальнейшие подсказки только от последнего
        ref_id = new_node.get("ref")
        if ref_id:
            await self._openNode(user, ref_id, answer)
        await self._userManager.save_users_dirty(user)
