"""Unit tests for the spreadsheet ops router.

The endpoint is the external-cron entry point for the nightly drain of the
pending sheet-sync queue. These tests cover the HTTP wiring — that the endpoint
invokes the drain and echoes its summary — with the scheduler's drain stubbed
(its own logic is covered in the email_scheduler tests).
"""

from fastapi.testclient import TestClient

from app import routers
from app.main import app

client = TestClient(app)


def test_drain_invokes_scheduler_and_returns_summary(monkeypatch):
    calls = {"count": 0}
    fake_summary = {"pending": 3, "written": 2, "duplicates": 1, "failed": 0}

    class FakeScheduler:
        def _process_pending_sheet_syncs(self):
            calls["count"] += 1
            return fake_summary

    monkeypatch.setattr(routers.spreadsheet_ops, "email_scheduler", FakeScheduler())

    resp = client.post("/spreadsheet/drain-pending-syncs")

    assert resp.status_code == 200
    assert calls["count"] == 1
    body = resp.json()
    assert body["summary"] == fake_summary
    assert body["message"] == "Pending sheet syncs drained"


def test_drain_returns_500_when_scheduler_raises(monkeypatch):
    class BoomScheduler:
        def _process_pending_sheet_syncs(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(routers.spreadsheet_ops, "email_scheduler", BoomScheduler())

    resp = client.post("/spreadsheet/drain-pending-syncs")

    assert resp.status_code == 500
    assert "Failed to drain" in resp.json()["detail"]
