from zonelogger import logger, LogZone
from core.dialogNodeHandlersManager import DialogNodeHandlersManager
from YAMLLoader import YAMLLoader
from core.userManager import UserManager
from data_base.MongoUserDB import MongoUserDB
from core.messageManager import MessageManager
from boundary.api_handlers.telegramApi import TelegramApiManager
from boundary.api_handlers.consoleApi import ConsoleApi
from tgToken import tg_token
import asyncio
from models.nodesDict import NodesRootIDs
from enums.languages import Language
from models.messageAnswerQueue import MessageAnswerQueue
from boundary.infra.apiRegistry import ApiRegistry
from enums.apiIDs import ApiId
from boundary.infra.apiManager import ApiManager
from boundary.infra.apiSendManager import ApiSendManager
from core.bUserParser import BUserParser

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

    bUserParser = BUserParser(user_manager)

    messageAnswerQueue : MessageAnswerQueue = MessageAnswerQueue()
    message_manager = MessageManager(dialogs, user_manager, messageAnswerQueue, bUserParser)

    tg_api = TelegramApiManager(messageAnswerQueue, tg_token, "https://ca32-193-179-66-62.ngrok-free.app" , "/webhook", 8000)
    console_api = ConsoleApi(messageAnswerQueue)
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