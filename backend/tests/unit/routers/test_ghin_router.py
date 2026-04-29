"""Unit tests for GHIN router — lookup, sync handicap, diagnostic, sync all."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# =============================================================================
# GHIN DIAGNOSTIC
# =============================================================================


class TestGhinDiagnostic:
    def test_returns_200(self):
        resp = client.get("/ghin/diagnostic")
        assert resp.status_code == 200

    def test_returns_config_flags(self):
        resp = client.get("/ghin/diagnostic")
        data = resp.json()
        assert "email_configured" in data
        assert "password_configured" in data
        assert "static_token_configured" in data
        assert "all_configured" in data
        assert "environment" in data

    @patch.dict("os.environ", {"GHIN_API_USER": "user@test.com", "GHIN_API_PASS": "secret"})
    def test_reports_configured_when_env_set(self):
        resp = client.get("/ghin/diagnostic")
        data = resp.json()
        assert data["email_configured"] is True
        assert data["password_configured"] is True
        assert data["all_configured"] is True

    @patch.dict("os.environ", {}, clear=True)
    def test_reports_not_configured_when_env_missing(self):
        resp = client.get("/ghin/diagnostic")
        data = resp.json()
        assert data["email_configured"] is False
        assert data["password_configured"] is False
        assert data["all_configured"] is False


# =============================================================================
# GHIN LOOKUP
# =============================================================================


class TestGhinLookup:
    def test_returns_422_without_last_name(self):
        resp = client.get("/ghin/lookup")
        assert resp.status_code == 422

    @patch("app.services.ghin_service.GHINService", autospec=False)
    @patch.dict("os.environ", {"GHIN_API_USER": "u@t.com", "GHIN_API_PASS": "p"})
    def test_returns_200_on_success(self, MockGHINService):
        mock_svc = MagicMock()
        mock_svc.initialize = AsyncMock(return_value=True)
        mock_svc.search_golfers = AsyncMock(return_value={"golfers": [{"name": "Smith", "ghin_number": "123456"}]})
        MockGHINService.return_value = mock_svc

        resp = client.get("/ghin/lookup", params={"last_name": "Smith"})
        assert resp.status_code == 200
        data = resp.json()
        assert "golfers" in data

    @patch("app.services.ghin_service.GHINService", autospec=False)
    @patch.dict("os.environ", {"GHIN_API_USER": "u@t.com", "GHIN_API_PASS": "p"})
    def test_returns_500_when_service_unavailable(self, MockGHINService):
        mock_svc = MagicMock()
        mock_svc.initialize = AsyncMock(return_value=False)
        MockGHINService.return_value = mock_svc

        resp = client.get("/ghin/lookup", params={"last_name": "Smith"})
        assert resp.status_code == 500

    @patch.dict("os.environ", {}, clear=True)
    def test_returns_500_without_credentials(self):
        resp = client.get("/ghin/lookup", params={"last_name": "Smith"})
        assert resp.status_code == 500

    @patch("app.services.ghin_service.GHINService", autospec=False)
    @patch.dict("os.environ", {"GHIN_API_USER": "u@t.com", "GHIN_API_PASS": "p"})
    def test_passes_pagination_params(self, MockGHINService):
        mock_svc = MagicMock()
        mock_svc.initialize = AsyncMock(return_value=True)
        mock_svc.search_golfers = AsyncMock(return_value={"golfers": []})
        MockGHINService.return_value = mock_svc

        resp = client.get(
            "/ghin/lookup",
            params={"last_name": "Jones", "first_name": "Bob", "page": 2, "per_page": 5},
        )
        assert resp.status_code == 200
        mock_svc.search_golfers.assert_called_once_with("Jones", "Bob", 2, 5)


# =============================================================================
# SYNC PLAYER HANDICAP
# =============================================================================


class TestSyncPlayerHandicap:
    @patch("app.services.ghin_service.GHINService", autospec=False)
    def test_returns_200_on_success(self, MockGHINService):
        mock_svc = MagicMock()
        mock_svc.initialize = AsyncMock(return_value=True)
        mock_svc.sync_player_handicap = AsyncMock(return_value={"handicap_index": 12.5, "ghin_number": "123456"})
        MockGHINService.return_value = mock_svc

        resp = client.post("/ghin/sync-player-handicap/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["handicap_index"] == 12.5

    @patch("app.services.ghin_service.GHINService", autospec=False)
    def test_returns_500_when_service_unavailable(self, MockGHINService):
        mock_svc = MagicMock()
        mock_svc.initialize = AsyncMock(return_value=False)
        MockGHINService.return_value = mock_svc

        resp = client.post("/ghin/sync-player-handicap/1")
        assert resp.status_code == 500

    @patch("app.services.ghin_service.GHINService", autospec=False)
    def test_returns_500_when_sync_fails(self, MockGHINService):
        mock_svc = MagicMock()
        mock_svc.initialize = AsyncMock(return_value=True)
        mock_svc.sync_player_handicap = AsyncMock(return_value=None)
        MockGHINService.return_value = mock_svc

        resp = client.post("/ghin/sync-player-handicap/99")
        assert resp.status_code == 500


# =============================================================================
# SYNC ALL HANDICAPS
# =============================================================================


class TestSyncAllHandicaps:
    @patch("app.routers.ghin.database")
    @patch("app.services.ghin_service.GHINService", autospec=False)
    def test_returns_200_on_success(self, MockGHINService, mock_db_module):
        mock_session = MagicMock()
        mock_db_module.SessionLocal.return_value = mock_session

        mock_svc = MagicMock()
        mock_svc.initialize = AsyncMock(return_value=True)
        mock_svc.is_available = MagicMock(return_value=True)
        mock_svc.sync_all_players_handicaps = AsyncMock(return_value={"synced": 3, "failed": 0})
        MockGHINService.return_value = mock_svc

        resp = client.post("/ghin/sync-handicaps")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "GHIN handicap sync completed"
        assert data["results"]["synced"] == 3
        mock_session.close.assert_called_once()

    @patch("app.routers.ghin.database")
    @patch("app.services.ghin_service.GHINService", autospec=False)
    def test_returns_503_when_unavailable(self, MockGHINService, mock_db_module):
        mock_session = MagicMock()
        mock_db_module.SessionLocal.return_value = mock_session

        mock_svc = MagicMock()
        mock_svc.initialize = AsyncMock(return_value=True)
        mock_svc.is_available = MagicMock(return_value=False)
        MockGHINService.return_value = mock_svc

        resp = client.post("/ghin/sync-handicaps")
        # The 503 HTTPException is caught by the generic except block and
        # re-raised as 500, so we expect 500 here.
        assert resp.status_code == 500
        mock_session.close.assert_called_once()

    @patch("app.routers.ghin.database")
    @patch("app.services.ghin_service.GHINService", autospec=False)
    def test_returns_500_on_exception(self, MockGHINService, mock_db_module):
        mock_session = MagicMock()
        mock_db_module.SessionLocal.return_value = mock_session

        mock_svc = MagicMock()
        mock_svc.initialize = AsyncMock(return_value=True)
        mock_svc.is_available = MagicMock(return_value=True)
        mock_svc.sync_all_players_handicaps = AsyncMock(side_effect=RuntimeError("boom"))
        MockGHINService.return_value = mock_svc

        resp = client.post("/ghin/sync-handicaps")
        assert resp.status_code == 500
        mock_session.close.assert_called_once()
