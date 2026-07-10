"""Unit tests for the badge showcase toggle — POST /api/badges/me/{id}/showcase.

Covers: equip sets showcase_position, calling again on an equipped badge
un-equips it, the max-6 slot limit, ownership (can't toggle someone else's
badge), and that public-profile sorts showcased badges first.
"""

from __future__ import annotations

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Badge, PlayerBadgeEarned, PlayerProfile
from app.services.auth_service import get_current_user
from app.utils.time import utc_now


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    session.add(PlayerProfile(id=1, name="Player One", created_at=utc_now().isoformat()))
    session.add(PlayerProfile(id=2, name="Player Two", created_at=utc_now().isoformat()))
    for badge_id in range(1, 8):
        session.add(
            Badge(
                badge_id=badge_id,
                name=f"Badge {badge_id}",
                description="test",
                category="progression",
                rarity="common",
                trigger_condition={"type": "games_played_milestone", "games_threshold": 1},
                trigger_type="career_milestone",
                is_active=True,
                created_at=utc_now().isoformat(),
            )
        )
    session.commit()

    # Player 1 earns badges 1-7; player 2 earns badge 1.
    for badge_id in range(1, 8):
        session.add(
            PlayerBadgeEarned(
                player_profile_id=1,
                badge_id=badge_id,
                earned_at=utc_now().isoformat(),
                serial_number=1,
                created_at=utc_now().isoformat(),
            )
        )
    session.add(
        PlayerBadgeEarned(
            player_profile_id=2,
            badge_id=1,
            earned_at=utc_now().isoformat(),
            serial_number=1,
            created_at=utc_now().isoformat(),
        )
    )
    session.commit()

    yield session, TestingSessionLocal
    session.close()


@pytest.fixture
def client(db_session):
    session, TestingSessionLocal = db_session

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def _override_get_current_user(db=Depends(get_db)):
        return db.query(PlayerProfile).filter_by(id=1).first()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _earned_id(session, player_id, badge_id):
    return session.query(PlayerBadgeEarned).filter_by(player_profile_id=player_id, badge_id=badge_id).first().id


class TestToggleShowcase:
    def test_equips_a_badge(self, client, db_session):
        session, _ = db_session
        earned_id = _earned_id(session, 1, 1)

        resp = client.post(f"/api/badges/me/{earned_id}/showcase")

        assert resp.status_code == 200
        assert resp.json() == {"showcased": True, "position": 1}

    def test_toggling_again_unequips(self, client, db_session):
        session, _ = db_session
        earned_id = _earned_id(session, 1, 1)

        client.post(f"/api/badges/me/{earned_id}/showcase")
        resp = client.post(f"/api/badges/me/{earned_id}/showcase")

        assert resp.json() == {"showcased": False}

    def test_max_six_slots_enforced(self, client, db_session):
        session, _ = db_session
        for badge_id in range(1, 7):
            client.post(f"/api/badges/me/{_earned_id(session, 1, badge_id)}/showcase")

        resp = client.post(f"/api/badges/me/{_earned_id(session, 1, 7)}/showcase")

        assert resp.status_code == 400
        assert "max 6" in resp.json()["detail"]

    def test_cannot_toggle_another_players_badge(self, client, db_session):
        session, _ = db_session
        other_players_earned_id = _earned_id(session, 2, 1)

        resp = client.post(f"/api/badges/me/{other_players_earned_id}/showcase")

        assert resp.status_code == 404

    def test_public_profile_lists_showcased_badges_first(self, client, db_session):
        session, _ = db_session
        # Equip badge 7 (earned last, so it wouldn't sort first by recency alone).
        client.post(f"/api/badges/me/{_earned_id(session, 1, 7)}/showcase")

        resp = client.get("/players/1/public-profile")

        assert resp.status_code == 200
        badges = resp.json()["badges"]
        assert badges[0]["name"] == "Badge 7"
        assert badges[0]["showcased"] is True
