from abc import ABC, abstractmethod

class IDialogLoader:
    @abstractmethod
    def getNodes(self):
        pass

    @abstractmethod
    def getNode(self, id):
        pass