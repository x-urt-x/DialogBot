from data_base.IUserDB import IDataBase
from models.user import User
from zonelogger import logger, LogZone
from enums.apiIDs import ApiId
from enums.languages import Language
from enums.roles import Roles
from typing import Any
from collections import deque

class UserRepository:
    def __init__(self, db:IDataBase):
        self._db : IDataBase = db

    async def createUser(self, api:ApiId, ID) -> User:
        user = User(api, ID)
        await self._db.createUser(api, ID, UserRepository.serialize(user.to_dict()))
        return user

    async def getUserDB(self, api:ApiId, ID) -> User | None:
        userData = await self._db.getUserData(api, ID)
        if not userData:
            return None
        user = User(api, ID)
        deser_data = UserRepository.deserialize(userData)
        user.from_dict(deser_data)
        logger.debug(LogZone.USERS, f"{api} {ID} user was in db")
        return user

    async def saveUserDirty(self, user: User):
        dirty = user.get_dirty_fields()
        if dirty:
            ser_dirty = UserRepository.serialize(dirty)
            await self._db.updateUserData(user.api,user.ID, ser_dirty, {})
            if dirty.get("data", {}).get("stack", None) is not None:
                user.fixCurrentStack()


    @staticmethod
    def serialize(raw: dict[str, Any]) -> dict[str, Any]:
        def serializeIn(obj: Any) -> Any:
            if isinstance(obj, (ApiId, Language)):
                return obj.value
            elif isinstance(obj, Roles):
                return int(obj)
            elif isinstance(obj, deque):
                return list(obj)
            elif isinstance(obj, dict):
                return {k: serializeIn(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serializeIn(v) for v in obj]
            return obj

        return {k: serializeIn(v) for k, v in raw.items()}

    @staticmethod
    def deserialize(raw: dict[str, Any]) -> dict[str, Any]:
        def deserializeIn(key: str, obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: deserializeIn(k, v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [deserializeIn(key, v) for v in obj]

            if key == "api" and isinstance(obj, str):
                return ApiId(obj)
            if key == "lang" and isinstance(obj, str):
                return Language(obj)
            if key in ("roles", "role") and isinstance(obj, int):
                return Roles(obj)
            if key == "stack" and isinstance(obj, list):
                return deque(obj)
            return obj

        return {k: deserializeIn(k, v) for k, v in raw.items()}