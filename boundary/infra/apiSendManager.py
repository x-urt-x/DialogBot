from asyncio import Queue
from apiRegistry import ApiRegistry
from models.messageAnswerQueue import MessageAnswerQueue
from core.userManager import UserManager
from models.answer import Answer
from IApi import IApiSender
from zonelogger import logger, LogZone
from enums.apiIDs import ApiId

class ApiSendManager:
    def __init__(self, queue: MessageAnswerQueue, registry: ApiRegistry, user_manager: UserManager):
        self._queue : Queue = queue.outgoing
        self._registry = registry
        self._user_manager = user_manager

    async def process_queue(self):
        if self._queue.empty():
            return

        answer: Answer = await self._queue.get()
        api_id = ApiId(answer.to_user_id.split(":")[0])
        if answer.to_user_id is None:
            logger.warning(LogZone.API_PROCES, f"no user to send")
            return

        try:
            sender: IApiSender = self._registry.get_sender(api_id)
        except KeyError:
            logger.warning(LogZone.API_PROCES, f"no {api_id} api to send")
            return
        await sender.send(answer)