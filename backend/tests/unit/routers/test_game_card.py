"""Attach a card photo to any finished round; numbers stay as they are."""

import base64
import uuid
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import models
from app.database import SessionLocal, engine
from app.main import app
from app.services.auth_service import get_current_user

client = TestClient(app)
HISTORY = [{"hole": 1, "points_delta": {"a": 2, "b": -2}}]


def profile(**kw):
    base = {
        "id": 9001,
        "name": "Stranger",
        "email": "stranger@test.com",
        "preferences": {},
        "admin_granted": 0,
        "is_active": 1,
    }
    return SimpleNamespace(**{**base, **kw})


MEMBER = profile(id=501, name="Alice")


@pytest.fixture
def as_profile():
    def _set(p):
        app.dependency_overrides[get_current_user] = lambda: p

    yield _set
    app.dependency_overrides.pop(get_current_user, None)


def make_round(image=None):
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        gid = str(uuid.uuid4())
        state = {
            "players": [{"id": "a", "name": "A", "player_profile_id": 501}, {"id": "b", "name": "B"}],
            "hole_history": HISTORY,
        }
        db.add(models.GameStateModel(game_id=gid, game_status="completed", state=state, scorecard_image=image))
        db.commit()
        return gid
    finally:
        db.close()


def stored(gid):
    db = SessionLocal()
    try:
        g = db.query(models.GameStateModel).filter_by(game_id=gid).one()
        return g.scorecard_image, dict(g.state)
    finally:
        db.close()


def jpeg(w=3000, h=2000):
    buf = BytesIO()
    Image.new("RGB", (w, h), "white").save(buf, format="JPEG")
    return buf.getvalue()


def put(gid, data, name="card.jpg", ctype="image/jpeg"):
    return client.put(f"/games/{gid}/scorecard-photo", files={"file": (name, data, ctype)})


def test_put_photo_stores_downscaled_jpeg_and_leaves_numbers(as_profile):
    gid = make_round()
    as_profile(MEMBER)
    assert put(gid, jpeg()).status_code == 200
    image, state = stored(gid)
    assert image.startswith("data:image/jpeg;base64,")
    img = Image.open(BytesIO(base64.b64decode(image.split(",", 1)[1])))
    assert max(img.size) == 2000
    assert state["hole_history"] == HISTORY
    assert state["card_edited_by"] == "Alice"


def test_put_photo_replaces_existing(as_profile):
    gid = make_round(image="data:image/jpeg;base64,b2xk")
    as_profile(MEMBER)
    assert put(gid, jpeg(100, 100)).status_code == 200
    assert stored(gid)[0] != "data:image/jpeg;base64,b2xk"


def test_put_photo_rejects_non_image_and_keeps_old_photo(as_profile):
    gid = make_round(image="data:image/jpeg;base64,b2xk")
    as_profile(MEMBER)
    assert put(gid, b"%PDF-1.4 not an image", "card.pdf", "application/pdf").status_code == 400
    assert stored(gid)[0] == "data:image/jpeg;base64,b2xk"


def test_put_photo_rejects_over_20mb(as_profile, monkeypatch):
    from app.routers import game_card

    monkeypatch.setattr(game_card, "CARD_MAX_UPLOAD_BYTES", 10)
    gid = make_round()
    as_profile(MEMBER)
    assert put(gid, jpeg(100, 100)).status_code == 413


def test_put_photo_forbidden_for_non_member(as_profile):
    gid = make_round()
    as_profile(profile())
    assert put(gid, jpeg(100, 100)).status_code == 403


def test_put_photo_unauthorized_when_signed_out():
    gid = make_round()
    assert put(gid, jpeg(100, 100)).status_code == 401


def test_card_reports_access_photo_and_last_edit(as_profile):
    gid = make_round()
    as_profile(MEMBER)
    assert client.get(f"/games/{gid}/card").json() == {
        "has_photo": False,
        "can_edit": True,
        "edited_by": None,
        "edited_at": None,
    }
    put(gid, jpeg(100, 100))
    body = client.get(f"/games/{gid}/card").json()
    assert body["has_photo"] is True and body["edited_by"] == "Alice"
    as_profile(profile())
    assert client.get(f"/games/{gid}/card").json()["can_edit"] is False


def test_card_404_for_unknown_round(as_profile):
    as_profile(MEMBER)
    assert client.get("/games/nope/card").status_code == 404
