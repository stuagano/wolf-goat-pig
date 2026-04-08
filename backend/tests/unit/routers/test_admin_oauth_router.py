"""Unit tests for admin OAuth2 router — OAuth2 status, authorize, callback, test email."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ADMIN_EMAIL = "stuagano@gmail.com"
NON_ADMIN_EMAIL = "random@example.com"
ADMIN_HEADER = {"X-Admin-Email": ADMIN_EMAIL}
NON_ADMIN_HEADER = {"X-Admin-Email": NON_ADMIN_EMAIL}


# =============================================================================
# GET /admin/oauth2-status
# =============================================================================


class TestGetOAuth2Status:
    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_200_for_admin(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.get_configuration_status.return_value = {"provider": "gmail", "configured": True}
        mock_get_svc.return_value = mock_svc
        resp = client.get("/admin/oauth2-status", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_status_payload(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.get_configuration_status.return_value = {"provider": "gmail", "configured": True}
        mock_get_svc.return_value = mock_svc
        resp = client.get("/admin/oauth2-status", headers=ADMIN_HEADER)
        data = resp.json()
        assert "status" in data
        assert data["status"]["configured"] is True

    def test_returns_403_without_header(self):
        resp = client.get("/admin/oauth2-status")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get("/admin/oauth2-status", headers=NON_ADMIN_HEADER)
        assert resp.status_code == 403

    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_500_on_service_error(self, mock_get_svc):
        mock_get_svc.side_effect = RuntimeError("boom")
        resp = client.get("/admin/oauth2-status", headers=ADMIN_HEADER)
        assert resp.status_code == 500


# =============================================================================
# POST /admin/oauth2-authorize
# =============================================================================


class TestStartOAuth2Authorization:
    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_200_with_auth_url(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.get_auth_url.return_value = "https://accounts.google.com/o/oauth2/auth?foo=bar"
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/admin/oauth2-authorize",
            json={"from_email": "test@example.com"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "auth_url" in data
        assert data["auth_url"].startswith("https://")

    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_message_field(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.get_auth_url.return_value = "https://example.com"
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/admin/oauth2-authorize",
            json={},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_returns_403_without_header(self):
        resp = client.post("/admin/oauth2-authorize", json={})
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.post(
            "/admin/oauth2-authorize",
            json={},
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403

    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_400_when_credentials_missing(self, mock_get_svc):
        mock_get_svc.side_effect = FileNotFoundError("no creds")
        resp = client.post(
            "/admin/oauth2-authorize",
            json={},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 400
        assert "credentials" in resp.json()["detail"].lower()

    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_500_on_unexpected_error(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.get_auth_url.side_effect = RuntimeError("unexpected")
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/admin/oauth2-authorize",
            json={},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 500

    @patch("app.routers.admin_oauth.get_email_service")
    def test_sets_from_email_on_service(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.get_auth_url.return_value = "https://example.com"
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/admin/oauth2-authorize",
            json={"from_email": "custom@example.com", "from_name": "Custom Name"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200
        assert mock_svc.from_email == "custom@example.com"
        assert mock_svc.from_name == "Custom Name"


# =============================================================================
# GET /admin/oauth2-callback
# =============================================================================


class TestHandleOAuth2Callback:
    @patch("app.routers.admin_oauth.get_email_service")
    def test_success_returns_html_200(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.handle_oauth_callback.return_value = True
        mock_get_svc.return_value = mock_svc
        resp = client.get("/admin/oauth2-callback", params={"code": "authcode123"})
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Authorization Successful" in resp.text

    @patch("app.routers.admin_oauth.get_email_service")
    def test_failure_returns_html_400(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.handle_oauth_callback.return_value = False
        mock_get_svc.return_value = mock_svc
        resp = client.get("/admin/oauth2-callback", params={"code": "badcode"})
        assert resp.status_code == 400
        assert "text/html" in resp.headers["content-type"]
        assert "Authorization Failed" in resp.text

    def test_missing_code_returns_422(self):
        resp = client.get("/admin/oauth2-callback")
        assert resp.status_code == 422

    @patch("app.routers.admin_oauth.get_email_service")
    def test_exception_returns_html_500(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.handle_oauth_callback.side_effect = RuntimeError("token exchange failed")
        mock_get_svc.return_value = mock_svc
        resp = client.get("/admin/oauth2-callback", params={"code": "err"})
        assert resp.status_code == 500
        assert "text/html" in resp.headers["content-type"]
        assert "OAuth2 Error" in resp.text

    @patch("app.routers.admin_oauth.get_email_service")
    def test_accepts_optional_state_param(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.handle_oauth_callback.return_value = True
        mock_get_svc.return_value = mock_svc
        resp = client.get(
            "/admin/oauth2-callback",
            params={"code": "abc", "state": "mystate"},
        )
        assert resp.status_code == 200


# =============================================================================
# POST /admin/oauth2-test-email
# =============================================================================


class TestOAuth2TestEmail:
    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_200_on_success(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_test_email.return_value = True
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/admin/oauth2-test-email",
            json={"test_email": "user@example.com"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "user@example.com" in data["message"]

    def test_returns_403_without_header(self):
        resp = client.post(
            "/admin/oauth2-test-email",
            json={"test_email": "user@example.com"},
        )
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.post(
            "/admin/oauth2-test-email",
            json={"test_email": "user@example.com"},
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403

    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_400_without_test_email(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/admin/oauth2-test-email",
            json={},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 400

    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_400_when_not_configured(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = False
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/admin/oauth2-test-email",
            json={"test_email": "user@example.com"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 400

    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_500_when_send_fails(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_test_email.return_value = False
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/admin/oauth2-test-email",
            json={"test_email": "user@example.com"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 500

    @patch("app.routers.admin_oauth.get_email_service")
    def test_returns_500_on_unexpected_error(self, mock_get_svc):
        mock_svc = MagicMock()
        mock_svc.is_configured = True
        mock_svc.send_test_email.side_effect = RuntimeError("SMTP down")
        mock_get_svc.return_value = mock_svc
        resp = client.post(
            "/admin/oauth2-test-email",
            json={"test_email": "user@example.com"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 500
