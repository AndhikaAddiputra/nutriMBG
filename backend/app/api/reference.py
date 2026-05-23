from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.entities import FoodItem, LocalCatalogItem, NutritionAKG
from app.schemas.reference import AKGItem, FoodItemOut

router = APIRouter(prefix="/api/v1/reference", tags=["reference"])


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/akg/{education_level}", response_model=list[AKGItem])
async def get_akg_by_level(education_level: str, db: AsyncSession = Depends(get_db)):
    query = (
        select(NutritionAKG)
        .where(NutritionAKG.education_level == education_level.upper())
        .order_by(NutritionAKG.nutrient_code.asc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/foods", response_model=list[FoodItemOut])
async def get_foods(
    kabupaten: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    if kabupaten:
        query = (
            select(FoodItem)
            .join(LocalCatalogItem, LocalCatalogItem.food_item_id == FoodItem.id)
            .where(
                LocalCatalogItem.kabupaten == kabupaten,
                LocalCatalogItem.is_available.is_(True),
                FoodItem.is_active.is_(True),
            )
            .order_by(FoodItem.name.asc())
            .limit(limit)
        )
    else:
        query = select(FoodItem).where(FoodItem.is_active.is_(True)).order_by(FoodItem.name.asc()).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/kabupatens", response_model=list[str])
async def get_kabupatens(db: AsyncSession = Depends(get_db)):
    query = select(LocalCatalogItem.kabupaten).distinct().order_by(LocalCatalogItem.kabupaten.asc())
    result = await db.execute(query)
    return [row[0] for row in result.all()]
