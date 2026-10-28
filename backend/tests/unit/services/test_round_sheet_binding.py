"""Durable token lifecycle through actual HTTP review, worker and full ingestion."""

from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.routers import round_reconciliation as api
from app.schemas.round_identity import ResolutionDecision
from app.services.auth_service import get_current_user
from app.services.completed_game_service import persist_final_results
from app.services.round_evidence import accepted_draft
from app.services.round_reconciliation import resolve_issue
from app.services.round_sheet_delivery import process_sheet_job
from tests.unit.services.test_round_sheet_delivery import delivery_engine, sheet_job_fixture
from tests.unit.services.test_round_sheet_review import enqueue, refresh


@pytest.fixture
def reviewed_export(sheet_job_fixture):
    engine, _, rows, calls, initial, original, contract = sheet_job_fixture
    with Session(engine) as db, db.begin():
        db.get(models.PendingSheetSync, initial).status = "held"
        draft = accepted_draft(db, original)
        for player, slot in zip(draft.players, ["p1", "p2"], strict=True):
            player.participant_id = slot
        game = models.GameStateModel(game_id=str(uuid4()), state={}, game_status="completed")
        db.add(game)
        db.flush()
        persist_final_results(db, game, draft)
        game_id = game.game_id
        db.add(models.PlayerProfile(id=8, name="Synthetic admin", is_active=1, admin_granted=1))
    job = enqueue(engine, contract, game_id, "export", "insert", "exported")
    process_sheet_job(engine, job)
    assert all(o.status == "unchanged" for o in refresh(engine, contract))
    with Session(engine) as db:
        source = db.query(models.RoundSource).filter_by(game_id=game_id).one()
        source_id, mapping = source.id, dict(source.binding_evidence["participant_tokens"])
    app = FastAPI()
    app.include_router(api.router)

    def database():
        with Session(engine) as db:
            yield db

    def actor():
        with Session(engine) as db:
            return db.get(models.PlayerProfile, 8)

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_user] = actor
    yield engine, rows, calls, contract, game_id, source_id, mapping, TestClient(app)


def decision(engine, source_id, target=None):
    with Session(engine) as db:
        issue = db.query(models.RoundIssue).filter_by(source_id=source_id, kind="continuity", status="open").one()
        source = db.get(models.RoundSource, source_id)
        game = db.query(models.GameStateModel).filter_by(game_id=source.game_id).one()
        target_game = db.query(models.GameStateModel).filter_by(game_id=target or game.game_id).one()
        return issue.id, {
            "action": "bind_existing",
            "reason": "Synthetic continuity review",
            "target_game_id": target_game.game_id,
            "expected_game_revision": game.revision,
            "expected_target_game_revision": target_game.revision,
            "expected_issue_revision": issue.revision,
            "expected_head_revision": issue.head_revision,
        }


def changed(fixture, value=False):
    engine, rows, _, contract, _, source_id, *_ = fixture
    for row in rows:
        row[8] = "external-operation"
        if value:
            row[4] = "Unreviewed Course"
    assert all(o.status == "held" for o in refresh(engine, contract))
    return decision(engine, source_id)


@pytest.mark.parametrize("value_change", [False, True])
def test_same_uuid_review_preserves_map_and_value_conflicts(reviewed_export, value_change):
    engine, rows, calls, contract, game_id, source_id, mapping, client = reviewed_export
    issue_id, body = changed(reviewed_export, value_change)
    with Session(engine) as db:
        before_revision = db.get(models.RoundSource, source_id).revision
    # Shared service has no internal commit: rollback restores binding, heads and audit.
    with Session(engine) as db:
        resolve_issue(db, issue_id, ResolutionDecision(**body), actor_profile_id=8)
        db.rollback()
    with Session(engine) as db:
        assert db.get(models.RoundSource, source_id).revision == before_revision
        assert db.get(models.RoundSource, source_id).binding_evidence["participant_tokens"] == mapping
        assert db.query(models.RoundResolution).count() == 0
    response = client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=body)
    assert response.status_code == (202 if value_change else 200), response.text
    with Session(engine) as db:
        source = db.get(models.RoundSource, source_id)
        assert source.game_id == game_id and source.revision == before_revision + 1
        assert source.binding_evidence["participant_tokens"] == mapping
        audit = db.query(models.RoundResolution).filter_by(issue_id=issue_id).one()
        assert audit.target_game_id == game_id and audit.actor_profile_id == 8 and audit.observation_ids
        assert audit.value == {"game_id": game_id, "participant_tokens": mapping}
        assert audit.game_revision == body["expected_game_revision"]
        audit.value = {"participant_tokens": {"p1": "reassigned"}}
        with pytest.raises(ValueError, match="immutable"):
            db.flush()
        db.rollback()
        assert source.bound_by_profile_id == 8
        assert accepted_draft(db, game_id).course_name == "Synthetic Course"
    assert client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=body).status_code == 409
    for _ in range(2):
        outcomes = refresh(engine, contract)
        assert all(o.game_id == game_id for o in outcomes)
        assert all(o.status == ("held" if value_change else "unchanged") for o in outcomes)
    with Session(engine) as db:
        assert db.query(models.RoundIssue).filter_by(source_id=source_id, kind="roster").count() == 0
        values = db.query(models.RoundIssue).filter_by(source_id=source_id, kind="value", status="open").all()
        assert bool(values) == value_change
        # Continuity review must not accept a conflicting course implicitly.
        for issue in values:
            keep = {
                "action": "keep",
                "reason": "Keep accepted course",
                "expected_game_revision": body["expected_game_revision"],
                "expected_issue_revision": issue.revision,
                "expected_head_revision": issue.head_revision,
            }
            assert client.post(f"/round-reconciliation/issues/{issue.id}/resolve", json=keep).status_code == 200
    for operation in ["update-1", "update-2"]:
        job = enqueue(engine, contract, game_id, operation, token="exported")
        assert enqueue(engine, contract, game_id, operation, token="exported") == job
        calls["timeout"] = True
        process_sheet_job(engine, job)
        process_sheet_job(engine, job)
        with Session(engine) as db:
            assert db.get(models.PendingSheetSync, job).status == "done"
            assert db.get(models.RoundSource, source_id).binding_evidence["participant_tokens"] == mapping
        assert {r[7] for r in rows} == set(mapping.values())
        assert all(o.status == "unchanged" and o.game_id == game_id for o in refresh(engine, contract))
    assert calls["append"] == 1 and calls["update"] == 2


def test_different_uuid_rebind_holds_without_mutation_or_map_reassignment(reviewed_export):
    engine, _, _, _, game_id, source_id, mapping, client = reviewed_export
    changed(reviewed_export)
    with Session(engine) as db, db.begin():
        target = models.GameStateModel(game_id=str(uuid4()), state={}, game_status="completed")
        db.add(target)
        db.flush()
        # Even identical p1/p2 and identical guest names do not authorize reassignment.
        persist_final_results(db, target, accepted_draft(db, game_id))
        target_id = target.game_id
    issue_id, body = decision(engine, source_id, target_id)
    stale = {**body, "expected_target_game_revision": body["expected_target_game_revision"] + 1}
    assert client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=stale).status_code == 409
    response = client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=body)
    assert response.status_code == 409 and "participant mapping review" in response.text.lower()
    with Session(engine) as db:
        source = db.get(models.RoundSource, source_id)
        assert source.game_id == game_id and source.binding_evidence["participant_tokens"] == mapping
        assert db.get(models.RoundIssue, issue_id).status == "open"
        assert db.query(models.RoundResolution).count() == 0
        assert {p.participant_id for p in accepted_draft(db, target_id).players} == {"p1", "p2"}
        # The service itself rejects before any binding mutation, not merely HTTP rollback.
        with pytest.raises(HTTPException, match="participant mapping review"):
            resolve_issue(db, issue_id, ResolutionDecision(**body), actor_profile_id=8)
        assert db.get(models.RoundSource, source_id).game_id == game_id
        db.rollback()
