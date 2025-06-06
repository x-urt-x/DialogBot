from aiohttp import web
import httpx
from models.answer import Answer
from models.message import Message
from enums.apiIDs import ApiId
from models.bUser import BUser
from zonelogger import logger, LogZone
from boundary.infra.IApi import IApiSender, IApiLifecycle
from models.messageAnswerQueue import MessageAnswerQueue
from enums.languages import Language

class TelegramApiManager(IApiSender, IApiLifecycle):
    async def send(self, answer: Answer):
        keyboard = []
        payload = {
            "chat_id": answer.to_ID,
            "parse_mode": "HTML"
        }
        if answer.text:
            payload["text"] = "\n\n".join(msg for msg in answer.text if msg)
        else:
            payload["text"] = "no text for u"
        if answer.hints:
            for hint in answer.hints:
                keyboard.append([{"text": hint}])
            payload["reply_markup"] = {
                "keyboard": keyboard,
                "resize_keyboard": True,
                "one_time_keyboard": True,
            }
        async with httpx.AsyncClient() as client:
            await client.post(f"{self._api_url}/sendMessage", json=payload)

    def __init__(self, messageAnswerQueue: MessageAnswerQueue, token: str, public_url: str, webhook_path: str = "/webhook", port: int = 8000):
        self._port = port
        self._token = token
        self._api_url = f"https://api.telegram.org/bot{token}"
        self._webhook_url = public_url.rstrip("/") + webhook_path
        self._webhook_path = webhook_path
        self._queue = messageAnswerQueue.incoming

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
        ID = user_info.get("id")
        lang_raw = user_info.get("language_code")
        lang = None
        if lang_raw:
            try:
                lang =  Language(lang_raw)
                user_info.pop("language_code", None)
            except ValueError:
                lang = None

        logger.debug(LogZone.TG_API, f"from user {ID}: {text}")
        user = BUser(ApiId.TG, ID, lang, user_info)

        message = Message(text, ApiId.TG, None)
        if chat_id:
            await self._queue.put((user,message))
        return web.Response(status=200)

    async def set_webhook(self):
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self._api_url}/setWebhook",
                json={"url": self._webhook_url},
            )

    async def run(self):
        await self.set_webhook()
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, '0.0.0.0', self._port)
        await self._site.start()

    async def process(self):
        pass

    async def stop(self):
        if self._runner:
            await self._runner.cleanup()
