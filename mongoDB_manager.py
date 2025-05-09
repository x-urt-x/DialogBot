from motor.motor_asyncio import AsyncIOMotorClient
from roles import Roles
from IDataBase import IDataBase
from pymongo.errors import PyMongoError
from zonelogger import logger, LogZone

class MongoDb(IDataBase):
    def __init__(self, connection_string):
        self._client = AsyncIOMotorClient(connection_string)
        self._db = self._client["dialog_bot"]
        self._users = self._db["users"]
        self._massages = self._db["massages"]

    async def getUser(self, user_id):
        try:
            result = await self._users.find_one({"user_id": user_id})
            return result
        except PyMongoError as e:
            logger.info(LogZone.DB, f"cant get {user_id} user: {e}")
            return None

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

    async def createUser(self, user_id, user):
        try:
            existing = await self._users.find_one({"user_id": user_id})
            if existing:
                return False
            user_data = {
                "user_id": user_id,
                "role": user.role.value,
                "availableRoles": [role.value for role in getattr(user, "availableRoles", [Roles.USER])],
                "fields": {api_id.value: val for api_id, val in user.tmp_fields.items()}
            }
            result = await self._users.insert_one(user_data)
            return result.acknowledged
        except PyMongoError as e:
            logger.error(LogZone.DB, f"cant create user: {e}")
            return False
