"""Unit tests for spreadsheet_sync router — admin spreadsheet operations."""

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
# GET /admin/spreadsheet/leaderboard
# =============================================================================


class TestGetSpreadsheetLeaderboard:
    def test_returns_200_for_admin(self):
        resp = client.get("/admin/spreadsheet/leaderboard", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    def test_returns_list(self):
        resp = client.get("/admin/spreadsheet/leaderboard", headers=ADMIN_HEADER)
        assert isinstance(resp.json(), list)

    def test_returns_403_without_header(self):
        resp = client.get("/admin/spreadsheet/leaderboard")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get("/admin/spreadsheet/leaderboard", headers=NON_ADMIN_HEADER)
        assert resp.status_code == 403


# =============================================================================
# GET /admin/spreadsheet/rounds
# =============================================================================


class TestGetAllRounds:
    def test_returns_200_for_admin(self):
        resp = client.get("/admin/spreadsheet/rounds", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    def test_returns_list(self):
        resp = client.get("/admin/spreadsheet/rounds", headers=ADMIN_HEADER)
        assert isinstance(resp.json(), list)

    def test_respects_limit_param(self):
        resp = client.get(
            "/admin/spreadsheet/rounds",
            params={"limit": 5},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200

    def test_returns_422_for_limit_below_min(self):
        resp = client.get(
            "/admin/spreadsheet/rounds",
            params={"limit": 0},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 422

    def test_returns_422_for_limit_above_max(self):
        resp = client.get(
            "/admin/spreadsheet/rounds",
            params={"limit": 1001},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 422

    def test_returns_403_without_header(self):
        resp = client.get("/admin/spreadsheet/rounds")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get("/admin/spreadsheet/rounds", headers=NON_ADMIN_HEADER)
        assert resp.status_code == 403


# =============================================================================
# GET /admin/spreadsheet/rounds/by-date/{date}
# =============================================================================


class TestGetRoundsByDate:
    def test_returns_200_for_admin(self):
        resp = client.get(
            "/admin/spreadsheet/rounds/by-date/2026-04-06",
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200

    def test_returns_list(self):
        resp = client.get(
            "/admin/spreadsheet/rounds/by-date/2026-04-06",
            headers=ADMIN_HEADER,
        )
        assert isinstance(resp.json(), list)

    def test_empty_date_returns_empty_list(self):
        resp = client.get(
            "/admin/spreadsheet/rounds/by-date/1900-01-01",
            headers=ADMIN_HEADER,
        )
        assert resp.json() == []

    def test_returns_403_without_header(self):
        resp = client.get("/admin/spreadsheet/rounds/by-date/2026-04-06")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get(
            "/admin/spreadsheet/rounds/by-date/2026-04-06",
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403


# =============================================================================
# GET /admin/spreadsheet/player/{member_name}
# =============================================================================


class TestGetPlayerHistory:
    def test_returns_200_for_admin(self):
        resp = client.get(
            "/admin/spreadsheet/player/Alice",
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200

    def test_returns_list(self):
        resp = client.get(
            "/admin/spreadsheet/player/Alice",
            headers=ADMIN_HEADER,
        )
        assert isinstance(resp.json(), list)

    def test_unknown_player_returns_empty_list(self):
        resp = client.get(
            "/admin/spreadsheet/player/NonExistentPlayer12345",
            headers=ADMIN_HEADER,
        )
        assert resp.json() == []

    def test_returns_403_without_header(self):
        resp = client.get("/admin/spreadsheet/player/Alice")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get(
            "/admin/spreadsheet/player/Alice",
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403


# =============================================================================
# POST /admin/spreadsheet/sync-round
# =============================================================================


class TestSyncRoundToSpreadsheet:
    def _make_sync_payload(self, **overrides):
        payload = {
            "date": "2026-04-08",
            "group": "A",
            "location": "Wing Point",
            "player_scores": [
                {"name": "Alice", "score": 5},
                {"name": "Bob", "score": -5},
            ],
        }
        payload.update(overrides)
        return payload

    def test_returns_202_for_valid_request(self):
        resp = client.post(
            "/admin/spreadsheet/sync-round",
            json=self._make_sync_payload(),
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 202

    def test_returns_queued_status(self):
        resp = client.post(
            "/admin/spreadsheet/sync-round",
            json=self._make_sync_payload(),
            headers=ADMIN_HEADER,
        )
        data = resp.json()
        assert data["status"] == "queued"
        assert "job_id" in data
        assert data["date"] == "2026-04-08"
        assert data["group"] == "A"
        assert "Alice" in data["players"]
        assert "Bob" in data["players"]

    def test_returns_400_for_invalid_date_format(self):
        resp = client.post(
            "/admin/spreadsheet/sync-round",
            json=self._make_sync_payload(date="April 8 2026"),
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 400
        assert "Invalid date format" in resp.json()["detail"]

    def test_returns_422_for_missing_player_scores(self):
        resp = client.post(
            "/admin/spreadsheet/sync-round",
            json={"date": "2026-04-08", "group": "A", "location": "Wing Point"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 422

    def test_returns_422_for_missing_date(self):
        resp = client.post(
            "/admin/spreadsheet/sync-round",
            json={
                "group": "A",
                "location": "Wing Point",
                "player_scores": [{"name": "Alice", "score": 5}],
            },
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 422

    def test_accepts_optional_duration(self):
        resp = client.post(
            "/admin/spreadsheet/sync-round",
            json=self._make_sync_payload(duration="02:30:00"),
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 202

    def test_returns_403_without_header(self):
        resp = client.post(
            "/admin/spreadsheet/sync-round",
            json=self._make_sync_payload(),
        )
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.post(
            "/admin/spreadsheet/sync-round",
            json=self._make_sync_payload(),
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403


# =============================================================================
# GET /admin/spreadsheet/sync-status
# =============================================================================


class TestGetSyncQueueStatus:
    def test_returns_200_for_admin(self):
        resp = client.get("/admin/spreadsheet/sync-status", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    def test_returns_list(self):
        resp = client.get("/admin/spreadsheet/sync-status", headers=ADMIN_HEADER)
        assert isinstance(resp.json(), list)

    def test_respects_limit_param(self):
        resp = client.get(
            "/admin/spreadsheet/sync-status",
            params={"limit": 5},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200

    def test_returns_422_for_limit_below_min(self):
        resp = client.get(
            "/admin/spreadsheet/sync-status",
            params={"limit": 0},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 422

    def test_returns_422_for_limit_above_max(self):
        resp = client.get(
            "/admin/spreadsheet/sync-status",
            params={"limit": 201},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 422

    def test_returns_403_without_header(self):
        resp = client.get("/admin/spreadsheet/sync-status")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get(
            "/admin/spreadsheet/sync-status",
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403


# =============================================================================
# GET /admin/spreadsheet/config
# =============================================================================


class TestGetSpreadsheetConfig:
    @patch("app.routers.spreadsheet_sync._get_access_token")
    def test_returns_200_for_admin(self, mock_token):
        mock_token.return_value = None
        resp = client.get("/admin/spreadsheet/config", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    @patch("app.routers.spreadsheet_sync._get_access_token")
    def test_returns_expected_fields(self, mock_token):
        mock_token.return_value = None
        resp = client.get("/admin/spreadsheet/config", headers=ADMIN_HEADER)
        data = resp.json()
        assert "primary_sheet_id" in data
        assert "writable_sheet_id" in data
        assert "primary_url" in data
        assert "writable_url" in data
        assert "sheets" in data
        assert "details_columns" in data
        assert "oauth_status" in data
        assert "token_status" in data

    @patch("app.routers.spreadsheet_sync._get_access_token")
    def test_token_status_failed_when_no_token(self, mock_token):
        mock_token.return_value = None
        resp = client.get("/admin/spreadsheet/config", headers=ADMIN_HEADER)
        assert resp.json()["token_status"] == "failed"

    @patch("app.routers.spreadsheet_sync._get_access_token")
    def test_token_status_success_when_token_present(self, mock_token):
        mock_token.return_value = "fake-token-123"
        resp = client.get("/admin/spreadsheet/config", headers=ADMIN_HEADER)
        assert resp.json()["token_status"] == "success"

    def test_returns_403_without_header(self):
        resp = client.get("/admin/spreadsheet/config")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get("/admin/spreadsheet/config", headers=NON_ADMIN_HEADER)
        assert resp.status_code == 403


# =============================================================================
# GET /admin/spreadsheet/reconcile/status
# =============================================================================


class TestGetReconciliationStatus:
    @patch("app.routers.spreadsheet_sync.get_reconciliation_service")
    def test_returns_200_on_success(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_sync_status.return_value = {
            "primary": {"count": 100},
            "writable": {"count": 95},
            "is_synced": False,
        }
        mock_get_service.return_value = mock_service

        resp = client.get("/admin/spreadsheet/reconcile/status", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    @patch("app.routers.spreadsheet_sync.get_reconciliation_service")
    def test_returns_500_on_service_error(self, mock_get_service):
        mock_get_service.side_effect = Exception("Service unavailable")
        resp = client.get("/admin/spreadsheet/reconcile/status", headers=ADMIN_HEADER)
        assert resp.status_code == 500

    def test_returns_403_without_header(self):
        resp = client.get("/admin/spreadsheet/reconcile/status")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get(
            "/admin/spreadsheet/reconcile/status",
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403


# =============================================================================
# POST /admin/spreadsheet/reconcile/primary-to-writable
# =============================================================================


class TestSyncPrimaryToWritable:
    @patch("app.routers.spreadsheet_sync.get_reconciliation_service")
    def test_dry_run_returns_200(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.sync_primary_to_writable.return_value = {
            "dry_run": True,
            "rounds_to_copy": 5,
        }
        mock_get_service.return_value = mock_service

        resp = client.post(
            "/admin/spreadsheet/reconcile/primary-to-writable",
            params={"dry_run": True},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200

    @patch("app.routers.spreadsheet_sync.get_reconciliation_service")
    def test_actual_sync_returns_200(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.sync_primary_to_writable.return_value = {
            "dry_run": False,
            "rounds_copied": 5,
        }
        mock_get_service.return_value = mock_service

        resp = client.post(
            "/admin/spreadsheet/reconcile/primary-to-writable",
            params={"dry_run": False},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200

    @patch("app.routers.spreadsheet_sync.get_reconciliation_service")
    def test_default_is_dry_run(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.sync_primary_to_writable.return_value = {"dry_run": True}
        mock_get_service.return_value = mock_service

        client.post(
            "/admin/spreadsheet/reconcile/primary-to-writable",
            headers=ADMIN_HEADER,
        )
        mock_service.sync_primary_to_writable.assert_called_once_with(dry_run=True)

    @patch("app.routers.spreadsheet_sync.get_reconciliation_service")
    def test_returns_500_on_service_error(self, mock_get_service):
        mock_get_service.side_effect = Exception("Sync failed")
        resp = client.post(
            "/admin/spreadsheet/reconcile/primary-to-writable",
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 500

    def test_returns_403_without_header(self):
        resp = client.post("/admin/spreadsheet/reconcile/primary-to-writable")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.post(
            "/admin/spreadsheet/reconcile/primary-to-writable",
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403


# =============================================================================
# POST /admin/spreadsheet/reconcile/writable-to-primary
# =============================================================================


class TestSyncWritableToPrimary:
    @patch("app.routers.spreadsheet_sync.get_reconciliation_service")
    def test_dry_run_returns_200(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.sync_writable_to_primary.return_value = {
            "dry_run": True,
            "rounds_to_copy": 3,
        }
        mock_get_service.return_value = mock_service

        resp = client.post(
            "/admin/spreadsheet/reconcile/writable-to-primary",
            params={"dry_run": True},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200

    @patch("app.routers.spreadsheet_sync.get_reconciliation_service")
    def test_returns_500_on_service_error(self, mock_get_service):
        mock_get_service.side_effect = Exception("Sync failed")
        resp = client.post(
            "/admin/spreadsheet/reconcile/writable-to-primary",
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 500

    def test_returns_403_without_header(self):
        resp = client.post("/admin/spreadsheet/reconcile/writable-to-primary")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.post(
            "/admin/spreadsheet/reconcile/writable-to-primary",
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403


# =============================================================================
# GET /admin/spreadsheet/reconcile/diff
# =============================================================================


class TestGetReconciliationDiff:
    @patch("app.routers.spreadsheet_sync.get_reconciliation_service")
    def test_returns_200_on_success(self, mock_get_service):
        mock_result = MagicMock()
        mock_result.is_synced = True
        mock_result.primary_total = 100
        mock_result.writable_total = 100
        mock_result.matched = 100
        mock_result.primary_only = []
        mock_result.writable_only = []

        mock_service = MagicMock()
        mock_service.compare_sheets.return_value = mock_result
        mock_get_service.return_value = mock_service

        resp = client.get("/admin/spreadsheet/reconcile/diff", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    @patch("app.routers.spreadsheet_sync.get_reconciliation_service")
    def test_returns_expected_structure(self, mock_get_service):
        mock_primary_round = MagicMock()
        mock_primary_round.date = "2026-04-06"
        mock_primary_round.group = "A"
        mock_primary_round.member = "Alice"
        mock_primary_round.score = 5
        mock_primary_round.location = "Wing Point"

        mock_result = MagicMock()
        mock_result.is_synced = False
        mock_result.primary_total = 101
        mock_result.writable_total = 100
        mock_result.matched = 100
        mock_result.primary_only = [mock_primary_round]
        mock_result.writable_only = []

        mock_service = MagicMock()
        mock_service.compare_sheets.return_value = mock_result
        mock_get_service.return_value = mock_service

        resp = client.get("/admin/spreadsheet/reconcile/diff", headers=ADMIN_HEADER)
        data = resp.json()
        assert "summary" in data
        assert data["summary"]["is_synced"] is False
        assert data["summary"]["primary_total"] == 101
        assert data["summary"]["primary_only_count"] == 1
        assert data["summary"]["writable_only_count"] == 0
        assert len(data["primary_only"]) == 1
        assert data["primary_only"][0]["member"] == "Alice"

    @patch("app.routers.spreadsheet_sync.get_reconciliation_service")
    def test_returns_500_on_service_error(self, mock_get_service):
        mock_get_service.side_effect = Exception("Diff failed")
        resp = client.get("/admin/spreadsheet/reconcile/diff", headers=ADMIN_HEADER)
        assert resp.status_code == 500

    def test_returns_403_without_header(self):
        resp = client.get("/admin/spreadsheet/reconcile/diff")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get(
            "/admin/spreadsheet/reconcile/diff",
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403
