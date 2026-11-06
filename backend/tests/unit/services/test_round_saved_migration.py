"""Existing-only games cannot vanish behind a preserve-row decision."""

from datetime import date

import pytest
from sqlalchemy.orm import Session

from app import models
from app.services.round_identity_migration import apply_manifest, seal_manifest, verify_manifest
from tests.unit.services.test_round_identity_migration import approved, migration_fixture


@pytest.mark.parametrize("slot", [None, "original-slot"])
def test_existing_only_orphan_original_scores_publish_and_readback(migration_fixture, slot):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        record = models.GameRecord(
            game_id="saved-original",
            played_on=date(2026, 9, 2),
            player_count=1,
            roster_complete=True,
            accepted_revision=0,
        )
        db.add(record)
        db.flush()
        result = models.GamePlayerResult(
            game_record_id=record.id, participant_id=slot, player_name="Saved guest", total_earnings=8
        )
        db.add(result)
        db.commit()
        rid, pid = record.id, result.id
        snapshot.rounds = []  # No sheet membership is required to repair saved originals.
        manifest = approved(db, snapshot)
        assert len(manifest["saved_games"]) == 1
        manifest["saved_games"][0]["decision"] = {
            "action": "publish_original",
            "actor_profile_id": 1,
            "reason": "Original totals and complete saved roster",
            "roster_complete": True,
            "result_slots": {str(pid): "original-slot"},
        }
        manifest["approval"]["expected_standings"] = {
            "guest:original-slot": {"score": 8.0, "scored": 1, "participation": 1}
        }
        from tests.unit.services.test_round_identity_migration import approve_deltas

        approve_deltas(manifest, {"Saved guest": "guest:original-slot"})
        manifest = seal_manifest(manifest)
        apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert verify_manifest(db, manifest)["errors"] == []
    with Session(engine) as db:
        assert db.query(models.GameStateModel).filter_by(game_id="saved-original").one().state["standings"] == {
            "original-slot": 8
        }
        assert db.get(models.GameRecord, rid).accepted_revision > 0
        assert db.get(models.GamePlayerResult, pid).total_earnings == 8


def test_multigame_crash_after_first_commit_resumes_original_uuid(migration_fixture, monkeypatch):
    from copy import deepcopy

    from app.services import round_identity_migration as migration
    from app.services.round_evidence import fingerprint

    engine, snapshot = migration_fixture
    second = deepcopy(snapshot.rounds[0])
    second.source.round_token = "second"
    second.observation_key = "second"
    snapshot.rounds.append(second)
    with Session(engine) as db:
        manifest = approved(db, snapshot)
        # Both source rounds have explicit distinct decisions and contributions.
        manifest["approval"]["expected_standings"]["guest:slot-a"] = {"score": 0.0, "scored": 2, "participation": 2}
        from tests.unit.services.test_round_identity_migration import approve_deltas

        approve_deltas(manifest)
        manifest = seal_manifest(manifest)
        original = migration._apply_game

        def crash(db, manifest, item):
            if item["source"]["round_token"] == "token-a":
                raise RuntimeError("Second batch fixture crash")
            return original(db, manifest, item)

        monkeypatch.setattr(migration, "_apply_game", crash)
        with pytest.raises(RuntimeError):
            apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert db.query(models.RoundMigrationCheckpoint).count() == 1
        assert db.query(models.GameRecord).count() == 1
        monkeypatch.setattr(migration, "_apply_game", original)
        apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert verify_manifest(db, manifest)["errors"] == []
        assert {r.game_id for r in db.query(models.GameRecord)} == {w["game_id"] for w in manifest["games"]}


def test_preserve_inventory_cannot_omit_saved_game_publication(migration_fixture):
    engine, snapshot = migration_fixture
    with Session(engine) as db:
        db.add(models.GameRecord(game_id="missing-container", player_count=0))
        db.commit()
        manifest = approved(db, snapshot)
        manifest["saved_games"] = []
        manifest = seal_manifest(manifest)
        with pytest.raises(ValueError, match="Every saved game"):
            apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
