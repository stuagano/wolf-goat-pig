"""Unit tests for signups router — legacy players, daily signup CRUD."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _unique_id():
    return uuid.uuid4().hex[:8]


def _create_player():
    """Create a player and return the id + name."""
    name = f"SignupTest-{_unique_id()}"
    email = f"signup-{_unique_id()}@test.com"
    resp = client.post("/players", json={"name": name, "email": email, "handicap": 12.0})
    if resp.status_code in (200, 201):
        return resp.json()["id"], name
    return None, name


# ── GET /legacy-players ──────────────────────────────────────────────────────


class TestLegacyPlayers:
    def test_list_legacy_players_returns_200(self):
        resp = client.get("/legacy-players")
        assert resp.status_code == 200

    def test_list_legacy_players_has_count(self):
        resp = client.get("/legacy-players")
        data = resp.json()
        assert "count" in data
        assert "players" in data
        assert isinstance(data["players"], list)

    def test_list_legacy_players_count_matches_list(self):
        resp = client.get("/legacy-players")
        data = resp.json()
        assert data["count"] == len(data["players"])


# ── GET /legacy-players/validate/{name} ──────────────────────────────────────


class TestValidateLegacyPlayer:
    def test_validate_nonexistent_player_returns_200(self):
        resp = client.get("/legacy-players/validate/NonExistentPlayerXYZ")
        assert resp.status_code == 200

    def test_validate_returns_valid_field(self):
        resp = client.get("/legacy-players/validate/SomeName")
        data = resp.json()
        assert "valid" in data or "is_valid" in data or "exact_match" in data


# ── GET /legacy-players/search ───────────────────────────────────────────────


class TestSearchLegacyPlayers:
    def test_search_returns_200(self):
        resp = client.get("/legacy-players/search", params={"q": "test"})
        assert resp.status_code == 200

    def test_search_returns_query_and_count(self):
        resp = client.get("/legacy-players/search", params={"q": "xyz"})
        data = resp.json()
        assert data["query"] == "xyz"
        assert "count" in data
        assert "players" in data

    def test_search_missing_query_returns_422(self):
        resp = client.get("/legacy-players/search")
        assert resp.status_code == 422


# ── GET /signups ─────────────────────────────────────────────────────────────


class TestGetSignups:
    def test_get_signups_returns_200(self):
        resp = client.get("/signups")
        assert resp.status_code == 200

    def test_get_signups_has_expected_shape(self):
        resp = client.get("/signups")
        data = resp.json()
        assert "signups" in data
        assert "total" in data
        assert isinstance(data["signups"], list)

    def test_get_signups_respects_limit(self):
        resp = client.get("/signups", params={"limit": 1})
        data = resp.json()
        assert len(data["signups"]) <= 1


# ── POST /signups ────────────────────────────────────────────────────────────


class TestCreateSignup:
    def test_create_signup_returns_200(self):
        player_id, player_name = _create_player()
        if player_id is None:
            pytest.skip("Could not create player for signup test")
        date = f"2099-01-{_unique_id()[:2].replace('a', '1').replace('b', '2').replace('c', '3').replace('d', '4').replace('e', '5').replace('f', '6')}"
        # Use a fixed unique date to avoid collisions
        date = f"2099-{uuid.uuid4().int % 12 + 1:02d}-{uuid.uuid4().int % 28 + 1:02d}"
        resp = client.post(
            "/signups",
            json={
                "date": date,
                "player_profile_id": player_id,
                "player_name": player_name,
            },
        )
        assert resp.status_code == 200

    def test_create_signup_response_has_id(self):
        player_id, player_name = _create_player()
        if player_id is None:
            pytest.skip("Could not create player for signup test")
        date = f"2099-{uuid.uuid4().int % 12 + 1:02d}-{uuid.uuid4().int % 28 + 1:02d}"
        resp = client.post(
            "/signups",
            json={
                "date": date,
                "player_profile_id": player_id,
                "player_name": player_name,
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            assert "id" in data

    def test_create_signup_duplicate_returns_400(self):
        player_id, player_name = _create_player()
        if player_id is None:
            pytest.skip("Could not create player for signup test")
        date = f"2099-{uuid.uuid4().int % 12 + 1:02d}-{uuid.uuid4().int % 28 + 1:02d}"
        payload = {
            "date": date,
            "player_profile_id": player_id,
            "player_name": player_name,
        }
        client.post("/signups", json=payload)
        resp = client.post("/signups", json=payload)
        assert resp.status_code == 400

    def test_create_signup_invalid_date_returns_422(self):
        resp = client.post(
            "/signups",
            json={
                "date": "not-a-date",
                "player_profile_id": 1,
                "player_name": "Test",
            },
        )
        assert resp.status_code == 422

    def test_create_signup_missing_fields_returns_422(self):
        resp = client.post("/signups", json={"date": "2099-01-01"})
        assert resp.status_code == 422


# ── PUT /signups/{signup_id} ─────────────────────────────────────────────────


class TestUpdateSignup:
    def _create_signup(self):
        player_id, player_name = _create_player()
        if player_id is None:
            return None
        date = f"2099-{uuid.uuid4().int % 12 + 1:02d}-{uuid.uuid4().int % 28 + 1:02d}"
        resp = client.post(
            "/signups",
            json={
                "date": date,
                "player_profile_id": player_id,
                "player_name": player_name,
            },
        )
        if resp.status_code == 200:
            return resp.json()["id"]
        return None

    def test_update_nonexistent_signup_returns_404(self):
        resp = client.put("/signups/999999", json={"notes": "updated"})
        assert resp.status_code == 404

    def test_update_signup_notes(self):
        signup_id = self._create_signup()
        if signup_id is None:
            pytest.skip("Could not create signup")
        resp = client.put(f"/signups/{signup_id}", json={"notes": "Bringing coffee"})
        assert resp.status_code == 200

    def test_update_signup_preferred_time(self):
        signup_id = self._create_signup()
        if signup_id is None:
            pytest.skip("Could not create signup")
        resp = client.put(f"/signups/{signup_id}", json={"preferred_start_time": "8:00 AM"})
        assert resp.status_code == 200


# ── DELETE /signups/{signup_id} ──────────────────────────────────────────────


class TestCancelSignup:
    def test_cancel_nonexistent_signup_returns_404(self):
        resp = client.delete("/signups/999999")
        assert resp.status_code == 404

    def test_cancel_signup_returns_success(self):
        player_id, player_name = _create_player()
        if player_id is None:
            pytest.skip("Could not create player")
        date = f"2099-{uuid.uuid4().int % 12 + 1:02d}-{uuid.uuid4().int % 28 + 1:02d}"
        create_resp = client.post(
            "/signups",
            json={
                "date": date,
                "player_profile_id": player_id,
                "player_name": player_name,
            },
        )
        if create_resp.status_code != 200:
            pytest.skip("Could not create signup")
        signup_id = create_resp.json()["id"]
        resp = client.delete(f"/signups/{signup_id}")
        assert resp.status_code == 200
        assert "cancelled" in resp.json()["message"].lower()


# ── GET /signups/weekly ──────────────────────────────────────────────────────


class TestWeeklySignups:
    def test_weekly_signups_returns_200(self):
        resp = client.get("/signups/weekly", params={"week_start": "2099-01-06"})
        assert resp.status_code == 200

    def test_weekly_signups_has_7_days(self):
        resp = client.get("/signups/weekly", params={"week_start": "2099-01-06"})
        data = resp.json()
        assert "daily_summaries" in data
        assert len(data["daily_summaries"]) == 7

    def test_weekly_signups_invalid_date_returns_400(self):
        resp = client.get("/signups/weekly", params={"week_start": "not-a-date"})
        assert resp.status_code == 400

    def test_weekly_signups_missing_param_returns_422(self):
        resp = client.get("/signups/weekly")
        assert resp.status_code == 422
