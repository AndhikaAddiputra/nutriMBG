from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.generator import generate_menu_alternatives
from app.crud.crud_local_catalog import get_available_food_names_for_district
from app.models.entities import FoodItem


def _current_month() -> int:
    return datetime.now(tz=timezone.utc).month


async def get_local_catalog_for_district(
    db: AsyncSession,
    district_id: Optional[str],
) -> List[str]:
    if not district_id or district_id.strip() in ("", "Semua Kabupaten"):
        result = await db.execute(
            select(FoodItem.name)
            .where(FoodItem.is_active.is_(True))
            .order_by(FoodItem.name.asc())
        )
        return [row[0] for row in result.all()]

    current_month = _current_month()
    available = await get_available_food_names_for_district(
        db, district_id.strip(), current_month
    )

    if not available:
        result = await db.execute(
            select(FoodItem.name)
            .where(FoodItem.is_active.is_(True))
            .order_by(FoodItem.name.asc())
        )
        return [row[0] for row in result.all()]

    return available


async def recommend_for_district(
    db: AsyncSession,
    deficiencies: Dict[str, str],
    district_id: Optional[str],
    count: int = 3,
) -> List[str]:
    local_catalog = await get_local_catalog_for_district(db, district_id)
    return await generate_menu_alternatives(
        deficiencies=deficiencies,
        local_catalog=local_catalog,
        count=count,
    )