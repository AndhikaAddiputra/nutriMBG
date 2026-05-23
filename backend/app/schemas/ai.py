from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ParseMenuRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class ParsedIngredient(BaseModel):
    name: str
    weight_gram: float


class ParseMenuResponse(BaseModel):
    items: List[ParsedIngredient]


class RecommendRequest(BaseModel):
    deficiencies: Dict[str, str]
    local_catalog: List[str]
    count: int = Field(default=3, ge=1, le=5)


class RecommendResponse(BaseModel):
    recommendations: List[str]


class ManualAnalyzeRequest(BaseModel):
    items: List[ParsedIngredient]
    education_level: str = Field(min_length=1, max_length=20)
    kabupaten: Optional[str] = None
    count: int = Field(default=3, ge=1, le=5)


class ManualAnalyzeResponse(BaseModel):
    items: List[ParsedIngredient]
    totals: Dict[str, float]
    ratios: Dict[str, float]
    labels: Dict[str, str]
    score: float
    unmatched_items: List[str]
    recommendations: List[str]


class ClassifyMenuRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    education_level: str = Field(min_length=2, max_length=10)


class ClassifyMenuResponse(BaseModel):
    items: List[ParsedIngredient]
    totals: Dict[str, float]
    ratios: Dict[str, float]
    labels: Dict[str, str]
    score: float
    unmatched_items: List[str]
