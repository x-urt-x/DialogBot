from models.message import Message
from enums.apiIDs import ApiId
from core.dialogNodeHandlersManager import DialogNodeHandlersManager as dh
from core.handlerTypes import HandlerTypes as Ht
from zonelogger import LogZone, logger
from enums.languages import Language
from models.user import User
from core.userManager import UserManager
from enums.roles import Roles


@dh.reg(Ht.INPUT_PARSE, Language.ANY, "setRoleUser")
async def setRoleUser_input_parse_handler(msg: Message):
    user_input = msg.text
    try:
        parts = user_input.strip().split()
        api_str = parts[0].lower()
        ID = parts[1]
        return {"setRoleUserApi":api_str,"setRoleUserID": ID}
    except Exception:
        logger.info(LogZone.DIALOG_HANDLERS, f"invalid input string: {user_input!r}")
        return None

@dh.reg(Ht.INPUT_USER, Language.ANY, "setRoleUser")
async def setRoleUser_input_user_handler(user: User, user_manager: UserManager):
    setRoleUserApi = user.tmp.get("setRoleUserApi")
    setRoleUserID = user.tmp.get("setRoleUserID")
    user.tmp.pop("setRoleUserApi", None)
    user.tmp.pop("setRoleUserID", None)
    logger.debug(LogZone.DIALOG_HANDLERS, f"setRoleUserApi: {setRoleUserApi} setRoleUserID: {setRoleUserID}")
    if not setRoleUserApi or not setRoleUserID:
        logger.info(LogZone.DIALOG_HANDLERS, f"Missing setRoleUserApi or setRoleUserId in user: {user.ID}")
    try:
        api = ApiId(setRoleUserApi.lower())
    except ValueError:
        logger.info(LogZone.DIALOG_HANDLERS, f"Invalid API: {setRoleUserApi}")
    setRoleUser = await user_manager.getUser(api, setRoleUserID)

    if setRoleUser is None:
        logger.info(LogZone.DIALOG_HANDLERS, f"User not found: {setRoleUserApi} {setRoleUserID}")
    user.tmp["setRoleUser"] = setRoleUser

@dh.reg(Ht.INPUT_SWITCH, Language.ANY, "setRoleUser")
async def setRoleUser_input_switch_handler(tmp: dict, triggers: dict[str, int]):
    setRoleUser = tmp.get("setRoleUser")
    if setRoleUser:
        return triggers["good"]
    else:
        return triggers["bad"]

@dh.reg(Ht.INPUT_PARSE, Language.ANY, "setRoleRole")
async def setRoleRole_input_parse_handler(msg: Message):
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
    return {"setRoleUserRoles": bitmask}

@dh.reg(Ht.INPUT_USER, Language.ANY, "setRoleRole")
async def setRoleRole_input_user_handler(user: User, user_manager: UserManager):
    setRoleUser = user.tmp.get("setRoleUser")
    setRoleUserRoles = user.tmp.get("setRoleUserRoles")
    user.tmp.pop("setRoleUser", None)
    user.tmp.pop("setRoleUserRoles", None)
    if not setRoleUser or not setRoleUserRoles:
        return
    await user_manager.setRoles(setRoleUser.api, setRoleUser.ID, setRoleUserRoles)
    user.tmp["setRoleDone"] = True

@dh.reg(Ht.INPUT_SWITCH, Language.ANY, "setRoleRole")
async def setRoleRole_input_switch_handler(tmp: dict, triggers: dict[str, int]):
    setRoleDone = tmp.get("setRoleDone")
    if setRoleDone:
        return triggers["good"]
    else:
        return triggers["bad"]