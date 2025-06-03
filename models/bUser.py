from enums.apiIDs import ApiId
from enums.languages import Language

class BUser:
    def __init__(self, api: ApiId, ID, lang : Language | None, data: dict):
        self.api: ApiId = api
        self.ID = ID
        self.lang = lang
        self.data = data