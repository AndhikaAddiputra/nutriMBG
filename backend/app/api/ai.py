from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.fallback_parser import parse_menu_fallback
from app.ai.generator import generate_menu_alternatives
from app.ai.parser import parse_menu
from app.api.dependencies import CurrentUser, check_analyze_rate_limit, check_rate_limit, get_current_user as get_api_user
from app.crud.crud_analysis import create_analysis, create_ingredients, create_recommendation
from app.db.session import AsyncSessionLocal
from app.ml.classifier import predict_score
from app.ml.nutrition import (
    compute_ratios,
    compute_totals_from_items,
    label_deficiency,
    load_akg_targets,
    load_tkpi_index,
)
from app.models.entities import FoodItem, LocalCatalogItem
from app.schemas.ai import (
    ClassifyMenuRequest,
    ClassifyMenuResponse,
    ParseMenuRequest,
    ParseMenuResponse,
    RecommendRequest,
    RecommendResponse,
)

router = APIRouter(tags=["ai"])


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


def _normalize(name: str) -> str:
    return name.lower().strip()


@router.post("/parse", response_model=ParseMenuResponse, dependencies=[Depends(check_rate_limit)])
async def parse_menu_endpoint(payload: ParseMenuRequest) -> ParseMenuResponse:
    try:
        items = await parse_menu(payload.text)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ParseMenuResponse(items=items)


@router.post("/recommend", response_model=RecommendResponse, dependencies=[Depends(check_rate_limit)])
async def recommend_menu_endpoint(payload: RecommendRequest) -> RecommendResponse:
    try:
        recommendations = await generate_menu_alternatives(
            deficiencies=payload.deficiencies,
            local_catalog=payload.local_catalog,
            count=payload.count,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return RecommendResponse(recommendations=recommendations)


@router.post("/analyze", response_model=ClassifyMenuResponse, dependencies=[Depends(check_analyze_rate_limit)])
@router.post("/classify", response_model=ClassifyMenuResponse, dependencies=[Depends(check_analyze_rate_limit)])
async def classify_menu_endpoint(
    payload: ClassifyMenuRequest,
    current_user: CurrentUser = Depends(get_api_user),
    db: AsyncSession = Depends(get_db),
) -> ClassifyMenuResponse:
    level = payload.education_level.strip().upper()
    allowed_levels = ("SD_1_3", "SD_4_6", "SMP", "SMA")
    if level not in allowed_levels:
        raise HTTPException(
            status_code=400,
            detail=f"education_level harus salah satu dari: {', '.join(allowed_levels)}.",
        )
    try:
        try:
            items = await parse_menu(payload.text)
        except (RuntimeError, ValueError):
            items, _ = parse_menu_fallback(payload.text)
            if not items:
                raise HTTPException(status_code=500, detail="Gagal memproses menu dengan parser AI dan fallback.")
        tkpi_index = load_tkpi_index()
        totals, unmatched = compute_totals_from_items(items, tkpi_index)
        akg_targets = load_akg_targets().get(level)
        if not akg_targets:
            raise RuntimeError(f"AKG untuk level {level} tidak ditemukan.")
        ratios = compute_ratios(totals, akg_targets)
        labels = {nutrient: label_deficiency(ratio) for nutrient, ratio in ratios.items()}
        score = predict_score(ratios)

        # Persist analysis
        analysis = await create_analysis(
            db=db,
            user_id=current_user.id,
            menu_text=payload.text,
            education_level=level,
            score_total=score,
        )

        # Build food_item_id map from DB for matched ingredients
        result = await db.execute(
            select(FoodItem).where(FoodItem.is_active.is_(True))
        )
        food_rows = result.scalars().all()
        food_by_norm: Dict[str, int] = {
            _normalize(row.name): row.id for row in food_rows
        }
        food_item_ids: Dict[str, int] = {}
        for item in items:
            name = item.get("name", "")
            if name in food_by_norm:
                food_item_ids[name] = food_by_norm[name]
            else:
                norm = _normalize(name)
                if norm in food_by_norm:
                    food_item_ids[name] = food_by_norm[norm]

        await create_ingredients(
            db=db,
            analysis_id=analysis.id,
            ingredients=items,
            food_item_ids=food_item_ids,
        )

        # Generate & persist recommendations (filtered by kabupaten)
        deficiencies = {n: labels[n] for n in labels}
        try:
            if payload.kabupaten:
                local_result = await db.execute(
                    select(FoodItem)
                    .join(LocalCatalogItem, LocalCatalogItem.food_item_id == FoodItem.id)
                    .where(
                        LocalCatalogItem.kabupaten == payload.kabupaten,
                        LocalCatalogItem.is_available.is_(True),
                        FoodItem.is_active.is_(True),
                    )
                    .order_by(FoodItem.name.asc())
                )
                local_foods = local_result.scalars().all()
            else:
                local_foods = food_rows

            recommendations = await generate_menu_alternatives(
                deficiencies=deficiencies,
                local_catalog=[r.name for r in local_foods],
                count=3,
            )
            for rec_text in recommendations:
                await create_recommendation(
                    db=db,
                    analysis_id=analysis.id,
                    title=rec_text[:200],
                    projected_score=min(score + 10.0, 100.0),
                    notes=rec_text,
                )
        except (RuntimeError, ValueError):
            pass

        await db.commit()
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ClassifyMenuResponse(
        analysis_id=analysis.id,
        items=items,
        totals=totals,
        ratios=ratios,
        labels=labels,
        score=score,
        unmatched_items=unmatched,
    )
