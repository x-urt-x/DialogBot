from enums.apiIDs import ApiId

class Message:
    def __init__(self, text, apiId: ApiId, meta_data: dict | None):
        self.text = text
        self.meta_data = {apiId: meta_data}