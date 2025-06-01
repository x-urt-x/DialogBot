from abc import ABC, abstractmethod
from enums.roles import Roles
from models.user import User

class IDataBase(ABC):
    @abstractmethod
    async def getUser(self, user_id)->User:
        pass

    @abstractmethod
    async def setRole(self, user_id, role: Roles):
        pass

    @abstractmethod
    async def createUser(self, user_id, data : dict):
        pass

    @abstractmethod
    async def updateUserData(self, user_id, data:dict):
        pass