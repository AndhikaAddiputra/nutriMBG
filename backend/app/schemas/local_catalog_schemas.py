"""
schemas/local_catalog_schemas.py
=================================
Pydantic v2 schemas for the LocalIngredientCatalog admin CRUD endpoints.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Single-item update (PUT)
# ---------------------------------------------------------------------------


class LocalCatalogUpdate(BaseModel):
    """Payload for PUT /api/admin/local-catalog/{district_id}/{food_item_id}."""

    is_available: Optional[bool] = Field(
        default=None,
        description="Set availability for this ingredient in the district",
    )
    unavailable_months: Optional[List[int]] = Field(
        default=None,
        description="Months (1–12) when ingredient is seasonally unavailable. "
                    "Pass an empty list [] to clear seasonal restrictions.",
    )

    @field_validator("unavailable_months")
    @classmethod
    def validate_months(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is None:
            return v
        for month in v:
            if not (1 <= month <= 12):
                raise ValueError(f"Month {month} is out of range. Valid values: 1–12.")
        return sorted(set(v))  # deduplicate and sort


# ---------------------------------------------------------------------------
# Bulk update item (POST bulk)
# ---------------------------------------------------------------------------


class BulkCatalogItem(BaseModel):
    """A single row in a bulk update request."""

    food_item_id: int = Field(description="ID of the FoodItem")
    is_available: bool = Field(description="Availability flag")
    unavailable_months: Optional[List[int]] = Field(
        default=None,
        description="Months (1–12) when ingredient is seasonally unavailable",
    )

    @field_validator("unavailable_months")
    @classmethod
    def validate_months(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is None:
            return v
        for month in v:
            if not (1 <= month <= 12):
                raise ValueError(f"Month {month} is out of range. Valid values: 1–12.")
        return sorted(set(v))


class BulkCatalogUpdateRequest(BaseModel):
    """Payload for POST /api/admin/local-catalog/bulk."""

    district_id: str = Field(
        min_length=1,
        max_length=100,
        description="Kabupaten/Kota identifier",
    )
    items: List[BulkCatalogItem] = Field(
        min_length=1,
        description="List of food items to update for the district",
    )


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class LocalCatalogItemOut(BaseModel):
    """Response shape for catalog endpoints."""

    id: int
    food_item_id: int
    food_item_name: str
    district_id: str
    is_available: bool
    unavailable_months: Optional[List[int]]

    model_config = {"from_attributes": True}


class BulkCatalogUpdateResponse(BaseModel):
    """Summary response for bulk update."""

    district_id: str
    updated: int
    created: int
    errors: List[str] = Field(default_factory=list)
