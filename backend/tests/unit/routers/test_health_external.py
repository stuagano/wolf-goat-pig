"""Tests for GET /health/external: guard, cache, and status aggregation.
external_checks.check_all is patched so no real network occurs."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.observability.external_checks import ServiceStatus
from app.routers import health

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_cache():
    health._EXTERNAL_CACHE.update(at=0.0, payload=None, http_status=200)
    yield
    health._EXTERNAL_CACHE.update(at=0.0, payload=None, http_status=200)


def _stub(monkeypatch, statuses, counter=None):
    async def fake_check_all():
        if counter is not None:
            counter.append(1)
        return statuses

    monkeypatch.setattr(health, "check_all", fake_check_all)


def test_all_ok_returns_200_healthy(monkeypatch):
    monkeypatch.delenv("MONITOR_KEY", raising=False)
    _stub(monkeypatch, [ServiceStatus("groq", "ok", 10, "ok"), ServiceStatus("ghin", "not_configured")])
    resp = client.get("/health/external")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_one_down_returns_503_unhealthy(monkeypatch):
    monkeypatch.delenv("MONITOR_KEY", raising=False)
    _stub(monkeypatch, [ServiceStatus("groq", "down", 10, "boom"), ServiceStatus("ghin", "not_configured")])
    resp = client.get("/health/external")
    assert resp.status_code == 503
    assert resp.json()["status"] == "unhealthy"


def test_not_configured_does_not_make_unhealthy(monkeypatch):
    monkeypatch.delenv("MONITOR_KEY", raising=False)
    _stub(monkeypatch, [ServiceStatus("groq", "not_configured"), ServiceStatus("ghin", "not_configured")])
    resp = client.get("/health/external")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_guard_rejects_without_key(monkeypatch):
    monkeypatch.setenv("MONITOR_KEY", "secret")
    _stub(monkeypatch, [ServiceStatus("groq", "ok", 10, "ok")])
    assert client.get("/health/external").status_code == 403
    assert client.get("/health/external", headers={"X-Monitor-Key": "wrong"}).status_code == 403
    assert client.get("/health/external", headers={"X-Monitor-Key": "secret"}).status_code == 200


def test_cache_avoids_reprobe(monkeypatch):
    monkeypatch.delenv("MONITOR_KEY", raising=False)
    monkeypatch.setenv("EXTERNAL_HEALTH_TTL", "300")
    calls = []
    _stub(monkeypatch, [ServiceStatus("groq", "ok", 10, "ok")], counter=calls)
    first = client.get("/health/external")
    second = client.get("/health/external")
    assert len(calls) == 1
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
