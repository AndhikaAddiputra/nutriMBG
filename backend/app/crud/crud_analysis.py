from __future__ import annotations

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import MenuAnalysis, MenuIngredient, Recommendation


async def create_analysis(
    db: AsyncSession,
    user_id: Optional[int],
    menu_text: str,
    education_level: str,
    score_total: float,
) -> MenuAnalysis:
    analysis = MenuAnalysis(
        user_id=user_id,
        menu_text=menu_text,
        education_level=education_level,
        score_total=score_total,
    )
    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)
    return analysis


async def create_ingredients(
    db: AsyncSession,
    analysis_id: int,
    ingredients: List[dict],
    food_item_ids: dict,
) -> List[MenuIngredient]:
    rows = []
    for ing in ingredients:
        name = ing.get("name", "")
        food_item_id = food_item_ids.get(name)
        row = MenuIngredient(
            analysis_id=analysis_id,
            food_item_id=food_item_id,
            input_name=name,
            weight_gram=float(ing.get("weight_gram", 100.0)),
        )
        db.add(row)
        rows.append(row)
    await db.flush()
    return rows


async def create_recommendation(
    db: AsyncSession,
    analysis_id: int,
    title: str,
    projected_score: float,
    notes: str,
) -> Recommendation:
    rec = Recommendation(
        analysis_id=analysis_id,
        title=title,
        projected_score=projected_score,
        notes=notes,
    )
    db.add(rec)
    await db.flush()
    await db.refresh(rec)
    return rec
