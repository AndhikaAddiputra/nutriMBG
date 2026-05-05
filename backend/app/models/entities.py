from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="coordinator", nullable=False)
    province: Mapped[str] = mapped_column(String(100), nullable=False)
    kabupaten: Mapped[str] = mapped_column(String(100), nullable=False)
    default_education_level: Mapped[str] = mapped_column(String(20), default="SMP", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class NutritionAKG(Base):
    __tablename__ = "nutrition_akg"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    education_level: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    nutrient_code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="g", nullable=False)
    source: Mapped[str] = mapped_column(String(80), default="Permenkes No. 28 Tahun 2019", nullable=False)


class FoodItem(Base):
    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="DKBM", nullable=False)
    protein: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    carbohydrate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fat: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fiber: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    iron: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    vitamin_a: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class LocalCatalogItem(Base):
    __tablename__ = "local_catalog_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kabupaten: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    food_item_id: Mapped[int] = mapped_column(ForeignKey("food_items.id"), nullable=False, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    seasonal_month: Mapped[Optional[int]] = mapped_column(nullable=True)


class MenuAnalysis(Base):
    __tablename__ = "menu_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    menu_text: Mapped[str] = mapped_column(Text, nullable=False)
    education_level: Mapped[str] = mapped_column(String(20), nullable=False)
    score_total: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MenuIngredient(Base):
    __tablename__ = "menu_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("menu_analyses.id"), nullable=False, index=True)
    food_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("food_items.id"), nullable=True)
    input_name: Mapped[str] = mapped_column(String(150), nullable=False)
    weight_gram: Mapped[float] = mapped_column(Float, nullable=False)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("menu_analyses.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    projected_score: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
