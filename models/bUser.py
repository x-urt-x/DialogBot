from enums.apiIDs import ApiId

class BUser:
    def __init__(self, api: ApiId, user_id, data: dict):
        self.api: ApiId = api
        self.user_id = user_id
        self.data = data