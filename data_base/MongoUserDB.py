from motor.motor_asyncio import AsyncIOMotorClient
from enums.apiIDs import ApiId
from data_base.IUserDB import IDataBase
from pymongo.errors import PyMongoError
from bson.errors import InvalidDocument
from zonelogger import logger, LogZone

class MongoUserDB(IDataBase):
    def __init__(self, connection_string, db_name):
        self._client = AsyncIOMotorClient(connection_string)
        self._db = self._client[db_name]
        self._users = self._db["users"]
        self._massages = self._db["massages"]

    async def getUserData(self, api: ApiId, ID)-> dict | None:
        user_api_id = f"{api.value}:{ID}"
        try:
            data = await self._users.find_one({"api_id": user_api_id})
        except PyMongoError as e:
            logger.error(LogZone.DB, f"cant get {user_api_id} user: {e}")
            return None
        if data is None:
            logger.info(LogZone.DB, f"user {user_api_id} not in db")
            return None
        return data

    async def createUser(self, api: ApiId, ID, data : dict):
        user_api_id = f"{api.value}:{ID}"
        try:
            existing = await self._users.find_one({"api_id": user_api_id})
            if existing:
                return False
            data["api_id"] = user_api_id
            result = await self._users.insert_one(data)
            return result.acknowledged
        except PyMongoError as e:
            logger.error(LogZone.DB, f"cant create user: {e}")
            return False
        except InvalidDocument as e:
            logger.error(LogZone.DB, f"cannot encode object: {e}")

    async def updateUserData(self, api: ApiId, ID, set_data: dict, unset_data: dict):
        user_api_id = f"{api.value}:{ID}"
        if not set_data and not unset_data:
            return

        update: dict = {}
        if set_data:
            update["$set"] = MongoUserDB.flatten_dict(set_data)
        if unset_data:
            update["$unset"] = MongoUserDB.flatten_dict(unset_data)

        await self._users.update_one(
            {"api_id": user_api_id},
            update
        )

    @staticmethod
    def flatten_dict(d: dict, parent_key: str = '', sep: str = '.') -> dict:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(MongoUserDB.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)