from core.dialogNodeHandlersManager import DialogNodeHandlersManager as dh
from core.handlerTypes import HandlerTypes as Ht
from enums.roles import Roles
from enums.languages import Language
from models.user import User
from core.userManager import UserManager



def changeRole(user: User, role: Roles):
    user.role = role
    if user.role == role:
        user.tmp["changedRole"] = True
    else:
        user.tmp["changedRole"] = False

@dh.reg(Ht.OPEN_USER, Language.ANY, "changeRoleToUser")
async def changeRoleToUser_handler(user: User, user_manager: UserManager):
    changeRole(user, Roles.USER)

@dh.reg(Ht.OPEN_USER, Language.ANY, "changeRoleToAdmin")
async def changeRoleToUser_handler(user: User, user_manager: UserManager):
    changeRole(user, Roles.ADMIN)

@dh.reg(Ht.OPEN_USER, Language.ANY, "changeRoleToSupport")
async def changeRoleToUser_handler(user: User, user_manager: UserManager):
    changeRole(user, Roles.SUPPORT)

@dh.reg(Ht.OPEN_SWITCH, Language.ANY, "changeRoleRes")
async def changeRoleRes_handler(tmp: dict, triggers: dict[str, int]):
    changedRole = tmp.get("changedRole")
    if changedRole:
        return triggers["allowed"]
    else:
        return triggers["forbidden"]


@dh.reg(Ht.OPEN_USER, Language.ANY, "toRu")
async def toRu_handler(user: User, user_manager: UserManager):
    user.lang = Language.RU
    user.dirty_force = True

@dh.reg(Ht.OPEN_USER, Language.ANY, "toEn")
async def toEn_handler(user: User, user_manager: UserManager):
    user.lang = Language.EN
    user.dirty_force = True

@dh.reg(Ht.OPEN_USER, Language.ANY, "toUa")
async def toUa_handler(user: User, user_manager: UserManager):
    user.lang = Language.EN #does not support yet
    user.dirty_force = True