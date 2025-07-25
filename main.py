from data_base.MongoUserDB import MongoUserDB
from core.dialogNodeHandlersManager import DialogNodeHandlersManager
from core.userManager import UserManager
from core.userRepository import UserRepository
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
    user_repository = UserRepository(userDB)
    user_manager = UserManager(user_repository, config["cache"]["size"], config["cache"]["save_interval"])

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
    user_manager.run_sync_loop()
    await apiManager.run_all()
    tasks = [
        asyncio.create_task(apiManager.loop(), name="apiManagerLoop"),
        asyncio.create_task(message_manager.loop(), name="messageManagerLoop"),
        asyncio.create_task(apiSendManager.loop(), name="apiSendManagerLoop"),
    ]
    print("Telegram API started. Press Ctrl+C to stop.")
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("Shutting down...")
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        await apiManager.stop_all()
        await user_manager.stop_sync_loop()


if __name__ == "__main__":
    asyncio.run(main())