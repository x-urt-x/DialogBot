import asyncio
from answer import Answer
from message import Message
from api_ids import ApiId
from user import User
from user_manager import UserManager
from zonelogger import logger, LogZone
from IApi import IApiSender, IApiLifecycle
from messageAnswerQueue import MessageAnswerQueue
from roles import Roles


class ConsoleApi(IApiSender, IApiLifecycle):
    def __init__(self, user_manager: UserManager, message_answer_queue: MessageAnswerQueue):
        self._user_manager = user_manager
        self._in_queue = message_answer_queue.incoming
        self._out_queue = message_answer_queue.outgoing
        self._running = True

    async def run(self):
        asyncio.create_task(self._read_loop())

    async def _read_loop(self):
        while self._running:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(None, input, ">> ")
                if user_input.strip().lower() == "/exit":
                    print("Console API stopping...")
                    await self.stop()
                    return
                user: User = await self._user_manager.getUserOrCreate(f"{ApiId.CONSOLE.value}:local_user")
                user["roles"] = user["roles"] | Roles.ADMIN
                if user_input.strip() == "/start":
                    user["dialog_stack"] = []
                    user_input = ""
                message = Message(user_input, ApiId.CONSOLE, None)
                await self._in_queue.put((user, message))
            except Exception as e:
                logger.error(LogZone.API_PROCES, f"Console input error: {e}")

    async def process(self):
        if not self._out_queue.empty():
            answer: Answer = await self._out_queue.get()
            await self.send(answer)

    async def stop(self):
        self._running = False

    async def send(self, answer: Answer):
        print("\n" + "\n\n".join(msg for msg in answer.text if msg) if answer.text else "\n[No text]")
        if answer.hints:
            print("Hints: " + ", ".join(answer.hints))
