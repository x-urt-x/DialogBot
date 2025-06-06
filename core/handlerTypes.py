from inspect import signature
from typing import Awaitable, Callable, Any
from enum import Enum
from typing import get_origin, get_args

class HandlerTypes(Enum):
    OPEN_SWITCH = "open_switch"
    INPUT_SWITCH = "input_switch"
    OPEN_TEXT = "open_text"
    INPUT_MSG = "input_msg"
    INPUT_PARSE = "input_parse"
    INPUT_USER = "input_user"
    OPEN_USER = "open_user"


HandlerSignatures: dict[HandlerTypes, list[type]] = {
    HandlerTypes.OPEN_SWITCH:  [dict, dict[str, int]],  # tmp, triggers
    HandlerTypes.INPUT_SWITCH: [dict, dict[str, int]],  # tmp, triggers
    HandlerTypes.OPEN_TEXT:    [str],   # text
    HandlerTypes.INPUT_MSG:    ['Message'],  # msg
    HandlerTypes.INPUT_PARSE:  ['Message'],  # msg
    HandlerTypes.INPUT_USER:   ['User', 'UserManager'], # user, user_manager
    HandlerTypes.OPEN_USER:    ['User', 'UserManager'], # user, user_manager
}


def validate_handler(fn: Callable[..., Awaitable[Any]], handler_type: HandlerTypes):
    expected_types = HandlerSignatures[handler_type]
    sig = signature(fn)
    params = list(sig.parameters.values())

    if len(params) != len(expected_types):
        raise TypeError(f"{handler_type.value} handler must take exactly {len(expected_types)} arguments")

    for i, (param, expected_type) in enumerate(zip(params, expected_types)):
        ann = param.annotation
        if isinstance(expected_type, str):
            expected_name = expected_type
            if ann.__name__ != expected_name:
                raise TypeError(f"Argument {i+1} of {handler_type.value} handler must be '{expected_name}', got '{ann.__name__}'")
        elif not (get_origin(ann) == get_origin(expected_type) and get_args(ann) == get_args(expected_type)):
            raise TypeError(f"Argument {i+1} of {handler_type.value} handler must be {expected_type}, got {ann}")

HandlerValidators: dict[HandlerTypes, Callable[[Callable[..., Awaitable[Any]]], None]] = {
    ht: (lambda ht=ht: lambda fn: validate_handler(fn, ht))()
    for ht in HandlerTypes
}
