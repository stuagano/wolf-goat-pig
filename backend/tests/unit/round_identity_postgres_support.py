"""Task12 physical-connection harness: isolated disposable PostgreSQL 15 only."""

import copy
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app import models
from app.database import get_db
from app.routers import games, games_holes, member_rounds, players, round_reconciliation, round_stories, unified_data


def race(*operations):
    """Start independent transactions together; every join has a deadline."""
    barrier = Barrier(len(operations))

    def run(operation):
        barrier.wait(timeout=10)
        return operation()

    with ThreadPoolExecutor(max_workers=len(operations)) as workers:
        futures = [workers.submit(run, operation) for operation in operations]
        return [future.result(timeout=20) for future in futures]


@pytest.fixture
def identity_pg():
    raw = os.getenv("SCORE_SAVE_TEST_DATABASE_URL")
    if not raw:
        if os.getenv("SCORE_SAVE_REQUIRE_POSTGRES") == "1":
            pytest.fail("Required physical identity proof needs SCORE_SAVE_TEST_DATABASE_URL")
        pytest.skip("Explicit disposable localhost PostgreSQL 15 *_test database required")
    url = make_url(raw)
    if (
        url.get_backend_name() != "postgresql"
        or url.host not in {"127.0.0.1", "localhost", "::1"}
        or not (url.database or "").endswith("_test")
        or url.query
    ):
        pytest.fail("Only localhost PostgreSQL *_test databases without URL query overrides allowed")
    admin = create_engine(url.set(drivername="postgresql+psycopg2"), poolclass=NullPool)
    schema = "identity_proof_" + uuid4().hex
    with admin.begin() as conn:
        assert int(conn.scalar(text("SHOW server_version_num"))) // 10000 == 15, "Identity proof requires PG15"
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        url.set(drivername="postgresql+psycopg2"),
        poolclass=NullPool,
        connect_args={
            "options": f"-csearch_path={schema} -cstatement_timeout=10000 -clock_timeout=8000",
            "connect_timeout": 5,
        },
    )
    sessions = sessionmaker(engine, expire_on_commit=True)
    writer_pids = set()

    def snapshot():
        with sessions() as db:
            assert db.scalar(text("SELECT pg_backend_pid()")) not in writer_pids
            return {
                model.__tablename__: [
                    copy.deepcopy(dict(row)) for row in db.execute(select(model.__table__)).mappings()
                ]
                for model in (
                    models.GameStateModel,
                    models.GameRecord,
                    models.GamePlayerResult,
                    models.RoundSource,
                    models.RoundObservation,
                    models.RoundIssue,
                    models.RoundDelivery,
                    models.Notification,
                    models.RoundResolution,
                    models.RoundRequest,
                    models.RoundAlias,
                )
            }

    def database():
        with sessions() as db:
            writer_pids.add(db.scalar(text("SELECT pg_backend_pid()")))
            yield db

    app = FastAPI()
    for router in (
        games.router,
        games_holes.router,
        member_rounds.router,
        players.router,
        round_reconciliation.router,
        round_stories.router,
        unified_data.router,
    ):
        app.include_router(router)
    app.dependency_overrides[get_db] = database
    try:
        models.Base.metadata.create_all(engine)
        with sessions() as db:
            db.add(models.AppConfig(name="round_identity", value={"mode": "canonical", "epoch": 4, "season": 2026}))
            db.add_all(
                [
                    models.PlayerProfile(id=1, name="Avery", legacy_name="Avery", is_active=1),
                    models.PlayerProfile(id=2, name="Blair", legacy_name="Blair", is_active=1),
                    models.PlayerProfile(
                        id=7,
                        name="Reviewer",
                        email="review@example.invalid",
                        is_active=1,
                        preferences={"auth0_id": "auth0|fixture"},
                    ),
                    models.PlayerProfile(id=8, name="Admin", is_active=1, admin_granted=1),
                ]
            )
            db.commit()
        with TestClient(app, raise_server_exceptions=False) as client:
            yield SimpleNamespace(
                engine=engine, sessions=sessions, client=client, app=app, writer_pids=writer_pids, snapshot=snapshot
            )
    finally:
        engine.dispose()
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()
