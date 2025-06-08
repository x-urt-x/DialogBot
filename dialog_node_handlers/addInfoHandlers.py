from models.message import Message
from enums.apiIDs import ApiId
from core.dialogNodeHandlersManager import DialogNodeHandlersManager as dh
from core.handlerTypes import HandlerTypes as Ht
from zonelogger import LogZone, logger
from enums.languages import Language
from models.user import User
from core.userManager import UserManager
from enums.roles import Roles

@dh.reg(Ht.INPUT_PARSE, Language.ANY,"enterName")
async def enterName_input_parser_handler(msg:Message):
    input_text = msg.text
    if len(input_text) > 2:
        return {"enterName":input_text.strip()}
    return {}

@dh.reg(Ht.INPUT_USER, Language.ANY, "enterName")
async def enterName_input_user_handler(user: User, user_manager: UserManager):
    name = user.tmp.pop("enterName")
    if name:
        user.infoDataSet("name", name)
        user.dirty_force = True
        user.tmp["enterNameDone"] = True

@dh.reg(Ht.INPUT_SWITCH, Language.ANY, "enterName")
async def enterName_input_switch_handler(tmp:dict,triggers:dict[str,int]):
    done = tmp.pop("enterNameDone")
    if done:
        return triggers["good"]
    return triggers["bad"]

@dh.reg(Ht.INPUT_PARSE, Language.ANY, "enterSurName")
async def enterSurName_input_parser_handler(msg: Message):
    input_text = msg.text
    if len(input_text) > 2:
        return {"enterSurName": input_text.strip()}
    return {}

@dh.reg(Ht.INPUT_USER, Language.ANY, "enterSurName")
async def enterSurName_input_user_handler(user: User, user_manager: UserManager):
    surname = user.tmp.pop("enterSurName", None)
    if surname:
        user.infoDataSet("surname", surname)
        user.dirty_force = True
        user.tmp["enterSurNameDone"] = True

@dh.reg(Ht.INPUT_SWITCH, Language.ANY, "enterSurName")
async def enterSurName_input_switch_handler(tmp: dict, triggers: dict[str, int]):
    done = tmp.pop("enterSurNameDone", False)
    return triggers["good"] if done else triggers["bad"]

@dh.reg(Ht.INPUT_PARSE, Language.ANY, "enterLastName")
async def enterLastName_input_parser_handler(msg: Message):
    input_text = msg.text
    if len(input_text) > 2:
        return {"enterLastName": input_text.strip()}
    return {}

@dh.reg(Ht.INPUT_USER, Language.ANY, "enterLastName")
async def enterLastName_input_user_handler(user: User, user_manager: UserManager):
    lastname = user.tmp.pop("enterLastName", None)
    if lastname:
        user.infoDataSet("lastname", lastname)
        user.dirty_force = True
        user.tmp["enterLastNameDone"] = True

@dh.reg(Ht.INPUT_SWITCH, Language.ANY, "enterLastName")
async def enterLastName_input_switch_handler(tmp: dict, triggers: dict[str, int]):
    done = tmp.pop("enterLastNameDone", False)
    return triggers["good"] if done else triggers["bad"]