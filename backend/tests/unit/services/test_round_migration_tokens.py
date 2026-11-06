"""Raw external tokens and permanent participant slots are different identities."""

import pytest
from sqlalchemy.orm import Session

from app import models
from app.schemas.round_identity import RoundDraft
from app.services.round_identity_migration import apply_manifest, seal_manifest, verify_manifest
from app.services.round_reconciliation import observe_round
from app.services.round_sheet_values import mapped_draft
from tests.unit.services.test_round_identity_migration import approved, migration_fixture


@pytest.mark.parametrize("null_slot", [False, True])
def test_trusted_unequal_tokens_map_before_migration_and_actual_reimport(migration_fixture, null_slot):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        db.info["round_migration_transaction"] = True
        original = snapshot.rounds[0].draft
        canonical = RoundDraft.model_validate(
            {**original.model_dump(), "players": [{"participant_id": "p1", "name": "Guest", "quarters": 0}]}
        )
        first = observe_round(
            db,
            snapshot.rounds[0].source,
            canonical,
            observation_key="initial",
            raw_payload={},
            continuity_verified=True,
            create_without_candidate=True,
        )
        source = db.query(models.RoundSource).one()
        source.binding_evidence = {**source.binding_evidence, "participant_tokens": {"p1": "opaque-a"}}
        result = db.query(models.GamePlayerResult).one()
        result_id = result.id
        if null_slot:
            result.participant_id = None
            db.query(models.GameRecord).one().accepted_revision = 0
        db.commit()
        snapshot.rounds[0].draft = RoundDraft.model_validate(
            {**original.model_dump(), "players": [{"participant_id": "opaque-a", "name": "Guest", "quarters": 0}]}
        )
        manifest = approved(db, snapshot)
        manifest["saved_games"][0]["decision"]["result_slots"] = {str(result_id): "p1"}
        manifest["games"][0]["game_id"] = first.game_id
        manifest["games"][0]["decision"].update(action="bind_existing", source_participant_tokens={"p1": "opaque-a"})
        for entry in manifest["inventory"]["legacy_rounds"]:
            entry["decision"]["participant_id"] = "p1"
        manifest["approval"]["expected_standings"] = {"guest:p1": {"score": 0.0, "scored": 1, "participation": 1}}
        from tests.unit.services.test_round_identity_migration import approve_deltas

        approve_deltas(manifest, {"Guest": "guest:p1"})
        manifest = seal_manifest(manifest)
        apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert verify_manifest(db, manifest)["errors"] == []
        config = db.get(models.AppConfig, "round_identity")
        config.value = {**config.value, "mode": "canonical"}
        db.commit()
        row = db.query(models.RoundSource).one()
        reimport = observe_round(
            db,
            snapshot.rounds[0].source,
            mapped_draft(row, snapshot.rounds[0].draft),
            observation_key="actual-reimport",
            raw_payload={},
            continuity_verified=True,
        )
        db.commit()
        assert reimport.status == "unchanged" and not reimport.issue_ids
        assert db.query(models.GamePlayerResult).one().participant_id == "p1"
        assert manifest["snapshot"]["rounds"][0]["draft"]["players"][0]["participant_id"] == "opaque-a"
