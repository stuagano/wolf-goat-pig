"""A generic approval and replacement totals cannot erase a contribution."""

import pytest
from sqlalchemy.orm import Session

from app.services.round_identity_migration import apply_manifest, seal_manifest
from tests.unit.services.test_round_identity_migration import approved, migration_fixture


def test_duplicate_labels_map_each_original_contribution_and_require_each_delta(migration_fixture):
    from app import models
    from app.services.round_migration_deltas import delta_ledger, validate_deltas

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        db.add(
            models.LegacyRound(date="2026-10-02", group="B", member="Guest", score=5, source="sheet", status="attested")
        )
        db.commit()
        manifest = approved(db, snapshot)
        contributions = manifest["baseline_contributions"]
        assert len(contributions) == 2
        manifest["identity_mapping"] = {
            c["key"]: {
                "identity": f"guest:explicit-{i}",
                "actor_profile_id": 1,
                "reason": "Separate reviewed guests with the same label",
            }
            for i, c in enumerate(contributions)
        }
        manifest["approval"]["expected_standings"] = {}
        ledger = delta_ledger(manifest, {})
        manifest["approval"]["deltas"] = ledger
        with pytest.raises(ValueError, match="individual reason"):
            validate_deltas(manifest, {})
        for entry in ledger.values():
            entry.update(actor_profile_id=1, reason="This guest contribution explicitly held")
        validate_deltas(manifest, {})
        next(iter(ledger.values()))["old"]["participation"] = 123
        with pytest.raises(ValueError, match="recomputation"):
            validate_deltas(manifest, {})


def test_generic_reason_and_empty_standings_cannot_remove_original(migration_fixture):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest = approved(db, snapshot)
        manifest["games"][0]["decision"]["action"] = "hold"
        manifest["approval"]["expected_standings"] = {}
        manifest["approval"].pop("deltas", None)
        manifest = seal_manifest(manifest)
        with pytest.raises(ValueError, match="delta ledger"):
            apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
