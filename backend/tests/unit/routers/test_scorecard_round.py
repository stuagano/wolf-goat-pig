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


def test_from_scorecard_unlinked_player_is_not_auto_linked_by_name():
    # A guest the user marked "keep as typed (unlinked)" must NOT be linked to a
    # roster member who happens to share the typed name — that would corrupt the
    # member's standings with a round they didn't play.
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(models.PlayerProfile).filter_by(legacy_name="GuestClash").first():
            db.add(
                models.PlayerProfile(
                    name="Real GuestClash Member", legacy_name="GuestClash", created_at="2026-06-18T00:00:00"
                )
            )
            db.commit()
    finally:
        db.close()

    body = {
        "players": [
            {"name": "GuestClash", "unlinked": True},
            {"name": "B"},
            {"name": "C"},
            {"name": "D"},
        ],
        "per_hole_quarters": _per_hole_4p(),
    }
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 200, resp.text
    game_id = resp.json()["game_id"]
    db = SessionLocal()
    try:
        rec = db.query(models.GameRecord).filter_by(game_id=game_id).first()
        row = db.execute(
            text(
                "SELECT player_profile_id FROM game_player_results "
                "WHERE game_record_id = :rid AND player_name = 'GuestClash'"
            ),
            {"rid": rec.id},
        ).first()
        assert row.player_profile_id is None
    finally:
        db.close()


def test_from_scorecard_round_is_retrievable_via_game_state():
    # The success screen links to /game/{id}, which loads /games/{id}/state.
    # Confirm a scan-created completed round renders there with players+standings.
    body = {
        "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
        "per_hole_quarters": _per_hole_4p(),
    }
    game_id = client.post("/games/from-scorecard", json=body).json()["game_id"]
    state = client.get(f"/games/{game_id}/state")
    assert state.status_code == 200, state.text
    data = state.json()
    assert data["game_status"] == "completed"
    assert len(data["players"]) == 4
    assert "standings" in data


def test_from_scorecard_rejects_bad_player_index():
    pq = _per_hole_4p()
    pq.append({"player_index": 9, "hole": 1, "quarters": 0})
    body = {
        "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
        "per_hole_quarters": pq,
    }
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 400


def test_from_scorecard_stores_image_base64():
    models.Base.metadata.create_all(bind=engine)
    body = {
        "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
        "per_hole_quarters": _per_hole_4p(),
        "image_base64": "data:image/jpeg;base64,SGVsbG8=",
    }
    game_id = client.post("/games/from-scorecard", json=body).json()["game_id"]
    db = SessionLocal()
    try:
        row = db.query(models.GameStateModel).filter_by(game_id=game_id).first()
        assert row.scorecard_image == "data:image/jpeg;base64,SGVsbG8="
    finally:
        db.close()


def test_from_scorecard_ignores_oversize_image_but_still_saves():
    models.Base.metadata.create_all(bind=engine)
    body = {
        "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
        "per_hole_quarters": _per_hole_4p(),
        "image_base64": "x" * (2_000_001),  # over the 2MB ceiling
    }
    resp = client.post("/games/from-scorecard", json=body)
    assert resp.status_code == 200  # round still saved
    row = SessionLocal().query(models.GameStateModel).filter_by(game_id=resp.json()["game_id"]).first()
    assert row.scorecard_image is None
