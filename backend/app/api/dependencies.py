from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, Response
from jose import JWTError, jwt

from app.core.rate_limiter import RateLimitResult, get_analyze_rate_limiter, get_rate_limiter
from app.core.settings import settings
from app.db.session import AsyncSessionLocal


@dataclass(frozen=True)
class CurrentUser:
    id: int
    role: str = "coordinator"


def _extract_user_from_jwt(request: Request) -> Optional[CurrentUser]:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = int(payload.get("sub", "0"))
        role = payload.get("role", "coordinator")
        return CurrentUser(id=user_id, role=role)
    except (JWTError, ValueError):
        return None


async def get_current_user(
    request: Request,
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(default=None, alias="X-User-Role"),
) -> CurrentUser:
    jwt_user = _extract_user_from_jwt(request)
    if jwt_user is not None:
        return jwt_user

    user_id = 1
    if x_user_id is not None:
        try:
            user_id = int(x_user_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="X-User-Id harus berupa bilangan bulat.") from exc

    role = (x_user_role or "coordinator").strip().lower()
    return CurrentUser(id=user_id, role=role)


async def check_rate_limit(response: Response, current_user: CurrentUser = Depends(get_current_user)) -> None:
    limiter = get_rate_limiter()
    if limiter.backend == "db":
        async with AsyncSessionLocal() as db:
            result: RateLimitResult = await limiter.check(current_user.id, current_user.role, db=db)
    else:
        result = await limiter.check(current_user.id, current_user.role)
    response.headers["X-RateLimit-Limit"] = str(result.limit)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    response.headers["X-RateLimit-Reset"] = str(result.reset_epoch)

    if result.exceeded:
        raise HTTPException(
            status_code=429,
            detail="Batas harian 100 permintaan tercapai. Reset pada 00:00 UTC.",
            headers={
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(result.reset_epoch),
            },
        )


async def check_analyze_rate_limit(response: Response, current_user: CurrentUser = Depends(get_current_user)) -> None:
    limiter = get_analyze_rate_limiter()
    if limiter.backend == "db":
        async with AsyncSessionLocal() as db:
            result: RateLimitResult = await limiter.check(current_user.id, current_user.role, db=db)
    else:
        result = await limiter.check(current_user.id, current_user.role)
    response.headers["X-RateLimit-Limit"] = str(result.limit)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    response.headers["X-RateLimit-Reset"] = str(result.reset_epoch)

    if result.exceeded:
        raise HTTPException(
            status_code=429,
            detail="Batas harian 10 analisa menu tercapai. Reset pada 00:00 UTC.",
            headers={
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(result.reset_epoch),
            },
        )