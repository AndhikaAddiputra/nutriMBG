"""
crud/crud_food_item.py
======================
Async database operations for the FoodItem entity.
All public-facing food lookups already filter is_active=True; soft-delete
simply sets is_active=False on the row.
"""

from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import FoodItem
from app.schemas.food_item_schemas import FoodItemCreate, FoodItemUpdate


def _normalize(name: str) -> str:
    return name.strip().lower()


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


async def list_food_items(
    db: AsyncSession,
    *,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    include_inactive: bool = False,
) -> Tuple[list[FoodItem], int]:
    """
    Return a page of FoodItem rows + total count.

    Parameters
    ----------
    page            : 1-based page number
    per_page        : rows per page (1–100)
    search          : optional partial name filter (case-insensitive)
    include_inactive: if True, soft-deleted items are included (admin use)
    """
    base_q = select(FoodItem)
    count_q = select(func.count(FoodItem.id))

    if not include_inactive:
        base_q = base_q.where(FoodItem.is_active.is_(True))
        count_q = count_q.where(FoodItem.is_active.is_(True))

    if search:
        like_expr = f"%{search.strip().lower()}%"
        base_q = base_q.where(FoodItem.normalized_name.like(like_expr))
        count_q = count_q.where(FoodItem.normalized_name.like(like_expr))

    offset = (page - 1) * per_page
    base_q = base_q.order_by(FoodItem.name.asc()).limit(per_page).offset(offset)

    total_result = await db.execute(count_q)
    total: int = total_result.scalar_one()

    rows_result = await db.execute(base_q)
    items = list(rows_result.scalars().all())

    return items, total


async def get_food_item(db: AsyncSession, item_id: int) -> Optional[FoodItem]:
    result = await db.execute(select(FoodItem).where(FoodItem.id == item_id))
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def create_food_item(db: AsyncSession, payload: FoodItemCreate) -> FoodItem:
    """
    Insert a new FoodItem.
    Raises ValueError if the normalised name already exists (active or soft-deleted).
    """
    norm = _normalize(payload.name)

    existing = await db.execute(
        select(FoodItem).where(FoodItem.normalized_name == norm)
    )
    if existing.scalar_one_or_none():
        raise ValueError(
            f"Bahan makanan dengan nama '{payload.name}' sudah ada di database."
        )

    item = FoodItem(
        name=payload.name.strip(),
        normalized_name=norm,
        source=payload.source,
        protein=payload.protein,
        carbohydrate=payload.carbohydrate,
        fat=payload.fat,
        fiber=payload.fiber,
        iron=payload.iron,
        vitamin_a=payload.vitamin_a,
        is_active=True,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


async def update_food_item(
    db: AsyncSession,
    item: FoodItem,
    payload: FoodItemUpdate,
) -> FoodItem:
    """Apply non-None fields from payload onto item and persist."""
    update_data = payload.model_dump(exclude_none=True)

    if "name" in update_data:
        new_norm = _normalize(update_data["name"])
        # Check uniqueness — exclude the item itself
        conflict = await db.execute(
            select(FoodItem).where(
                FoodItem.normalized_name == new_norm,
                FoodItem.id != item.id,
            )
        )
        if conflict.scalar_one_or_none():
            raise ValueError(
                f"Bahan makanan dengan nama '{update_data['name']}' sudah ada."
            )
        update_data["normalized_name"] = new_norm

    for field, value in update_data.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    return item


# ---------------------------------------------------------------------------
# Soft-delete
# ---------------------------------------------------------------------------


async def soft_delete_food_item(db: AsyncSession, item: FoodItem) -> FoodItem:
    """Set is_active=False without removing the row from the database."""
    item.is_active = False
    await db.commit()
    await db.refresh(item)
    return item