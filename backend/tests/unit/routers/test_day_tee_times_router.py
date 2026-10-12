"""Tee times are stored per day: writing one date never shows up on another."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import PlayerProfile
from app.services.auth_service import get_current_user


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with SessionLocal() as db:
        db.add(PlayerProfile(id=1, name="Stuart Gano", created_at="2026-01-01T00:00:00"))
        db.commit()

    def _override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)
    Base.metadata.drop_all(bind=engine)


def _login():
    user = PlayerProfile(id=1, name="Stuart Gano")
    app.dependency_overrides[get_current_user] = lambda: user


def test_tee_times_are_tied_to_their_day(client):
    _login()
    saved = client.put("/signups/tee-times/2026-10-18", json={"tee_times": "12:48 (1-4)\n12:56 (5-8)"})
    assert saved.status_code == 200

    # Read-after-write: the same day reads back exactly what was written...
    assert client.get("/signups/tee-times/2026-10-18").json()["tee_times"] == "12:48 (1-4)\n12:56 (5-8)"
    # ...and a different day is untouched.
    other = client.get("/signups/tee-times/2026-10-19").json()
    assert other == {"date": "2026-10-19", "tee_times": "", "updated_at": None}


def test_editing_one_day_leaves_the_other_alone(client):
    _login()
    client.put("/signups/tee-times/2026-10-18", json={"tee_times": "Sunday times"})
    client.put("/signups/tee-times/2026-10-19", json={"tee_times": "Monday times"})
    client.put("/signups/tee-times/2026-10-18", json={"tee_times": "Sunday updated"})

    assert client.get("/signups/tee-times/2026-10-18").json()["tee_times"] == "Sunday updated"
    assert client.get("/signups/tee-times/2026-10-19").json()["tee_times"] == "Monday times"


def test_reading_is_public_but_writing_requires_sign_in(client):
    assert client.get("/signups/tee-times/2026-10-18").status_code == 200
    assert client.put("/signups/tee-times/2026-10-18", json={"tee_times": "x"}).status_code in (401, 403)


@pytest.mark.parametrize("bad_date", ["2026-13-01", "10-18-2026", "2026-1-8"])
def test_rejects_bad_dates(client, bad_date):
    _login()
    assert client.get(f"/signups/tee-times/{bad_date}").status_code == 400
    assert client.put(f"/signups/tee-times/{bad_date}", json={"tee_times": "x"}).status_code == 400


def test_rejects_oversized_text(client):
    _login()
    assert client.put("/signups/tee-times/2026-10-18", json={"tee_times": "x" * 2001}).status_code == 422
