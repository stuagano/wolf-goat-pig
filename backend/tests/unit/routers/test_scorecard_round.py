# backend/tests/unit/routers/test_scorecard_round.py
from fastapi.testclient import TestClient

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
