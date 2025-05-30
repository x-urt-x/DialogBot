from dialog_node_handlers_manager import DialogNodeHandlersManager as dh
from handlerTypes import HandlerTypes
from roles import Roles
from zonelogger import LogZone, logger
from languages import Language
from user import User
from user_manager import UserManager

@dh.reg(HandlerTypes.CMD, Language.EN, "hi")
async def hi_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    logger.info(LogZone.DIALOG_HANDLERS, f"hi from user {user.getId()}")

@dh.reg(HandlerTypes.CMD, Language.EN, "changeRoleToUser")
async def changeRoleToUser_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    res = await user_manager.setRole(user.getId(), Roles.USER)
    if res:
        return triggers.get("allowed")
    else:
        return triggers.get("forbidden")

@dh.reg(HandlerTypes.CMD, Language.EN, "changeRoleToAdmin")
async def changeRoleToUser_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    res = await user_manager.setRole(user.getId(), Roles.ADMIN)
    if res:
        return triggers.get("allowed")
    else:
        return triggers.get("forbidden")

@dh.reg(HandlerTypes.CMD, Language.EN, "changeRoleToSupport")
async def changeRoleToUser_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    res = await user_manager.setRole(user.getId(), Roles.SUPPORT)
    if res:
        return triggers.get("allowed")
    else:
        return triggers.get("forbidden")