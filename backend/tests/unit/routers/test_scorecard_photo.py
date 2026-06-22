import base64
import uuid

from fastapi.testclient import TestClient

from app import models
from app.database import SessionLocal, engine
from app.main import app

client = TestClient(app)


def _make_round_with_image(image_b64: str | None) -> str:
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        gid = str(uuid.uuid4())
        g = models.GameStateModel(game_id=gid, game_status="completed", state={}, scorecard_image=image_b64)
        db.merge(g)
        db.commit()
        return g.game_id
    finally:
        db.close()


def test_get_scorecard_photo_returns_image_bytes():
    raw = b"\xff\xd8\xff\xe0jpegbytes"
    gid = _make_round_with_image("data:image/jpeg;base64," + base64.b64encode(raw).decode())
    resp = client.get(f"/games/{gid}/scorecard-photo")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")
    assert resp.content == raw


def test_get_scorecard_photo_404_when_none():
    gid = _make_round_with_image(None)
    assert client.get(f"/games/{gid}/scorecard-photo").status_code == 404


def test_patch_scorecard_recomputes_standings_from_new_per_hole():
    # create a round (totals-only: A +8 on hole 18, B -8)
    models.Base.metadata.create_all(bind=engine)
    create = client.post(
        "/games/from-scorecard",
        json={
            "players": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}],
            "per_hole_quarters": [{"player_index": i, "hole": 18, "quarters": q} for i, q in enumerate([8, -8, 4, -4])],
        },
    )
    gid = create.json()["game_id"]
    # backfill: spread A's +8 across holes 1 and 2 (sum still 8) — standings unchanged
    patch = client.patch(
        f"/games/{gid}/scorecard",
        json={
            "per_hole_quarters": [
                {"player_index": 0, "hole": 1, "quarters": 5},
                {"player_index": 0, "hole": 2, "quarters": 3},
                {"player_index": 1, "hole": 1, "quarters": -5},
                {"player_index": 1, "hole": 2, "quarters": -3},
                {"player_index": 2, "hole": 1, "quarters": 4},
                {"player_index": 3, "hole": 1, "quarters": -4},
            ]
        },
    )
    assert patch.status_code == 200, patch.text
    db = SessionLocal()
    try:
        state = db.query(models.GameStateModel).filter_by(game_id=gid).first().state
        # hole_history now has holes 1 and 2 (not just 18)
        assert {e["hole"] for e in state["hole_history"]} == {1, 2}
        # standings preserved: A total +8
        assert state["standings"]["p1"] == 8
    finally:
        db.close()


def test_patch_scorecard_404_for_missing_round():
    assert client.patch("/games/nope/scorecard", json={"per_hole_quarters": []}).status_code == 404
