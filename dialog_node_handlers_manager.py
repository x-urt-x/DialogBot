from collections import defaultdict
from languages import Language
from zonelogger import LogZone, logger
# Словарь вида { "en": {"say_hello": fn}, "ru": {"скажи_привет": fn} }
handler_registry = defaultdict(dict)

def dialog_node_reg(lang : Language, id_):
    def decorator(fn):
        if id_ in handler_registry[lang]:
            logger.warning(LogZone.DIALOG_HANDLERS,"Handler '{id_}' already registered for language '{lang}'")
        handler_registry[lang][id_] = fn
        return fn
    return decorator

def load_dialog_node_handlers():
    import importlib
    import pkgutil
    import dialog_node_handlers

    for _, modname, _ in pkgutil.iter_modules(dialog_node_handlers.__path__):
        importlib.import_module(f"dialog_node_handlers.{modname}")