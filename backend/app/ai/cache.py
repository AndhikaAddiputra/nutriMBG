"""
ai/cache.py
===========
Simple in-memory cache for AI responses.

Avoids redundant API calls for identical prompts within a TTL window.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Optional


class _CacheEntry:
    __slots__ = ("data", "expires_at")

    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.expires_at = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class AIResponseCache:
    def __init__(self, ttl_seconds: int = 300, max_entries: int = 256):
        self._ttl = ttl_seconds
        self._max = max_entries
        self._store: dict[str, _CacheEntry] = {}

    def _key(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()

    def get(self, prompt: str) -> Optional[Any]:
        entry = self._store.get(self._key(prompt))
        if entry is None:
            return None
        if entry.is_expired():
            del self._store[self._key(prompt)]
            return None
        return entry.data

    def set(self, prompt: str, data: Any) -> None:
        if len(self._store) >= self._max:
            self._evict()
        self._store[self._key(prompt)] = _CacheEntry(data, self._ttl)

    def _evict(self) -> None:
        oldest = min(self._store.keys(), key=lambda k: self._store[k].expires_at)
        del self._store[oldest]

    def clear(self) -> None:
        self._store.clear()


_cache = AIResponseCache()


def get_ai_cache() -> AIResponseCache:
    return _cache
