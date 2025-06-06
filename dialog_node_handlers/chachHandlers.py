from models.message import Message
from enums.apiIDs import ApiId
from core.dialogNodeHandlersManager import DialogNodeHandlersManager as dh
from core.handlerTypes import HandlerTypes as Ht
from zonelogger import LogZone, logger
from enums.languages import Language
from models.user import User
from core.userManager import UserManager
from enums.roles import Roles

@dh.reg(Ht.INPUT_PARSE, Language.ANY, "clearCache")
async def clearCache_input_parse_handler(msg: Message):
    user_input = msg.text
    try:
        parts = user_input.strip().split()
        api_str = parts[0].lower()
        ID = parts[1]
        return {"clearCacheApi": api_str, "clearCacheID": ID}
    except Exception:
        logger.info(LogZone.DIALOG_HANDLERS, f"invalid input string: {user_input!r}")
        return None

@dh.reg(Ht.INPUT_USER, Language.ANY, "clearCache")
async def clearCache_input_user_handler(user: User, user_manager: UserManager):
    api_str = user.tmp.pop("clearCacheApi", None)
    ID = user.tmp.pop("clearCacheID", None)

    if not api_str or not ID:
        logger.info(LogZone.DIALOG_HANDLERS, "Missing clearCacheApi or clearCacheID")
        return

    try:
        api = ApiId(api_str)
    except ValueError:
        logger.info(LogZone.DIALOG_HANDLERS, f"Invalid API: {api_str}")
        return

    target_user = await user_manager.getUser(api, ID)
    if target_user:
        user_manager.remove_user_from_cache((api, ID))
        user.tmp["clearCacheDone"] = True
    else:
        logger.info(LogZone.DIALOG_HANDLERS, f"User not found for cache clear: {api_str} {ID}")

@dh.reg(Ht.INPUT_SWITCH, Language.ANY, "clearCache")
async def clearCache_input_switch_handler(tmp: dict, triggers: dict[str, int]):
    if tmp.pop("clearCacheDone", False):
        return triggers["good"]
    return triggers["bad"]
