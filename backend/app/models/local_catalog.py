"""
models/local_catalog.py
=======================
SQLAlchemy model for the LocalIngredientCatalog table.

Links FoodItem → District with availability flags and optional
seasonal unavailability (list of month numbers 1–12).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LocalIngredientCatalog(Base):
    __tablename__ = "local_ingredient_catalog"
    __table_args__ = (
        UniqueConstraint(
            "food_item_id",
            "district_id",
            name="uq_local_catalog_food_district",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    food_item_id: Mapped[int] = mapped_column(
        ForeignKey("food_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    district_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Kabupaten/Kota identifier, e.g. 'Kabupaten Bandung'",
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the ingredient is available in this district",
    )
    # Stored as a PostgreSQL INTEGER[] array (month numbers 1-12).
    # NULL means available all year; a non-empty array means the ingredient
    # is unavailable during those months.
    unavailable_months: Mapped[Optional[List[int]]] = mapped_column(
        ARRAY(Integer),
        nullable=True,
        default=None,
        comment="Months (1–12) when the ingredient is not available seasonally",
    )
