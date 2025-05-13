from roles import Roles
import IDataBase
from user import User
from zonelogger import logger, LogZone

class UserManager:
    _users = {}
    def __init__(self, db:IDataBase):
        self._db : IDataBase = db

    async def getUser(self, user_id) -> User:
        if user_id in self._users:
            logger.debug(LogZone.USERS, f"{user_id} user was in cache")
            return self._users[user_id]
        user = await self._db.getUser(user_id)
        if user:
            logger.debug(LogZone.USERS, f"{user_id} user was in db")
            self._users[user_id] = user
            return user
        logger.debug(LogZone.USERS, f"{user_id} user was not find")
        user = User(user_id)
        await self._db.createUser(user_id,user.to_dict())
        self._users[user_id] = user
        return user

    async def setRole(self, user_id, role : Roles) -> bool:
        user = await self.getUser(user_id)
        if role not in user["availableRoles"]:
            return False
        self._db.setRole(user_id, role)
        self._users[user_id][role] = role
        return True

    async def save_user(self, user_id, user: User):
        dirty = user.get_dirty_fields()
        if dirty:
            await self._db.updateUserData(user_id, dirty)
            user.clear_dirty()