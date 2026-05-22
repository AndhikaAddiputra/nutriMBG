"""
tests/test_akg_api.py
=====================
Integration tests for POST/GET/PUT /api/admin/nutrition-akg.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.admin import nutrition_akg as akg_module
from app.core.settings import settings
from app.db.base import Base
from app.main import app
from app.models.entities import NutritionAKG


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
    db_file = tmp_path / "test_akg.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_file}")
    testing_session = async_sessionmaker(engine, expire_on_commit=False)

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with testing_session() as session:
            session.add_all([
                NutritionAKG(
                    education_level="SMP",
                    nutrient_code="protein",
                    target_value=65.0,
                    unit="g",
                    source="Permenkes No. 28 Tahun 2019",
                ),
                NutritionAKG(
                    education_level="SMP",
                    nutrient_code="iron",
                    target_value=15.0,
                    unit="mg",
                    source="Permenkes No. 28 Tahun 2019",
                ),
            ])
            await session.commit()

    asyncio.run(_setup())
    monkeypatch.setattr(akg_module, "AsyncSessionLocal", testing_session)

    with TestClient(app) as c:
        yield c

    asyncio.run(engine.dispose())


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

def test_list_akg_requires_admin(client):
    r = client.get("/api/admin/nutrition-akg")
    assert r.status_code in (401, 403)

def test_list_akg_rejects_coordinator(client):
    r = client.get("/api/admin/nutrition-akg", headers=USER_HEADERS)
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/admin/nutrition-akg
# ---------------------------------------------------------------------------

def test_list_returns_all(client):
    r = client.get("/api/admin/nutrition-akg", headers=ADMIN_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    codes = {row["nutrient_code"] for row in body}
    assert codes == {"protein", "iron"}


def test_list_filter_by_level(client):
    r = client.get("/api/admin/nutrition-akg", headers=ADMIN_HEADERS, params={"education_level": "SMA"})
    assert r.status_code == 200
    assert r.json() == []


# ---------------------------------------------------------------------------
# POST /api/admin/nutrition-akg  (upsert)
# ---------------------------------------------------------------------------

def test_create_new_akg(client):
    payload = {
        "education_level": "SMA",
        "nutrient_code": "vitamin_a",
        "target_value": 700.0,
        "unit": "mcg",
        "source": "Permenkes No. 28 Tahun 2019",
    }
    r = client.post("/api/admin/nutrition-akg", json=payload, headers=ADMIN_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["education_level"] == "SMA"
    assert body["nutrient_code"] == "vitamin_a"
    assert body["target_value"] == 700.0
    assert "id" in body


def test_upsert_existing_updates_value(client):
    """POST with existing (SMP, protein) should update, not duplicate."""
    payload = {
        "education_level": "SMP",
        "nutrient_code": "protein",
        "target_value": 70.0,       # changed from 65.0
        "unit": "g",
        "source": "Revisi 2025",
    }
    r = client.post("/api/admin/nutrition-akg", json=payload, headers=ADMIN_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert body["target_value"] == 70.0
    assert body["source"] == "Revisi 2025"

    # Verify total count is still 2 (no duplicate created)
    r2 = client.get("/api/admin/nutrition-akg", headers=ADMIN_HEADERS)
    smp_rows = [row for row in r2.json() if row["education_level"] == "SMP"]
    protein_rows = [row for row in smp_rows if row["nutrient_code"] == "protein"]
    assert len(protein_rows) == 1


def test_create_invalid_nutrient_code(client):
    payload = {
        "education_level": "SMP",
        "nutrient_code": "sugar",   # invalid
        "target_value": 50.0,
        "unit": "g",
    }
    r = client.post("/api/admin/nutrition-akg", json=payload, headers=ADMIN_HEADERS)
    assert r.status_code == 422


def test_create_invalid_education_level(client):
    payload = {
        "education_level": "UNIVERSITAS",   # invalid
        "nutrient_code": "protein",
        "target_value": 65.0,
        "unit": "g",
    }
    r = client.post("/api/admin/nutrition-akg", json=payload, headers=ADMIN_HEADERS)
    assert r.status_code == 422


def test_create_zero_target_value(client):
    payload = {
        "education_level": "SMP",
        "nutrient_code": "fat",
        "target_value": 0.0,   # must be > 0
        "unit": "g",
    }
    r = client.post("/api/admin/nutrition-akg", json=payload, headers=ADMIN_HEADERS)
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/admin/nutrition-akg/{id}
# ---------------------------------------------------------------------------

def _get_smp_protein_id(client) -> int:
    rows = client.get("/api/admin/nutrition-akg", headers=ADMIN_HEADERS).json()
    return next(r["id"] for r in rows if r["education_level"] == "SMP" and r["nutrient_code"] == "protein")


def test_update_akg(client):
    akg_id = _get_smp_protein_id(client)
    r = client.put(
        f"/api/admin/nutrition-akg/{akg_id}",
        json={"target_value": 68.0, "source": "Permenkes 2024"},
        headers=ADMIN_HEADERS,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["target_value"] == 68.0
    assert body["source"] == "Permenkes 2024"
    assert body["nutrient_code"] == "protein"   # immutable field unchanged


def test_update_akg_partial(client):
    akg_id = _get_smp_protein_id(client)
    r = client.put(
        f"/api/admin/nutrition-akg/{akg_id}",
        json={"unit": "mg"},
        headers=ADMIN_HEADERS,
    )
    assert r.status_code == 200
    assert r.json()["unit"] == "mg"


def test_update_nonexistent_returns_404(client):
    r = client.put(
        "/api/admin/nutrition-akg/9999",
        json={"target_value": 50.0},
        headers=ADMIN_HEADERS,
    )
    assert r.status_code == 404
