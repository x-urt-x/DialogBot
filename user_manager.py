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
        user = await self.loadUser(user_id)
        if user:
            logger.debug(LogZone.USERS, f"{user_id} user was in db")
            self._users[user_id] = user
            return user
        logger.debug(LogZone.USERS, f"{user_id} user was not find")
        user = User()
        await self._db.createUser(user_id,user)
        self._users[user_id] = user
        return user

    async def loadUser(self, user_id) -> User:
        return await self._db.getUser(user_id)

    async def setRole(self, user_id, role : Roles) -> bool:
        user = await self.getUser(user_id)
        if role not in user.availableRoles:
            return False
        self._db.setRole(user_id, role)
        self._users[user_id][role] = role
        return True