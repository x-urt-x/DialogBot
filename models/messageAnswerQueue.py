import asyncio
from typing import Tuple
from models.bUser import BUser
from models.message import Message
from models.answer import Answer

class MessageAnswerQueue:
    def __init__(self):
        self.incoming: asyncio.Queue[Tuple[BUser, Message]] = asyncio.Queue()
        self.outgoing: asyncio.Queue[Answer] = asyncio.Queue()