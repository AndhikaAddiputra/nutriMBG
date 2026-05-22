"""
schemas/akg_schemas.py
======================
Pydantic v2 schemas for the NutritionAKG admin CRUD endpoints.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

# Valid nutrient codes used across the system
VALID_NUTRIENT_CODES = {
    "protein",
    "carbohydrate",
    "fat",
    "fiber",
    "iron",
    "vitamin_a",
}

VALID_EDUCATION_LEVELS = {"SD_1_3", "SD_4_6", "SMP", "SMA"}


# ---------------------------------------------------------------------------
# Create / Upsert
# ---------------------------------------------------------------------------


class AKGCreate(BaseModel):
    """
    Payload for POST /api/admin/nutrition-akg.
    Acts as an upsert: if (education_level, nutrient_code) already exists,
    the existing row is updated instead of raising a duplicate error.
    """

    education_level: str = Field(
        description="Jenjang pendidikan: SD_1_3 | SD_4_6 | SMP | SMA",
    )
    nutrient_code: str = Field(
        description="Kode nutrien: protein | carbohydrate | fat | fiber | iron | vitamin_a",
    )
    target_value: float = Field(gt=0.0, description="Nilai target AKG (harus > 0)")
    unit: str = Field(default="g", max_length=20, description="Satuan (g, mg, mcg, dll.)")
    source: str = Field(
        default="Permenkes No. 28 Tahun 2019",
        max_length=80,
        description="Referensi peraturan / publikasi",
    )

    @field_validator("education_level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in VALID_EDUCATION_LEVELS:
            raise ValueError(
                f"education_level tidak valid. Pilihan: {', '.join(sorted(VALID_EDUCATION_LEVELS))}"
            )
        return v

    @field_validator("nutrient_code")
    @classmethod
    def validate_nutrient(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_NUTRIENT_CODES:
            raise ValueError(
                f"nutrient_code tidak valid. Pilihan: {', '.join(sorted(VALID_NUTRIENT_CODES))}"
            )
        return v


# ---------------------------------------------------------------------------
# Update (partial)
# ---------------------------------------------------------------------------


class AKGUpdate(BaseModel):
    """Payload for PUT /api/admin/nutrition-akg/{id}. All fields optional."""

    target_value: Optional[float] = Field(default=None, gt=0.0)
    unit: Optional[str] = Field(default=None, max_length=20)
    source: Optional[str] = Field(default=None, max_length=80)


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class AKGOut(BaseModel):
    """Response shape for all AKG endpoints."""

    id: int
    education_level: str
    nutrient_code: str
    target_value: float
    unit: str
    source: str

    model_config = {"from_attributes": True}