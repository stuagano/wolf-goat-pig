"""Admin overwrite of official pairings for a signup day."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import DailySignup, GeneratedPairing, PlayerProfile
from app.routers import team_formation
from app.services.auth_service import get_current_auth0_user


def test_pairing_overwrite_is_admin_only_and_replaces_the_day(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    game_date = "2099-06-07"
    with sessions() as db:
        db.add(
            PlayerProfile(
                id=1,
                name="Env Admin",
                email="env@example.com",
                preferences={"auth0_id": "auth0|env"},
                created_at="2026-01-01",
            )
        )
        for index, name in enumerate(("Ada", "Bea", "Cam", "Dee"), start=1):
            db.add(
                DailySignup(
                    id=index,
                    date=game_date,
                    player_profile_id=index,
                    player_name=name,
                    signup_time="2099-06-01T12:00:00",
                    status="signed_up",
                    created_at="2099-06-01T12:00:00",
                    updated_at="2099-06-01T12:00:00",
                )
            )
        db.add(
            GeneratedPairing(
                id=9,
                game_date=game_date,
                generated_at="2099-06-06T12:00:00",
                generated_by="scheduler",
                player_count=4,
                team_count=1,
                pairings_data={"teams": [{"players": [{"player_name": "Old Draw"}]}]},
                created_at="2099-06-06T12:00:00",
            )
        )
        db.commit()

    def database():
        with sessions() as db:
            yield db

    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "env@example.com")
    monkeypatch.setattr(team_formation.database, "SessionLocal", sessions)
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|guest", "email": "guest@example.com"}
    client = TestClient(app)
    try:
        denied = client.post(f"/pairings/{game_date}/generate", params={"force": "true", "send_notifications": "false"})
        assert denied.status_code == 403

        app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|env", "email": "env@example.com"}
        overwritten = client.post(
            f"/pairings/{game_date}/generate", params={"force": "true", "send_notifications": "false"}
        )
        assert overwritten.status_code == 200, overwritten.text
        body = overwritten.json()
        assert body["success"] is True
        assert body["notifications"]["enabled"] is False
        names = [player["player_name"] for team in body["pairings"]["teams"] for player in team["players"]]
        assert set(names) == {"Ada", "Bea", "Cam", "Dee"}

        with sessions() as db:
            saved = db.query(GeneratedPairing).filter(GeneratedPairing.game_date == game_date).all()
            assert len(saved) == 1
            assert saved[0].id != 9
            assert saved[0].generated_by == "env@example.com"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_auth0_user, None)
        engine.dispose()
