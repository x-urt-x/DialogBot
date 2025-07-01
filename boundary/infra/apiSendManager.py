from asyncio import Queue
from boundary.infra.apiRegistry import ApiRegistry
from boundary.infra.IApi import IApiSender
from models.messageAnswerQueue import MessageAnswerQueue
from models.answer import Answer
from core.userManager import UserManager
from zonelogger import logger, LogZone
from enums.apiIDs import ApiId

class ApiSendManager:
    def __init__(self, queue: MessageAnswerQueue, registry: ApiRegistry, user_manager: UserManager):
        self._queue : Queue = queue.outgoing
        self._registry = registry
        self._user_manager = user_manager

    async def loop(self):
        while True:
            try:
                await self._process_queue()
            except Exception:
                logger.exception("error on ApiSend")

    async def _process_queue(self):
        answer: Answer = await self._queue.get()
        api_id = ApiId(answer.to_api)
        if answer.to_ID is None:
            logger.warning(LogZone.API_PROCES, f"no user to send")
            return

        try:
            sender: IApiSender = self._registry.get_sender(api_id)
        except KeyError:
            logger.warning(LogZone.API_PROCES, f"no {api_id} api to send")
            return
        await sender.send(answer)