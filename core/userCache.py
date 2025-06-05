from collections import OrderedDict
from typing import Any

class UserCache:
    def __init__(self, max_size: int):
        self._max_size = max_size
        self._cache: OrderedDict[tuple, Any] = OrderedDict()

    def get(self, key: tuple) -> Any | None:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def set(self, key: tuple, value: Any):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def remove(self, key: tuple):
        self._cache.pop(key, None)

    def clear(self):
        self._cache.clear()

    def __getitem__(self, key: tuple) -> Any:
        result = self.get(key)
        if result is None:
            raise KeyError(f"{key} not found or expired")
        return result

    def __setitem__(self, key: tuple, value: Any):
        self.set(key, value)

    def __delitem__(self, key: tuple):
        self.remove(key)

    def __contains__(self, key: tuple) -> bool:
        return key in self._cache

    def __len__(self) -> int:
        return len(self._cache)