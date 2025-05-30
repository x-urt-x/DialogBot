import asyncio
from typing import Tuple
from user import User
from message import Message
from answer import Answer

class MessageAnswerQueue:
    def __init__(self):
        self.incoming: asyncio.Queue[Tuple[User, Message]] = asyncio.Queue()
        self.outgoing: asyncio.Queue[Answer] = asyncio.Queue()