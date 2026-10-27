"""Round posting authorization and durable completion, using an isolated database."""

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import get_db
from app.routers import games, games_holes
from app.services.auth_service import get_current_user


@pytest.fixture
def round_api():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    app = FastAPI()
    app.include_router(games.router)
    app.include_router(games_holes.router)

    def database():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = database
    with sessions() as db:
        db.add(
            models.GameStateModel(
                game_id="round",
                game_status="in_progress",
                state={
                    "players": [{"id": f"p{i}", "name": f"Player {i}", "player_profile_id": i} for i in range(1, 5)]
                },
            )
        )
        db.commit()
    yield TestClient(app), app, sessions
    engine.dispose()


def sign_in(app, player_id=1, admin=False):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=player_id, email="player@example.test", preferences={}, admin_granted=admin, is_active=1
    )


def scores(value=1, count=18):
    return {
        "holes": [
            {"hole_number": h, "quarters": {"p1": value, "p2": -value, "p3": 0, "p4": 0}} for h in range(1, count + 1)
        ]
    }


def scan_body():
    return {
        "players": [{"name": f"Player {i}", "player_profile_id": i} for i in range(1, 5)],
        "per_hole_quarters": [
            {"hole": h["hole_number"], "player_index": i, "quarters": q}
            for h in scores()["holes"]
            for i, q in enumerate(h["quarters"].values())
        ],
    }


@pytest.mark.parametrize(
    "path,body",
    [("/games/round/scores", scores()), ("/games/round/complete", {}), ("/games/from-scorecard", scan_body())],
)
def test_anonymous_cannot_post(round_api, path, body):
    client, _, sessions = round_api
    assert client.post(path, json=body).status_code in (401, 403)
    with sessions() as db:
        assert db.query(models.GameRecord).count() == 0


@pytest.mark.parametrize(
    "path,body",
    [("/games/round/scores", scores()), ("/games/round/complete", {}), ("/games/from-scorecard", scan_body())],
)
def test_nonparticipant_cannot_post(round_api, path, body):
    client, app, _ = round_api
    sign_in(app, player_id=99)
    assert client.post(path, json=body).status_code == 403


@pytest.mark.parametrize("admin", [False, True])
def test_authorized_scores_and_correction_keep_result_rows(round_api, admin):
    client, app, sessions = round_api
    sign_in(app, player_id=99 if admin else 1, admin=admin)
    response = client.post("/games/round/scores", json=scores())
    assert response.status_code == 200, response.text
    with sessions() as db:
        initial = {r.player_name: (r.id, r.total_earnings) for r in db.query(models.GamePlayerResult)}
        assert initial["Player 1"][1] == 18
    response = client.post("/games/round/scores", json=scores(2))
    assert response.status_code == 200, response.text
    with sessions() as db:
        corrected = {r.player_name: (r.id, r.total_earnings) for r in db.query(models.GamePlayerResult)}
        assert len(corrected) == 4
        assert corrected["Player 1"] == (initial["Player 1"][0], 36)
        assert db.query(models.GameRecord).one().final_scores["p1"] == 36


@pytest.mark.parametrize("quarters", [{}, {"p1": 0}, {"p1": 0, "p2": 0, "p3": 0, "p4": 0, "unknown": 0}])
def test_incomplete_or_unknown_scores_rejected(round_api, quarters):
    client, app, sessions = round_api
    sign_in(app)
    body = scores()
    body["holes"][0]["quarters"] = quarters
    assert client.post("/games/round/scores", json=body).status_code == 400
    with sessions() as db:
        assert db.query(models.GameStateModel).one().game_status == "in_progress"
        assert db.query(models.GamePlayerResult).count() == 0


def test_empty_round_cannot_complete(round_api):
    client, app, _ = round_api
    sign_in(app)
    assert client.post("/games/round/complete").status_code == 400


def test_partial_round_save_remains_supported(round_api):
    client, app, _ = round_api
    sign_in(app)
    response = client.post("/games/round/scores", json=scores(0, count=1))
    assert response.status_code == 200, response.text
    assert response.json()["game_status"] == "in_progress"


@pytest.mark.parametrize("admin", [False, True])
def test_scan_and_backfill_preserve_rows(round_api, admin):
    client, app, sessions = round_api
    sign_in(app, player_id=99 if admin else 1, admin=admin)
    response = client.post("/games/from-scorecard", json=scan_body())
    assert response.status_code == 200, response.text
    gid = response.json()["game_id"]
    with sessions() as db:
        original = db.query(models.GamePlayerResult).filter_by(player_name="Player 1").one()
        row_id = original.id
        assert original.total_earnings == 18
    body = scan_body()
    for entry in body["per_hole_quarters"]:
        entry["quarters"] *= 2
    response = client.patch(f"/games/{gid}/scorecard", json={"per_hole_quarters": body["per_hole_quarters"]})
    assert response.status_code == 200, response.text
    with sessions() as db:
        result = db.query(models.GamePlayerResult).filter_by(player_name="Player 1").one()
        assert (result.id, result.total_earnings) == (row_id, 36)
        assert db.query(models.GamePlayerResult).count() == 4
    assert client.post(f"/games/{gid}/complete").status_code == 200


@pytest.mark.parametrize("entries", [[], [{"hole": 1, "player_index": 0, "quarters": 0}]])
def test_incomplete_scan_is_rejected(round_api, entries):
    client, app, sessions = round_api
    sign_in(app)
    body = scan_body()
    body["per_hole_quarters"] = entries
    assert client.post("/games/from-scorecard", json=body).status_code == 400
    with sessions() as db:
        assert db.query(models.GameRecord).count() == 0


def test_result_failure_rolls_back_score_correction(round_api):
    from sqlalchemy import event

    client, app, sessions = round_api
    sign_in(app)
    assert client.post("/games/round/scores", json=scores()).status_code == 200

    def fail_result_write(connection, cursor, statement, parameters, context, executemany):
        if statement.startswith("UPDATE game_player_results"):
            raise RuntimeError("simulated result write failure")

    engine = sessions.kw["bind"]
    event.listen(engine, "before_cursor_execute", fail_result_write)
    try:
        response = client.post("/games/round/scores", json=scores(2))
        assert response.status_code == 500
    finally:
        event.remove(engine, "before_cursor_execute", fail_result_write)
    with sessions() as db:
        assert db.query(models.GameStateModel).one().state["standings"]["p1"] == 18
        assert db.query(models.GameRecord).one().final_scores["p1"] == 18
        assert db.query(models.GamePlayerResult).filter_by(player_name="Player 1").one().total_earnings == 18
        assert db.query(models.HoleEvent).filter_by(player_id="p1", hole_number=1).one().quarters == 1


def test_single_player_correction_updates_permanent_result(round_api):
    client, app, sessions = round_api
    sign_in(app)
    assert client.post("/games/round/scores", json=scores()).status_code == 200
    with sessions() as db:
        row_id = db.query(models.GamePlayerResult).filter_by(player_name="Player 1").one().id
    response = client.patch("/games/round/holes/1/players/p1", json={"quarters": 19})
    assert response.status_code == 200, response.text
    with sessions() as db:
        result = db.query(models.GamePlayerResult).filter_by(player_name="Player 1").one()
        assert (result.id, result.total_earnings) == (row_id, 36)
        assert db.query(models.GameStateModel).one().state["standings"]["p1"] == 36
        assert db.query(models.GameRecord).one().final_scores["p1"] == 36
    assert client.patch("/games/round/holes/1/players/unknown", json={"quarters": 0}).status_code == 400
    assert client.delete("/games/round/holes/1").status_code == 400


@pytest.mark.parametrize("badge_fails", [False, True])
def test_completion_badges_use_separate_postcommit_session(round_api, monkeypatch, badge_fails):
    from sqlalchemy import event

    client, app, sessions = round_api
    sign_in(app)
    with sessions() as db:
        row = db.query(models.GameStateModel).one()
        row.state = {
            **row.state,
            "hole_history": [{"hole": h["hole_number"], "points_delta": h["quarters"]} for h in scores()["holes"]],
        }
        db.add(models.GamePlayer(game_id="round", player_slot_id="p1", player_profile_id=1))
        db.commit()
    source_sessions = []
    source_postcommit_queries = []
    badge_sessions = []

    def database():
        with sessions() as db:
            source_sessions.append(db)
            committed = []
            event.listen(db, "after_commit", lambda session: committed.append(True))
            event.listen(
                db, "do_orm_execute", lambda execute: source_postcommit_queries.append(True) if committed else None
            )
            yield db

    app.dependency_overrides[get_db] = database

    def badge_check(engine, record_id, profile_id):
        badge_sessions.append(engine.db)
        assert engine.db not in source_sessions
        # Separate session observes canonical commit before badges run.
        with sessions() as verifier:
            assert verifier.query(models.GameRecord).filter_by(id=record_id).one().final_scores["p1"] == 18
            assert verifier.query(models.GamePlayerResult).count() == 4
        assert profile_id == 1
        if badge_fails:
            engine.db.rollback()
            raise RuntimeError("synthetic badge failure")
        engine.db.commit()
        return []

    monkeypatch.setattr(games.BadgeEngine, "check_post_game_achievements", badge_check)
    response = client.post("/games/round/complete")
    assert response.status_code == 200, response.text
    assert badge_sessions
    assert source_postcommit_queries == []
    with sessions() as db:
        assert db.query(models.GameStateModel).one().game_status == "completed"
        assert db.query(models.GameRecord).one().final_scores["p1"] == 18
        assert db.query(models.GamePlayerResult).count() == 4


def test_quarters_only_correction_preserves_existing_detail(round_api):
    client, app, sessions = round_api
    sign_in(app)
    body = scores()
    body["holes"][0].update(gross_scores={"p1": 4}, notes="keep", teams=[["p1", "p2"], ["p3", "p4"]])
    assert client.post("/games/round/scores", json=body).status_code == 200
    assert client.post("/games/round/scores", json=scores(2)).status_code == 200
    with sessions() as db:
        first = db.query(models.GameStateModel).one().state["hole_history"][0]
        assert first["gross_scores"] == {"p1": 4}
        assert first["notes"] == "keep"
        assert first["teams"] == [["p1", "p2"], ["p3", "p4"]]
        result = db.query(models.GamePlayerResult).filter_by(participant_id="p1").one()
        assert result.hole_scores[0]["gross_score"] == 4
        assert result.hole_scores[0]["notes"] == "keep"


def test_scanned_gross_correction_preserves_quarters(round_api):
    client, app, sessions = round_api
    sign_in(app)
    gid = client.post("/games/from-scorecard", json=scan_body()).json()["game_id"]
    response = client.patch(f"/games/{gid}/holes/1/players/p1", json={"score": 4})
    assert response.status_code == 200, response.text
    assert response.json()["quarters"] == 1
    with sessions() as db:
        event = db.query(models.HoleEvent).filter_by(game_id=gid, hole_number=1, player_id="p1").one()
        assert (event.score, event.quarters) == (4, 1)
        result = db.query(models.GamePlayerResult).filter_by(player_name="Player 1").one()
        assert result.total_earnings == 18
        assert result.hole_scores[0]["gross_score"] == 4
