from roles import Roles
from zonelogger import logger, LogZone
from dialog_node_handlers_manager import DialogNodeHandlersManager
from YAMLLoader import YAMLLoader
from user_manager import UserManager, User
from MongoUserDB import MongoUserDB
from message_manager import MessageManager
from telegramApi import TelegramApiManager
from consoleApi import ConsoleApi
from tgToken import tg_token
import asyncio
from nodesDict import NodesRootIDs
from languages import Language
from messageAnswerQueue import MessageAnswerQueue
from apiRegistry import ApiRegistry
from api_ids import ApiId
from apiManager import ApiManager
from apiSendManager import ApiSendManager

async def main():
    logger.enable_zone(LogZone.USERS)
    logger.enable_zone(LogZone.TG_API)
    logger.enable_zone(LogZone.MESSAGE_PROCESS)
    logger.enable_zone(LogZone.DIALOG_HANDLERS)
    logger.enable_zone(LogZone.API_PROCES)


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

    messageAnswerQueue : MessageAnswerQueue = MessageAnswerQueue()
    message_manager = MessageManager(dialogs, user_manager, messageAnswerQueue)

    tg_api = TelegramApiManager(tg_token, "https://ca32-193-179-66-62.ngrok-free.app", user_manager, messageAnswerQueue, "/webhook", 8000)
    console_api = ConsoleApi(user_manager, messageAnswerQueue)
    apiRegistry = ApiRegistry()
    apiRegistry.register(ApiId.TG,tg_api)
    apiRegistry.register(ApiId.CONSOLE,console_api)

    apiManager = ApiManager(apiRegistry)
    apiSendManager = ApiSendManager(messageAnswerQueue, apiRegistry, user_manager)

    await apiManager.run_all()
    print("Telegram API started. Press Ctrl+C to stop.")
    try:
        while True:
            await apiManager.process_all()
            await message_manager.process_queue()
            await apiSendManager.process_queue()
            await asyncio.sleep(0.001)
    except KeyboardInterrupt:
        print("Shutting down...")
        await apiManager.stop_all()


if __name__ == "__main__":
    asyncio.run(main())