from enums.apiIDs import ApiId

class Message:
    def __init__(self, text, apiId: ApiId, meta_data: dict | None):
        self.text = text
        self.meta_data = {apiId: meta_data}

class MessageView:
    def __init__(self, message: Message, *, can_read_text=True, can_edit_text=False, can_read_meta=True, can_edit_meta=False):
        self._msg = message
        self._can_read_text = can_read_text
        self._can_edit_text = can_edit_text
        self._can_read_meta = can_read_meta
        self._can_edit_meta = can_edit_meta

    @property
    def text(self):
        if not self._can_read_text:
            raise PermissionError("Text reading not allowed")
        return self._msg.text

    @text.setter
    def text(self, value):
        if not self._can_edit_text:
            raise PermissionError("Text editing not allowed")
        self._msg.text = value

    @property
    def meta_data(self):
        if not self._can_read_meta:
            raise PermissionError("Metadata reading not allowed")
        return self._msg.meta_data

    @meta_data.setter
    def meta_data(self, value):
        if not self._can_edit_meta:
            raise PermissionError("Metadata editing not allowed")
        self._msg.meta_data = value