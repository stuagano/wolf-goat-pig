"""Unit tests for sheet_integration router — analyze, sync, fetch, compare, export."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# =============================================================================
# POST /sheet-integration/analyze-structure
# =============================================================================


class TestAnalyzeSheetStructure:
    def test_returns_200_with_valid_headers(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json=["Member", "Score", "Average", "Rounds", "Date"],
        )
        assert resp.status_code == 200

    def test_returns_column_mappings(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json=["Member", "Score", "Average", "Rounds", "Date"],
        )
        data = resp.json()
        assert "column_mappings" in data
        assert "total_columns" in data
        assert "mapped_columns" in data

    def test_maps_member_column(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json=["Member"],
        )
        mappings = resp.json()["column_mappings"]
        assert mappings[0]["db_field"] == "player_name"

    def test_maps_score_column(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json=["Score"],
        )
        mappings = resp.json()["column_mappings"]
        assert mappings[0]["db_field"] == "total_earnings"

    def test_maps_average_column(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json=["Average"],
        )
        mappings = resp.json()["column_mappings"]
        assert mappings[0]["db_field"] == "avg_earnings_per_game"

    def test_maps_rounds_column(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json=["Rounds"],
        )
        mappings = resp.json()["column_mappings"]
        assert mappings[0]["db_field"] == "games_played"

    def test_maps_qb_column(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json=["QB"],
        )
        mappings = resp.json()["column_mappings"]
        assert mappings[0]["db_field"] == "qb_count"

    def test_maps_date_column(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json=["Date"],
        )
        mappings = resp.json()["column_mappings"]
        assert mappings[0]["db_field"] == "last_played"

    def test_unmapped_column_gets_empty_string(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json=["UnknownColumn"],
        )
        mappings = resp.json()["column_mappings"]
        assert mappings[0]["db_field"] == ""

    def test_total_columns_count(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json=["Member", "Score", "Foo"],
        )
        assert resp.json()["total_columns"] == 3

    def test_empty_headers_returns_200(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json=[],
        )
        assert resp.status_code == 200
        assert resp.json()["total_columns"] == 0

    def test_player_name_variations(self):
        """All player-name-like headers should map to player_name."""
        for header in ["Player", "Name", "Golfer"]:
            resp = client.post(
                "/sheet-integration/analyze-structure",
                json=[header],
            )
            mappings = resp.json()["column_mappings"]
            assert mappings[0]["db_field"] == "player_name", f"Failed for header: {header}"

    def test_score_column_variations(self):
        """All score-like headers should map to total_earnings."""
        for header in ["Quarters", "Total"]:
            resp = client.post(
                "/sheet-integration/analyze-structure",
                json=[header],
            )
            mappings = resp.json()["column_mappings"]
            assert mappings[0]["db_field"] == "total_earnings", f"Failed for header: {header}"

    def test_returns_422_for_invalid_body(self):
        resp = client.post(
            "/sheet-integration/analyze-structure",
            json="not a list",
        )
        assert resp.status_code == 422


# =============================================================================
# POST /sheet-integration/create-leaderboard
# =============================================================================


class TestCreateLeaderboardFromSheet:
    @patch("app.services.leaderboard_service.LeaderboardService")
    def test_returns_200_on_success(self, mock_cls):
        mock_service = MagicMock()
        mock_service.create_from_sheet_data.return_value = [
            {"name": "Alice", "score": 10},
        ]
        mock_cls.return_value = mock_service

        resp = client.post(
            "/sheet-integration/create-leaderboard",
            json=[{"name": "Alice", "score": 10}],
        )
        assert resp.status_code == 200

    @patch("app.services.leaderboard_service.LeaderboardService")
    def test_returns_leaderboard_fields(self, mock_cls):
        mock_service = MagicMock()
        mock_service.create_from_sheet_data.return_value = [
            {"name": "Alice", "score": 10},
        ]
        mock_cls.return_value = mock_service

        resp = client.post(
            "/sheet-integration/create-leaderboard",
            json=[{"name": "Alice", "score": 10}],
        )
        data = resp.json()
        assert "leaderboard" in data
        assert "player_count" in data
        assert "created_at" in data

    def test_returns_500_when_service_unavailable(self):
        # Without mocking, the real service import may fail or error
        resp = client.post(
            "/sheet-integration/create-leaderboard",
            json=[{"name": "Alice", "score": 10}],
        )
        assert resp.status_code == 500

    def test_returns_422_for_invalid_body(self):
        resp = client.post(
            "/sheet-integration/create-leaderboard",
            json="not a list",
        )
        assert resp.status_code == 422


# =============================================================================
# POST /sheet-integration/sync-data
# =============================================================================


class TestSyncSheetData:
    def test_returns_500_when_service_unavailable(self):
        resp = client.post(
            "/sheet-integration/sync-data",
            json={"source": "test"},
        )
        assert resp.status_code == 500

    def test_returns_422_for_invalid_body(self):
        resp = client.post(
            "/sheet-integration/sync-data",
            json="not a dict",
        )
        assert resp.status_code == 422


# =============================================================================
# GET /sheet-integration/export-current-data
# =============================================================================


class TestExportCurrentData:
    @patch("app.services.leaderboard_service.LeaderboardService")
    def test_returns_200_on_success(self, mock_cls):
        mock_service = MagicMock()
        mock_service.export_for_sheets.return_value = [
            {"name": "Alice", "score": 10},
        ]
        mock_cls.return_value = mock_service

        resp = client.get(
            "/sheet-integration/export-current-data",
            params={"sheet_headers": ["Member", "Score"]},
        )
        assert resp.status_code == 200

    @patch("app.services.leaderboard_service.LeaderboardService")
    def test_returns_expected_fields(self, mock_cls):
        mock_service = MagicMock()
        mock_service.export_for_sheets.return_value = [{"name": "Alice"}]
        mock_cls.return_value = mock_service

        resp = client.get(
            "/sheet-integration/export-current-data",
            params={"sheet_headers": ["Member"]},
        )
        data = resp.json()
        assert "data" in data
        assert "headers" in data
        assert "row_count" in data
        assert "exported_at" in data

    def test_returns_422_without_headers_param(self):
        resp = client.get("/sheet-integration/export-current-data")
        assert resp.status_code == 422

    def test_returns_500_when_service_unavailable(self):
        resp = client.get(
            "/sheet-integration/export-current-data",
            params={"sheet_headers": ["Member"]},
        )
        assert resp.status_code == 500


# =============================================================================
# POST /sheet-integration/sync-wgp-sheet
# =============================================================================


class TestSyncWgpSheetData:
    def test_returns_400_without_csv_url(self):
        resp = client.post(
            "/sheet-integration/sync-wgp-sheet",
            json={},
        )
        assert resp.status_code == 400
        assert "CSV URL is required" in resp.json()["detail"]

    @patch("app.routers.sheet_integration.sheet_sync_cache")
    @patch("app.routers.sheet_integration.rate_limiter")
    def test_returns_cached_result_when_available(self, mock_rate_limiter, mock_cache):
        cached = {
            "sync_results": {},
            "player_count": 5,
            "synced_at": "2026-04-08T00:00:00",
        }
        mock_cache.get.return_value = cached

        resp = client.post(
            "/sheet-integration/sync-wgp-sheet",
            json={"csv_url": "https://docs.google.com/spreadsheets/d/test/export?format=csv"},
        )
        assert resp.status_code == 200
        assert resp.json()["player_count"] == 5

    @patch("app.routers.sheet_integration.sheet_sync_cache")
    @patch("app.routers.sheet_integration.rate_limiter")
    @patch("httpx.AsyncClient")
    def test_returns_400_for_empty_sheet(self, mock_httpx_cls, mock_rate_limiter, mock_cache):
        mock_cache.get.return_value = None

        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        resp = client.post(
            "/sheet-integration/sync-wgp-sheet",
            json={"csv_url": "https://example.com/sheet.csv"},
        )
        assert resp.status_code == 400

    @patch("app.routers.sheet_integration.sheet_sync_cache")
    @patch("app.routers.sheet_integration.rate_limiter")
    @patch("httpx.AsyncClient")
    def test_parses_csv_and_syncs_players(self, mock_httpx_cls, mock_rate_limiter, mock_cache):
        mock_cache.get.return_value = None

        csv_content = (
            "Member,Score,Rounds,Average\n"
            "Alice,10,5,2.0\n"
            "Bob,-5,3,-1.67\n"
        )
        mock_response = MagicMock()
        mock_response.text = csv_content
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        resp = client.post(
            "/sheet-integration/sync-wgp-sheet",
            json={"csv_url": "https://example.com/sheet.csv"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["player_count"] == 2
        assert "Alice" in data["players_synced"]
        assert "Bob" in data["players_synced"]

    @patch("app.routers.sheet_integration.sheet_sync_cache")
    @patch("app.routers.sheet_integration.rate_limiter")
    @patch("httpx.AsyncClient")
    def test_skips_summary_rows(self, mock_httpx_cls, mock_rate_limiter, mock_cache):
        mock_cache.get.return_value = None

        csv_content = (
            "Member,Quarters,Rounds\n"
            "Alice,10,5\n"
            "Total,100,50\n"
        )
        mock_response = MagicMock()
        mock_response.text = csv_content
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        resp = client.post(
            "/sheet-integration/sync-wgp-sheet",
            json={"csv_url": "https://example.com/sheet.csv"},
        )
        assert resp.status_code == 200
        assert "Total" not in resp.json().get("players_synced", [])

    @patch("app.routers.sheet_integration.sheet_sync_cache")
    @patch("app.routers.sheet_integration.rate_limiter")
    @patch("httpx.AsyncClient")
    def test_stops_at_summary_section(self, mock_httpx_cls, mock_rate_limiter, mock_cache):
        mock_cache.get.return_value = None

        csv_content = (
            "Member,Quarters,Rounds\n"
            "Alice,10,5\n"
            "Most Rounds Played,,\n"
            "Bob,20,10\n"
        )
        mock_response = MagicMock()
        mock_response.text = csv_content
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        resp = client.post(
            "/sheet-integration/sync-wgp-sheet",
            json={"csv_url": "https://example.com/sheet.csv"},
        )
        assert resp.status_code == 200
        # Bob should not be synced because parsing stops at "Most Rounds Played"
        assert "Bob" not in resp.json().get("players_synced", [])

    @patch("app.routers.sheet_integration.sheet_sync_cache")
    @patch("app.routers.sheet_integration.rate_limiter")
    def test_scheduled_job_bypasses_rate_limit(self, mock_rate_limiter, mock_cache):
        cached = {"sync_results": {}, "player_count": 1, "synced_at": "now"}
        mock_cache.get.return_value = cached

        resp = client.post(
            "/sheet-integration/sync-wgp-sheet",
            json={"csv_url": "https://example.com/sheet.csv"},
            headers={"X-Scheduled-Job": "true"},
        )
        assert resp.status_code == 200
        # Rate limiter should NOT have been called for scheduled jobs
        mock_rate_limiter.check_limit.assert_not_called()

    def test_returns_422_for_invalid_body(self):
        resp = client.post(
            "/sheet-integration/sync-wgp-sheet",
            json="not a dict",
        )
        assert resp.status_code == 422


# =============================================================================
# POST /sheet-integration/fetch-google-sheet
# =============================================================================


class TestFetchGoogleSheet:
    def test_returns_500_without_csv_url(self):
        """Missing csv_url raises HTTPException(400), but the outer except Exception
        catches it and re-raises as 500."""
        resp = client.post(
            "/sheet-integration/fetch-google-sheet",
            json={},
        )
        assert resp.status_code == 500

    @patch("httpx.AsyncClient")
    def test_returns_200_with_valid_csv(self, mock_httpx_cls):
        csv_content = "Name,Score\nAlice,10\nBob,5\n"
        mock_response = MagicMock()
        mock_response.text = csv_content
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        resp = client.post(
            "/sheet-integration/fetch-google-sheet",
            json={"csv_url": "https://example.com/sheet.csv"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["headers"] == ["Name", "Score"]
        assert data["row_count"] == 2
        assert "fetched_at" in data

    @patch("httpx.AsyncClient")
    def test_returns_200_for_headers_only_csv(self, mock_httpx_cls):
        """A CSV with only headers but no data rows returns 200 with empty data."""
        mock_response = MagicMock()
        mock_response.text = "Name,Score\n"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        resp = client.post(
            "/sheet-integration/fetch-google-sheet",
            json={"csv_url": "https://example.com/sheet.csv"},
        )
        assert resp.status_code == 200
        assert resp.json()["row_count"] == 0

    @patch("httpx.AsyncClient")
    def test_returns_400_on_network_error(self, mock_httpx_cls):
        import httpx

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.RequestError("Connection failed", request=MagicMock())
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_cls.return_value = mock_client

        resp = client.post(
            "/sheet-integration/fetch-google-sheet",
            json={"csv_url": "https://example.com/sheet.csv"},
        )
        assert resp.status_code == 400

    def test_returns_422_for_invalid_body(self):
        resp = client.post(
            "/sheet-integration/fetch-google-sheet",
            json="not a dict",
        )
        assert resp.status_code == 422


# =============================================================================
# POST /sheet-integration/compare-data
# =============================================================================


class TestCompareSheetToDbData:
    def test_returns_500_without_sheet_data(self):
        """Missing sheet_data raises HTTPException(400), but the outer except Exception
        catches it and re-raises as 500."""
        resp = client.post(
            "/sheet-integration/compare-data",
            json={},
        )
        assert resp.status_code == 500

    @patch("app.services.leaderboard_service.LeaderboardService")
    def test_returns_200_on_success(self, mock_cls):
        mock_service = MagicMock()
        mock_service.compare_with_sheet.return_value = {
            "differences": [],
        }
        mock_cls.return_value = mock_service

        resp = client.post(
            "/sheet-integration/compare-data",
            json={"sheet_data": [{"name": "Alice"}]},
        )
        assert resp.status_code == 200

    @patch("app.services.leaderboard_service.LeaderboardService")
    def test_returns_comparison_fields(self, mock_cls):
        mock_service = MagicMock()
        mock_service.compare_with_sheet.return_value = {
            "differences": [{"field": "score", "sheet": 10, "db": 5}],
        }
        mock_cls.return_value = mock_service

        resp = client.post(
            "/sheet-integration/compare-data",
            json={"sheet_data": [{"name": "Alice"}]},
        )
        data = resp.json()
        assert "comparison" in data
        assert "differences_found" in data
        assert "compared_at" in data
        assert data["differences_found"] == 1

    def test_returns_500_when_service_unavailable(self):
        resp = client.post(
            "/sheet-integration/compare-data",
            json={"sheet_data": [{"name": "Alice"}]},
        )
        assert resp.status_code == 500

    def test_returns_422_for_invalid_body(self):
        resp = client.post(
            "/sheet-integration/compare-data",
            json="not a dict",
        )
        assert resp.status_code == 422


# =============================================================================
# safe_float / safe_int helpers
# =============================================================================


class TestSafeFloat:
    """Test the safe_float utility used by the router."""

    def test_normal_conversion(self):
        from app.routers.sheet_integration import safe_float

        assert safe_float("3.14") == 3.14

    def test_none_returns_default(self):
        from app.routers.sheet_integration import safe_float

        assert safe_float(None) == 0.0

    def test_invalid_returns_default(self):
        from app.routers.sheet_integration import safe_float

        assert safe_float("abc") == 0.0

    def test_nan_returns_default(self):
        from app.routers.sheet_integration import safe_float

        assert safe_float(float("nan")) == 0.0

    def test_inf_returns_default(self):
        from app.routers.sheet_integration import safe_float

        assert safe_float(float("inf")) == 0.0

    def test_min_clamp(self):
        from app.routers.sheet_integration import safe_float

        assert safe_float(-10.0, min_val=0.0) == 0.0

    def test_max_clamp(self):
        from app.routers.sheet_integration import safe_float

        assert safe_float(200.0, max_val=100.0) == 100.0


class TestSafeInt:
    """Test the safe_int utility used by the router."""

    def test_normal_conversion(self):
        from app.routers.sheet_integration import safe_int

        assert safe_int("5") == 5

    def test_float_string(self):
        from app.routers.sheet_integration import safe_int

        assert safe_int("3.0") == 3

    def test_none_returns_default(self):
        from app.routers.sheet_integration import safe_int

        assert safe_int(None) == 0

    def test_invalid_returns_default(self):
        from app.routers.sheet_integration import safe_int

        assert safe_int("abc") == 0

    def test_min_clamp(self):
        from app.routers.sheet_integration import safe_int

        assert safe_int(-5, min_val=0) == 0

    def test_max_clamp(self):
        from app.routers.sheet_integration import safe_int

        assert safe_int(200, max_val=100) == 100
