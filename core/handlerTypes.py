from enum import Enum
from typing import Callable, Awaitable, Any
from inspect import signature
from core.userManager import UserManager
from models.user import User
from models.message import MessageView

class HandlerTypes(Enum):
    CMD = "cmd"                    # async def(user: User, user_manager: UserManager, cmd_triggers: dict[str, int]) -> int | None
    ANSWER = "answer"              # async def(user: dict, msg: str) -> str
    MESSAGE_PREPROCESS = "preprocess"  # async def(user: dict, msg: MessageView) -> None
    FREE_INPUT = "free_input"      # async def(user: dict, msg: MessageView) -> (dict | None, int | None)
    CMD_EXIT = "cmd_exit"          # async def(user: User, user_manager: UserManager, cmd_triggers: dict[str, int]) -> int | None


def validate_cmd(fn: Callable[..., Awaitable[Any]]):
    sig = signature(fn)
    params = list(sig.parameters.values())
    if len(params) != 3:
        raise TypeError("Cmd handler must take exactly three arguments: (user: User, user_manager: UserManager, cmd_triggers: dict[str, int])")
    if params[0].annotation is not User:
        raise TypeError("First argument of Cmd handler must be of type 'User'")
    if params[1].annotation is not UserManager:
        raise TypeError("Second argument of Cmd handler must be of type 'UserManager'")
    if params[2].annotation != dict[str, int]:
        raise TypeError("Third argument of Cmd handler must be of type 'dict[str, int]'")


def validate_answer(fn: Callable[..., Awaitable[Any]]):
    sig = signature(fn)
    params = list(sig.parameters.values())
    if len(params) != 2:
        raise TypeError("Answer handler must take exactly two arguments: (user: dict, msg: str)")
    if params[0].annotation != dict:
        raise TypeError("First argument of Answer handler must be of type 'dict'")
    if params[1].annotation is not str:
        raise TypeError("Second argument of Answer handler must be of type 'str'")


def validate_preprocess(fn: Callable[..., Awaitable[Any]]):
    sig = signature(fn)
    params = list(sig.parameters.values())
    if len(params) != 2:
        raise TypeError("MessagePreprocess handler must take exactly two arguments: (user: dict, msg: MessageView)")
    if params[0].annotation != dict:
        raise TypeError("First argument of MessagePreprocess handler must be of type 'dict'")
    if params[1].annotation is not MessageView:
        raise TypeError("Second argument of MessagePreprocess handler must be of type 'MessageView'")


def validate_free_input(fn: Callable[..., Awaitable[Any]]):
    sig = signature(fn)
    params = list(sig.parameters.values())
    if len(params) != 2:
        raise TypeError("FreeInput handler must take exactly three arguments: (user: dict, msg: MessageView, cmd_triggers: dict[str, int])")
    if params[0].annotation != dict:
        raise TypeError("First argument of FreeInput handler must be of type 'User'")
    if params[1].annotation is not MessageView:
        raise TypeError("Second argument of FreeInput handler must be of type 'MessageView'")

HandlerValidators: dict[HandlerTypes, Callable[[Callable[..., Awaitable[Any]]], None]] = {
    HandlerTypes.CMD: validate_cmd,
    HandlerTypes.ANSWER: validate_answer,
    HandlerTypes.MESSAGE_PREPROCESS: validate_preprocess,
    HandlerTypes.FREE_INPUT: validate_free_input,
    HandlerTypes.CMD_EXIT: validate_cmd
}
