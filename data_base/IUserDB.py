from abc import ABC, abstractmethod
from enums.apiIDs import ApiId

class IDataBase(ABC):
    @abstractmethod
    async def getUserData(self, api: ApiId, ID)-> dict | None:
        pass

    @abstractmethod
    async def createUser(self, api: ApiId, ID, data : dict):
        pass

    @abstractmethod
    async def updateUserData(self, api: ApiId, ID, set_data: dict, unset_data: dict):
        pass