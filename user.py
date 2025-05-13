from api_ids import ApiId
from typing import Any
from roles import Roles

class User:
    def __init__(self, user_id: str, role: Roles = Roles.USER):
        self._id = user_id
        self._role: Roles = Roles.USER
        self._availableRoles = Roles.USER
        self._data = {}
        self._tmp_fields: dict[ApiId, Any] = {}
        self._dirty: set[str] = set()

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any):
        self._data[key] = value
        self._dirty.add(key)

    @property
    def tmp(self) -> dict[ApiId, Any]:
        return self._tmp_fields

    def get_dirty_fields(self) -> dict:
        return {k: self._data[k] for k in self._dirty}

    def clear_dirty(self):
        self._dirty.clear()

    def to_dict(self) -> dict:
        data = self._data
        data["_role"] = self._role
        data["_availableRoles"] =self._availableRoles
        return data

    def from_dict(self, data: dict):
        self._role = data.pop("_role", None)
        self._availableRoles = data.pop("_availableRoles", None)
        self._data = data