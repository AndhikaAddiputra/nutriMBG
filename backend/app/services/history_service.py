"""
history_service.py
==================
Queries MenuAnalysis (and its linked MenuIngredient + FoodItem rows) to build
a 4-week rolling daily nutrition score for the Pelacak Tren Gizi Mingguan.

Supported components
--------------------
  "composite"   – score_total column of MenuAnalysis
  "protein"     – daily avg protein ratio vs AKG
  "carbohydrate"
  "fat"
  "fiber"
  "iron"
  "vitamin_a"

Outlier flag
------------
A date is flagged (is_flagged=True) when its daily average score is more than
one population standard deviation below the global mean of the time window.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import FoodItem, MenuAnalysis, MenuIngredient, NutritionAKG
from app.schemas.history import TrendDataPoint, TrendResponse

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

VALID_COMPONENTS = {
    "composite",
    "protein",
    "carbohydrate",
    "fat",
    "fiber",
    "iron",
    "vitamin_a",
}

# Nutrient columns that exist directly on FoodItem
_NUTRIENT_COLS = {
    "protein": "protein",
    "carbohydrate": "carbohydrate",
    "fat": "fat",
    "fiber": "fiber",
    "iron": "iron",
    "vitamin_a": "vitamin_a",
}

# Fallback AKG targets (Permenkes 28/2019, SMP as default)
_DEFAULT_AKG: Dict[str, float] = {
    "protein": 65.0,
    "carbohydrate": 300.0,
    "fat": 65.0,
    "fiber": 28.0,
    "iron": 15.0,
    "vitamin_a": 600.0,
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _flag_outliers(daily_scores: Dict[date, float]) -> Dict[date, bool]:
    """Return a mapping of date → is_flagged.

    A day is flagged when its score is more than one standard deviation
    below the mean.  If there are fewer than 2 data points we cannot
    compute a std-dev, so nothing is flagged.
    """
    if len(daily_scores) < 2:
        return {d: False for d in daily_scores}

    values = list(daily_scores.values())
    mean = statistics.mean(values)
    # Use population std-dev (whole window, not a sample)
    stdev = statistics.pstdev(values)

    threshold = mean - stdev
    return {d: (score < threshold) for d, score in daily_scores.items()}


async def _load_akg(db: AsyncSession, education_level: str = "SMP") -> Dict[str, float]:
    """Load AKG targets from the DB; fall back to hard-coded defaults."""
    result = await db.execute(
        select(NutritionAKG).where(
            NutritionAKG.education_level == education_level.upper()
        )
    )
    rows = result.scalars().all()
    if not rows:
        return _DEFAULT_AKG.copy()
    return {row.nutrient_code: row.target_value for row in rows}


# ---------------------------------------------------------------------------
# Composite score path
# ---------------------------------------------------------------------------


async def _composite_daily(
    db: AsyncSession,
    since: datetime,
) -> Dict[date, List[float]]:
    """Return {date: [score, ...]} from score_total on MenuAnalysis."""
    result = await db.execute(
        select(
            func.date(MenuAnalysis.created_at).label("day"),
            MenuAnalysis.score_total,
        ).where(MenuAnalysis.created_at >= since)
    )
    daily: Dict[date, List[float]] = defaultdict(list)
    for row in result:
        day = row.day if isinstance(row.day, date) else date.fromisoformat(str(row.day))
        daily[day].append(float(row.score_total))
    return daily


# ---------------------------------------------------------------------------
# Per-nutrient score path
# ---------------------------------------------------------------------------


async def _nutrient_daily(
    db: AsyncSession,
    component: str,
    since: datetime,
    akg: Dict[str, float],
) -> Dict[date, List[float]]:
    """
    Return {date: [ratio_score, ...]} where ratio_score = min(intake/target, 1.0) * 100.

    We join MenuIngredient → FoodItem to compute per-analysis nutrient intake,
    then bucket by day.
    """
    food_col = getattr(FoodItem, _NUTRIENT_COLS[component])

    # Sum of (weight_gram / 100) * nutrient_per_100g per analysis
    result = await db.execute(
        select(
            MenuAnalysis.id.label("analysis_id"),
            func.date(MenuAnalysis.created_at).label("day"),
            func.sum(MenuIngredient.weight_gram / 100.0 * food_col).label("intake"),
        )
        .join(MenuIngredient, MenuIngredient.analysis_id == MenuAnalysis.id)
        .join(FoodItem, FoodItem.id == MenuIngredient.food_item_id)
        .where(MenuAnalysis.created_at >= since)
        .group_by(MenuAnalysis.id, func.date(MenuAnalysis.created_at))
    )

    target = akg.get(component, _DEFAULT_AKG.get(component, 1.0))
    daily: Dict[date, List[float]] = defaultdict(list)
    for row in result:
        day = row.day if isinstance(row.day, date) else date.fromisoformat(str(row.day))
        intake = float(row.intake or 0.0)
        score = min(intake / target, 1.0) * 100.0 if target > 0 else 0.0
        daily[day].append(score)
    return daily


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_trend(
    db: AsyncSession,
    *,
    days: int = 28,
    component: str = "all",
    education_level: str = "SMP",
) -> List[TrendResponse]:
    """
    Build trend data for the requested component(s).

    Parameters
    ----------
    db              : AsyncSession
    days            : rolling window in calendar days (default 28)
    component       : one of VALID_COMPONENTS, or "all" to return every component
    education_level : used when fetching AKG targets for per-nutrient ratios

    Returns
    -------
    List[TrendResponse] – one entry per component requested.
    """
    since = _utc_now() - timedelta(days=days)

    if component == "all":
        components = list(VALID_COMPONENTS)
    elif component in VALID_COMPONENTS:
        components = [component]
    else:
        components = ["composite"]

    akg = await _load_akg(db, education_level)
    results: List[TrendResponse] = []

    for comp in components:
        # ----- fetch raw daily buckets -----
        if comp == "composite":
            daily_buckets = await _composite_daily(db, since)
        else:
            daily_buckets = await _nutrient_daily(db, comp, since, akg)

        # ----- average each day -----
        daily_avg: Dict[date, float] = {
            d: (sum(scores) / len(scores)) for d, scores in daily_buckets.items()
        }

        # ----- flag outliers -----
        flags = _flag_outliers(daily_avg)

        # ----- build data points sorted ascending -----
        data_points: List[TrendDataPoint] = [
            TrendDataPoint(
                date=d,
                score=round(daily_avg[d], 2),
                component=comp,
                is_flagged=flags[d],
            )
            for d in sorted(daily_avg.keys())
        ]

        has_enough = len(daily_avg) >= 7

        results.append(
            TrendResponse(
                days=days,
                component=comp,
                data=data_points,
                has_enough_data=has_enough,
            )
        )

    return results
