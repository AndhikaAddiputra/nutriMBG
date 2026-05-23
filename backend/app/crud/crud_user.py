from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import User


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    include_inactive: bool = False,
) -> Tuple[List[User], int]:
    query = select(User)
    if not include_inactive:
        query = query.where(User.is_active.is_(True))
    if search:
        pattern = f"%{search}%"
        query = query.where(User.full_name.ilike(pattern) | User.email.ilike(pattern))
    query = query.order_by(User.created_at.desc())

    count_q = select(User.id).where(User.is_active.is_(True))
    if search:
        count_q = count_q.where(User.full_name.ilike(pattern) | User.email.ilike(pattern))

    total_result = await db.execute(count_q)
    total = len(total_result.scalars().all())

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def create_user(
    db: AsyncSession,
    full_name: str,
    email: str,
    password_hash: str,
    role: str,
    province: str,
    kabupaten: str,
    default_education_level: str,
) -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        role=role,
        province=province,
        kabupaten=kabupaten,
        default_education_level=default_education_level,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    user: User,
    **kwargs,
) -> User:
    for key, value in kwargs.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    await db.flush()
    await db.refresh(user)
    return user


async def soft_delete_user(db: AsyncSession, user: User) -> User:
    user.is_active = False
    await db.flush()
    return user
