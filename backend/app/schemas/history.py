from datetime import date
from typing import List, Literal

from pydantic import BaseModel


COMPONENT_LITERAL = Literal[
    "composite",
    "protein",
    "carbohydrate",
    "fat",
    "fiber",
    "iron",
    "vitamin_a",
]


class TrendDataPoint(BaseModel):
    """A single data point in a nutrition trend series."""

    date: date
    score: float
    component: str
    is_flagged: bool  # True when score is > 1 std-dev below the rolling mean


class TrendResponse(BaseModel):
    """Full trend response envelope."""

    days: int
    component: str
    data: List[TrendDataPoint]
    has_enough_data: bool  # False when fewer than 7 calendar days have data
