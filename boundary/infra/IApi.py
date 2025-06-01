from abc import ABC, abstractmethod
from models.answer import Answer

class IApiLifecycle(ABC):
    @abstractmethod
    async def run(self):
        ...

    @abstractmethod
    async def process(self):
        ...

    @abstractmethod
    async def stop(self):
        ...

class IApiSender(ABC):
    @abstractmethod
    async def send(self, answer: Answer):
        ...