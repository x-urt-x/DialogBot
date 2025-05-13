from zonelogger import logger, LogZone
from dialog_node_handlers_manager import handler_registry, load_dialog_node_handlers
from dialogs_loader import YAMLLoader
from user_manager import UserManager, User
from mongoDB_manager import MongoDb
from api_ids import ApiId
import asyncio

async def main():
    logger.enable_zone(LogZone.USERS)
    logger.enable_zone(LogZone.DB)
    logger.enable_zone(LogZone.MAIN)
    load_dialog_node_handlers()
    logger.info(LogZone.MAIN, handler_registry)
    en_dialogs = YAMLLoader()
    en_dialogs.load_folder("dialogs/en")
    mongoDB = MongoDb("localhost:27017")
    user_manager = UserManager(mongoDB)

    user_id_1 = "111"
    user1: User = await user_manager.getUser(user_id_1)
    #user1["name"] = "test name"
    await user_manager.save_user(user_id_1, user1)
    user2: User = await user_manager.getUser("222")
    logger.info(LogZone.MAIN, user1.to_dict())
    logger.info(LogZone.MAIN, user2.to_dict())

if __name__ == "__main__":
    asyncio.run(main())
