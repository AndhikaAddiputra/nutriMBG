"""
api/history.py
==============
GET /api/v1/history/trend

Query parameters
----------------
days        : int  – rolling window in calendar days (default 28, max 90)
component   : str  – one of composite | protein | carbohydrate | fat |
                      fiber | iron | vitamin_a | all   (default "all")
education_level : str – AKG reference level (default "SMP")
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.schemas.history import TrendResponse
from app.services.history_service import VALID_COMPONENTS, get_trend

router = APIRouter(prefix="/api/v1/history", tags=["history"])


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/trend", response_model=List[TrendResponse])
async def nutrition_trend(
    days: int = Query(default=28, ge=1, le=90, description="Rolling window in calendar days"),
    component: str = Query(
        default="all",
        description=(
            "Nutrition component to return. One of: "
            + ", ".join(sorted(VALID_COMPONENTS))
            + ", or 'all' for every component."
        ),
    ),
    education_level: str = Query(
        default="SMP",
        description="AKG reference education level (SD_1_3 | SD_4_6 | SMP | SMA)",
    ),
    db: AsyncSession = Depends(get_db),
) -> List[TrendResponse]:
    valid_values = VALID_COMPONENTS | {"all"}
    if component not in valid_values:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Nilai component tidak valid: '{component}'. "
                f"Pilihan yang tersedia: {', '.join(sorted(valid_values))}."
            ),
        )

    return await get_trend(db, days=days, component=component, education_level=education_level)
