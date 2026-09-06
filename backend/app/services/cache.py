"""Small async cache with an in-process fallback and optional Redis backend."""
from __future__ import annotations

import json
import os
import time
from typing import Any


class TTLCache:
    def __init__(self) -> None:
        self._memory: dict[str, tuple[float, Any]] = {}
        self._redis = None
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                from redis.asyncio import from_url
                self._redis = from_url(redis_url, decode_responses=True)
            except ImportError:
                self._redis = None

    async def get(self, key: str) -> Any:
        item = self._memory.get(key)
        if item and item[0] > time.monotonic():
            return item[1]
        self._memory.pop(key, None)
        if self._redis:
            try:
                value = await self._redis.get(key)
                return json.loads(value) if value else None
            except Exception:
                return None
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._memory[key] = (time.monotonic() + ttl_seconds, value)
        if self._redis:
            try:
                await self._redis.set(key, json.dumps(value), ex=ttl_seconds)
            except Exception:
                pass


cache = TTLCache()