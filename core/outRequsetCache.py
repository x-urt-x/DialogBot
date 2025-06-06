import time
from typing import Any, Optional

class OutRequestCache:
    def __init__(self):
        self._cache: dict[str, tuple[Any, float]] = {}

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        expires_at = time.time() + ttl_seconds
        self._cache[key] = (value, expires_at)

    def get(self, key: str) -> Optional[Any]:
        item = self._cache.get(key)
        if item is None:
            return None
        value, expires_at = item
        if time.time() < expires_at:
            return value
        else:
            del self._cache[key]
            return None

    def clear(self) -> None:
        self._cache.clear()

    def cleanup(self) -> None:
        now = time.time()
        keys_to_delete = [k for k, (_, exp) in self._cache.items() if now >= exp]
        for k in keys_to_delete:
            del self._cache[k]

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

request_cache = OutRequestCache()