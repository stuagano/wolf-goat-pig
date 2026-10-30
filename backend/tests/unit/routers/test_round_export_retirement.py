"""Mounted historical export must fail explicitly, not invoke a missing writer."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import models
from app.database import get_db
from app.routers import sheet_integration


@pytest.mark.parametrize("mode", ["legacy", "paused", "canonical"])
def test_mounted_export_is_explicitly_retired_without_sql_or_provider_effects(mode):
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    models.Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(models.AppConfig(name="round_identity", value={"mode": mode, "epoch": 5}))
        db.add(models.PlayerProfile(id=1, name="Original"))
        db.commit()
    app = FastAPI()
    app.include_router(sheet_integration.router)  # Same router/prefix mounted by app.main.

    def database():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = database
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/sheet-integration/export-current-data", params={"sheet_headers": ["Name", "Quarters"]})
        assert response.status_code == 410, response.text
        assert "canonical" in response.json()["detail"]
    with Session(engine) as db:
        assert db.get(models.PlayerProfile, 1).name == "Original"
        assert db.query(models.GameRecord).count() == 0
        assert db.query(models.PendingSheetSync).count() == 0
    engine.dispose()
