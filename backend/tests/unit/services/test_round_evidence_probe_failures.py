"""Unrelated database errors are never physical immutability evidence."""

import sqlite3

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app import models
from app.services.round_evidence_guards import prove_evidence_guards
from tests.unit.services.test_round_identity_migration import migration_fixture


def test_unrelated_sql_failure_fails_proof_with_rows_preserved(migration_fixture, monkeypatch):
    engine, _ = migration_fixture
    with Session(engine) as db:
        source = models.RoundSource(kind="fixture", scope="proof", round_token="proof")
        db.add(source)
        db.flush()
        observation = models.RoundObservation(
            source_id=source.id,
            observation_key="proof",
            raw_payload={},
            parsed_values={},
            present_fields={},
            content_fingerprint="proof",
        )
        db.add(observation)
        db.flush()
        issue = models.RoundIssue(source_id=source.id, kind="identity", field="identity", fingerprint="proof")
        db.add(issue)
        db.flush()
        db.add(
            models.RoundResolution(
                issue_id=issue.id, actor_profile_id=1, action="keep", reason="Proof", observation_ids=[observation.id]
            )
        )
        db.commit()
        execute = db.execute

        def failing(statement, *args, **kwargs):
            if str(statement).startswith(("UPDATE", "DELETE")):
                raise OperationalError(str(statement), {}, sqlite3.OperationalError("database is locked"))
            return execute(statement, *args, **kwargs)

        monkeypatch.setattr(db, "execute", failing)
        with pytest.raises(ValueError, match="immutability"):
            prove_evidence_guards(db)
        assert db.query(models.RoundObservation).count() == 1
        assert db.query(models.RoundResolution).count() == 1
