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
        bUserId = bUser.ID
        if not bUserId or not bUserApi:
            logger.warning(LogZone.API_PROCES, f" miss api {bUserApi} or ID {bUserId} on parsing")
            return None
        user = await self._user_manager.getUserOrCreate(bUserApi, bUserId)
        for key, value in bUser.data.items():
            if key == "id": continue
            user.apiDataSet(key, value)
        if bUserApi == ApiId.CONSOLE and not (user.roles & Roles.ADMIN):
            await self._user_manager.setRoles(bUserApi, bUserId, user.roles | Roles.ADMIN)
        return user