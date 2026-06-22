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
