"""Disposable localhost PostgreSQL transaction/race proof, never external DBs."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app import models
from app.schemas.round_identity import RoundDraft, SourceRef
from app.services.round_reconciliation import observe_round


@pytest.fixture
def pg_engine():
    url = os.environ.get("ROUND_IDENTITY_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Disposable localhost PostgreSQL URL required")
    parsed = urlparse(url)
    assert parsed.hostname in {"127.0.0.1", "localhost"} and parsed.path.endswith("round_identity_test")
    url = url.replace("postgresql://", "postgresql+psycopg2://")
    engine = create_engine(url)
    schema = "race_" + uuid4().hex
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    isolated = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    models.Base.metadata.create_all(isolated)
    yield isolated
    isolated.dispose()
    with engine.begin() as conn:
        conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    engine.dispose()


def ingest(session, token):
    return observe_round(
        session,
        SourceRef(kind="sheet", scope=token, round_token=token),
        RoundDraft(
            played_on="2026-01-01", players=[{"participant_id": "a", "name": "A", "quarters": 0}], roster_complete=True
        ),
        observation_key="one",
        raw_payload={},
        continuity_verified=True,
    )


@pytest.mark.parametrize("same_source", [True, False])
def test_global_lock_rechecks_committed_winner(pg_engine, same_source):
    started, finished = Event(), Event()
    with Session(pg_engine) as first:
        winner = ingest(first, "one")

        def second_worker():
            with Session(pg_engine) as second:
                started.set()
                result = ingest(second, "one" if same_source else "two")
                second.commit()
                finished.set()
                return result

        with ThreadPoolExecutor(max_workers=1) as workers:
            future = workers.submit(second_worker)
            assert started.wait(5)
            assert not finished.wait(0.2), "second transaction must wait for first transaction lock"
            first.commit()
            result = future.result(timeout=10)
    with Session(pg_engine) as readback:
        assert readback.query(models.GameRecord).count() == 1
        assert readback.query(models.GamePlayerResult).count() == 1
        if same_source:
            assert result.game_id == winner.game_id
            assert result.status == "unchanged"
            assert readback.query(models.RoundSource).count() == 1
        else:
            assert result.status == "held" and result.game_id is None
            assert readback.query(models.RoundSource).count() == 2
            assert readback.query(models.RoundDelivery).count() == 2


def test_postgres_rollback_has_no_evidence_or_intents(pg_engine):
    with Session(pg_engine) as db:
        ingest(db, "one")
        ingest(db, "two")
        db.rollback()
    with Session(pg_engine) as readback:
        for model in (
            models.GameRecord,
            models.GameStateModel,
            models.GamePlayerResult,
            models.RoundSource,
            models.RoundObservation,
            models.RoundIssue,
            models.RoundDelivery,
        ):
            assert readback.query(model).count() == 0
