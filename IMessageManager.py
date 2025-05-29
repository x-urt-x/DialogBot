from abc import ABC, abstractmethod
from message import Message
from answer import Answer
from user import User

class IMessageManager(ABC):
    @abstractmethod
    async def process(self, user: User, message: Message, answer: Answer) -> Answer:
        ...