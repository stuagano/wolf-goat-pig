"""Unit tests for email routes router — send/status/confirmation/reminder/summary/scheduler."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# =============================================================================
# POST /email/send-test
# =============================================================================


class TestSendTestEmail:
    @patch("app.routers.email_routes.get_email_service")
    def test_returns_200_on_success(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_signup_confirmation.return_value = True
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/send-test",
            json={"to_email": "user@example.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["to_email"] == "user@example.com"

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_503_when_not_configured(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = False
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/send-test",
            json={"to_email": "user@example.com"},
        )
        assert resp.status_code == 503

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_400_without_to_email(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_get_svc.return_value = mock_svc
        resp = client.post("/email/send-test", json={})
        assert resp.status_code == 400

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_500_when_send_fails(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_signup_confirmation.return_value = False
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/send-test",
            json={"to_email": "user@example.com"},
        )
        assert resp.status_code == 500

    @patch("app.routers.email_routes.get_email_service")
    def test_passes_optional_fields(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_signup_confirmation.return_value = True
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/send-test",
            json={
                "to_email": "user@example.com",
                "player_name": "Jane",
                "signup_date": "2026-04-10",
            },
        )
        assert resp.status_code == 200
        mock_svc.send_signup_confirmation.assert_called_once_with(
            to_email="user@example.com",
            player_name="Jane",
            signup_date="2026-04-10",
        )

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_500_on_unexpected_error(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_signup_confirmation.side_effect = RuntimeError("oops")
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/send-test",
            json={"to_email": "user@example.com"},
        )
        assert resp.status_code == 500


# =============================================================================
# GET /email/status
# =============================================================================


class TestGetEmailServiceStatus:
    @patch("app.routers.email_routes.get_email_service")
    def test_returns_200(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.get_provider_status.return_value = {"provider": "smtp", "configured": True}
        mock_get_svc.return_value = mock_svc
        resp = client.get("/email/status")
        assert resp.status_code == 200
        assert resp.json()["provider"] == "smtp"

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_500_on_error(self, mock_get_svc):
        mock_get_svc.side_effect = RuntimeError("boom")
        resp = client.get("/email/status")
        assert resp.status_code == 500


# =============================================================================
# POST /email/signup-confirmation
# =============================================================================


class TestSendSignupConfirmation:
    @patch("app.routers.email_routes.get_email_service")
    def test_returns_200_on_success(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_signup_confirmation.return_value = True
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/signup-confirmation",
            json={
                "to_email": "player@example.com",
                "player_name": "Alice",
                "signup_date": "2026-04-10",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["to_email"] == "player@example.com"

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_503_when_not_configured(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = False
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/signup-confirmation",
            json={
                "to_email": "player@example.com",
                "player_name": "Alice",
                "signup_date": "2026-04-10",
            },
        )
        assert resp.status_code == 503

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_400_for_missing_fields(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_get_svc.return_value = mock_svc
        # Missing player_name and signup_date
        resp = client.post(
            "/email/signup-confirmation",
            json={"to_email": "player@example.com"},
        )
        assert resp.status_code == 400
        assert "player_name" in resp.json()["detail"]

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_400_for_all_missing(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_get_svc.return_value = mock_svc
        resp = client.post("/email/signup-confirmation", json={})
        assert resp.status_code == 400

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_500_when_send_fails(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_signup_confirmation.return_value = False
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/signup-confirmation",
            json={
                "to_email": "player@example.com",
                "player_name": "Alice",
                "signup_date": "2026-04-10",
            },
        )
        assert resp.status_code == 500


# =============================================================================
# POST /email/daily-reminder
# =============================================================================


class TestSendDailyReminder:
    @patch("app.routers.email_routes.get_email_service")
    def test_returns_200_on_success(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_daily_signup_reminder.return_value = True
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/daily-reminder",
            json={"to_email": "player@example.com", "player_name": "Bob"},
        )
        assert resp.status_code == 200

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_503_when_not_configured(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = False
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/daily-reminder",
            json={"to_email": "player@example.com", "player_name": "Bob"},
        )
        assert resp.status_code == 503

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_400_for_missing_fields(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_get_svc.return_value = mock_svc
        resp = client.post("/email/daily-reminder", json={"to_email": "a@b.com"})
        assert resp.status_code == 400
        assert "player_name" in resp.json()["detail"]

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_500_when_send_fails(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_daily_signup_reminder.return_value = False
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/daily-reminder",
            json={"to_email": "player@example.com", "player_name": "Bob"},
        )
        assert resp.status_code == 500

    @patch("app.routers.email_routes.get_email_service")
    def test_passes_available_dates(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_daily_signup_reminder.return_value = True
        mock_get_svc.return_value = mock_svc
        dates = ["2026-04-10", "2026-04-12"]
        resp = client.post(
            "/email/daily-reminder",
            json={
                "to_email": "player@example.com",
                "player_name": "Bob",
                "available_dates": dates,
            },
        )
        assert resp.status_code == 200
        mock_svc.send_daily_signup_reminder.assert_called_once_with(
            to_email="player@example.com",
            player_name="Bob",
            available_dates=dates,
        )


# =============================================================================
# POST /email/weekly-summary
# =============================================================================


class TestSendWeeklySummary:
    @patch("app.routers.email_routes.get_email_service")
    def test_returns_200_on_success(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_weekly_summary.return_value = True
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/weekly-summary",
            json={"to_email": "player@example.com", "player_name": "Carol"},
        )
        assert resp.status_code == 200

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_503_when_not_configured(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = False
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/weekly-summary",
            json={"to_email": "player@example.com", "player_name": "Carol"},
        )
        assert resp.status_code == 503

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_400_for_missing_fields(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_get_svc.return_value = mock_svc
        resp = client.post("/email/weekly-summary", json={})
        assert resp.status_code == 400

    @patch("app.routers.email_routes.get_email_service")
    def test_returns_500_when_send_fails(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_weekly_summary.return_value = False
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/email/weekly-summary",
            json={"to_email": "player@example.com", "player_name": "Carol"},
        )
        assert resp.status_code == 500

    @patch("app.routers.email_routes.get_email_service")
    def test_passes_summary_data(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_weekly_summary.return_value = True
        mock_get_svc.return_value = mock_svc
        summary = {"total_games": 3, "net_score": 12}
        resp = client.post(
            "/email/weekly-summary",
            json={
                "to_email": "player@example.com",
                "player_name": "Carol",
                "summary_data": summary,
            },
        )
        assert resp.status_code == 200
        mock_svc.send_weekly_summary.assert_called_once_with(
            to_email="player@example.com",
            player_name="Carol",
            summary_data=summary,
        )


# =============================================================================
# POST /email/initialize-scheduler
# =============================================================================


class TestInitializeScheduler:
    @patch("app.routers.email_routes.get_email_scheduler")
    def test_returns_already_initialized(self, mock_get_scheduler):
        mock_get_scheduler.return_value = MagicMock()
        resp = client.post("/email/initialize-scheduler")
        assert resp.status_code == 200
        assert resp.json()["status"] == "already_initialized"

    @patch("app.routers.email_routes.set_email_scheduler")
    @patch("app.routers.email_routes.get_email_scheduler")
    def test_initializes_scheduler_on_demand(self, mock_get_scheduler, mock_set_scheduler):
        mock_get_scheduler.return_value = None
        with patch(
            "app.services.email_scheduler.email_scheduler",
            create=True,
        ) as mock_scheduler:
            mock_scheduler.start = MagicMock()
            resp = client.post("/email/initialize-scheduler")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "scheduled_jobs" in data


# =============================================================================
# GET /email/scheduler-status
# =============================================================================


class TestGetSchedulerStatus:
    @patch("app.routers.email_routes.get_email_scheduler")
    def test_returns_not_initialized(self, mock_get_scheduler):
        mock_get_scheduler.return_value = None
        resp = client.get("/email/scheduler-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["initialized"] is False
        assert data["running"] is False

    @patch("app.routers.email_routes.get_email_scheduler")
    def test_returns_initialized_and_running(self, mock_get_scheduler):
        mock_scheduler = MagicMock()
        mock_scheduler._started = True
        mock_get_scheduler.return_value = mock_scheduler
        resp = client.get("/email/scheduler-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["initialized"] is True
        assert data["running"] is True
        assert "running" in data["message"].lower()
