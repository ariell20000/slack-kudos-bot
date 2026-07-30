#tests/test_app.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


def test_app_builds_and_registers_routes_without_error():
    """Route registration exercises FastAPI/Pydantic response-model schema
    generation for every endpoint, which unit tests that import services
    directly never trigger. This caught a real bug: TypedDict response
    models imported from `typing` (instead of `typing_extensions`) crash
    on Python < 3.12 during this exact step, but only on app startup."""
    from main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
