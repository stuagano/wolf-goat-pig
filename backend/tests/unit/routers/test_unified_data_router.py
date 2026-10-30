"""Unit tests for unified_data router — leaderboard, rounds, player history, stats, status, sync."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.usefixtures("mock_admin_identity")

client = TestClient(app)


# ── Mock data factories ─────────────────────────────────────────────────────


def _make_mock_round(date="15-Mar", member="Alice", score=5, group="A", source="database"):
    """Create a mock UnifiedRound-like object."""
    mock = MagicMock()
    mock.date = date
    mock.date_sortable = "2025-03-15"
    mock.group = group
    mock.member = member
    mock.score = score
    mock.location = "Wing Point"
    mock.duration = "4:30"
    mock.source = source
    mock.game_id = None
    mock.game_key = None
    mock.player_id = None
    mock.participant_id = None
    mock.score_eligible = True
    mock.detail_coverage = None
    return mock


def _make_mock_leaderboard_entry(member="Alice", quarters=20, rounds=4, rank=1):
    """Create a mock UnifiedLeaderboardEntry-like object."""
    mock = MagicMock()
    mock.member = member
    mock.quarters = quarters
    mock.rounds = rounds
    mock.average = quarters / rounds if rounds else 0
    mock.best_round = quarters // rounds + 2 if rounds else 0
    mock.worst_round = quarters // rounds - 1 if rounds else 0
    mock.sources = {"database", "primary_sheet"}
    mock.player_id = None
    mock.known_participation_count = rounds
    mock.incomplete_round_count = 0
    return mock


# ── GET /data/leaderboard ──────────────────────────────────────────────────


class TestGetUnifiedLeaderboard:
    @patch("app.routers.unified_data.get_unified_data_service")
    def test_leaderboard_returns_200(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_unified_leaderboard.return_value = []
        mock_get_service.return_value = mock_service

        resp = client.get("/data/leaderboard")
        assert resp.status_code == 200

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_leaderboard_returns_list(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_unified_leaderboard.return_value = [
            _make_mock_leaderboard_entry("Alice", 20, 4),
            _make_mock_leaderboard_entry("Bob", 15, 3),
        ]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/leaderboard")
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_leaderboard_entry_has_expected_fields(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_unified_leaderboard.return_value = [
            _make_mock_leaderboard_entry("Alice", 20, 4),
        ]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/leaderboard")
        entry = resp.json()[0]
        assert entry["rank"] == 1
        assert entry["member"] == "Alice"
        assert "quarters" in entry
        assert "rounds" in entry
        assert "average" in entry
        assert "best_round" in entry
        assert "worst_round" in entry
        assert "sources" in entry

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_leaderboard_respects_limit(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_unified_leaderboard.return_value = [
            _make_mock_leaderboard_entry(f"Player{i}", i * 5, i + 1) for i in range(10)
        ]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/leaderboard", params={"limit": 3})
        data = resp.json()
        assert len(data) == 3

    def test_leaderboard_limit_validation_min(self):
        resp = client.get("/data/leaderboard", params={"limit": 0})
        assert resp.status_code == 422

    def test_leaderboard_limit_validation_max(self):
        resp = client.get("/data/leaderboard", params={"limit": 201})
        assert resp.status_code == 422

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_leaderboard_empty_returns_empty_list(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_unified_leaderboard.return_value = []
        mock_get_service.return_value = mock_service

        resp = client.get("/data/leaderboard")
        assert resp.json() == []


# ── GET /data/leaderboard/scores ───────────────────────────────────────────


class TestSeasonExtremeScores:
    @patch("app.routers.unified_data.get_unified_data_service")
    def test_best_scores_are_descending(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_season_rounds.return_value = [
            _make_mock_round("1-Aug", "Alice", 4),
            _make_mock_round("2-Aug", "Bob", 20),
            _make_mock_round("3-Aug", "Cara", -8),
        ]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/leaderboard/scores", params={"kind": "best", "limit": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert [row["member"] for row in data] == ["Bob", "Alice"]
        assert data[0]["quarters"] == 20
        assert data[0]["date"] == "2-Aug"
        assert "location" in data[0]

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_worst_scores_are_ascending(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_season_rounds.return_value = [
            _make_mock_round("1-Aug", "Alice", 4),
            _make_mock_round("2-Aug", "Bob", -30),
            _make_mock_round("3-Aug", "Cara", -8),
        ]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/leaderboard/scores", params={"kind": "worst", "limit": 5})
        assert [row["member"] for row in resp.json()] == ["Bob", "Cara", "Alice"]

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_extreme_scores_expose_optional_saved_card(self, mock_get_service):
        card = "4358722d-8bf0-4991-af07-9b40cfc65fd7"
        saved = _make_mock_round("2-Aug", "Alice", 10)
        saved.game_id = card
        sheet = _make_mock_round("1-Aug", "Bob", 5, source="primary_sheet")
        mock_service = MagicMock()
        mock_service.get_season_rounds.return_value = [saved, sheet]
        mock_get_service.return_value = mock_service

        rows = client.get("/data/leaderboard/scores", params={"kind": "best"}).json()
        assert [row["game_id"] for row in rows] == [card, None]

    def test_scores_require_kind(self):
        resp = client.get("/data/leaderboard/scores")
        assert resp.status_code == 422

    def test_scores_reject_unknown_kind(self):
        resp = client.get("/data/leaderboard/scores", params={"kind": "median"})
        assert resp.status_code == 422


class TestSeasonRoundDetails:
    @patch("app.routers.unified_data.get_unified_data_service")
    def test_groups_players_and_keeps_newest_first(self, mock_get_service):
        newer = _make_mock_round("2-Aug", "Bob", -3, group="A")
        newer.date_sortable = "2026-08-02"
        newer.location = "Gold Mountain"
        same = _make_mock_round("2-Aug", "Alice", 3, group="A")
        same.date_sortable = "2026-08-02"
        same.location = "Gold Mountain"
        older = _make_mock_round("1-Aug", "Cara", 1, group="B")
        older.date_sortable = "2026-08-01"
        mock_service = MagicMock()
        mock_service.get_season_rounds.return_value = [newer, same, older]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/leaderboard/rounds")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["date_sortable"] == "2026-08-02"
        assert data[0]["location"] == "Gold Mountain"
        assert [(p["member"], p["quarters"]) for p in data[0]["players"]] == [("Bob", -3), ("Alice", 3)]
        assert data[1]["players"][0]["member"] == "Cara"
        assert data[0]["game_id"] is None

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_two_saved_games_on_one_day_stay_separate(self, mock_get_service):
        """Date/group/course collides for two app games; the saved id keeps them apart."""
        first_card = "4358722d-8bf0-4991-af07-9b40cfc65fd7"
        second_card = "9f1f3d2e-55aa-4ff0-bb42-0c7d1f9e2a31"
        rounds = []
        for card, member, score in (
            (first_card, "Bob", -3),
            (first_card, "Alice", 3),
            (second_card, "Cara", 7),
            (second_card, "Dave", -7),
        ):
            row = _make_mock_round("2-Aug", member, score, group="A")
            row.date_sortable = "2026-08-02"
            row.location = "Wing Point"
            row.game_id = card
            row.game_key = ("database", card)
            rounds.append(row)
        mock_service = MagicMock()
        mock_service.get_season_rounds.return_value = rounds
        mock_get_service.return_value = mock_service

        resp = client.get("/data/leaderboard/rounds")
        data = resp.json()
        assert [row["game_id"] for row in data] == [first_card, second_card]
        assert [[p["member"] for p in row["players"]] for row in data] == [["Bob", "Alice"], ["Cara", "Dave"]]

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_internal_keys_keep_unreachable_saved_games_separate(self, mock_get_service):
        rows = [_make_mock_round(member="Alice"), _make_mock_round(member="Bob")]
        for index, row in enumerate(rows):
            row.game_key = ("database", index)
        mock_get_service.return_value.get_season_rounds.return_value = rows

        resp = client.get("/data/leaderboard/rounds")
        assert resp.status_code == 200
        assert len(resp.json()) == 2
        assert all(row["game_id"] is None for row in resp.json())
        assert all("game_key" not in row for row in resp.json())

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_sheet_rows_without_a_card_still_group_together(self, mock_get_service):
        rows = []
        for member, score in (("Bob", -3), ("Alice", 3)):
            row = _make_mock_round("2-Aug", member, score, group="A", source="primary_sheet")
            row.date_sortable = "2026-08-02"
            row.location = "Wing Point"
            row.game_key = ("primary_sheet", "2-Aug", "A", "Wing Point")
            rows.append(row)
        mock_service = MagicMock()
        mock_service.get_season_rounds.return_value = rows
        mock_get_service.return_value = mock_service

        data = client.get("/data/leaderboard/rounds").json()
        assert len(data) == 1
        assert data[0]["game_id"] is None
        assert [p["member"] for p in data[0]["players"]] == ["Bob", "Alice"]


# ── GET /data/rounds ───────────────────────────────────────────────────────


class TestGetUnifiedRounds:
    @patch("app.routers.unified_data.get_unified_data_service")
    def test_rounds_returns_200(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_all_rounds.return_value = []
        mock_get_service.return_value = mock_service

        resp = client.get("/data/rounds")
        assert resp.status_code == 200

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_rounds_returns_list(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_all_rounds.return_value = [
            _make_mock_round("15-Mar", "Alice", 5),
            _make_mock_round("14-Mar", "Bob", -3),
        ]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/rounds")
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_rounds_entry_has_expected_fields(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_all_rounds.return_value = [_make_mock_round()]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/rounds")
        entry = resp.json()[0]
        assert "date" in entry
        assert "date_sortable" in entry
        assert "group" in entry
        assert "member" in entry
        assert "score" in entry
        assert "location" in entry
        assert "source" in entry
        assert entry["game_id"] is None

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_rounds_expose_the_saved_card_when_present(self, mock_get_service):
        card = "4358722d-8bf0-4991-af07-9b40cfc65fd7"
        saved = _make_mock_round(source="database")
        saved.game_id = card
        mock_service = MagicMock()
        mock_service.get_all_rounds.return_value = [saved, _make_mock_round(source="primary_sheet")]
        mock_get_service.return_value = mock_service

        rows = client.get("/data/rounds").json()
        assert [row["game_id"] for row in rows] == [card, None]

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_rounds_respects_limit_and_offset(self, mock_get_service):
        mock_service = MagicMock()
        rounds = [_make_mock_round(member=f"Player{i}") for i in range(10)]
        mock_service.get_all_rounds.return_value = rounds
        mock_get_service.return_value = mock_service

        resp = client.get("/data/rounds", params={"limit": 3, "offset": 2})
        data = resp.json()
        assert len(data) == 3

    def test_rounds_limit_validation_min(self):
        resp = client.get("/data/rounds", params={"limit": 0})
        assert resp.status_code == 422

    def test_rounds_offset_validation_negative(self):
        resp = client.get("/data/rounds", params={"offset": -1})
        assert resp.status_code == 422


@pytest.mark.parametrize(
    ("path", "service_method"),
    [
        ("/data/rounds/by-date/15-Mar", "get_rounds_by_date"),
        ("/data/player/Alice", "get_player_history"),
    ],
)
@patch("app.routers.unified_data.get_unified_data_service")
def test_filtered_rounds_preserve_optional_game_identity(mock_get_service, path, service_method):
    saved = _make_mock_round()
    saved.game_id = "8571419c-c312-4b3c-a8bd-12ee060fd056"
    getattr(mock_get_service.return_value, service_method).return_value = [saved, _make_mock_round()]

    resp = client.get(path)
    assert resp.status_code == 200
    assert [row["game_id"] for row in resp.json()] == [saved.game_id, None]
    assert all("game_key" not in row for row in resp.json())


# ── GET /data/rounds/by-date/{date} ────────────────────────────────────────


class TestGetRoundsByDate:
    @patch("app.routers.unified_data.get_unified_data_service")
    def test_rounds_by_date_returns_200(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_rounds_by_date.return_value = [
            _make_mock_round("15-Mar", "Alice", 5),
        ]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/rounds/by-date/15-Mar")
        assert resp.status_code == 200

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_rounds_by_date_empty(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_rounds_by_date.return_value = []
        mock_get_service.return_value = mock_service

        resp = client.get("/data/rounds/by-date/01-Jan")
        data = resp.json()
        assert data == []

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_rounds_by_date_passes_date_arg(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_rounds_by_date.return_value = []
        mock_get_service.return_value = mock_service

        client.get("/data/rounds/by-date/27-Jan")
        mock_service.get_rounds_by_date.assert_called_once_with("27-Jan")


# ── GET /data/player/{member_name} ─────────────────────────────────────────


class TestGetPlayerHistory:
    @patch("app.routers.unified_data.get_unified_data_service")
    def test_player_history_returns_200(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_player_history.return_value = [
            _make_mock_round(member="Alice"),
        ]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/player/Alice")
        assert resp.status_code == 200

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_player_history_empty(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_player_history.return_value = []
        mock_get_service.return_value = mock_service

        resp = client.get("/data/player/Nobody")
        assert resp.json() == []

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_player_history_passes_name_arg(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_player_history.return_value = []
        mock_get_service.return_value = mock_service

        client.get("/data/player/Alice")
        mock_service.get_player_history.assert_called_once_with("Alice")


# ── GET /data/player/{member_name}/stats ───────────────────────────────────


class TestGetPlayerStats:
    @patch("app.routers.unified_data.get_unified_data_service")
    def test_player_stats_returns_200(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_player_history.return_value = [
            _make_mock_round(member="Alice", score=5),
            _make_mock_round(member="Alice", score=3),
        ]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/player/Alice/stats")
        assert resp.status_code == 200

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_player_stats_has_expected_fields(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_player_history.return_value = [
            _make_mock_round(member="Alice", score=5),
            _make_mock_round(member="Alice", score=3),
        ]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/player/Alice/stats")
        data = resp.json()
        assert data["found"] is True
        assert data["member"] == "Alice"
        assert "total_quarters" in data
        assert "rounds_played" in data
        assert "average_per_round" in data
        assert "best_round" in data
        assert "worst_round" in data
        assert "sources" in data
        assert "recent_form" in data

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_player_stats_calculates_totals(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_player_history.return_value = [
            _make_mock_round(member="Alice", score=5),
            _make_mock_round(member="Alice", score=3),
        ]
        mock_get_service.return_value = mock_service

        resp = client.get("/data/player/Alice/stats")
        data = resp.json()
        assert data["total_quarters"] == 8
        assert data["rounds_played"] == 2
        assert data["average_per_round"] == 4.0

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_player_stats_not_found(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_player_history.return_value = []
        mock_get_service.return_value = mock_service

        resp = client.get("/data/player/Nobody/stats")
        data = resp.json()
        assert data["found"] is False
        assert "message" in data

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_player_stats_recent_form(self, mock_get_service):
        mock_service = MagicMock()
        # 7 rounds, recent_form should use the first 5
        rounds = [_make_mock_round(member="Alice", score=i + 1) for i in range(7)]
        mock_service.get_player_history.return_value = rounds
        mock_get_service.return_value = mock_service

        resp = client.get("/data/player/Alice/stats")
        data = resp.json()
        assert data["recent_form"]["rounds"] == 5


# ── GET /data/status ───────────────────────────────────────────────────────


class TestGetDataStatus:
    @patch("app.routers.unified_data.get_unified_data_service")
    def test_status_returns_200(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_data_sources_status.return_value = {
            "primary_sheet": {"available": False, "record_count": 0, "error": "No key"},
            "writable_sheet": {"available": False, "record_count": 0},
            "database": {"available": True, "record_count": 10},
            "unified_total": 10,
            "deduplicated_total": 10,
        }
        mock_get_service.return_value = mock_service

        resp = client.get("/data/status")
        assert resp.status_code == 200

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_status_has_expected_structure(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_data_sources_status.return_value = {
            "primary_sheet": {"available": True, "record_count": 50, "id": "sheet123"},
            "writable_sheet": {"available": True, "record_count": 20, "id": "sheet456"},
            "database": {"available": True, "record_count": 30},
            "unified_total": 100,
            "deduplicated_total": 80,
        }
        mock_get_service.return_value = mock_service

        resp = client.get("/data/status")
        data = resp.json()
        assert "primary_sheet" in data
        assert "writable_sheet" in data
        assert "database" in data
        assert data["unified_total"] == 100
        assert data["deduplicated_total"] == 80
        assert data["primary_sheet"]["available"] is True
        assert data["database"]["record_count"] == 30


# ── POST /data/sync-sheets ────────────────────────────────────────────────


class TestSyncSheets:
    def test_sync_without_admin_header_returns_403(self):
        resp = client.post("/data/sync-sheets")
        assert resp.status_code == 403

    def test_sync_with_wrong_admin_email_returns_403(self):
        resp = client.post(
            "/data/sync-sheets",
            headers={"X-Admin-Email": "nobody@example.com"},
        )
        assert resp.status_code == 403

    @patch("app.routers.unified_data.get_unified_data_service")
    def test_sync_with_valid_admin_returns_200(self, mock_get_service):
        mock_service = MagicMock()
        mock_service.get_all_rounds.return_value = []
        mock_get_service.return_value = mock_service

        resp = client.post(
            "/data/sync-sheets",
            headers={"X-Admin-Email": "stuagano@gmail.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # No rounds from sheets means error response
        assert data["success"] is False

    @patch("app.services.spreadsheet_sync_service.refresh_round_history")
    def test_sync_returns_shared_redacted_failure_health(self, refresh):
        refresh.return_value = {"success": False, "status": "held", "held": 1, "synced": 0}
        resp = client.post(
            "/data/sync-sheets",
            headers={"X-Admin-Email": "stuagano@gmail.com"},
        )
        assert resp.status_code == 200
        assert resp.json() == refresh.return_value
        refresh.assert_called_once()
