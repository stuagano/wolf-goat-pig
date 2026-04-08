"""Unit tests for analytics router — game stats, player performance, overview."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ── Helper for game-stats mocking ───────────────────────────────────────────


@contextmanager
def _mock_game_stats_deps():
    """Patch database, models, and course_manager so game-stats can succeed."""
    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 0

    mock_course_mgr = MagicMock()
    mock_course_mgr.get_courses.return_value = {"Pine Valley": {}, "Augusta": {}}

    with (
        patch("app.routers.analytics.database.SessionLocal", return_value=mock_db),
        patch("app.routers.analytics.models") as mock_models,
        patch("app.routers.analytics.get_course_manager", return_value=mock_course_mgr),
    ):
        mock_models.GameRecord = MagicMock()
        mock_models.SimulationResult = MagicMock()
        yield


# =============================================================================
# GAME STATS
# =============================================================================


class TestGetGameStats:
    """The /analytics/game-stats endpoint references the removed SimulationResult
    model, so it returns 500 in the current codebase. Tests document this and
    exercise the happy path via mocks."""

    def test_returns_500_without_simulation_result_model(self):
        resp = client.get("/analytics/game-stats")
        assert resp.status_code == 500

    def test_returns_500_error_detail(self):
        resp = client.get("/analytics/game-stats")
        data = resp.json()
        assert "detail" in data

    def test_returns_200_with_mocked_deps(self):
        with _mock_game_stats_deps():
            resp = client.get("/analytics/game-stats")
            assert resp.status_code == 200

    def test_returns_expected_keys_with_mocked_deps(self):
        with _mock_game_stats_deps():
            resp = client.get("/analytics/game-stats")
            data = resp.json()
            assert "total_games" in data
            assert "total_simulations" in data
            assert "available_courses" in data
            assert "course_names" in data
            assert "game_modes" in data
            assert "betting_types" in data
            assert "last_updated" in data

    def test_game_modes_values(self):
        with _mock_game_stats_deps():
            resp = client.get("/analytics/game-stats")
            data = resp.json()
            assert "4-man" in data["game_modes"]
            assert "5-man" in data["game_modes"]
            assert "6-man" in data["game_modes"]

    def test_betting_types_values(self):
        with _mock_game_stats_deps():
            resp = client.get("/analytics/game-stats")
            data = resp.json()
            assert "Wolf" in data["betting_types"]
            assert "Goat" in data["betting_types"]
            assert "Pig" in data["betting_types"]
            assert "Aardvark" in data["betting_types"]

    def test_last_updated_is_iso_string(self):
        with _mock_game_stats_deps():
            resp = client.get("/analytics/game-stats")
            data = resp.json()
            assert isinstance(data["last_updated"], str)
            assert "T" in data["last_updated"]

    def test_course_names_reflects_mock(self):
        with _mock_game_stats_deps():
            resp = client.get("/analytics/game-stats")
            data = resp.json()
            assert isinstance(data["course_names"], list)
            assert data["available_courses"] == 2

    def test_counts_are_integers(self):
        with _mock_game_stats_deps():
            resp = client.get("/analytics/game-stats")
            data = resp.json()
            assert isinstance(data["total_games"], int)
            assert isinstance(data["total_simulations"], int)
            assert isinstance(data["available_courses"], int)


# =============================================================================
# PLAYER PERFORMANCE
# =============================================================================


class TestGetPlayerPerformance:
    def test_returns_200(self):
        resp = client.get("/analytics/player-performance")
        assert resp.status_code == 200

    def test_returns_expected_keys(self):
        resp = client.get("/analytics/player-performance")
        data = resp.json()
        assert "total_players" in data
        assert "active_players" in data
        assert "recent_signups" in data
        assert "average_handicap" in data
        assert "performance_metrics" in data
        assert "last_updated" in data

    def test_total_players_is_non_negative(self):
        resp = client.get("/analytics/player-performance")
        data = resp.json()
        assert isinstance(data["total_players"], int)
        assert data["total_players"] >= 0

    def test_active_players_is_non_negative(self):
        resp = client.get("/analytics/player-performance")
        data = resp.json()
        assert isinstance(data["active_players"], int)
        assert data["active_players"] >= 0

    def test_recent_signups_is_non_negative(self):
        resp = client.get("/analytics/player-performance")
        data = resp.json()
        assert isinstance(data["recent_signups"], int)
        assert data["recent_signups"] >= 0

    def test_average_handicap_is_numeric(self):
        resp = client.get("/analytics/player-performance")
        data = resp.json()
        assert isinstance(data["average_handicap"], (int, float))

    def test_performance_metrics_has_expected_keys(self):
        resp = client.get("/analytics/player-performance")
        data = resp.json()
        metrics = data["performance_metrics"]
        assert "games_played" in metrics
        assert "average_score" in metrics
        assert "best_round" in metrics
        assert "worst_round" in metrics

    def test_last_updated_is_iso_string(self):
        resp = client.get("/analytics/player-performance")
        data = resp.json()
        assert isinstance(data["last_updated"], str)
        assert "T" in data["last_updated"]


# =============================================================================
# ANALYTICS OVERVIEW
# =============================================================================


class TestGetAnalyticsOverview:
    def test_returns_200(self):
        resp = client.get("/analytics/overview")
        assert resp.status_code == 200

    def test_returns_expected_keys(self):
        resp = client.get("/analytics/overview")
        data = resp.json()
        assert "total_players" in data
        assert "active_players" in data
        assert "total_games" in data
        assert "game_mode_analytics" in data
        assert "generated_at" in data

    def test_total_players_is_non_negative(self):
        resp = client.get("/analytics/overview")
        data = resp.json()
        assert isinstance(data["total_players"], int)
        assert data["total_players"] >= 0

    def test_active_players_is_non_negative(self):
        resp = client.get("/analytics/overview")
        data = resp.json()
        assert isinstance(data["active_players"], int)
        assert data["active_players"] >= 0

    def test_total_games_is_non_negative(self):
        resp = client.get("/analytics/overview")
        data = resp.json()
        assert isinstance(data["total_games"], int)
        assert data["total_games"] >= 0

    def test_game_mode_analytics_is_dict(self):
        resp = client.get("/analytics/overview")
        data = resp.json()
        assert isinstance(data["game_mode_analytics"], (dict, list))

    def test_generated_at_is_iso_string(self):
        resp = client.get("/analytics/overview")
        data = resp.json()
        assert isinstance(data["generated_at"], str)
        assert "T" in data["generated_at"]
