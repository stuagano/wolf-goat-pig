"""Confirmation-pause behaviour: no login gate, asked once, and expiry says so."""

import pytest

from app.agent import REQUEST_CONFIRMATION_DECL, SYSTEM_INSTRUCTION, confirm_job
from app.config import Settings
from app.jobs import BookingJob, JobKind


def test_login_is_not_a_confirmation_kind():
    """A login pause stranded jobs: the instance scaled away while the user read the prompt."""
    kinds = REQUEST_CONFIRMATION_DECL.parameters_json_schema["properties"]["kind"]["enum"]
    assert "login" not in kinds
    assert "submit" in kinds


def test_system_instruction_logs_in_without_asking():
    assert "enter_foretees_credentials() directly" in SYSTEM_INSTRUCTION
    assert 'request_confirmation(kind="login")' not in SYSTEM_INSTRUCTION


def test_confirmation_is_requested_at_most_once():
    """Asking at every submit-ish step cost the user three taps for one booking."""
    assert "ONCE per" in SYSTEM_INSTRUCTION
    assert "at most once per booking" in REQUEST_CONFIRMATION_DECL.description


def test_a_fresh_job_has_not_been_confirmed():
    job = BookingJob(id="j1", kind=JobKind.BOOK, args={})
    assert job.action_confirmed is False


def test_confirm_window_stays_under_cloud_run_idle_reap():
    """Cloud Run reclaims an idle instance at ~15min, taking the job's live browser."""
    assert Settings().job_ttl_seconds < 900


@pytest.mark.asyncio
async def test_confirming_an_unknown_job_reports_expired():
    result = await confirm_job("does-not-exist", True)
    assert result["status"] == "expired"
    assert result["success"] is False
    assert "start the booking again" in result["error"]
