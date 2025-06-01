import asyncio
from typing import Tuple
from bUser import BUser
from models.message import Message
from answer import Answer

class MessageAnswerQueue:
    def __init__(self):
        self.incoming: asyncio.Queue[Tuple[BUser, Message]] = asyncio.Queue()
        self.outgoing: asyncio.Queue[Answer] = asyncio.Queue()