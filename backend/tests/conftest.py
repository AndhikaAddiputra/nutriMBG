import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.rate_limiter import get_rate_limiter


@pytest.fixture(autouse=True)
def clear_rate_limiter_memory():
    limiter = get_rate_limiter()
    limiter.clear_memory()
    yield
    limiter.clear_memory()


from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
