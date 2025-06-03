from encodings.uu_codec import uu_encode

from core.dialogNodeHandlersManager import DialogNodeHandlersManager as dh
from core.handlerTypes import HandlerTypes
from enums.roles import Roles
from zonelogger import LogZone, logger
from enums.languages import Language
from models.user import User
from core.userManager import UserManager
from models.message import MessageView
from enums.apiIDs import ApiId

@dh.reg(HandlerTypes.CMD, Language.EN, "hi")
async def hi_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    logger.info(LogZone.DIALOG_HANDLERS, f"hi from user {user.ID}")

@dh.reg(HandlerTypes.CMD, Language.ANY, "changeRoleToUser")
async def changeRoleToUser_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    user.role = Roles.USER
    if user.role == Roles.USER:
        return triggers.get("allowed")
    else:
        return triggers.get("forbidden")

@dh.reg(HandlerTypes.CMD, Language.ANY, "changeRoleToAdmin")
async def changeRoleToUser_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    user.role = Roles.ADMIN
    if user.role == Roles.ADMIN:
        return triggers.get("allowed")
    else:
        return triggers.get("forbidden")

@dh.reg(HandlerTypes.CMD, Language.ANY, "changeRoleToSupport")
async def changeRoleToUser_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    user.role = Roles.SUPPORT
    if user.role == Roles.SUPPORT:
        return triggers.get("allowed")
    else:
        return triggers.get("forbidden")

@dh.reg(HandlerTypes.FREE_INPUT, Language.ANY, "setRolesUser")
async def setRolesUsers_input_handler(user: dict, msg: MessageView) -> dict | None:
    user_input = msg.text
    try:
        parts = user_input.strip().split()
        api_str = parts[0].lower()
        ID = parts[1]
        return {"setRoleUserApi":api_str,"setRoleUserID": ID}
    except Exception:
        logger.info(LogZone.DIALOG_HANDLERS, f"invalid input string: {user_input!r}")
        return None

@dh.reg(HandlerTypes.CMD_EXIT, Language.ANY, "setRolesUser")
async def setRolesUsers_cmdExit_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    setRoleUserApi = user.tmp.get("setRoleUserApi")
    setRoleUserID = user.tmp.get("setRoleUserID")
    logger.debug(LogZone.DIALOG_HANDLERS, f"setRoleUserApi: {setRoleUserApi} setRoleUserID: {setRoleUserID}")
    if not setRoleUserApi or not setRoleUserID:
        logger.info(LogZone.DIALOG_HANDLERS, f"Missing setRoleUserApi or setRoleUserId in user: {user.ID}")
        user.tmp.pop("setRoleUserApi", None)
        user.tmp.pop("setRoleUserID", None)
        return triggers["bad"]
    try:
        api_id = ApiId(setRoleUserApi.lower())
    except ValueError:
        logger.info(LogZone.DIALOG_HANDLERS, f"Invalid API: {setRoleUserApi}")
        return triggers["bad"]

    setRoleUser = await user_manager.getUser(api_id, setRoleUserID)
    user.tmp.pop("setRoleUserApi", None)
    user.tmp.pop("setRoleUserID", None)
    if setRoleUser is None:
        logger.info(LogZone.DIALOG_HANDLERS, f"User not found: {setRoleUserApi} {setRoleUserID}")
        return triggers["bad"]
    user.tmp["setRoleUser"] = setRoleUser
    return triggers["good"]

@dh.reg(HandlerTypes.FREE_INPUT, Language.ANY, "setRolesRole")
async def setRolesRoles_input_handler(user: dict, msg: MessageView) -> dict | None:
    bit_str = msg.text
    if not all(c in '01' for c in bit_str):
        logger.info(LogZone.USERS, f"Invalid role bit string (invalid characters): {bit_str}")
        return None

    if len(bit_str) != len(Roles):
        logger.info(LogZone.USERS, f"Invalid role bit string length: {bit_str} (expected {len(Roles)} bits)")
        return None

    bit_str = bit_str[::-1]  # reverse: LSB on the right
    bitmask = 0
    for i, char in enumerate(bit_str):
        if char == '1':
            bitmask |= (1 << i)
    return {"setRoleUserRoles":bitmask}

@dh.reg(HandlerTypes.CMD_EXIT, Language.ANY, "setRolesRole")
async def setRolesRoles_cmdExit_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    setRoleUser = user.tmp.get("setRoleUser")
    setRoleUserRoles = user.tmp.get("setRoleUserRoles")
    if not setRoleUser or not setRoleUserRoles:
        user.tmp.pop("setRoleUser", None)
        user.tmp.pop("setRoleUserRoles", None)
        return triggers["bad"]
    await user_manager.setRoles(setRoleUser.api, setRoleUser.ID, setRoleUserRoles)
    user.tmp.pop("setRoleUser", None)
    user.tmp.pop("setRoleUserRoles", None)
    return triggers["good"]

@dh.reg(HandlerTypes.CMD, Language.ANY, "toRu")
async def toRu_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    user.lang = Language.RU
    await user_manager.save_users_dirty(user)
    return 0

@dh.reg(HandlerTypes.CMD, Language.ANY, "toEn")
async def toEn_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    user.lang = Language.EN
    await user_manager.save_users_dirty(user)
    return 0

@dh.reg(HandlerTypes.CMD, Language.ANY, "toUa")
async def toUa_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    user.lang = Language.EN #does not support yet
    await user_manager.save_users_dirty(user)
    return 0