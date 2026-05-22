from fastapi import APIRouter, Depends, HTTPException
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.generator import generate_menu_alternatives
from app.ai.parser import parse_menu, ManualInputRequired
from app.api.dependencies import check_rate_limit
from app.api.reference import get_db
from app.ml.classifier import predict_score
from app.ml.nutrition import (
    compute_ratios,
    compute_totals_from_items,
    label_deficiency,
    load_akg_targets,
    load_tkpi_index,
)
from app.models.entities import FoodItem, LocalCatalogItem, NutritionAKG
from app.schemas.ai import (
    ClassifyMenuRequest,
    ClassifyMenuResponse,
    ManualAnalyzeRequest,
    ManualAnalyzeResponse,
    ParseMenuRequest,
    ParseMenuResponse,
    RecommendRequest,
    RecommendResponse,
)

router = APIRouter(tags=["ai"])


def _normalize_kabupaten(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned or cleaned == "Semua Kabupaten":
        return None
    return cleaned


async def _load_akg_targets_from_db(db: AsyncSession, education_level: str) -> dict[str, float]:
    query = (
        select(NutritionAKG)
        .where(NutritionAKG.education_level == education_level.upper())
        .order_by(NutritionAKG.nutrient_code.asc())
    )
    result = await db.execute(query)
    rows = result.scalars().all()
    if not rows:
        raise RuntimeError(f"AKG untuk level {education_level} tidak ditemukan.")
    return {row.nutrient_code: row.target_value for row in rows}


def _fallback_akg_level(education_level: str) -> str:
    level = education_level.strip().upper()
    if level in {"SD_1_3", "SD_4_6"}:
        return "SD"
    if level in {"SD", "SMP", "SMA"}:
        return level
    return level


async def _load_food_names_from_db(db: AsyncSession, kabupaten: str | None) -> list[str]:
    if kabupaten:
        query = (
            select(FoodItem.name)
            .join(LocalCatalogItem, LocalCatalogItem.food_item_id == FoodItem.id)
            .where(
                LocalCatalogItem.kabupaten == kabupaten,
                LocalCatalogItem.is_available.is_(True),
                FoodItem.is_active.is_(True),
            )
            .order_by(FoodItem.name.asc())
        )
    else:
        query = select(FoodItem.name).where(FoodItem.is_active.is_(True)).order_by(FoodItem.name.asc())

    result = await db.execute(query)
    names = [row[0] for row in result.all() if row and row[0]]
    return list(dict.fromkeys(names))


@router.post("/parse", response_model=ParseMenuResponse, dependencies=[Depends(check_rate_limit)])
async def parse_menu_endpoint(payload: ParseMenuRequest) -> ParseMenuResponse:
    try:
        items = await parse_menu(payload.text)
    except ManualInputRequired as exc:
        logging.info("Manual input required for parse_menu_endpoint: %s", exc)
        raise HTTPException(
            status_code=422,
            detail={"error": "manual_input_required", "message": str(exc)},
        ) from exc
    except (RuntimeError, ValueError) as exc:
        logging.exception("Error in parse_menu_endpoint")
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


@router.post("/analyze", response_model=ClassifyMenuResponse, dependencies=[Depends(check_rate_limit)])
@router.post("/classify", response_model=ClassifyMenuResponse, dependencies=[Depends(check_rate_limit)])
async def classify_menu_endpoint(payload: ClassifyMenuRequest) -> ClassifyMenuResponse:
    level = payload.education_level.strip().upper()
    if level not in ("SD", "SMP", "SMA"):
        raise HTTPException(status_code=400, detail="education_level harus salah satu dari: SD, SMP, SMA.")
    try:
        items = await parse_menu(payload.text)
        tkpi_index = load_tkpi_index()
        totals, unmatched = compute_totals_from_items(items, tkpi_index)
        akg_targets = load_akg_targets().get(level)
        if not akg_targets:
            raise RuntimeError(f"AKG untuk level {level} tidak ditemukan.")
        ratios = compute_ratios(totals, akg_targets)
        labels = {nutrient: label_deficiency(ratio) for nutrient, ratio in ratios.items()}
        score = predict_score(ratios)
    except ManualInputRequired as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "manual_input_required", "message": str(exc)},
        ) from exc
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ClassifyMenuResponse(
        items=items,
        totals=totals,
        ratios=ratios,
        labels=labels,
        score=score,
        unmatched_items=unmatched,
    )


@router.post("/analyze-manual", response_model=ManualAnalyzeResponse, dependencies=[Depends(check_rate_limit)])
async def analyze_manual_endpoint(
    payload: ManualAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> ManualAnalyzeResponse:
    items = [item.model_dump() for item in payload.items]
    kabupaten = _normalize_kabupaten(payload.kabupaten)
    try:
        tkpi_index = load_tkpi_index()
        totals, unmatched = compute_totals_from_items(items, tkpi_index)
        try:
            akg_targets = await _load_akg_targets_from_db(db, payload.education_level)
        except RuntimeError:
            fallback_level = _fallback_akg_level(payload.education_level)
            akg_targets = load_akg_targets().get(fallback_level)
            if not akg_targets:
                raise
        ratios = compute_ratios(totals, akg_targets)
        labels = {nutrient: label_deficiency(ratio) for nutrient, ratio in ratios.items()}
        score = predict_score(ratios)
        local_catalog = await _load_food_names_from_db(db, kabupaten)
        try:
            recommendations = await generate_menu_alternatives(
                deficiencies=labels,
                local_catalog=local_catalog,
                count=payload.count,
            )
        except (RuntimeError, ValueError):
            logging.exception("Failed to generate menu recommendations for manual analysis")
            recommendations = []
    except (RuntimeError, ValueError, FileNotFoundError) as exc:
        logging.exception("Error in analyze_manual_endpoint")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logging.exception("Unexpected error in analyze_manual_endpoint")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ManualAnalyzeResponse(
        items=items,
        totals=totals,
        ratios=ratios,
        labels=labels,
        score=score,
        unmatched_items=unmatched,
        recommendations=recommendations,
    )
