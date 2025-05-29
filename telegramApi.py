from aiohttp import web
import httpx
import asyncio
from answer import Answer
from message import Message
from api_ids import ApiId
from user import User
from IMessageManager import IMessageManager
from user_manager import UserManager
from zonelogger import logger, LogZone

class TelegramApiManager:
    def __init__(self, token: str, public_url: str, message_manager: IMessageManager, user_manager: UserManager,webhook_path: str = "/webhook"):
        self._token = token
        self._api_url = f"https://api.telegram.org/bot{token}"
        self._webhook_url = public_url.rstrip("/") + webhook_path
        self._webhook_path = webhook_path
        self._message_manager = message_manager
        self._user_manager = user_manager

        self._app = web.Application()
        self._app.router.add_post(self._webhook_path, self._handle_webhook)

    async def _handle_webhook(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except Exception:
            return web.Response(status=400, text="Invalid JSON")

        tg_message = data.get("message", {})
        chat_id = tg_message.get("chat", {}).get("id")
        text = tg_message.get("text", "")
        user_info = tg_message.get("from", {})
        user_id = user_info.get("id")

        logger.debug(LogZone.TG_API, f"from user {user_id}: {text}")

        user: User = await self._user_manager.getUser(user_id)
        if text == "/start":
            user["dialog_stack"] = []
            text = ""
        message = Message(text, ApiId.TG, None)
        answer : Answer = Answer()
        if chat_id:
            await self._message_manager.process(user, message, answer)

            await self._send_response(chat_id, answer)

        return web.Response(status=200)

    async def _send_response(self, chat_id: int, response: Answer):
        keyboard = []
        payload = {"chat_id": chat_id}
        if response.text:
            payload["text"] = "\n\n".join(msg for msg in response.text if msg)
        else:
            payload["text"] = "no text for u"
        if response.hints:
            for hint in response.hints:
                keyboard.append([{"text": hint}])
            payload["reply_markup"] = {
                "keyboard": keyboard,
                "resize_keyboard": True,
                "one_time_keyboard": True
            }
        async with httpx.AsyncClient() as client:
            await client.post(f"{self._api_url}/sendMessage", json=payload)

    async def set_webhook(self):
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._api_url}/setWebhook",
                json={"url": self._webhook_url},
            )

    async def run(self, port: int = 8000):
        await self.set_webhook()

        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, '0.0.0.0', port)
        await self._site.start()

    async def shutdown(self):
        if self._runner:
            await self._runner.cleanup()
