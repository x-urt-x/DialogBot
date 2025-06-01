from motor.motor_asyncio import AsyncIOMotorClient
from enums.roles import Roles
from IUserDB import IDataBase
from pymongo.errors import PyMongoError
from zonelogger import logger, LogZone
from models.user import User

class MongoUserDB(IDataBase):
    def __init__(self, connection_string, db_name):
        self._client = AsyncIOMotorClient(connection_string)
        self._db = self._client[db_name]
        self._users = self._db["users"]
        self._massages = self._db["massages"]

    async def getUser(self, user_id) -> User | None:
        try:
            data = await self._users.find_one({"user_id": user_id})
        except PyMongoError as e:
            logger.error(LogZone.DB, f"cant get {user_id} user: {e}")
            return None
        if data is None:
            logger.info(LogZone.DB, f"user {user_id} not in db")
            return None
        user = User(user_id)
        user.from_dict(dict(data))
        return user

    async def setRole(self, user_id, role: Roles) -> bool:
        if not isinstance(role, Roles):
            logger.error(LogZone.DB,"bad role to set")
            return False
        try:
            result = await self._users.update_one(
                {"user_id": user_id},
                {"$set": {"role": role.name}},
                upsert=False
            )
            if result.matched_count == 0:
                logger.error(LogZone.DB, f"cant find {user_id} user to set role")
                return False
            return True
        except PyMongoError as e:
            logger.error(LogZone.DB, f"cant update role: {e}")
            return False

    async def createUser(self, user_id, data):
        try:
            existing = await self._users.find_one({"user_id": user_id})
            if existing:
                return False
            data["user_id"] = user_id
            result = await self._users.insert_one(data)
            return result.acknowledged
        except PyMongoError as e:
            logger.error(LogZone.DB, f"cant create user: {e}")
            return False

    async def updateUserData(self, user_id, data: dict):
        if not data:
            return
        await self._users.update_one(
            {"user_id": user_id},
            {"$set": data}
        )
