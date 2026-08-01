"""Tests for custom game creation with real + ghost players."""

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import PlayerProfile

client = TestClient(app)


def _player(name, handicap=18, is_ghost=False, profile_id=None):
    return {"name": name, "handicap": handicap, "is_ghost": is_ghost, "player_profile_id": profile_id}


SCRATCH_NAME = "Zzz Scratch Testcase"
SCRATCH_HANDICAP = 0.2


@pytest.fixture
def scratch_profile():
    """A rostered scratch golfer — the case where a stray 18 does real damage."""
    db = SessionLocal()
    try:
        db.query(PlayerProfile).filter(PlayerProfile.name == SCRATCH_NAME).delete()
        profile = PlayerProfile(name=SCRATCH_NAME, handicap=SCRATCH_HANDICAP, created_at="2026-01-01T00:00:00")
        db.add(profile)
        db.commit()
        db.refresh(profile)
        profile_id = profile.id
    finally:
        db.close()

    yield {"id": profile_id, "name": SCRATCH_NAME, "handicap": SCRATCH_HANDICAP}

    db = SessionLocal()
    try:
        db.query(PlayerProfile).filter(PlayerProfile.name == SCRATCH_NAME).delete()
        db.commit()
    finally:
        db.close()


def _handicap_of(game_id, name):
    state = client.get(f"/games/{game_id}/state").json()
    players = state.get("players", state.get("state", {}).get("players", []))
    return next(p["handicap"] for p in players if p["name"] == name)


def _create(players):
    resp = client.post("/games/create-custom", json={"players": players})
    assert resp.status_code == 200, resp.text
    return resp.json()["game_id"]


class TestHandicapResolution:
    """An omitted handicap must come from the roster, never the 18 placeholder.

    A scratch player silently entered as an 18 gets strokes on most holes, which
    throws off every net score and quarter in the round.
    """

    def test_omitted_handicap_uses_roster_profile(self, scratch_profile):
        game_id = _create(
            [
                {"name": SCRATCH_NAME},
                {"name": "Filler One"},
                {"name": "Filler Two"},
                {"name": "Filler Three"},
            ]
        )
        assert _handicap_of(game_id, SCRATCH_NAME) == pytest.approx(SCRATCH_HANDICAP)

    def test_matches_roster_name_ignoring_case_and_punctuation(self, scratch_profile):
        game_id = _create(
            [
                {"name": "  zzz  scratch-testcase "},
                {"name": "Filler One"},
                {"name": "Filler Two"},
                {"name": "Filler Three"},
            ]
        )
        assert _handicap_of(game_id, "  zzz  scratch-testcase ") == pytest.approx(SCRATCH_HANDICAP)

    def test_profile_id_resolves_even_when_name_differs(self, scratch_profile):
        game_id = _create(
            [
                {"name": "Nickname Only", "player_profile_id": scratch_profile["id"]},
                {"name": "Filler One"},
                {"name": "Filler Two"},
                {"name": "Filler Three"},
            ]
        )
        assert _handicap_of(game_id, "Nickname Only") == pytest.approx(SCRATCH_HANDICAP)

    def test_explicit_handicap_overrides_roster(self, scratch_profile):
        game_id = _create(
            [
                {"name": SCRATCH_NAME, "handicap": 9},
                {"name": "Filler One"},
                {"name": "Filler Two"},
                {"name": "Filler Three"},
            ]
        )
        assert _handicap_of(game_id, SCRATCH_NAME) == pytest.approx(9)

    def test_explicit_eighteen_is_kept_for_an_unrostered_player(self):
        game_id = _create(
            [
                {"name": "Walk On Guest", "handicap": 18},
                {"name": "Filler One"},
                {"name": "Filler Two"},
                {"name": "Filler Three"},
            ]
        )
        assert _handicap_of(game_id, "Walk On Guest") == pytest.approx(18)

    def test_unknown_name_falls_back_to_placeholder(self):
        game_id = _create(
            [
                {"name": "Nobody Byname Zzq"},
                {"name": "Filler One"},
                {"name": "Filler Two"},
                {"name": "Filler Three"},
            ]
        )
        assert _handicap_of(game_id, "Nobody Byname Zzq") == pytest.approx(18)


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
