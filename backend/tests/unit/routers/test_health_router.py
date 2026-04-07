"""Unit tests for health router endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_valid_status_code(self):
        resp = client.get("/health")
        # 200 = healthy, 503 = unhealthy (no real DB in test env)
        assert resp.status_code in (200, 503)

    def test_health_has_status_or_error_field(self):
        resp = client.get("/health")
        data = resp.json()
        # 200 → {"status": ..., "components": ...}
        # 503 → {"error": ..., "detail": ...}
        assert "status" in data or "error" in data

    def test_health_response_is_json(self):
        resp = client.get("/health")
        assert resp.headers["content-type"].startswith("application/json")

    def test_healthz_alias_responds(self):
        resp = client.get("/healthz")
        assert resp.status_code in (200, 503)

    def test_ready_endpoint_exists(self):
        resp = client.get("/ready")
        assert resp.status_code in (200, 503)


class TestHealthComponents:
    def test_health_components_is_dict_when_healthy(self):
        resp = client.get("/health")
        if resp.status_code == 200:
            assert isinstance(resp.json()["components"], dict)

    def test_health_unhealthy_has_detail(self):
        resp = client.get("/health")
        if resp.status_code == 503:
            assert "detail" in resp.json()
