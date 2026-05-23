import pytest
from fastapi.testclient import TestClient

from app.api import ai as ai_api
from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_parse_menu_endpoint(client, monkeypatch):
    async def fake_parse_menu(text: str):
        return [{"name": "nasi", "weight_gram": 100.0}]

    monkeypatch.setattr(ai_api, "parse_menu", fake_parse_menu)
    response = client.post("/api/v1/ai/parse", json={"text": "nasi"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["name"] == "nasi"


def test_recommend_menu_endpoint(client, monkeypatch):
    async def fake_generate(deficiencies, local_catalog, count=3):
        return ["Menu A", "Menu B"][:count]

    monkeypatch.setattr(ai_api, "generate_menu_alternatives", fake_generate)
    response = client.post(
        "/api/v1/ai/recommend",
        json={"deficiencies": {"fiber": "Defisien"}, "local_catalog": ["bayam"], "count": 2},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendations"] == ["Menu A", "Menu B"]


def test_classify_menu_endpoint(client, monkeypatch):
    async def fake_parse_menu(text: str):
        return [{"name": "nasi", "weight_gram": 100.0}]

    async def fake_create_analysis(db, user_id, menu_text, education_level, score_total):
        class FakeAnalysis:
            id = 42
            def __getattr__(self, _): return None
        return FakeAnalysis()

    async def fake_create_ingredients(db, analysis_id, ingredients, food_item_ids):
        return []

    async def fake_create_recommendation(db, analysis_id, title, projected_score, notes):
        return None

    class FakeResult:
        def scalars(self): return self
        def all(self): return []

    class FakeDB:
        async def execute(self, *a, **kw): return FakeResult()
        async def commit(self): pass
        async def rollback(self): pass

    async def fake_get_db():
        yield FakeDB()

    monkeypatch.setattr(ai_api, "parse_menu", fake_parse_menu)
    monkeypatch.setattr(ai_api, "create_analysis", fake_create_analysis)
    monkeypatch.setattr(ai_api, "create_ingredients", fake_create_ingredients)
    monkeypatch.setattr(ai_api, "create_recommendation", fake_create_recommendation)
    monkeypatch.setattr(ai_api, "get_db", fake_get_db)
    monkeypatch.setattr(
        ai_api,
        "load_tkpi_index",
        lambda: {
            "nasi": {
                "protein": 2.7,
                "carbohydrate": 28.0,
                "fat": 0.3,
                "fiber": 0.4,
                "iron": 0.2,
                "vitamin_a": 0.0,
            }
        },
    )
    monkeypatch.setattr(
        ai_api,
        "load_akg_targets",
        lambda: {
            "SMP": {
                "protein": 65.0,
                "carbohydrate": 300.0,
                "fat": 80.0,
                "fiber": 25.0,
                "iron": 13.0,
                "vitamin_a": 700.0,
            }
        },
    )
    monkeypatch.setattr(ai_api, "predict_score", lambda ratios: 72.5)

    async def fake_generate(deficiencies, local_catalog, count):
        return []
    monkeypatch.setattr(ai_api, "generate_menu_alternatives", fake_generate)

    response = client.post("/api/v1/ai/classify", json={"text": "nasi", "education_level": "SMP"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["score"] == 72.5
    assert payload["analysis_id"] == 42
    assert payload["labels"]["protein"] in {"Cukup", "Perlu Perhatian", "Defisien"}
