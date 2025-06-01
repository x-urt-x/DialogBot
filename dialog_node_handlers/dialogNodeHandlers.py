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

@dh.reg(HandlerTypes.FREE_INPUT, Language.EN, "setRolesUser")
async def setRolesUsers_input_handler(user: dict, msg: MessageView) -> dict | None:
    user_input = msg.text
    try:
        parts = user_input.strip().split()
        api_str = parts[0].lower()
        user_id_raw = parts[1]
        return {"setRoleUserApi":api_str,"setRoleUserIdRaw": user_id_raw}
    except Exception:
        logger.info(LogZone.DIALOG_HANDLERS, f"invalid input string: {user_input!r}")
        return None

@dh.reg(HandlerTypes.CMD_EXIT, Language.EN, "setRolesUser")
async def setRolesUsers_cmdExit_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    setRoleUserApi = user["setRoleUserApi"]
    setRoleUserIdRaw = user["setRoleUserIdRaw"]
    logger.debug(LogZone.DIALOG_HANDLERS, f"setRoleUserApi: {setRoleUserApi} setRoleUserIdRaw: {setRoleUserIdRaw}")
    if not setRoleUserApi or not setRoleUserIdRaw:
        logger.info(LogZone.DIALOG_HANDLERS, f"Missing setRoleUserApi or setRoleUserId in user: {user.getId()}")
        return triggers["bad"]
    try:
        api_id = ApiId(setRoleUserApi.lower())
    except ValueError:
        logger.info(LogZone.DIALOG_HANDLERS, f"Invalid API: {setRoleUserApi}")
        return triggers["bad"]
    setRoleUserId = f"{api_id.value}:{setRoleUserIdRaw}"
    setRoleUser = await user_manager.getUser(setRoleUserId)
    if setRoleUser is None:
        logger.info(LogZone.DIALOG_HANDLERS, f"User not found: {setRoleUserId}")
        return triggers["bad"]
    user["setRoleUserId"] = setRoleUserId
    return triggers["good"]

@dh.reg(HandlerTypes.FREE_INPUT, Language.EN, "setRolesRole")
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

@dh.reg(HandlerTypes.CMD_EXIT, Language.EN, "setRolesRole")
async def setRolesRoles_cmdExit_handler(user: User, user_manager: UserManager, triggers: dict[str, int]):
    setRoleUserId = user["setRoleUserId"]
    setRoleUserRoles = user["setRoleUserRoles"]
    if setRoleUserId and setRoleUserRoles:
        await user_manager.setRoles(setRoleUserId, setRoleUserRoles)
        return triggers["good"]
    else:
        return triggers["bad"]