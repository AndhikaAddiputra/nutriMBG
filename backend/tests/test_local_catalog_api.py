"""
tests/test_local_catalog_api.py
================================
Integration tests for GET/PUT/POST /api/admin/local-catalog.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.admin import local_catalog as catalog_module
from app.core.settings import settings
from app.db.base import Base
from app.main import app
from app.models.entities import FoodItem
from app.models.local_catalog import LocalIngredientCatalog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_token(role: str = "admin") -> str:
    payload = {
        "sub": "1",
        "role": role,
        "exp": int(datetime(2099, 1, 1, tzinfo=timezone.utc).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


ADMIN_HEADERS = {"Authorization": f"Bearer {_make_token('admin')}"}
USER_HEADERS = {"Authorization": f"Bearer {_make_token('coordinator')}"}

DISTRICT_A = "Kabupaten Bandung"
DISTRICT_B = "Kabupaten Sleman"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test_catalog.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    testing_session = async_sessionmaker(engine, expire_on_commit=False)

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with testing_session() as session:
            foods = [
                FoodItem(
                    name="Bayam",
                    normalized_name="bayam",
                    source="DKBM",
                    protein=2.9, carbohydrate=3.6, fat=0.4,
                    fiber=2.2, iron=2.7, vitamin_a=470.0,
                    is_active=True,
                ),
                FoodItem(
                    name="Wortel",
                    normalized_name="wortel",
                    source="DKBM",
                    protein=0.9, carbohydrate=9.6, fat=0.2,
                    fiber=2.8, iron=0.3, vitamin_a=835.0,
                    is_active=True,
                ),
                FoodItem(
                    name="Tempe",
                    normalized_name="tempe",
                    source="DKBM",
                    protein=20.8, carbohydrate=13.5, fat=8.8,
                    fiber=1.4, iron=2.7, vitamin_a=0.0,
                    is_active=True,
                ),
            ]
            session.add_all(foods)
            await session.flush()

            # Seed some catalog entries for DISTRICT_A
            session.add_all([
                LocalIngredientCatalog(
                    food_item_id=foods[0].id,
                    district_id=DISTRICT_A,
                    is_available=True,
                    unavailable_months=None,
                ),
                LocalIngredientCatalog(
                    food_item_id=foods[1].id,
                    district_id=DISTRICT_A,
                    is_available=False,
                    unavailable_months=[6, 7],
                ),
            ])
            await session.commit()

    asyncio.run(_setup())
    monkeypatch.setattr(catalog_module, "AsyncSessionLocal", testing_session)

    with TestClient(app) as c:
        yield c

    asyncio.run(engine.dispose())


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------


def test_requires_admin(client):
    r = client.get(f"/api/admin/local-catalog?district_id={DISTRICT_A}")
    assert r.status_code in (401, 403)


def test_rejects_coordinator(client):
    r = client.get(
        f"/api/admin/local-catalog?district_id={DISTRICT_A}",
        headers=USER_HEADERS,
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/admin/local-catalog
# ---------------------------------------------------------------------------


def test_list_catalog_returns_entries(client):
    r = client.get(
        "/api/admin/local-catalog",
        headers=ADMIN_HEADERS,
        params={"district_id": DISTRICT_A},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert "X-Total-Count" in r.headers
    assert r.headers["X-Total-Count"] == "2"


def test_list_catalog_include_unavailable_false(client):
    r = client.get(
        "/api/admin/local-catalog",
        headers=ADMIN_HEADERS,
        params={"district_id": DISTRICT_A, "include_unavailable": False},
    )
    assert r.status_code == 200
    data = r.json()
    assert all(item["is_available"] for item in data)
    assert len(data) == 1


def test_list_catalog_empty_district(client):
    r = client.get(
        "/api/admin/local-catalog",
        headers=ADMIN_HEADERS,
        params={"district_id": DISTRICT_B},
    )
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# GET /api/admin/local-catalog/districts
# ---------------------------------------------------------------------------


def test_list_districts(client):
    r = client.get("/api/admin/local-catalog/districts", headers=ADMIN_HEADERS)
    assert r.status_code == 200
    districts = r.json()
    assert DISTRICT_A in districts


# ---------------------------------------------------------------------------
# PUT /api/admin/local-catalog/{district_id}/{food_item_id}
# ---------------------------------------------------------------------------


def _get_food_id(client, name: str) -> int:
    r = client.get(
        "/api/admin/local-catalog",
        headers=ADMIN_HEADERS,
        params={"district_id": DISTRICT_A},
    )
    for item in r.json():
        if item["food_item_name"] == name:
            return item["food_item_id"]
    raise ValueError(f"Food '{name}' not found in catalog")


def test_toggle_availability(client):
    food_id = _get_food_id(client, "Bayam")
    r = client.put(
        f"/api/admin/local-catalog/{DISTRICT_A}/{food_id}",
        headers=ADMIN_HEADERS,
        json={"is_available": False, "unavailable_months": []},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["is_available"] is False
    assert body["food_item_name"] == "Bayam"


def test_set_seasonal_months(client):
    food_id = _get_food_id(client, "Bayam")
    r = client.put(
        f"/api/admin/local-catalog/{DISTRICT_A}/{food_id}",
        headers=ADMIN_HEADERS,
        json={"is_available": True, "unavailable_months": [11, 12, 1]},
    )
    assert r.status_code == 200
    body = r.json()
    assert sorted(body["unavailable_months"]) == [1, 11, 12]


def test_create_entry_new_district(client):
    """PUT to a district with no catalog should create a new entry."""
    # Get any food_item_id from existing foods by listing admin food-items
    r_foods = client.get(
        "/api/admin/local-catalog",
        headers=ADMIN_HEADERS,
        params={"district_id": DISTRICT_A},
    )
    food_id = r_foods.json()[0]["food_item_id"]

    r = client.put(
        f"/api/admin/local-catalog/{DISTRICT_B}/{food_id}",
        headers=ADMIN_HEADERS,
        json={"is_available": True, "unavailable_months": []},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["district_id"] == DISTRICT_B
    assert body["is_available"] is True


def test_put_invalid_month(client):
    food_id = _get_food_id(client, "Bayam")
    r = client.put(
        f"/api/admin/local-catalog/{DISTRICT_A}/{food_id}",
        headers=ADMIN_HEADERS,
        json={"is_available": True, "unavailable_months": [13]},  # invalid month
    )
    assert r.status_code == 422


def test_put_nonexistent_food(client):
    r = client.put(
        f"/api/admin/local-catalog/{DISTRICT_A}/9999",
        headers=ADMIN_HEADERS,
        json={"is_available": True},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/admin/local-catalog/bulk
# ---------------------------------------------------------------------------


def test_bulk_update(client):
    # Get food IDs from existing catalog
    r_catalog = client.get(
        "/api/admin/local-catalog",
        headers=ADMIN_HEADERS,
        params={"district_id": DISTRICT_A},
    )
    items = r_catalog.json()
    bulk_items = [
        {
            "food_item_id": item["food_item_id"],
            "is_available": not item["is_available"],  # flip all
            "unavailable_months": [],
        }
        for item in items
    ]

    r = client.post(
        "/api/admin/local-catalog/bulk",
        headers=ADMIN_HEADERS,
        json={"district_id": DISTRICT_A, "items": bulk_items},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["district_id"] == DISTRICT_A
    assert body["updated"] == len(bulk_items)
    assert body["created"] == 0
    assert body["errors"] == []


def test_bulk_update_invalid_food_id(client):
    r = client.post(
        "/api/admin/local-catalog/bulk",
        headers=ADMIN_HEADERS,
        json={
            "district_id": DISTRICT_A,
            "items": [{"food_item_id": 9999, "is_available": True}],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["errors"]) == 1
    assert "9999" in body["errors"][0]


def test_bulk_creates_new_entries(client):
    """Bulk update for a district with no prior catalog creates entries."""
    r_catalog = client.get(
        "/api/admin/local-catalog",
        headers=ADMIN_HEADERS,
        params={"district_id": DISTRICT_A},
    )
    items = r_catalog.json()

    r = client.post(
        "/api/admin/local-catalog/bulk",
        headers=ADMIN_HEADERS,
        json={
            "district_id": DISTRICT_B,
            "items": [
                {"food_item_id": item["food_item_id"], "is_available": True}
                for item in items
            ],
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["created"] == len(items)
    assert body["updated"] == 0
