import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api import reference
from app.db.base import Base
from app.main import app
from app.models.entities import FoodItem, LocalCatalogItem, NutritionAKG


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    testing_session_local = async_sessionmaker(engine, expire_on_commit=False)

    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with testing_session_local() as session:
            ayam = FoodItem(
                name="Ayam Goreng",
                normalized_name="ayam goreng",
                source="DKBM",
                protein=26.0,
                carbohydrate=5.0,
                fat=14.0,
                fiber=0.0,
                iron=1.3,
                vitamin_a=60.0,
                is_active=True,
            )
            bayam = FoodItem(
                name="Bayam",
                normalized_name="bayam",
                source="DKBM",
                protein=2.9,
                carbohydrate=3.6,
                fat=0.4,
                fiber=2.2,
                iron=2.7,
                vitamin_a=470.0,
                is_active=True,
            )
            session.add_all([ayam, bayam])
            await session.flush()

            session.add_all(
                [
                    NutritionAKG(education_level="SMP", nutrient_code="protein", target_value=65.0, unit="g"),
                    NutritionAKG(education_level="SMP", nutrient_code="fiber", target_value=25.0, unit="g"),
                    LocalCatalogItem(kabupaten="Kabupaten Bandung", food_item_id=ayam.id, is_available=True),
                    LocalCatalogItem(kabupaten="Kabupaten Bandung", food_item_id=bayam.id, is_available=False),
                ]
            )
            await session.commit()

    asyncio.run(init_db())
    monkeypatch.setattr(reference, "AsyncSessionLocal", testing_session_local)

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(engine.dispose())


def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_akg_by_level(client):
    response = client.get("/api/v1/reference/akg/SMP")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert {item["nutrient_code"] for item in payload} == {"protein", "fiber"}


def test_get_foods_all(client):
    response = client.get("/api/v1/reference/foods")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2


def test_get_foods_by_kabupaten_filters_availability(client):
    response = client.get("/api/v1/reference/foods", params={"kabupaten": "Kabupaten Bandung"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["name"] == "Ayam Goreng"
