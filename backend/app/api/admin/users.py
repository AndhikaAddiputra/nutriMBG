from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import TokenPayload, require_admin
from app.crud.crud_user import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    list_users,
    soft_delete_user,
    update_user,
)
from app.db.session import AsyncSessionLocal
from app.schemas.auth import RegisterRequest, UserOut

router = APIRouter(prefix="/api/admin/users", tags=["admin – users"])

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@router.get("", response_model=dict)
async def list_users_endpoint(
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    include_inactive: bool = Query(default=False),
):
    users, total = await list_users(
        db, page=page, per_page=per_page, search=search, include_inactive=include_inactive
    )
    return {
        "items": [UserOut.model_validate(u).model_dump() for u in users],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    payload: RegisterRequest,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    existing = await get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email sudah terdaftar.")
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


@router.put("/{user_id}", response_model=UserOut)
async def update_user_endpoint(
    user_id: int,
    payload: dict,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan.")
    if "password" in payload:
        payload["password_hash"] = _hash_password(payload.pop("password"))
    user = await update_user(db, user, **payload)
    await db.commit()
    return UserOut.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: int,
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan.")
    await soft_delete_user(db, user)
    await db.commit()
