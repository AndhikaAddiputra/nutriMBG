from app.api import ai as ai_api
from app.core.rate_limiter import get_rate_limiter


def test_101st_request_returns_429(client, monkeypatch):
    limiter = get_rate_limiter()
    limiter.clear_memory()

    async def fake_parse_menu(text: str):
        return [{"name": "nasi", "weight_gram": 100.0}]

    monkeypatch.setattr(ai_api, "parse_menu", fake_parse_menu)

    headers = {"X-User-Id": "42", "X-User-Role": "coordinator"}

    for attempt in range(100):
        response = client.post("/api/menu/parse", json={"text": "nasi"}, headers=headers)
        assert response.status_code == 200, attempt
        assert response.headers["X-RateLimit-Limit"] == "100"
        assert response.headers["X-RateLimit-Remaining"] == str(99 - attempt)

    response = client.post("/api/menu/parse", json={"text": "nasi"}, headers=headers)
    assert response.status_code == 429
    assert response.json() == {"detail": "Batas harian 100 permintaan tercapai. Reset pada 00:00 UTC."}
    assert response.headers["X-RateLimit-Limit"] == "100"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert int(response.headers["X-RateLimit-Reset"]) > 0