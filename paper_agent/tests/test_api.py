"""API endpoint tests using TestClient."""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

try:
    from paper_agent.backend.main import app
    client = TestClient(app)
except Exception as e:
    pytest.skip(f"API tests require running backend: {e}", allow_module_level=True)


class TestHealth:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
