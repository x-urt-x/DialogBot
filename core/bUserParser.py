from enums.apiIDs import ApiId
from core.userManager import UserManager
from models.user import User
from models.bUser import BUser
from zonelogger import logger, LogZone
from enums.roles import Roles

class BUserParser:
    def __init__(self, user_manager: UserManager):
        self._user_manager = user_manager

    async def parse(self, bUser: BUser) -> User| None:
        bUserApi = bUser.api
        bUserId = bUser.user_id
        if not bUserId or bUserApi:
            logger.warning(LogZone.API_PROCES, f"")
        userId = f"{bUserApi.value}:{bUserId}"
        user = await self._user_manager.getUserOrCreate(userId)
        for key, value in bUser.data.items():
            user.api[key] = value
        if bUserApi == ApiId.CONSOLE:
            user["roles"] = user["roles"] | Roles.ADMIN
        return user