"""Unit tests for tee_sheet router — request-shape validation."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestTeeSheetSignupValidation:
    def test_whitespace_only_name_returns_422(self):
        resp = client.post("/tee-sheet/signup", json={"date": "2026-06-20", "name": "  "})
        assert resp.status_code == 422
