from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class CacheEntry:
    value: object
    expires_at: float | None


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}

    def get(self, key: str) -> object | None:
        entry = self._store.get(key)
        if not entry:
            return None
        if entry.expires_at and entry.expires_at < time.time():
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: object, ttl_seconds: int | None = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        self._store[key] = CacheEntry(value=value, expires_at=expires_at)
