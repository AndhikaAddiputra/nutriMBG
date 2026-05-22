"""
crud/crud_akg.py
================
Async database operations for the NutritionAKG entity.
POST semantics are upsert: if (education_level, nutrient_code) already
exists, the row is updated in place rather than raising a duplicate error.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import NutritionAKG
from app.schemas.akg_schemas import AKGCreate, AKGUpdate


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


async def list_akg(
    db: AsyncSession,
    *,
    education_level: Optional[str] = None,
) -> List[NutritionAKG]:
    """Return all AKG rows, optionally filtered by education_level."""
    q = select(NutritionAKG).order_by(
        NutritionAKG.education_level.asc(),
        NutritionAKG.nutrient_code.asc(),
    )
    if education_level:
        q = q.where(NutritionAKG.education_level == education_level.upper())
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_akg(db: AsyncSession, akg_id: int) -> Optional[NutritionAKG]:
    result = await db.execute(select(NutritionAKG).where(NutritionAKG.id == akg_id))
    return result.scalar_one_or_none()


async def _find_by_level_and_code(
    db: AsyncSession,
    education_level: str,
    nutrient_code: str,
) -> Optional[NutritionAKG]:
    result = await db.execute(
        select(NutritionAKG).where(
            NutritionAKG.education_level == education_level,
            NutritionAKG.nutrient_code == nutrient_code,
        )
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Upsert (POST)
# ---------------------------------------------------------------------------


async def upsert_akg(db: AsyncSession, payload: AKGCreate) -> tuple[NutritionAKG, bool]:
    """
    Create or update an AKG row identified by (education_level, nutrient_code).

    Returns
    -------
    (row, created)  — created=True if a new row was inserted, False if updated.
    """
    existing = await _find_by_level_and_code(
        db, payload.education_level, payload.nutrient_code
    )

    if existing:
        existing.target_value = payload.target_value
        existing.unit = payload.unit
        existing.source = payload.source
        await db.commit()
        await db.refresh(existing)
        return existing, False

    row = NutritionAKG(
        education_level=payload.education_level,
        nutrient_code=payload.nutrient_code,
        target_value=payload.target_value,
        unit=payload.unit,
        source=payload.source,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row, True


# ---------------------------------------------------------------------------
# Update (PUT)
# ---------------------------------------------------------------------------


async def update_akg(
    db: AsyncSession,
    row: NutritionAKG,
    payload: AKGUpdate,
) -> NutritionAKG:
    """Apply non-None fields from payload and persist."""
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row