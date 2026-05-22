from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from threading import Lock
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.models.rate_limit_log import RateLimitLog

try:
    import redis.asyncio as redis
except ImportError:  # pragma: no cover - optional dependency
    redis = None


@dataclass(frozen=True)
class RateLimitResult:
    limit: int
    remaining: int
    reset_epoch: int
    exceeded: bool


class RateLimiter:
    def __init__(self, limit: int, backend: str = "auto", redis_url: Optional[str] = None) -> None:
        self.limit = limit
        self.backend = backend.lower()
        self.redis_url = redis_url
        self._redis_client = None
        self._memory_lock = Lock()
        self._memory_counts: dict[str, int] = {}

    def clear_memory(self) -> None:
        with self._memory_lock:
            self._memory_counts.clear()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @classmethod
    def _day_key(cls, when: Optional[datetime] = None) -> str:
        return (when or cls._utc_now()).date().isoformat()

    @classmethod
    def _reset_epoch(cls, when: Optional[datetime] = None) -> int:
        current = when or cls._utc_now()
        midnight = datetime(current.year, current.month, current.day, tzinfo=timezone.utc) + timedelta(days=1)
        return int(midnight.timestamp())

    async def _get_redis_client(self):
        if redis is None or not self.redis_url:
            return None
        if self._redis_client is None:
            self._redis_client = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
        return self._redis_client

    async def check(self, user_id: int, role: str, db: Optional[AsyncSession] = None) -> RateLimitResult:
        if role.strip().lower() == "admin":
            return RateLimitResult(
                limit=self.limit,
                remaining=self.limit,
                reset_epoch=self._reset_epoch(),
                exceeded=False,
            )

        if self.backend == "db":
            if db is None:
                raise RuntimeError("Database session diperlukan untuk backend rate limit db.")
            return await self._check_db(db, user_id)

        redis_client = await self._get_redis_client()
        if self.backend in {"auto", "redis"} and redis_client is not None:
            return await self._check_redis(redis_client, user_id)

        return self._check_memory(user_id)

    async def _check_redis(self, client, user_id: int) -> RateLimitResult:
        key = self._redis_key(user_id)
        count = await client.incr(key)
        if count == 1:
            await client.expireat(key, self._reset_epoch())
        remaining = max(self.limit - count, 0)
        return RateLimitResult(
            limit=self.limit,
            remaining=remaining,
            reset_epoch=self._reset_epoch(),
            exceeded=count > self.limit,
        )

    async def _check_db(self, db: AsyncSession, user_id: int) -> RateLimitResult:
        today = self._current_date()
        existing = await db.execute(
            select(RateLimitLog).where(RateLimitLog.user_id == user_id, RateLimitLog.rate_date == today)
        )
        record = existing.scalar_one_or_none()
        if record is None:
            record = RateLimitLog(user_id=user_id, rate_date=today, count=1)
            db.add(record)
            await db.flush()
            count = 1
        else:
            record.count += 1
            count = record.count
            await db.flush()
        await db.commit()
        remaining = max(self.limit - count, 0)
        return RateLimitResult(
            limit=self.limit,
            remaining=remaining,
            reset_epoch=self._reset_epoch(),
            exceeded=count > self.limit,
        )

    def _check_memory(self, user_id: int) -> RateLimitResult:
        key = self._memory_key(user_id)
        with self._memory_lock:
            count = self._memory_counts.get(key, 0) + 1
            self._memory_counts[key] = count
        remaining = max(self.limit - count, 0)
        return RateLimitResult(
            limit=self.limit,
            remaining=remaining,
            reset_epoch=self._reset_epoch(),
            exceeded=count > self.limit,
        )

    def _redis_key(self, user_id: int) -> str:
        return f"ratelimit:{user_id}:{self._day_key()}"

    def _memory_key(self, user_id: int) -> str:
        return self._redis_key(user_id)

    @staticmethod
    def _current_date() -> date:
        return datetime.now(timezone.utc).date()


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            limit=settings.rate_limit_limit,
            backend=settings.rate_limit_backend,
            redis_url=settings.redis_url,
        )
    return _rate_limiter