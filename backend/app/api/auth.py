from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.core.dependencies import TokenPayload
from app.core.settings import settings
from app.crud.crud_user import create_user, get_user_by_email
from app.db.session import AsyncSessionLocal
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _create_token(user_id: int, role: str) -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(hours=settings.jwt_exp_hours)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, payload.email)
    if user is None or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau kata sandi salah.",
        )
    token = _create_token(user.id, user.role)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    existing = await get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email sudah terdaftar.",
        )
    password_hash = _hash_password(payload.password)
    user = await create_user(
        db=db,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=password_hash,
        role=payload.role,
        province=payload.province,
        kabupaten=payload.kabupaten,
        default_education_level=payload.default_education_level,
    )
    await db.commit()
    return UserOut.model_validate(user)
