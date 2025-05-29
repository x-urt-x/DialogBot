from abc import ABC, abstractmethod
from roles import Roles

class IDialogLoader:
    @abstractmethod
    def getNodes(self):
        ...

    @abstractmethod
    def getNode(self, id: int):
        ...

    @abstractmethod
    def getRootNodeId(self, role: Roles) -> int:
        ...