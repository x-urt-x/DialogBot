from operator import truediv

from roles import Roles
from IUserDB import IDataBase
from user import User
from zonelogger import logger, LogZone

class UserManager:
    _users = {}
    def __init__(self, db:IDataBase):
        self._db : IDataBase = db

    async def getUserOrCreate(self, user_id) -> User:
        user = await self.getUser(user_id)
        if user:
            return user
        logger.debug(LogZone.USERS, f"{user_id} user was not find")
        user = User(user_id)
        await self._db.createUser(user_id,user.to_dict())
        self._users[user_id] = user
        return user

    async def getUser(self, user_id) -> User | None:
        if user_id in self._users:
            logger.debug(LogZone.USERS, f"{user_id} user was in cache")
            return self._users[user_id]
        user = await self._db.getUser(user_id)
        if user:
            logger.debug(LogZone.USERS, f"{user_id} user was in db")
            self._users[user_id] = user
            return user

    async def setRole(self, user_id, role : Roles) -> bool:
        user = await self.getUserOrCreate(user_id)
        if not (user["roles"] & role):
            return False
        await self._db.setRole(user_id, role)
        self._users[user_id]["role"] = role
        return True

    async def save_users_dirty(self, user: User):
        dirty = user.get_dirty_fields()
        if dirty:
            await self._db.updateUserData(user.getId(), dirty)
            user.clear_dirty()

    async def setRoles(self, user_id, roles: Roles):
        if roles is None:
            return
        if roles == 0:
            logger.warning(LogZone.USERS, f"set no roles for {user_id} user")
        user = await self.getUserOrCreate(user_id)
        user["roles"] = roles
        role = user["role"]
        if roles != 0:
            if not (roles & role):
                user["role"] = roles & -roles
        await self.save_users_dirty(user)