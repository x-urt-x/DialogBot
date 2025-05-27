from roles import Roles
from zonelogger import logger, LogZone
from dialog_node_handlers_manager import handler_registry, load_dialog_node_handlers
from YAMLLoader import YAMLLoader
from user_manager import UserManager, User
from MongoUserDB import MongoUserDB
from api_ids import ApiId
from message_manager import MessageManager
import asyncio

from answer import Answer
from message import Message

async def main():
    logger.enable_zone(LogZone.USERS)
    logger.enable_zone(LogZone.DB)
    logger.enable_zone(LogZone.MAIN)
    load_dialog_node_handlers()
    logger.info(LogZone.MAIN, handler_registry)
    en_dialogs = YAMLLoader()
    en_dialogs.load_folder("dialogs/en")
    userDB = MongoUserDB("localhost:27017", "dialog_bot")
    user_manager = UserManager(userDB)
    en_message_manager = MessageManager(en_dialogs, user_manager)

    user_id_1 = "111"
    user1: User = await user_manager.getUser(user_id_1)
    user_roles = user1["roles"]
    user1["roles"] = user_roles | Roles.ADMIN
    user1["dialog_stack"].append(1)
    user1.setDirty("dialog_stack")
    await user_manager.save_users_dirty(user1)
    await user_manager.setRole(user_id_1, Roles.ADMIN)
    ans = Answer()
    msg = Message("set role", ApiId.TG, None)
    await en_message_manager.process(user1, msg, ans)
    logger.info(LogZone.MAIN, ans.text)


if __name__ == "__main__":
    asyncio.run(main())
