"""Task 11 review regressions: actual authority, never passing JSON flags."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import models
from app.services.round_cutover import pause_writers
from app.services.round_migration_accounting import baseline
from app.services.unified_data_service import UnifiedDataService


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/review.db")
    models.Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(models.AppConfig(name="round_identity", value={"mode": "legacy", "epoch": 1}))
        session.add(
            models.LegacyRound(
                date="2026-10-01", group="A", member="Original", score=7, source="sheet", status="attested"
            )
        )
        session.commit()
        yield session
    engine.dispose()


def test_pause_first_preserves_legacy_reader_and_independent_baseline(db):
    assert baseline(db, 2026)["Original"]["score"] == 7
    pause_writers(db, expected_epoch=1, reason="Synthetic window")
    db.commit()
    assert baseline(db, 2026)["Original"]["score"] == 7
    assert UnifiedDataService(db=db).get_all_rounds()[0].member == "Original"
    row = db.get(models.AppConfig, "round_identity")
    row.value = {**row.value, "reader_mode": "canonical"}
    db.commit()
    assert UnifiedDataService(db=db).get_all_rounds() == []
    assert baseline(db, 2026)["Original"]["score"] == 7


def test_normal_fresh_default_legacy_commissioner_http(db, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app import database
    from app.routers import commissioner

    engine = db.get_bind()
    monkeypatch.setattr(database, "engine", engine)
    from sqlalchemy.orm import sessionmaker

    monkeypatch.setattr(database, "SessionLocal", sessionmaker(engine))
    database.init_db()
    app = FastAPI()
    app.include_router(commissioner.router)

    def sessions():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[database.get_db] = sessions
    monkeypatch.setattr(commissioner, "commissioner_provider", lambda: "fake")

    async def fake_llm(question, system):
        return "```sql SELECT member, score FROM legacy_rounds_official ```"

    monkeypatch.setattr(commissioner, "llm_generate", fake_llm)
    with TestClient(app) as client:
        response = client.post("/api/commissioner/data-chat", json={"question": "standings"})
        assert response.status_code == 200
        assert response.json()["data"]["table_data"]["rows"] == [["Original", 7.0]]


def test_mounted_attestation_and_delete_refuse_paused_unchanged(db):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from app.database import get_db
    from app.routers import games, member_rounds
    from app.services.auth_service import get_current_user

    require_admin = games.require_admin

    engine = db.get_bind()
    factory = sessionmaker(engine)
    db.add(models.PlayerProfile(id=1, name="Witness", legacy_name="Witness", is_active=1))
    row = db.query(models.LegacyRound).one()
    row.source, row.status, row.foursome = "member", "pending", ["Witness"]
    db.add(models.GameStateModel(game_id="retained", state={}, revision=0))
    db.commit()
    pause_writers(db, expected_epoch=1, reason="Fixture")
    db.commit()
    app = FastAPI()
    app.include_router(member_rounds.router)
    app.include_router(games.router)

    def sessions():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = sessions
    app.dependency_overrides[get_current_user] = lambda: db.get(models.PlayerProfile, 1)
    app.dependency_overrides[require_admin] = lambda: {}
    with TestClient(app) as client:
        assert client.post(f"/rounds/{row.id}/attest").status_code == 409
        assert client.delete("/games/retained").status_code == 409
        config = db.get(models.AppConfig, "round_identity")
        config.value = {**config.value, "mode": "canonical"}
        db.commit()
        assert client.delete("/games/retained").status_code == 409
    db.expire_all()
    assert db.get(models.LegacyRound, row.id).status == "pending"
    assert db.query(models.GameStateModel).filter_by(game_id="retained").one()
