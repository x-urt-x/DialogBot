import asyncio
from dialog_node_handlers_manager import dialog_node_reg
from zonelogger import LogZone, logger
from languages import Language

@dialog_node_reg(Language.EN,"hi")
async def hi_hendler():
    logger.info(LogZone.DIALOG_HANDLERS, "hi")