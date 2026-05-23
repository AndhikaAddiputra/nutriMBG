from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import TokenPayload, require_admin
from app.db.session import AsyncSessionLocal
from app.models.entities import FoodItem, MenuAnalysis, NutritionAKG, User

router = APIRouter(prefix="/api/admin/stats", tags=["admin – stats"])


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@router.get("")
async def get_admin_stats(
    _admin: Annotated[TokenPayload, Depends(require_admin)],
    db: AsyncSession = Depends(get_db),
):
    total_users = await db.scalar(select(func.count(User.id)).where(User.is_active.is_(True)))
    total_foods = await db.scalar(select(func.count(FoodItem.id)).where(FoodItem.is_active.is_(True)))
    total_analyses = await db.scalar(select(func.count(MenuAnalysis.id)))
    total_akg = await db.scalar(select(func.count(NutritionAKG.id)))

    avg_score = await db.scalar(select(func.avg(MenuAnalysis.score_total)))

    today_result = await db.execute(
        select(func.count(MenuAnalysis.id))
        .where(func.date(MenuAnalysis.created_at) == func.current_date())
    )
    today_analyses = today_result.scalar()

    recent_result = await db.execute(
        select(MenuAnalysis).order_by(MenuAnalysis.created_at.desc()).limit(10)
    )
    recent_analyses = recent_result.scalars().all()

    return {
        "total_users": total_users or 0,
        "total_foods": total_foods or 0,
        "total_analyses": total_analyses or 0,
        "total_akg_entries": total_akg or 0,
        "average_score": round(float(avg_score or 0.0), 2),
        "today_analyses": today_analyses or 0,
        "recent_analyses": [
            {
                "id": a.id,
                "user_id": a.user_id,
                "menu_text": a.menu_text[:80],
                "education_level": a.education_level,
                "score_total": a.score_total,
                "created_at": a.created_at.isoformat() if hasattr(a.created_at, "isoformat") else str(a.created_at),
            }
            for a in recent_analyses
        ],
    }
