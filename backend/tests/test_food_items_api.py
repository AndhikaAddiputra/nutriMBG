"""
tests/test_food_items_api.py
============================
Integration tests for POST/GET/PUT/DELETE /api/admin/food-items.

Strategy
--------
* SQLite in-memory via aiosqlite (matches existing project test pattern)
* JWT tokens minted with the same jwt_secret as Settings so require_admin passes
* The `admin_client` fixture injects an admin-role bearer token automatically
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.admin import food_items as food_items_module
from app.core.settings import settings
from app.db.base import Base
from app.main import app
from app.models.entities import FoodItem


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
USER_HEADERS  = {"Authorization": f"Bearer {_make_token('coordinator')}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(tmp_path, monkeypatch) -> Generator:
    db_file = tmp_path / "test_food.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    testing_session = async_sessionmaker(engine, expire_on_commit=False)

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with testing_session() as session:
            session.add_all([
                FoodItem(
                    name="Ayam Goreng",
                    normalized_name="ayam goreng",
                    source="DKBM",
                    protein=26.0, carbohydrate=5.0, fat=14.0,
                    fiber=0.0, iron=1.3, vitamin_a=60.0,
                    is_active=True,
                ),
                FoodItem(
                    name="Bayam",
                    normalized_name="bayam",
                    source="DKBM",
                    protein=2.9, carbohydrate=3.6, fat=0.4,
                    fiber=2.2, iron=2.7, vitamin_a=470.0,
                    is_active=True,
                ),
            ])
            await session.commit()

    asyncio.run(_setup())
    monkeypatch.setattr(food_items_module, "AsyncSessionLocal", testing_session)

    with TestClient(app) as c:
        yield c

    asyncio.run(engine.dispose())


# ---------------------------------------------------------------------------
# Auth guard tests
# ---------------------------------------------------------------------------

def test_list_requires_auth(client):
    # No token at all → HTTPBearer raises 403 (auto_error=True behaviour in Starlette)
    r = client.get("/api/admin/food-items")
    assert r.status_code in (401, 403)


def test_list_rejects_non_admin(client):
    r = client.get("/api/admin/food-items", headers=USER_HEADERS)
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/admin/food-items
# ---------------------------------------------------------------------------

def test_list_returns_all_active(client):
    r = client.get("/api/admin/food-items", headers=ADMIN_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert "X-Total-Count" in r.headers
    assert r.headers["X-Total-Count"] == "2"


def test_list_pagination(client):
    r = client.get("/api/admin/food-items", headers=ADMIN_HEADERS, params={"per_page": 1, "page": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["page"] == 1
    assert body["per_page"] == 1


def test_list_search(client):
    r = client.get("/api/admin/food-items", headers=ADMIN_HEADERS, params={"search": "ayam"})
    assert r.status_code == 200
    body = r.json()
    # SQLite LIKE is case-insensitive for ASCII; results should include Ayam Goreng
    names = [i["name"] for i in body["items"]]
    assert "Ayam Goreng" in names
    assert all("ayam" in n.lower() for n in names)


# ---------------------------------------------------------------------------
# POST /api/admin/food-items
# ---------------------------------------------------------------------------

def test_create_food_item(client):
    payload = {
        "name": "Tempe Goreng",
        "source": "TKPI",
        "protein": 18.3,
        "carbohydrate": 13.5,
        "fat": 7.7,
        "fiber": 1.4,
        "iron": 4.0,
        "vitamin_a": 0.0,
    }
    r = client.post("/api/admin/food-items", json=payload, headers=ADMIN_HEADERS)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Tempe Goreng"
    assert body["is_active"] is True
    assert "id" in body


def test_create_duplicate_name_returns_422(client):
    payload = {
        "name": "Ayam Goreng",
        "protein": 1.0, "carbohydrate": 1.0, "fat": 1.0,
        "fiber": 0.0, "iron": 0.0, "vitamin_a": 0.0,
    }
    r = client.post("/api/admin/food-items", json=payload, headers=ADMIN_HEADERS)
    assert r.status_code == 422


def test_create_negative_protein_returns_422(client):
    payload = {
        "name": "Invalid Item",
        "protein": -1.0, "carbohydrate": 1.0, "fat": 1.0,
        "fiber": 0.0, "iron": 0.0, "vitamin_a": 0.0,
    }
    r = client.post("/api/admin/food-items", json=payload, headers=ADMIN_HEADERS)
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/admin/food-items/{id}
# ---------------------------------------------------------------------------

def _get_ayam_id(client) -> int:
    r = client.get("/api/admin/food-items", headers=ADMIN_HEADERS, params={"search": "ayam"})
    return r.json()["items"][0]["id"]


def test_update_food_item(client):
    item_id = _get_ayam_id(client)
    r = client.put(
        f"/api/admin/food-items/{item_id}",
        json={"protein": 30.0, "source": "Manual"},
        headers=ADMIN_HEADERS,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["protein"] == 30.0
    assert body["source"] == "Manual"
    assert body["name"] == "Ayam Goreng"  # unchanged


def test_update_nonexistent_returns_404(client):
    r = client.put("/api/admin/food-items/9999", json={"protein": 1.0}, headers=ADMIN_HEADERS)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/admin/food-items/{id}  (soft-delete)
# ---------------------------------------------------------------------------

def test_soft_delete(client):
    item_id = _get_ayam_id(client)
    r = client.delete(f"/api/admin/food-items/{item_id}", headers=ADMIN_HEADERS)
    assert r.status_code == 204

    # Item should NOT appear in active listing
    r2 = client.get("/api/admin/food-items", headers=ADMIN_HEADERS)
    names = [i["name"] for i in r2.json()["items"]]
    assert "Ayam Goreng" not in names

    # But should appear when include_inactive=true
    r3 = client.get(
        "/api/admin/food-items",
        headers=ADMIN_HEADERS,
        params={"include_inactive": True},
    )
    all_names = [i["name"] for i in r3.json()["items"]]
    assert "Ayam Goreng" in all_names
    deleted = next(i for i in r3.json()["items"] if i["name"] == "Ayam Goreng")
    assert deleted["is_active"] is False


def test_delete_nonexistent_returns_404(client):
    r = client.delete("/api/admin/food-items/9999", headers=ADMIN_HEADERS)
    assert r.status_code == 404