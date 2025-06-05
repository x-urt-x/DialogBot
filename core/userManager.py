from collections import deque
from typing import Any

from enums.languages import Language
from enums.roles import Roles
from data_base.IUserDB import IDataBase
from models.user import User
from zonelogger import logger, LogZone
from enums.apiIDs import ApiId
from core.userCache import UserCache

class UserManager:
    def __init__(self, db:IDataBase, cache_size):
        self._db : IDataBase = db
        self._users = UserCache(cache_size)

    async def getUserOrCreate(self, api:ApiId, ID) -> User:
        user = await self.getUser(api, ID)
        if user:
            return user
        logger.debug(LogZone.USERS, f"{api} {ID} user was not find")
        user = User(api, ID)
        await self._db.createUser(api, ID, UserManager.serialize(user.to_dict()))
        self._users[(api,ID)] = user
        return user

    async def getUser(self, api:ApiId, ID) -> User | None:
        user = self._users.get((api,ID))
        if user:
            logger.debug(LogZone.USERS, f"{api} {ID} user was in cache")
            return user
        userData = await self._db.getUserData(api, ID)
        if not userData:
            return None
        user = User(api, ID)
        deser_data = UserManager.deserialize(userData)
        user.from_dict(deser_data)
        logger.debug(LogZone.USERS, f"{api} {ID} user was in db")
        self._users[(api,ID)] = user
        return user

    async def save_users_dirty(self, user: User):
        dirty = user.get_dirty_fields()
        ser_dirty = UserManager.serialize(dirty)
        if dirty:
            await self._db.updateUserData(user.api,user.ID, ser_dirty, {})
            user.clear_dirty()

    async def setRoles(self, api:ApiId, ID, roles: Roles):
        if roles is None:
            return
        if roles == 0:
            logger.warning(LogZone.USERS, f"set no roles for {api}:{ID} user")
        user = await self.getUserOrCreate(api, ID)
        user._data["roles"] = roles
        user._setDirty("data", "roles")
        role = user.role
        if roles != 0:
            if not (roles & role):
                user.role = roles & -roles
        await self.save_users_dirty(user)
        self._users.remove((api, ID))

    def remove_user_from_cache(self, key: tuple):
        del self._users[key]

    def clear_user_cache(self):
        self._users.clear()

    def dump_user_cache(self) -> dict:
        return dict(self._users._cache)

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
