"""Endpoints that used to be callable anonymously."""

import pytest
from fastapi.testclient import TestClient

from app import routers
from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("path", ["/admin/ensure-schema", "/admin/seed-course-holes"])
def test_schema_tools_reject_anonymous(path):
    assert client.post(path).status_code in (401, 403)


def test_callout_run_disabled_without_configured_token(monkeypatch):
    monkeypatch.delenv("INTERNAL_JOB_TOKEN", raising=False)
    assert client.post("/callouts/run?window=pre_pairing").status_code == 503


def test_callout_run_rejects_wrong_token(monkeypatch):
    monkeypatch.setenv("INTERNAL_JOB_TOKEN", "right")
    resp = client.post("/callouts/run?window=pre_pairing", headers={"X-Internal-Job-Token": "wrong"})
    assert resp.status_code == 403


def test_callout_run_accepts_right_token(monkeypatch):
    monkeypatch.setenv("INTERNAL_JOB_TOKEN", "right")
    monkeypatch.setattr(routers.callouts, "run_callout_for_next_sunday", lambda db, window: {"sent": 0})
    resp = client.post("/callouts/run?window=pre_pairing", headers={"X-Internal-Job-Token": "right"})
    assert resp.status_code == 200
