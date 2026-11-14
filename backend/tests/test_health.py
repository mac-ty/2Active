"""
Health endpoint tests.

Verifies that the health check endpoint is accessible and
returns the expected response when the application is running.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}