"""Tests for custom game creation with real + ghost players."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _player(name, handicap=18, is_ghost=False, profile_id=None):
    return {"name": name, "handicap": handicap, "is_ghost": is_ghost, "player_profile_id": profile_id}


class TestCreateCustomGame:
    def test_creates_started_game_with_mixed_players(self):
        resp = client.post(
            "/games/create-custom",
            json={
                "course_name": "Wing Point Golf & Country Club",
                "players": [
                    _player("Stuart Gano", 11, is_ghost=False),
                    _player("Steve Sutorius", 1, is_ghost=True),
                    _player("Hart Williams", 8, is_ghost=True),
                    _player("Brett Saks", 2, is_ghost=True),
                ],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "in_progress"
        assert body["player_count"] == 4
        assert body["has_ghosts"] is True
        assert {p["name"] for p in body["players"]} == {"Stuart Gano", "Steve Sutorius", "Hart Williams", "Brett Saks"}

    def test_player_count_validation(self):
        resp = client.post("/games/create-custom", json={"players": [_player("A"), _player("B")]})
        # 2 players fails pydantic min_length (422)
        assert resp.status_code == 422

    def test_three_players_rejected(self):
        resp = client.post(
            "/games/create-custom",
            json={"players": [_player("A"), _player("B"), _player("C")]},
        )
        # min_length=4 -> 422
        assert resp.status_code == 422

    def test_ghost_flag_carried_to_game_state(self):
        resp = client.post(
            "/games/create-custom",
            json={
                "players": [
                    _player("Real One", is_ghost=False),
                    _player("Ghost Two", is_ghost=True),
                    _player("Ghost Three", is_ghost=True),
                    _player("Ghost Four", is_ghost=True),
                ],
            },
        )
        game_id = resp.json()["game_id"]
        state = client.get(f"/games/{game_id}/state").json()
        players = state.get("players", state.get("state", {}).get("players", []))
        by_name = {p["name"]: p for p in players}
        assert by_name["Real One"]["is_authenticated"] is True
        assert by_name["Ghost Two"]["is_authenticated"] is False
        assert by_name["Ghost Two"]["is_ghost"] is True

    def test_all_real_has_no_ghosts(self):
        resp = client.post(
            "/games/create-custom",
            json={"players": [_player(n) for n in ["A", "B", "C", "D"]]},
        )
        assert resp.json()["has_ghosts"] is False


class TestRosterSuggestions:
    def test_returns_player_list(self):
        resp = client.get("/games/roster-suggestions")
        assert resp.status_code == 200
        assert "players" in resp.json()
        assert isinstance(resp.json()["players"], list)


class TestCreateCustomGamePlayerCount:
    """The 4-6 player bound is enforced by the Pydantic model (422)."""

    def _client(self):
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_three_players_rejected_with_422(self):
        client = self._client()
        players = [{"name": f"P{i}", "handicap": 10, "is_ghost": False} for i in range(3)]
        resp = client.post("/games/create-custom", json={"players": players})
        assert resp.status_code == 422

    def test_seven_players_rejected_with_422(self):
        client = self._client()
        players = [{"name": f"P{i}", "handicap": 10, "is_ghost": False} for i in range(7)]
        resp = client.post("/games/create-custom", json={"players": players})
        assert resp.status_code == 422
