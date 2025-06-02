from enums.apiIDs import ApiId

class Answer:
    def __init__(self):
        self.text = []
        self.hints = []
        self.to_ID : str | None = None
        self.to_api: ApiId | None = None