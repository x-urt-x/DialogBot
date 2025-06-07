from enums.apiIDs import ApiId
from enums.roles import Roles
from enums.languages import Language
from collections import deque

class User:
    def __init__(self, api: ApiId, ID: str):
        self._api = {}
        self._info = {}
        self._tmp = {}
        self._data = {
            "ID": ID,
            "api": api,
            "role": Roles.USER,
            "roles": Roles.USER,
            "stack": deque(),
        }
        self._dirty: dict[str,set[str]] = {
            "api": set(),
            "data": set(),
            "info": set()
        }


    def _setDirty(self, section, key: str):
        self._dirty[section].add(key)

    def clear_dirty(self):
        for v in self._dirty.values():
            v.clear()

    @property
    def role(self)->Roles:
        return self._data["role"]
    @role.setter
    def role(self, role: Roles):
        if self._data["roles"] & role:
            self._data["role"] = role
            self._setDirty("data","role")

    @property
    def roles(self) -> Roles:
        return self._data["roles"]

    @property
    def lang(self)->Language|None:
        return self._data.get("lang")
    @lang.setter
    def lang(self, lang:Language):
        self._data["lang"] = lang
        self._setDirty("data", "lang")

    @property
    def api(self):
        return self._data["api"]

    @property
    def ID(self):
        return self._data["ID"]

    def stackPeek(self):
        return self._data["stack"][-1]

    def stackPopN(self, n: int) -> int | None:
        stack = self._data["stack"]
        if n == 0:
            return None
        if n > len(stack):
            n = len(stack)
        res = None
        for _ in range(n):
            res = stack.pop()
        self._setDirty("data", "stack")
        return res

    def stackSetToOne(self, n:int):
        stack = self._data["stack"]
        stack.clear()
        stack.append(n)
        self._setDirty("data", "stack")

    def stackAppend(self, n:int):
        self._data["stack"].append(n)
        self._setDirty("data", "stack")

    def stackLen(self):
        return len(self._data["stack"])

    def stackClear(self):
        self._data["stack"].clear()
        self._setDirty("data", "stack")

    def stackToRoot(self, roots) ->int | None:
        stack = self._data["stack"]
        stack.clear()
        root_id = roots.get(self._data["role"])
        if not root_id:
            return None
        stack.append(root_id)
        self._setDirty("data", "stack")
        return root_id

    @property
    def tmp(self):
        return self._tmp

    @property
    def api_data(self):
        return self._api

    def apiDataGet(self, key: str):
        return self._api.get(key)

    def apiDataSet(self, key: str, val):
        if self._api.get(key) == val:
            return
        self._api[key] = val
        self._setDirty("data", key)

    @property
    def info(self):
        return self._info

    def infoDataGet(self, key: str):
        return self._info.get(key)

    def infoDataSet(self, key: str, val):
        if self._info.get(key) == val:
            return
        self._info[key] = val
        self._setDirty("info", key)

    def get_dirty_fields(self) -> dict:
        result = {"data":{},"api":{}, "info":{}}
        for key in self._dirty["data"]:
            if key in self._data:
                result["data"][key] = self._data[key]
        for key in self._dirty["api"]:
            if key in self._api:
                result["api"][key] = self._api[key]
        for key in self._dirty["info"]:
            if key in self._info:
                result["info"][key] = self._info[key]
        return result

    def to_dict(self) -> dict:
        return {"data":self._data,"api":self._api, "info":self._info}

    def from_dict(self, raw_data: dict):
        api = raw_data.get("api")
        if api is not None:
            self._api = api
        data = raw_data.get("data")
        if data is not None:
            self._data = data
        info = raw_data.get("info")
        if info is not None:
            self._info = info