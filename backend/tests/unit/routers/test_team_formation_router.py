"""Unit tests for team_formation router — random teams, balanced teams, rotations, Sunday pairings, players list."""

import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

TEST_DATE = "2099-01-15"


def _unique_name():
    return f"TFPlayer-{uuid.uuid4().hex[:6]}"


def _create_profile(name=None, handicap=15.0):
    """Create a player profile and return the JSON response."""
    name = name or _unique_name()
    resp = client.post("/players", json={"name": name, "handicap": handicap})
    assert resp.status_code == 200, f"Failed to create profile: {resp.text}"
    return resp.json()


def _create_signup(date, profile_id, player_name, preferred_start_time=None):
    """Create a daily signup and return the JSON response."""
    payload = {
        "date": date,
        "player_profile_id": profile_id,
        "player_name": player_name,
    }
    if preferred_start_time:
        payload["preferred_start_time"] = preferred_start_time
    resp = client.post("/signups", json=payload)
    assert resp.status_code == 200, f"Failed to create signup: {resp.text}"
    return resp.json()


def _unique_date():
    """Generate a date string that is extremely unlikely to collide with any other test."""
    # Use uuid to ensure uniqueness even across repeated test runs with persistent DB
    uid = uuid.uuid4().int
    year = 2200 + (uid % 800)  # 2200-2999
    month = uid % 12 + 1
    day = (uid >> 4) % 28 + 1
    return f"{year}-{month:02d}-{day:02d}"


def _seed_signups(count, date=None):
    """Create `count` player profiles + signups for the given date.  Returns (date, profiles)."""
    date = date or _unique_date()
    profiles = []
    for i in range(count):
        name = _unique_name()
        profile = _create_profile(name=name, handicap=10.0 + i * 2)
        _create_signup(date, profile["id"], name)
        profiles.append(profile)
    return date, profiles


# ── POST /signups/{date}/team-formation/random ─────────────────────────────


class TestGenerateRandomTeams:
    def test_random_teams_returns_200_with_enough_players(self):
        date, _ = _seed_signups(4)
        resp = client.post(f"/signups/{date}/team-formation/random")
        assert resp.status_code == 200

    def test_random_teams_response_shape(self):
        date, _ = _seed_signups(4)
        resp = client.post(f"/signups/{date}/team-formation/random")
        data = resp.json()
        assert "summary" in data
        assert "teams" in data
        assert "validation" in data
        assert "remaining_players" in data

    def test_random_teams_produces_one_team_from_four_players(self):
        date, _ = _seed_signups(4)
        resp = client.post(f"/signups/{date}/team-formation/random")
        data = resp.json()
        assert len(data["teams"]) == 1

    def test_random_teams_produces_two_teams_from_eight_players(self):
        date, _ = _seed_signups(8)
        resp = client.post(f"/signups/{date}/team-formation/random")
        data = resp.json()
        assert len(data["teams"]) == 2

    def test_random_teams_remainder_players(self):
        date, _ = _seed_signups(5)
        resp = client.post(f"/signups/{date}/team-formation/random")
        data = resp.json()
        assert data["remaining_players"] == 1

    def test_random_teams_seed_produces_deterministic_result(self):
        date, _ = _seed_signups(8)
        resp1 = client.post(f"/signups/{date}/team-formation/random", params={"seed": 42})
        resp2 = client.post(f"/signups/{date}/team-formation/random", params={"seed": 42})

        # Compare player names per team (timestamps may differ between calls)
        def _team_names(teams):
            return [[p["player_name"] for p in t["players"]] for t in teams]

        assert _team_names(resp1.json()["teams"]) == _team_names(resp2.json()["teams"])

    def test_random_teams_max_teams_limits_output(self):
        date, _ = _seed_signups(8)
        resp = client.post(f"/signups/{date}/team-formation/random", params={"max_teams": 1})
        data = resp.json()
        assert len(data["teams"]) == 1

    def test_random_teams_too_few_players_returns_400(self):
        # Use a date with no signups
        empty_date = _unique_date()
        resp = client.post(f"/signups/{empty_date}/team-formation/random")
        assert resp.status_code == 400

    def test_random_teams_summary_includes_date(self):
        date, _ = _seed_signups(4)
        resp = client.post(f"/signups/{date}/team-formation/random")
        data = resp.json()
        assert data["summary"]["date"] == date


# ── POST /signups/{date}/team-formation/balanced ───────────────────────────


class TestGenerateBalancedTeams:
    def test_balanced_teams_returns_200(self):
        date, _ = _seed_signups(4)
        resp = client.post(f"/signups/{date}/team-formation/balanced")
        assert resp.status_code == 200

    def test_balanced_teams_response_shape(self):
        date, _ = _seed_signups(4)
        resp = client.post(f"/signups/{date}/team-formation/balanced")
        data = resp.json()
        assert "summary" in data
        assert "teams" in data
        assert "validation" in data

    def test_balanced_teams_too_few_players_returns_400(self):
        empty_date = _unique_date()
        resp = client.post(f"/signups/{empty_date}/team-formation/balanced")
        assert resp.status_code == 400

    def test_balanced_teams_seed_deterministic(self):
        date, _ = _seed_signups(8)
        resp1 = client.post(f"/signups/{date}/team-formation/balanced", params={"seed": 99})
        resp2 = client.post(f"/signups/{date}/team-formation/balanced", params={"seed": 99})

        def _team_names(teams):
            return [[p["player_name"] for p in t["players"]] for t in teams]

        assert _team_names(resp1.json()["teams"]) == _team_names(resp2.json()["teams"])


# ── POST /signups/{date}/team-formation/rotations ──────────────────────────


class TestGenerateTeamRotations:
    def test_rotations_returns_200(self):
        date, _ = _seed_signups(4)
        resp = client.post(f"/signups/{date}/team-formation/rotations")
        assert resp.status_code == 200

    def test_rotations_response_shape(self):
        date, _ = _seed_signups(4)
        resp = client.post(f"/signups/{date}/team-formation/rotations")
        data = resp.json()
        assert "date" in data
        assert "total_signups" in data
        assert "num_rotations" in data
        assert "rotations" in data

    def test_rotations_default_count_is_three(self):
        date, _ = _seed_signups(8)
        resp = client.post(f"/signups/{date}/team-formation/rotations")
        data = resp.json()
        assert data["num_rotations"] == 3

    def test_rotations_custom_count(self):
        date, _ = _seed_signups(8)
        resp = client.post(f"/signups/{date}/team-formation/rotations", params={"num_rotations": 5})
        data = resp.json()
        assert data["num_rotations"] == 5

    def test_rotations_too_few_players_returns_400(self):
        empty_date = _unique_date()
        resp = client.post(f"/signups/{empty_date}/team-formation/rotations")
        assert resp.status_code == 400


# ── POST /signups/{date}/sunday-game/pairings ──────────────────────────────


class TestSundayGamePairings:
    def test_sunday_pairings_returns_200(self):
        date, _ = _seed_signups(4)
        resp = client.post(f"/signups/{date}/sunday-game/pairings")
        assert resp.status_code == 200

    def test_sunday_pairings_response_shape(self):
        date, _ = _seed_signups(4)
        resp = client.post(f"/signups/{date}/sunday-game/pairings")
        data = resp.json()
        assert "date" in data
        assert "total_signups" in data
        assert "player_count" in data
        assert "rotations" in data
        assert "random_seed" in data

    def test_sunday_pairings_too_few_players_returns_400(self):
        empty_date = _unique_date()
        resp = client.post(f"/signups/{empty_date}/sunday-game/pairings")
        assert resp.status_code == 400

    def test_sunday_pairings_seed_deterministic(self):
        date, _ = _seed_signups(8)
        resp1 = client.post(f"/signups/{date}/sunday-game/pairings", params={"seed": 7})
        resp2 = client.post(f"/signups/{date}/sunday-game/pairings", params={"seed": 7})
        d1, d2 = resp1.json(), resp2.json()
        assert d1["player_count"] == d2["player_count"]

        # Compare player names in selected rotation (timestamps differ between calls)
        def _extract_names(rotation):
            return [[p["player_name"] for p in t["players"]] for t in rotation.get("teams", [])]

        assert _extract_names(d1["selected_rotation"]) == _extract_names(d2["selected_rotation"])

    def test_sunday_pairings_custom_rotations(self):
        date, _ = _seed_signups(8)
        resp = client.post(f"/signups/{date}/sunday-game/pairings", params={"num_rotations": 5})
        data = resp.json()
        assert data["pairing_sets_available"] == 5


# ── GET /signups/{date}/players ────────────────────────────────────────────


class TestGetPlayersForDate:
    def test_get_players_returns_200(self):
        date, _ = _seed_signups(3)
        resp = client.get(f"/signups/{date}/players")
        assert resp.status_code == 200

    def test_get_players_response_shape(self):
        date, _ = _seed_signups(2)
        resp = client.get(f"/signups/{date}/players")
        data = resp.json()
        assert "date" in data
        assert "total_players" in data
        assert "players" in data
        assert "can_form_teams" in data
        assert "max_complete_teams" in data

    def test_get_players_count_matches(self):
        date, _profiles = _seed_signups(5)
        resp = client.get(f"/signups/{date}/players")
        data = resp.json()
        assert data["total_players"] == 5
        assert data["can_form_teams"] is True
        assert data["max_complete_teams"] == 1
        assert data["remaining_players"] == 1

    def test_get_players_empty_date(self):
        empty_date = _unique_date()
        resp = client.get(f"/signups/{empty_date}/players")
        data = resp.json()
        assert data["total_players"] == 0
        assert data["can_form_teams"] is False

    def test_get_players_includes_handicap(self):
        date, profiles = _seed_signups(1)
        resp = client.get(f"/signups/{date}/players")
        data = resp.json()
        player = data["players"][0]
        assert "handicap" in player
        assert player["handicap"] == profiles[0]["handicap"]


# ── GET /pairings/{date} ──────────────────────────────────────────────────


class TestGetGeneratedPairings:
    def test_get_pairings_nonexistent_returns_exists_false(self):
        empty_date = _unique_date()
        resp = client.get(f"/pairings/{empty_date}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["exists"] is False

    def test_get_pairings_returns_200(self):
        resp = client.get(f"/pairings/{TEST_DATE}")
        assert resp.status_code == 200


# ── DELETE /pairings/{date} ────────────────────────────────────────────────


class TestDeleteGeneratedPairings:
    def test_delete_nonexistent_pairings_returns_404(self):
        empty_date = _unique_date()
        resp = client.delete(f"/pairings/{empty_date}")
        assert resp.status_code == 404


# ── POST /pairings/{date}/notify ───────────────────────────────────────────


class TestResendPairingNotifications:
    def test_notify_nonexistent_pairings_returns_404(self):
        empty_date = _unique_date()
        resp = client.post(f"/pairings/{empty_date}/notify")
        assert resp.status_code == 404
