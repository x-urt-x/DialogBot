from data_base.MongoUserDB import MongoUserDB
from core.dialogNodeHandlersManager import DialogNodeHandlersManager
from core.userManager import UserManager
from core.messageManager import MessageManager
from core.bUserParser import BUserParser
from boundary.api_handlers.telegramApi import TelegramApiManager
from boundary.api_handlers.consoleApi import ConsoleApi
from boundary.infra.apiRegistry import ApiRegistry
from boundary.infra.apiManager import ApiManager
from boundary.infra.apiSendManager import ApiSendManager
from models.nodesDict import NodesRootIDs
from models.messageAnswerQueue import MessageAnswerQueue
from zonelogger import logger, LogZone
from YAMLLoader import YAMLLoader
from enums.languages import Language
from enums.apiIDs import ApiId
import asyncio
import yaml

async def main():
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logger.enable_zone(LogZone.DB)
    #logger.enable_zone(LogZone.USERS)
    logger.enable_zone(LogZone.TG_API)
    logger.enable_zone(LogZone.MESSAGE_PROCESS)
    logger.enable_zone(LogZone.DIALOG_HANDLERS)
    #logger.enable_zone(LogZone.API_PROCES)

    handlers_manager = DialogNodeHandlersManager(config["handlers"]["folder"])
    handlers = handlers_manager.get_all()
    logger.info(LogZone.MAIN, handlers)

    dialogs_loader = YAMLLoader(handlers)
    dialogs: dict[Language, NodesRootIDs] = {
        Language(lang_code.lower()): dialogs_loader.load_folder(dialog_conf["folder"], Language(lang_code.lower()))
        for lang_code, dialog_conf in config["dialogs"].items()
    }

    userDB = MongoUserDB(config["database"]["uri"], config["database"]["name"])
    user_manager = UserManager(userDB, config["cache"]["size"])

    bUserParser = BUserParser(user_manager)

    messageAnswerQueue : MessageAnswerQueue = MessageAnswerQueue()
    message_manager = MessageManager(dialogs, user_manager, messageAnswerQueue, bUserParser)

    token = config["telegram"]["token"]
    url = config["telegram"]["public_url"]
    port = config["telegram"]["port"]
    tg_api = TelegramApiManager(messageAnswerQueue, token, url, "/webhook", port)
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