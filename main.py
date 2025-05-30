from roles import Roles
from zonelogger import logger, LogZone
from dialog_node_handlers_manager import DialogNodeHandlersManager
from YAMLLoader import YAMLLoader
from user_manager import UserManager, User
from MongoUserDB import MongoUserDB
from message_manager import MessageManager
from telegramApi import TelegramApiManager
from tgToken import tg_token
import asyncio
from nodesDict import NodesRootIDs
from languages import Language

async def main():
    logger.enable_zone(LogZone.USERS)
    logger.enable_zone(LogZone.TG_API)
    logger.enable_zone(LogZone.MESSAGE_PROCESS)
    logger.enable_zone(LogZone.DIALOG_HANDLERS)
    handlers_manager = DialogNodeHandlersManager("dialog_node_handlers")
    handlers = handlers_manager.get_all()
    logger.info(LogZone.MAIN, handlers)
    dialogs_loader = YAMLLoader(handlers)
    dialogs : dict[Language,NodesRootIDs] = {
        Language.EN: dialogs_loader.load_folder("dialogs/en", Language.EN),
        Language.RU: dialogs_loader.load_folder("dialogs/ru", Language.RU)
    }

    userDB = MongoUserDB("localhost:27017", "dialog_bot")
    user_manager = UserManager(userDB)
    message_manager = MessageManager(dialogs, user_manager)
    tg_api = TelegramApiManager(tg_token, "https://e371-193-179-66-62.ngrok-free.app", message_manager, user_manager)
    await tg_api.run()
    print("Telegram API started. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("Shutting down...")
        await tg_api.shutdown()
    # user_id_1 = "111"
    # user1: User = await user_manager.getUser(user_id_1)
    # user_roles = user1["roles"]
    # user1["roles"] = user_roles | Roles.ADMIN
    # user1["dialog_stack"].append(1)
    # user1.setDirty("dialog_stack")
    # await user_manager.save_users_dirty(user1)
    # await user_manager.setRole(user_id_1, Roles.ADMIN)
    # ans = Answer()
    # msg = Message("set role", ApiId.TG, None)
    # await en_message_manager.process(user1, msg, ans)
    # logger.info(LogZone.MAIN, ans.text)


if __name__ == "__main__":
    asyncio.run(main())