"""Unit tests for the callouts router.

The endpoint is the external-cron entry point for the headcount callout. These
tests cover the HTTP wiring — window validation, default vs explicit date
dispatch, and response shape — with the service layer stubbed (its own logic is
covered in test_callout_service.py).
"""

from fastapi.testclient import TestClient

from app import routers
from app.main import app

client = TestClient(app)


def test_invalid_window_returns_422():
    resp = client.post("/callouts/run?window=whenever")
    assert resp.status_code == 422
    assert "window must be one of" in resp.json()["detail"]


def test_missing_window_returns_422():
    resp = client.post("/callouts/run")
    assert resp.status_code == 422


def test_default_date_dispatches_to_next_sunday(monkeypatch):
    calls = {}

    def fake_next_sunday(db, window):
        calls["window"] = window
        return {"fired": False, "reason": "not_short", "window": window}

    monkeypatch.setattr(routers.callouts, "run_callout_for_next_sunday", fake_next_sunday)

    resp = client.post("/callouts/run?window=pre_pairing")

    assert resp.status_code == 200
    assert calls["window"] == "pre_pairing"
    assert resp.json()["result"]["reason"] == "not_short"


def test_explicit_date_dispatches_to_run_callout(monkeypatch):
    calls = {}

    def fake_run(db, game_date, window):
        calls["game_date"] = game_date
        calls["window"] = window
        return {"fired": True, "game_date": game_date, "window": window, "recipient_count": 2}

    monkeypatch.setattr(routers.callouts, "run_callout", fake_run)

    resp = client.post("/callouts/run?window=morning_of&game_date=2026-06-21")

    assert resp.status_code == 200
    assert calls == {"game_date": "2026-06-21", "window": "morning_of"}
    assert resp.json()["result"]["recipient_count"] == 2
