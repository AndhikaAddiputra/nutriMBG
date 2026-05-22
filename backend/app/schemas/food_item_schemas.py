"""
schemas/food_item_schemas.py
============================
Pydantic v2 schemas for the FoodItem admin CRUD endpoints.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared nutrition field constraints
# ---------------------------------------------------------------------------

_GE_ZERO = Field(ge=0.0)


class _NutritionBase(BaseModel):
    protein: float = Field(ge=0.0, description="Protein per 100 g (gram)")
    carbohydrate: float = Field(ge=0.0, description="Karbohidrat per 100 g (gram)")
    fat: float = Field(ge=0.0, description="Lemak per 100 g (gram)")
    fiber: float = Field(ge=0.0, description="Serat per 100 g (gram)")
    iron: float = Field(ge=0.0, description="Zat besi per 100 g (mg)")
    vitamin_a: float = Field(ge=0.0, description="Vitamin A per 100 g (mcg RE)")


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class FoodItemCreate(_NutritionBase):
    """Payload for POST /api/admin/food-items."""

    name: str = Field(
        min_length=1,
        max_length=150,
        description="Nama bahan makanan (harus unik)",
    )
    source: str = Field(
        default="DKBM",
        max_length=20,
        description="Sumber data gizi (mis. DKBM, TKPI, Manual)",
    )

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


# ---------------------------------------------------------------------------
# Update (all fields optional — partial update / PATCH semantics via PUT)
# ---------------------------------------------------------------------------


class FoodItemUpdate(BaseModel):
    """Payload for PUT /api/admin/food-items/{id}. All fields optional."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    source: Optional[str] = Field(default=None, max_length=20)
    protein: Optional[float] = Field(default=None, ge=0.0)
    carbohydrate: Optional[float] = Field(default=None, ge=0.0)
    fat: Optional[float] = Field(default=None, ge=0.0)
    fiber: Optional[float] = Field(default=None, ge=0.0)
    iron: Optional[float] = Field(default=None, ge=0.0)
    vitamin_a: Optional[float] = Field(default=None, ge=0.0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v is not None else v


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class FoodItemOut(_NutritionBase):
    """Response shape for all food-item endpoints."""

    id: int
    name: str
    source: str
    is_active: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Paginated list envelope
# ---------------------------------------------------------------------------


class FoodItemPage(BaseModel):
    items: list[FoodItemOut]
    total: int
    page: int
    per_page: int