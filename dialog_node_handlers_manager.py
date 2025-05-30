from typing import Callable, Type, Awaitable, Any
from inspect import iscoroutinefunction
from collections import defaultdict
from importlib import import_module
import pkgutil
from handlerTypes import HandlerTypes, HandlerValidators
from languages import Language
from zonelogger import LogZone, logger


class DialogNodeHandlersManager:
    _instance: "DialogNodeHandlersManager" = None
    _buffered_registrations: list[tuple[HandlerTypes, Language, str, Callable[..., Awaitable[Any]]]] = []

    def __new__(cls, *args, **kwargs) -> "DialogNodeHandlersManager":
        if cls._instance is not None:
            raise RuntimeError("HandlerManager already created. Create it only once in main()")
        cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, handler_package: str):
        self._registry: dict[HandlerTypes, dict[Language, dict[str, Callable[..., Awaitable[Any]]]]] = defaultdict(lambda: defaultdict(dict))
        self._handler_package = handler_package
        self._autoload_handlers()
        self._process_buffer()

    @classmethod
    def reg(cls, handler_type: HandlerTypes, lang: Language, id_: str) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            if not iscoroutinefunction(fn):
                raise TypeError(f"Handler '{id_}' must be async")

            if cls._instance is not None:
                validator = HandlerValidators.get(handler_type)
                if validator:
                    validator(fn)
                cls._instance._register(handler_type, lang, id_, fn)
            else:
                cls._buffered_registrations.append((handler_type, lang, id_, fn))

            return fn
        return decorator

    def _register(self, handler_type: HandlerTypes, lang: Language, id_: str, fn: Callable[..., Awaitable[Any]]) -> None:
        if id_ in self._registry[handler_type][lang]:
            logger.warning(
                LogZone.DIALOG_HANDLERS,
                f"Handler '{id_}' already registered for {lang} and {handler_type.__name__}"
            )
        self._registry[handler_type][lang][id_] = fn

    def get_all(self) -> dict[HandlerTypes, dict[Language, dict[str, Callable[..., Awaitable[Any]]]]]:
        return self._registry

    def _process_buffer(self) -> None:
        for handler_type, lang, id_, fn in self._buffered_registrations:
            self._register(handler_type, lang, id_, fn)
        self._buffered_registrations.clear()

    def _autoload_handlers(self) -> None:
        try:
            root = import_module(self._handler_package)
            for _, modname, ispkg in pkgutil.iter_modules(root.__path__):
                if not ispkg and not modname.startswith("_"):
                    import_module(f"{self._handler_package}.{modname}")
        except Exception as e:
            logger.warning(LogZone.DIALOG_HANDLERS, f"Failed to autoload handlers: {e}")
