"""
crud/crud_local_catalog.py
==========================
Async database operations for the LocalIngredientCatalog entity.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import FoodItem
from app.models.local_catalog import LocalIngredientCatalog
from app.schemas.local_catalog_schemas import (
    BulkCatalogItem,
    LocalCatalogUpdate,
)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


async def list_catalog_for_district(
    db: AsyncSession,
    district_id: str,
    *,
    include_unavailable: bool = True,
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
) -> Tuple[List[Tuple[LocalIngredientCatalog, str]], int]:
    """
    Return catalog rows for a district joined with the food item name.

    Returns
    -------
    (rows, total) — rows is a list of (LocalIngredientCatalog, food_name)
    """
    base_q = (
        select(LocalIngredientCatalog, FoodItem.name.label("food_name"))
        .join(FoodItem, FoodItem.id == LocalIngredientCatalog.food_item_id)
        .where(
            LocalIngredientCatalog.district_id == district_id,
            FoodItem.is_active.is_(True),
        )
    )
    count_q = (
        select(func.count(LocalIngredientCatalog.id))
        .join(FoodItem, FoodItem.id == LocalIngredientCatalog.food_item_id)
        .where(
            LocalIngredientCatalog.district_id == district_id,
            FoodItem.is_active.is_(True),
        )
    )

    if not include_unavailable:
        base_q = base_q.where(LocalIngredientCatalog.is_available.is_(True))
        count_q = count_q.where(LocalIngredientCatalog.is_available.is_(True))

    if search:
        like_expr = f"%{search.strip().lower()}%"
        base_q = base_q.where(FoodItem.normalized_name.like(like_expr))
        count_q = count_q.where(FoodItem.normalized_name.like(like_expr))

    offset = (page - 1) * per_page
    base_q = (
        base_q.order_by(FoodItem.name.asc())
        .limit(per_page)
        .offset(offset)
    )

    total_result = await db.execute(count_q)
    total: int = total_result.scalar_one()

    rows_result = await db.execute(base_q)
    rows = rows_result.all()
    return [(row[0], row[1]) for row in rows], total


async def get_catalog_entry(
    db: AsyncSession,
    district_id: str,
    food_item_id: int,
) -> Optional[LocalIngredientCatalog]:
    """Fetch a single catalog entry by district + food item."""
    result = await db.execute(
        select(LocalIngredientCatalog).where(
            LocalIngredientCatalog.district_id == district_id,
            LocalIngredientCatalog.food_item_id == food_item_id,
        )
    )
    return result.scalar_one_or_none()


async def get_available_food_names_for_district(
    db: AsyncSession,
    district_id: str,
    current_month: int,
) -> List[str]:
    """
    Return names of FoodItems that are available in the district right now.

    Availability rules:
      - is_available = TRUE
      - unavailable_months IS NULL  OR  current_month NOT IN unavailable_months
    """
    result = await db.execute(
        select(FoodItem.name)
        .join(
            LocalIngredientCatalog,
            LocalIngredientCatalog.food_item_id == FoodItem.id,
        )
        .where(
            LocalIngredientCatalog.district_id == district_id,
            LocalIngredientCatalog.is_available.is_(True),
            FoodItem.is_active.is_(True),
        )
        .order_by(FoodItem.name.asc())
    )
    all_names = [row[0] for row in result.all()]

    # Post-filter for seasonal unavailability (SQLAlchemy ARRAY ANY() is DB-specific)
    # We do it in Python to stay compatible with SQLite in tests.
    # For production PostgreSQL you can push this into the WHERE clause.
    filtered: List[str] = []
    entries_result = await db.execute(
        select(LocalIngredientCatalog, FoodItem.name)
        .join(FoodItem, FoodItem.id == LocalIngredientCatalog.food_item_id)
        .where(
            LocalIngredientCatalog.district_id == district_id,
            LocalIngredientCatalog.is_available.is_(True),
            FoodItem.is_active.is_(True),
        )
    )
    for entry, name in entries_result.all():
        months = entry.unavailable_months or []
        if current_month not in months:
            filtered.append(name)

    return sorted(set(filtered))


# ---------------------------------------------------------------------------
# Create / Upsert
# ---------------------------------------------------------------------------


async def upsert_catalog_entry(
    db: AsyncSession,
    district_id: str,
    food_item_id: int,
    payload: LocalCatalogUpdate,
) -> Tuple[LocalIngredientCatalog, bool]:
    """
    Create or update a catalog entry.

    Returns
    -------
    (entry, created)
    """
    existing = await get_catalog_entry(db, district_id, food_item_id)

    if existing:
        if payload.is_available is not None:
            existing.is_available = payload.is_available
        if payload.unavailable_months is not None:
            existing.unavailable_months = payload.unavailable_months or None
        await db.commit()
        await db.refresh(existing)
        return existing, False

    entry = LocalIngredientCatalog(
        district_id=district_id,
        food_item_id=food_item_id,
        is_available=payload.is_available if payload.is_available is not None else True,
        unavailable_months=payload.unavailable_months or None,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry, True


async def bulk_upsert_catalog(
    db: AsyncSession,
    district_id: str,
    items: List[BulkCatalogItem],
) -> Tuple[int, int, List[str]]:
    """
    Bulk-create or update catalog entries for a district.

    Returns
    -------
    (updated_count, created_count, error_messages)
    """
    updated = 0
    created = 0
    errors: List[str] = []

    for item in items:
        # Verify FoodItem exists
        food_result = await db.execute(
            select(FoodItem).where(FoodItem.id == item.food_item_id)
        )
        food = food_result.scalar_one_or_none()
        if food is None:
            errors.append(f"FoodItem id={item.food_item_id} tidak ditemukan.")
            continue

        payload = LocalCatalogUpdate(
            is_available=item.is_available,
            unavailable_months=item.unavailable_months,
        )
        _, was_created = await upsert_catalog_entry(db, district_id, item.food_item_id, payload)
        if was_created:
            created += 1
        else:
            updated += 1

    return updated, created, errors
