from fastapi import APIRouter, Depends, HTTPException

from app.ai.generator import generate_menu_alternatives
from app.ai.parser import parse_menu
from app.api.dependencies import check_rate_limit
from app.ml.classifier import predict_score
from app.ml.nutrition import (
    compute_ratios,
    compute_totals_from_items,
    label_deficiency,
    load_akg_targets,
    load_tkpi_index,
)
from app.schemas.ai import (
    ClassifyMenuRequest,
    ClassifyMenuResponse,
    ParseMenuRequest,
    ParseMenuResponse,
    RecommendRequest,
    RecommendResponse,
)

router = APIRouter(tags=["ai"])


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
