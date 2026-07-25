"""Tests for the Cloud Scheduler → /internal/jobs/* endpoints (Phase 4)."""

import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.routers import internal_jobs
from app.services.email_scheduler import EmailScheduler

TOKEN = "test-internal-token"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def token_set(monkeypatch):
    monkeypatch.setenv("INTERNAL_JOB_TOKEN", TOKEN)


@pytest.fixture
def no_side_effects(monkeypatch):
    """Stub run_job so tests never trigger real emails/syncs."""
    calls = []

    def fake_run_job(job_name):
        calls.append(job_name)
        return {"job": job_name, "status": "completed"}

    monkeypatch.setattr(internal_jobs.email_scheduler, "run_job", fake_run_job)
    return calls


def test_disabled_when_token_unset(client, monkeypatch, no_side_effects):
    """Fail-closed: no INTERNAL_JOB_TOKEN configured → 503, never dispatches."""
    monkeypatch.delenv("INTERNAL_JOB_TOKEN", raising=False)
    resp = client.post("/internal/jobs/daily-reminders")
    assert resp.status_code == 503
    assert no_side_effects == []


def test_wrong_token_forbidden(client, token_set, no_side_effects):
    resp = client.post("/internal/jobs/daily-reminders", headers={"X-Internal-Job-Token": "nope"})
    assert resp.status_code == 403
    assert no_side_effects == []


def test_missing_token_forbidden(client, token_set, no_side_effects):
    resp = client.post("/internal/jobs/daily-reminders")
    assert resp.status_code == 403
    assert no_side_effects == []


def test_unknown_job_404(client, token_set, no_side_effects):
    resp = client.post("/internal/jobs/does-not-exist", headers={"X-Internal-Job-Token": TOKEN})
    assert resp.status_code == 404
    assert no_side_effects == []


@pytest.mark.parametrize("job", list(EmailScheduler.JOB_METHODS))
def test_valid_job_dispatches_with_header(client, token_set, no_side_effects, job):
    resp = client.post(f"/internal/jobs/{job}", headers={"X-Internal-Job-Token": TOKEN})
    assert resp.status_code == 200
    assert resp.json() == {"job": job, "status": "completed"}
    assert no_side_effects == [job]


def test_token_via_query_param(client, token_set, no_side_effects):
    """Uptime/scheduler tools that can't send headers may use ?token=."""
    resp = client.post(f"/internal/jobs/ghin-sync?token={TOKEN}")
    assert resp.status_code == 200
    assert no_side_effects == ["ghin-sync"]


def test_job_methods_resolve_on_scheduler():
    """Every registry key must map to a real method on the scheduler."""
    sched = EmailScheduler()
    for method_name in EmailScheduler.JOB_METHODS.values():
        assert callable(getattr(sched, method_name, None)), method_name
