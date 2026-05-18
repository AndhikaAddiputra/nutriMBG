import pytest
from fastapi.testclient import TestClient
# from app.main import app

# Dummy
from fastapi import FastAPI
from app.api import auth
app = FastAPI()
app.include_router(auth.router)

client = TestClient(app)

def test_login_success_koordinator():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "koor@nutrimbg.go.id",
            "password": "koor123",
            "role": "koordinator"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "koordinator"
    assert "district" in data["user"]
    assert "default_education_level" in data["user"]

def test_login_success_admin():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@nutrimbg.go.id",
            "password": "admin123",
            "role": "administrator"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "administrator"
    assert "managed_provinces" in data["user"]
    assert type(data["user"]["managed_provinces"]) == list

def test_role_mismatch_koordinator_tab_admin():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "koor@nutrimbg.go.id",
            "password": "koor123",
            "role": "administrator"
        }
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Peran tidak sesuai. Silakan pilih peran yang benar."

def test_role_mismatch_admin_tab_koordinator():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@nutrimbg.go.id",
            "password": "admin123",
            "role": "koordinator"
        }
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Peran tidak sesuai. Silakan pilih peran yang benar."

def test_login_invalid_credentials():
    response = client.post(
        "/api/auth/login",
        json={
            "email": "koor@nutrimbg.go.id",
            "password": "salahpassword",
            "role": "koordinator"
        }
    )
    assert response.status_code == 401