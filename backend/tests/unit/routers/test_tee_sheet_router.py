"""Unit tests for tee_sheet router — request-shape validation + DB mirror."""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _enable_legacy_tee_sheet(monkeypatch):
    """The legacy CGI connection is off by default; these tests exercise the
    connected behavior, so enable it. The disabled path is covered separately."""
    monkeypatch.setenv("LEGACY_TEE_SHEET_ENABLED", "true")


class TestTeeSheetDisabled:
    def test_endpoints_return_503_when_disabled(self, monkeypatch):
        # No respx mock: the guard must short-circuit before any outbound call.
        monkeypatch.setenv("LEGACY_TEE_SHEET_ENABLED", "false")
        assert client.get("/tee-sheet?date=2026-06-20").status_code == 503
        assert client.post("/tee-sheet/signup", json={"date": "2026-06-20", "name": "Someone"}).status_code == 503


class TestTeeSheetSignupValidation:
    def test_whitespace_only_name_returns_422(self):
        resp = client.post("/tee-sheet/signup", json={"date": "2026-06-20", "name": "  "})
        assert resp.status_code == 422


class TestTeeSheetSignupSafety:
    """Live tee-sheet writes must be gated so preview/testing can't silently
    mutate the real, shared club sheet (issue #323)."""

    @respx.mock
    def test_non_production_returns_preview_without_live_write(self, monkeypatch):
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        monkeypatch.delenv("TEE_SHEET_ALLOW_LIVE_WRITES", raising=False)
        route = respx.post(url__startswith="https://thousand-cranes.com").mock(
            return_value=httpx.Response(200, text="OK")
        )

        resp = client.post("/tee-sheet/signup", json={"date": "2026-06-20", "name": "Preview Golfer"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["live_write"] is False
        assert body["dry_run"] is True
        assert body["would_sign_up"] == {"name": "Preview Golfer", "date": "2026-06-20"}
        # The live CGI was never called.
        assert not route.called

    @respx.mock
    def test_explicit_dry_run_never_writes_even_when_live_enabled(self, monkeypatch):
        monkeypatch.setenv("TEE_SHEET_ALLOW_LIVE_WRITES", "true")
        route = respx.post(url__startswith="https://thousand-cranes.com").mock(
            return_value=httpx.Response(200, text="OK")
        )

        resp = client.post(
            "/tee-sheet/signup",
            json={"date": "2026-06-20", "name": "Preview Golfer", "dry_run": True},
        )

        assert resp.status_code == 200
        assert resp.json()["live_write"] is False
        assert not route.called


class TestTeeSheetSignupMirror:
    """A successful CGI signup mirrors into daily_signups and emails the player.

    Without this, every downstream consumer of daily_signups (callouts,
    pairings, the confirmation email) is blind to thin-client signups.
    """

    @respx.mock
    def test_signup_mirrors_to_db_and_sends_confirmation(self, monkeypatch):
        # Live tee-sheet writes are gated (issue #323); opt this env in explicitly.
        monkeypatch.setenv("TEE_SHEET_ALLOW_LIVE_WRITES", "true")
        respx.post(url__startswith="https://thousand-cranes.com").mock(return_value=httpx.Response(200, text="OK"))

        legacy_name = "Mirrortest Player"
        canonical = "Mirror Canonical"
        email = "mirrortest@example.com"
        date = "2026-07-05"
        now = "2026-06-22T00:00:00"

        def _cleanup():
            db = SessionLocal()
            try:
                db.query(models.DailySignup).filter(models.DailySignup.player_name == legacy_name).delete()
                db.query(models.PlayerProfile).filter(models.PlayerProfile.legacy_name == legacy_name).delete()
                db.commit()
            finally:
                db.close()

        _cleanup()  # in case a prior run left rows in the shared sqlite file
        db = SessionLocal()
        try:
            db.add(
                models.PlayerProfile(
                    name=canonical,
                    legacy_name=legacy_name,
                    email=email,
                    created_at=now,
                    updated_at=now,
                )
            )
            db.commit()
        finally:
            db.close()

        sent: list[tuple] = []

        class _FakeEmail:
            def send_signup_confirmation(self, to_email, player_name, signup_date):
                sent.append((to_email, player_name, signup_date))
                return True

        monkeypatch.setattr("app.services.email_service.get_email_service", lambda: _FakeEmail())

        try:
            resp = client.post("/tee-sheet/signup", json={"date": date, "name": legacy_name})
            assert resp.status_code == 200

            db = SessionLocal()
            try:
                row = (
                    db.query(models.DailySignup)
                    .filter(models.DailySignup.player_name == legacy_name, models.DailySignup.date == date)
                    .first()
                )
                assert row is not None
                assert row.status == "signed_up"
            finally:
                db.close()

            # Confirmation email went to the resolved profile, under the canonical name.
            assert sent == [(email, canonical, date)]
        finally:
            _cleanup()
