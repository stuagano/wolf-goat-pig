"""Played dates and participant identity survive scorecard persistence."""

from datetime import UTC, datetime, timezone

import pytest
from fastapi import HTTPException

from app import models
from app.services.completed_game_service import persist_completed_game
from app.services.unified_data_service import UnifiedDataService
from tests.unit.routers.test_round_posting_p1 import round_api, scan_body, scores, sign_in


def test_live_start_preserves_profile_identity_through_completion(round_api):
    client, app, sessions = round_api
    sign_in(app)
    with sessions() as db:
        game = db.query(models.GameStateModel).one()
        players = game.state["players"]
        players[1]["name"] = players[0]["name"]
        players[0]["handicap_index"] = 7.5
        game.state = {"players": players, "tee_order_set": True, "player_count": 4}
        game.game_status = "setup"
        for i, player in enumerate(players):
            db.add(
                models.GamePlayer(
                    game_id="round",
                    player_slot_id=player["id"],
                    player_profile_id=player["player_profile_id"],
                    player_name=player["name"],
                    handicap=18,
                    tee_order=i,
                )
            )
        db.commit()
    response = client.post("/games/round/start")
    assert response.status_code == 200, response.text
    with sessions() as db:
        players = db.query(models.GameStateModel).one().state["players"]
        assert {p["id"]: p.get("player_profile_id") for p in players} == {"p1": 1, "p2": 2, "p3": 3, "p4": 4}
        assert next(p for p in players if p["id"] == "p1")["handicap_index"] == 7.5
    response = client.post("/games/round/scores", json=scores())
    assert response.status_code == 200, response.text
    with sessions() as db:
        results = db.query(models.GamePlayerResult).all()
        assert len(results) == 4
        assert {r.player_profile_id for r in results} == {1, 2, 3, 4}


def test_historical_scorecard_uses_played_date_and_preserves_audit_time(round_api, monkeypatch):
    client, app, sessions = round_api
    sign_in(app)
    now = datetime(2026, 10, 19, 18, tzinfo=UTC)
    monkeypatch.setattr("app.routers.games.utc_now", lambda: now)
    monkeypatch.setattr("app.utils.time.utc_now", lambda: now)
    body = {**scan_body(), "played_at": "2026-01-15", "course_name": "Wing Point"}
    response = client.post("/games/from-scorecard", json=body)
    assert response.status_code == 200, response.text
    with sessions() as db:
        record = db.query(models.GameRecord).one()
        assert record.completed_at == now.isoformat()
        assert record.created_at == now.isoformat()
        service = UnifiedDataService(db)
        rounds = service.get_all_rounds()
        assert len(rounds) == 4
        assert {r.date_sortable for r in rounds} == {"2026-01-15"}
        assert {r.date for r in rounds} == {"15-Jan"}
        # A later season's opening sheet round must not pull January into October.
        db.add(
            models.LegacyRound(
                date="2026-10-01", group="A", member="Other", score=3, location="Wing Point", source="primary_sheet"
            )
        )
        db.commit()
        assert {r.member for r in service.get_season_rounds()} == {"Other"}
        for i, score in enumerate((18, -18, 0, 0), 1):
            db.add(
                models.LegacyRound(
                    date="2026-01-15",
                    group="B",
                    member=f"Player {i}",
                    score=score,
                    location="Wing Point",
                    source="primary_sheet",
                )
            )
        db.commit()
        january = [r for r in service.get_all_rounds() if r.date_sortable == "2026-01-15"]
        assert len(january) == 4
        assert all(r.source == "primary_sheet" and len(r.hole_scores) == 18 for r in january)
    history = client.get("/games/history").json()["games"]
    assert history[0]["played_at"] == "2026-01-15"
    details = client.get(f"/games/{response.json()['game_id']}/details").json()
    assert details["game"]["played_at"] == "2026-01-15"


@pytest.mark.parametrize(
    "duplicate",
    [
        {"name": "Player 1"},
        {"name": "  pLAYER   1  "},
        {"name": "Another spelling", "player_profile_id": 1},
        {"name": "  "},
    ],
)
def test_ambiguous_scorecard_roster_rejected_before_writes(round_api, duplicate):
    client, app, sessions = round_api
    sign_in(app)
    body = scan_body()
    body["players"][1] = duplicate
    response = client.post("/games/from-scorecard", json=body)
    assert response.status_code == 400, response.text
    with sessions() as db:
        assert db.query(models.GameStateModel).count() == 1  # Only fixture's live game.
        assert db.query(models.GameRecord).count() == 0
        assert db.query(models.GamePlayerResult).count() == 0


@pytest.mark.parametrize("source,expected", [("scorecard_scan", "2026-01-15"), ("live", "2026-10-19")])
def test_legacy_scorecards_and_live_games_keep_their_date_semantics(round_api, source, expected):
    client, app, sessions = round_api
    sign_in(app)
    response = client.post("/games/from-scorecard", json=scan_body())
    assert response.status_code == 200, response.text
    with sessions() as db:
        record = db.query(models.GameRecord).one()
        record.created_at = "2026-01-15T12:00:00"
        record.completed_at = "2026-10-19T18:00:00"
        record.game_settings = {}
        game = db.query(models.GameStateModel).filter_by(game_id=record.game_id).one()
        game.created_at = record.created_at
        game.state = {key: value for key, value in game.state.items() if key != "played_at"}
        game.state["source"] = source
        db.commit()
        assert {r.date_sortable for r in UnifiedDataService(db).get_all_rounds()} == {expected}
    response = client.patch(f"/games/{response.json()['game_id']}/holes/1/players/p1", json={"quarters": 7})
    assert response.status_code == 200, response.text
    with sessions() as db:
        assert {r.date_sortable for r in UnifiedDataService(db).get_all_rounds()} == {expected}
        assert db.query(models.GameRecord).one().completed_at == "2026-10-19T18:00:00"
        assert db.query(models.GamePlayerResult).count() == 4


@pytest.mark.parametrize("played_at", ["garbage", "2026-02-30", "2026-01-15T12:00:00"])
def test_invalid_played_date_rejected_without_writes(round_api, played_at):
    client, app, sessions = round_api
    sign_in(app)
    response = client.post("/games/from-scorecard", json={**scan_body(), "played_at": played_at})
    assert response.status_code == 422, response.text
    with sessions() as db:
        assert db.query(models.GameRecord).count() == 0
        assert db.query(models.GameStateModel).count() == 1


@pytest.mark.parametrize("field,value", [("name", "Player 1"), ("player_profile_id", 1), ("id", "p1")])
def test_persistence_boundary_rejects_duplicate_players_before_creating_results(round_api, field, value):
    _, _, sessions = round_api
    with sessions() as db:
        game = db.query(models.GameStateModel).one()
        players = game.state["players"]
        players[1][field] = value
        if field == "name":
            players[1]["player_profile_id"] = None
        game.state = {**game.state, "players": players}
        with pytest.raises(HTTPException) as error:
            persist_completed_game(db, game)
        assert error.value.status_code == 400
        assert db.query(models.GameRecord).count() == 0
        assert db.query(models.GamePlayerResult).count() == 0


@pytest.mark.parametrize("count", [4, 5, 6])
def test_distinct_profiles_with_same_display_name_keep_all_results_and_corrections(round_api, count):
    client, app, sessions = round_api
    sign_in(app)
    body = {
        "players": [
            {"name": "Same Name" if i < 2 else f"Player {i + 1}", "player_profile_id": i + 1} for i in range(count)
        ],
        "per_hole_quarters": [
            {"hole": h, "player_index": i, "quarters": i} for h in range(1, 19) for i in range(count)
        ],
    }
    response = client.post("/games/from-scorecard", json=body)
    assert response.status_code == 200, response.text
    game_id = response.json()["game_id"]
    with sessions() as db:
        rows = db.query(models.GamePlayerResult).all()
        assert len(rows) == count
        initial = {r.player_profile_id: (r.id, r.total_earnings) for r in rows}
        assert initial[1][1] == 0
        assert initial[2][1] == 18
    response = client.patch(f"/games/{game_id}/holes/1/players/p1", json={"quarters": 7})
    assert response.status_code == 200, response.text
    with sessions() as db:
        rows = db.query(models.GamePlayerResult).all()
        assert len(rows) == count
        corrected = {r.player_profile_id: (r.id, r.total_earnings) for r in rows}
        assert corrected[1] == (initial[1][0], 7)
        assert corrected[2] == initial[2]


def test_same_name_profiles_with_tied_scores_survive_unified_history(round_api):
    client, app, sessions = round_api
    sign_in(app)
    body = scan_body()
    body["players"][1]["name"] = "Player 1"
    for entry in body["per_hole_quarters"]:
        entry["quarters"] = 0
    response = client.post("/games/from-scorecard", json=body)
    assert response.status_code == 200, response.text
    with sessions() as db:
        assert db.query(models.GamePlayerResult).count() == 4
        assert len(UnifiedDataService(db).get_all_rounds()) == 4


def test_history_paginates_by_played_date_not_posting_order(round_api):
    client, app, _ = round_api
    sign_in(app)
    for played_at in ("2026-02-15", "2026-01-15"):
        response = client.post("/games/from-scorecard", json={**scan_body(), "played_at": played_at})
        assert response.status_code == 200, response.text
    first = client.get("/games/history?limit=1").json()
    second = client.get("/games/history?limit=1&offset=1").json()
    assert first["total"] == second["total"] == 2
    assert first["games"][0]["played_at"] == "2026-02-15"
    assert second["games"][0]["played_at"] == "2026-01-15"


@pytest.mark.parametrize("unlinked,expected_status", [(False, 400), (True, 200)])
def test_ambiguous_alias_requires_selection_but_unlinked_guest_stays_unlinked(round_api, unlinked, expected_status):
    client, app, sessions = round_api
    sign_in(app)
    with sessions() as db:
        db.add_all(
            [
                models.PlayerProfile(id=10, name="Shared Name"),
                models.PlayerProfile(id=11, name="Other Name", legacy_name="shared name"),
            ]
        )
        db.commit()
    body = scan_body()
    body["players"][1] = {"name": "Shared Name", "unlinked": unlinked}
    response = client.post("/games/from-scorecard", json=body)
    assert response.status_code == expected_status, response.text
    with sessions() as db:
        if unlinked:
            assert (
                db.query(models.GamePlayerResult).filter_by(player_name="Shared Name").one().player_profile_id is None
            )
        else:
            assert db.query(models.GameRecord).count() == 0


@pytest.mark.parametrize("typed_name", ["Roster Alias", "  roster   ALIAS ", "Profile Name"])
def test_roster_aliases_cannot_repeat_an_explicit_profile(round_api, typed_name):
    client, app, sessions = round_api
    sign_in(app)
    with sessions() as db:
        db.add(models.PlayerProfile(id=1, name="Profile Name", legacy_name="Roster Alias"))
        db.commit()
    body = scan_body()
    body["players"][1] = {"name": typed_name}
    response = client.post("/games/from-scorecard", json=body)
    assert response.status_code == 400, response.text
    with sessions() as db:
        assert db.query(models.GameRecord).count() == 0
        assert db.query(models.GamePlayerResult).count() == 0
