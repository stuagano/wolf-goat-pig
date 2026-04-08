"""Unit tests for leaderboard router — rankings, metrics, game results."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_id():
    return uuid.uuid4().hex[:8]


# ── GET /leaderboard ─────────────────────────────────────────────────────────


class TestGetLeaderboard:
    def test_leaderboard_returns_200(self):
        resp = client.get("/leaderboard")
        assert resp.status_code == 200

    def test_leaderboard_returns_list(self):
        resp = client.get("/leaderboard")
        assert isinstance(resp.json(), list)

    def test_leaderboard_entries_have_expected_fields(self):
        resp = client.get("/leaderboard")
        data = resp.json()
        if len(data) > 0:
            entry = data[0]
            assert "rank" in entry
            assert "player_name" in entry
            assert "total_earnings" in entry
            assert "games_played" in entry

    def test_leaderboard_respects_limit(self):
        resp = client.get("/leaderboard", params={"limit": 2})
        data = resp.json()
        assert len(data) <= 2

    def test_leaderboard_sort_asc(self):
        resp = client.get("/leaderboard", params={"sort": "asc"})
        assert resp.status_code == 200
        data = resp.json()
        if len(data) >= 2:
            assert data[0]["total_earnings"] <= data[1]["total_earnings"]

    def test_leaderboard_sort_desc(self):
        resp = client.get("/leaderboard", params={"sort": "desc"})
        assert resp.status_code == 200
        data = resp.json()
        if len(data) >= 2:
            assert data[0]["total_earnings"] >= data[1]["total_earnings"]

    def test_leaderboard_invalid_sort_returns_422(self):
        resp = client.get("/leaderboard", params={"sort": "invalid"})
        assert resp.status_code == 422

    def test_leaderboard_limit_validation_min(self):
        resp = client.get("/leaderboard", params={"limit": 0})
        assert resp.status_code == 422

    def test_leaderboard_limit_validation_max(self):
        resp = client.get("/leaderboard", params={"limit": 200})
        assert resp.status_code == 422


# ── GET /leaderboard/{metric} ────────────────────────────────────────────────


class TestLeaderboardByMetric:
    def test_earnings_metric_returns_200(self):
        resp = client.get("/leaderboard/earnings")
        assert resp.status_code == 200

    def test_win_rate_metric_returns_200(self):
        resp = client.get("/leaderboard/win_rate")
        assert resp.status_code == 200

    def test_games_played_metric_returns_200(self):
        resp = client.get("/leaderboard/games_played")
        assert resp.status_code == 200

    def test_metric_response_has_expected_shape(self):
        resp = client.get("/leaderboard/earnings")
        data = resp.json()
        assert "metric" in data
        assert data["metric"] == "earnings"
        assert "leaderboard" in data
        assert "total_players" in data

    def test_metric_respects_limit(self):
        resp = client.get("/leaderboard/earnings", params={"limit": 3})
        data = resp.json()
        assert len(data["leaderboard"]) <= 3

    def test_unknown_metric_falls_back_to_earnings(self):
        resp = client.get("/leaderboard/unknown_metric")
        assert resp.status_code == 200
        data = resp.json()
        assert data["metric"] == "unknown_metric"


# ── POST /game-results ───────────────────────────────────────────────────────


class TestRecordGameResult:
    def _create_player(self):
        name = f"LB-{_unique_id()}"
        email = f"lb-{_unique_id()}@test.com"
        resp = client.post("/players", json={"name": name, "email": email, "handicap": 10.0})
        if resp.status_code in (200, 201):
            return resp.json()["id"]
        return None

    def test_record_result_missing_fields_returns_422(self):
        resp = client.post("/game-results", json={})
        assert resp.status_code == 422

    def test_record_result_invalid_payload_returns_422(self):
        resp = client.post("/game-results", json={"player_profile_id": "not_int"})
        assert resp.status_code == 422
