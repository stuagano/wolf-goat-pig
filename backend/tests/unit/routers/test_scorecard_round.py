# backend/tests/unit/routers/test_scorecard_round.py
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import models
from app.database import SessionLocal, engine
from app.main import app

client = TestClient(app)


def _per_hole_4p():
    out = []
    for h in range(1, 19):
        out += [
            {"player_index": 0, "hole": h, "quarters": 1},
            {"player_index": 1, "hole": h, "quarters": 1},
            {"player_index": 2, "hole": h, "quarters": -1},
            {"player_index": 3, "hole": h, "quarters": -1},
        ]
    return out


def test_from_scorecard_creates_completed_round_and_results():
    models.Base.metadata.create_all(bind=engine)
    body = {
        "players": [
            {"name": "Alice"},
            {"name": "Bob"},
            {"name": "Cara"},
            {"name": "Dan"},
        ],
        "per_hole_quarters": _per_hole_4p(),
        "course_name": "Wing Point",
        "played_at": "2026-06-18",
    }
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 200, resp.text
    game_id = resp.json()["game_id"]

    db = SessionLocal()
    try:
        game = db.query(models.GameStateModel).filter_by(game_id=game_id).first()
        assert game.game_status == "completed"
        rec = db.query(models.GameRecord).filter_by(game_id=game_id).first()
        assert rec is not None and rec.player_count == 4
    finally:
        db.close()


def test_from_scorecard_rejects_wrong_player_count():
    body = {
        "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
        "per_hole_quarters": [],
    }
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 400


def test_from_scorecard_allows_non_zero_sum_hole():
    pq = _per_hole_4p()
    pq[0]["quarters"] = 5  # break hole 1 zero-sum
    body = {
        "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
        "per_hole_quarters": pq,
    }
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 200
    assert 1 in {int(h) for h in resp.json().get("warnings", {})}


def test_from_scorecard_links_profile_by_legacy_name_else_null():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        prof = db.query(models.PlayerProfile).filter_by(legacy_name="AliceRT").first()
        if not prof:
            prof = models.PlayerProfile(
                name="Alice Profile RT", legacy_name="AliceRT", created_at="2026-06-18T00:00:00"
            )
            db.add(prof)
            db.commit()
            db.refresh(prof)
        prof_id = prof.id
    finally:
        db.close()

    body = {
        "players": [
            {"name": "AliceRT"},  # matches PlayerProfile.legacy_name -> linked
            {"name": "NoSuchRosterName"},  # no match -> null
            {"name": "Cara"},
            {"name": "Dan"},
        ],
        "per_hole_quarters": _per_hole_4p(),
    }
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 200, resp.text
    game_id = resp.json()["game_id"]

    db = SessionLocal()
    try:
        rec = db.query(models.GameRecord).filter_by(game_id=game_id).first()
        rows = db.execute(
            text("SELECT player_name, player_profile_id FROM game_player_results WHERE game_record_id = :rid"),
            {"rid": rec.id},
        ).fetchall()
        by_name = {r.player_name: r.player_profile_id for r in rows}
        assert by_name["AliceRT"] == prof_id
        assert by_name["NoSuchRosterName"] is None
    finally:
        db.close()


def test_from_scorecard_rejects_out_of_range_hole():
    pq = _per_hole_4p()
    pq.append({"player_index": 0, "hole": 19, "quarters": 0})
    body = {
        "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
        "per_hole_quarters": pq,
    }
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 400


def test_from_scorecard_rejects_bad_player_index():
    pq = _per_hole_4p()
    pq.append({"player_index": 9, "hole": 1, "quarters": 0})
    body = {
        "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
        "per_hole_quarters": pq,
    }
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 400
