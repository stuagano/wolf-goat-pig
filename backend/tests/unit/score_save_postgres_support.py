"""Real commit/readback fixture for score corrections; never use a shared database."""

import copy
import os
import time
import uuid
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app import database, models
from app.observability.score_save import ScoreSaveDiagnostics
from app.routers import games, games_holes
from app.services.auth_service import get_current_user

STAMP = "2026-01-02T03:04:05+00:00"
TABLES = (
    models.AppConfig,
    models.GameStateModel,
    models.GamePlayer,
    models.PlayerProfile,
    models.HoleEvent,
    models.GameRecord,
    models.GamePlayerResult,
)


def score_payload():
    return {
        "current_hole": 19,
        "holes": [
            {
                "hole_number": hole,
                "quarters": {"p1": 1, "p2": -1, "p3": 0, "p4": 0},
                "gross_scores": {f"p{i}": 4 for i in range(1, 5)},
                "notes": "private-score-note",
            }
            for hole in range(1, 19)
        ],
    }


def correction_payload():
    payload = score_payload()
    payload["holes"][6]["quarters"] = {"p1": -23, "p2": 23, "p3": 0, "p4": 0}
    payload["holes"][6]["gross_scores"]["p1"] = 5
    return payload


def seed_round(engine, game_id):
    """Seed independently of the save service, including existing result rows."""
    payload = score_payload()
    standings = {"p1": 18, "p2": -18, "p3": 0, "p4": 0}
    players = [
        {"id": f"p{i}", "name": f"private-player-{i}", "player_profile_id": i, "total_points": standings[f"p{i}"]}
        for i in range(1, 5)
    ]
    history = [
        {
            "hole": h["hole_number"],
            "points_delta": h["quarters"],
            "gross_scores": h["gross_scores"],
            "notes": h["notes"],
        }
        for h in payload["holes"]
    ]
    with Session(engine, autoflush=False, expire_on_commit=True) as db:
        db.add_all([models.PlayerProfile(id=i, name=p["name"], created_at=STAMP) for i, p in enumerate(players, 1)])
        db.add(
            models.GameStateModel(
                game_id=game_id,
                game_status="completed",
                created_at=STAMP,
                updated_at=STAMP,
                state={
                    "players": players,
                    "game_status": "completed",
                    "current_hole": 19,
                    "standings": standings,
                    "hole_history": history,
                },
            )
        )
        db.add_all(
            [
                models.HoleEvent(
                    game_id=game_id,
                    hole_number=h["hole_number"],
                    player_id=pid,
                    score=h["gross_scores"][pid],
                    quarters=q,
                    recorded_at=STAMP,
                )
                for h in payload["holes"]
                for pid, q in h["quarters"].items()
            ]
        )
        record = models.GameRecord(
            game_id=game_id,
            course_name="Test Course",
            player_count=4,
            total_holes_played=18,
            created_at=STAMP,
            completed_at=STAMP,
            final_scores=standings,
        )
        db.add(record)
        db.flush()
        for i, player in enumerate(players, 1):
            pid = player["id"]
            db.add(
                models.GamePlayerResult(
                    game_record_id=record.id,
                    player_profile_id=i,
                    player_name=player["name"],
                    final_position={"p1": 1, "p2": 4, "p3": 2, "p4": 3}[pid],
                    total_earnings=standings[pid],
                    holes_won=18 if i == 1 else 0,
                    created_at=STAMP,
                    hole_scores=[
                        {
                            "hole": h["hole"],
                            "quarters": h["points_delta"][pid],
                            "gross_score": 4,
                            "teams": None,
                            "wager": None,
                            "phase": None,
                        }
                        for h in history
                    ],
                )
            )
        db.commit()


def snapshot(harness):
    """NullPool guarantees a new physical connection, not just an identity map."""
    with Session(harness.engine, autoflush=False, expire_on_commit=True) as db:
        pid = db.scalar(text("select pg_backend_pid()"))
        assert pid not in harness.request_pids
        return {
            model.__tablename__: [
                copy.deepcopy(dict(row)) for row in db.execute(select(model.__table__).order_by(model.id)).mappings()
            ]
            for model in (models.GameStateModel, models.HoleEvent, models.GameRecord, models.GamePlayerResult)
        }


@pytest.fixture
def score_pg():
    raw_url = os.getenv("SCORE_SAVE_TEST_DATABASE_URL")
    if not raw_url:
        if os.getenv("SCORE_SAVE_REQUIRE_POSTGRES") == "1":
            pytest.fail("SCORE_SAVE_REQUIRE_POSTGRES=1 requires SCORE_SAVE_TEST_DATABASE_URL")
        pytest.skip("Set SCORE_SAVE_TEST_DATABASE_URL to an explicitly disposable localhost PostgreSQL *_test database")
    url = make_url(raw_url)
    # Disallow libpq query-string host overrides, sockets, and non-test databases.
    if (
        url.get_backend_name() != "postgresql"
        or url.host not in {"localhost", "127.0.0.1", "::1"}
        or not (url.database or "").endswith("_test")
        or url.query
    ):
        pytest.fail("Score-save tests require a localhost PostgreSQL *_test database URL without query parameters")
    schema = "score_save_" + uuid.uuid4().hex
    admin_engine = create_engine(url.set(drivername="postgresql+psycopg2"), poolclass=NullPool)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        url.set(drivername="postgresql+psycopg2"),
        poolclass=NullPool,
        connect_args={"options": f"-csearch_path={schema} -cstatement_timeout=10000", "connect_timeout": 5},
    )
    harness = SimpleNamespace(
        engine=engine,
        game_id=str(uuid.uuid4()),
        request_pids=[],
        sessions=[],
        commits=[],
        postcommit_queries=[],
        identity=SimpleNamespace(id=1, email="member@example.invalid", admin_granted=0, is_active=1),
    )
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=True)

    def get_test_db():
        with factory() as db:
            harness.sessions.append(db)
            harness.request_pids.append(db.scalar(text("select pg_backend_pid()")))

            def after_commit(session):
                session.info["committed"] = True
                harness.commits.append(time.time())

            def forbid_postcommit_orm(execution):
                if db.info.get("committed"):
                    harness.postcommit_queries.append(str(execution.statement))
                    raise AssertionError("Score save attempted ORM SQL after commit")

            event.listen(db, "after_commit", after_commit)
            event.listen(db, "do_orm_execute", forbid_postcommit_orm)
            try:
                yield db
            except Exception:
                db.rollback()
                raise

    app = FastAPI()
    app.include_router(games.router)
    app.include_router(games_holes.router)
    app.add_middleware(ScoreSaveDiagnostics)
    app.dependency_overrides[database.get_db] = get_test_db
    # Authorization remains real: only the verified-identity boundary is replaced.
    app.dependency_overrides[get_current_user] = lambda: harness.identity
    try:
        models.Base.metadata.create_all(engine, tables=[model.__table__ for model in TABLES])
        seed_round(engine, harness.game_id)
        with TestClient(app, raise_server_exceptions=False) as client:
            harness.client = client
            yield harness
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()
