from enums.apiIDs import ApiId

class BUser:
    def __init__(self, api: ApiId, ID, data: dict):
        self.api: ApiId = api
        self.ID = ID
        self.data = data