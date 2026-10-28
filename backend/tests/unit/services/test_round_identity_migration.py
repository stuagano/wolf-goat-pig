"""Synthetic, offline migration behavior; never customer data or transports."""

from dataclasses import asdict

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import models
from app.schemas.round_identity import RoundDraft, SourceRef
from app.services.round_snapshot import SheetRound, SheetSnapshot


@pytest.fixture
def migration_fixture(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/migration.db")
    models.Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(models.AppConfig(name="round_identity", value={"mode": "paused", "epoch": 3, "season": 2026}))
        db.add(models.PlayerProfile(id=1, name="Synthetic reviewer", is_active=1))
        db.add(
            models.LegacyRound(
                id=1,
                date="2026-10-01",
                group="A",
                member="Guest",
                score=0,
                location="",
                source="sheet",
                status="attested",
            )
        )
        db.add(
            models.RoundComment(
                id=1,
                round_date="2026-10-01",
                round_group="A",
                location="",
                author_profile_id=1,
                body="Original",
                created_at="2026-10-01",
            )
        )
        db.add(
            models.RoundReaction(
                id=1,
                round_date="2026-10-01",
                round_group="A",
                location="",
                profile_id=1,
                emoji="🔥",
                created_at="2026-10-01",
            )
        )
        db.commit()
    draft = RoundDraft(
        played_on="2026-10-01",
        group="A",
        roster_complete=True,
        players=[{"participant_id": "slot-a", "name": "Guest", "quarters": 0}],
    )
    snapshot = SheetSnapshot(
        "synthetic:42:2026",
        "external-label",
        True,
        "v1",
        [
            SheetRound(
                SourceRef(kind="sheet", scope="synthetic:42:2026", round_token="token-a"),
                draft,
                {"rows": [["2026-10-01", "A", "Guest", 0]]},
                "event-a",
                True,
            )
        ],
        season_year=2026,
        source_rows=[["2026-10-01", "A", "Guest", 0]],
    )
    yield engine, snapshot
    engine.dispose()


def approved(db, snapshot):
    from app.services.round_identity_migration import build_manifest, seal_manifest

    manifest = build_manifest(db, snapshot)
    game_id = manifest["games"][0]["game_id"] if manifest["games"] else None
    for game in manifest["games"]:
        game["decision"] = {
            "action": "confirm_distinct",
            "reason": "Synthetic distinct evidence",
            "actor_profile_id": 1,
        }
    for table, rows in manifest["inventory"].items():
        for row in rows:
            row["decision"] = {"action": "preserve", "reason": "Synthetic reviewed evidence", "actor_profile_id": 1}
            if game_id and table in {"legacy_rounds", "round_comments", "round_reactions"}:
                row["decision"].update(action="attach", game_id=game_id)
                if table == "legacy_rounds":
                    row["decision"]["participant_id"] = "slot-a"
    for item in manifest["saved_games"]:
        item["decision"] = {
            "action": "publish_original",
            "actor_profile_id": 1,
            "reason": "Synthetic original saved roster",
            "roster_complete": True,
        }
    manifest["approval"] = {
        "actor_profile_id": 1,
        "reason": "Synthetic fixture only",
        "expected_standings": {"guest:slot-a": {"score": 0.0, "scored": 1, "participation": 1}},
    }
    approve_deltas(manifest)
    return seal_manifest(manifest)


def approve_deltas(manifest, identities=None):
    """Synthetic operator decisions, not production automatic identity inference."""
    from app.services.round_migration_deltas import delta_ledger

    for contribution in manifest["baseline_contributions"]:
        manifest["identity_mapping"][contribution["key"]] = {
            "identity": (identities or {}).get(contribution["facts"]["member"], "guest:slot-a"),
            "actor_profile_id": 1,
            "reason": "Synthetic explicit contribution identity",
        }
    ledger = delta_ledger(manifest, manifest["approval"]["expected_standings"])
    manifest["approval"]["deltas"] = {
        k: {**v, "actor_profile_id": 1, "reason": "Synthetic reviewed individual correction"} for k, v in ledger.items()
    }


def test_manifest_rerun_keeps_uuid_and_social_ids(migration_fixture):
    from app.services.round_identity_migration import apply_manifest, verify_manifest

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest = approved(db, snapshot)
        first = apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        second = apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert first["game_ids"] == second["game_ids"]
        report = verify_manifest(db, manifest)
        assert report["unaccounted_source_rows"] == 0
        assert report["preserved_comment_ids"] == [1]
        assert report["preserved_reaction_ids"] == [1]
        assert report["errors"] == []
    with Session(engine) as reader:
        assert reader.get(models.RoundComment, 1).game_id == first["game_ids"][0]
        assert reader.get(models.RoundComment, 1).body == "Original"
        assert reader.get(models.LegacyRound, 1).id == 1
        assert reader.query(models.GamePlayerResult).one().total_earnings == 0


def test_build_readonly_and_raw_checksum_not_client_label(migration_fixture):
    from app.services.round_identity_migration import build_manifest

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        first = build_manifest(db, snapshot)
        assert not db.new and not db.dirty
        snapshot.source_rows[0][2] = "Changed raw evidence"
        second = build_manifest(db, snapshot)
        assert first["raw_source_checksum"] != second["raw_source_checksum"]
        assert first["snapshot"]["fingerprint"] == second["snapshot"]["fingerprint"]
        assert asdict(snapshot)["complete"] is True


def test_drift_and_unreviewed_manifest_refused(migration_fixture):
    from app.services.round_identity_migration import apply_manifest, build_manifest

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        unreviewed = build_manifest(db, snapshot)
        with pytest.raises(ValueError):
            apply_manifest(db, unreviewed, expected_checksum=unreviewed["checksum"])
        db.rollback()
        manifest = approved(db, snapshot)
        db.get(models.LegacyRound, 1).score = 9
        db.commit()
        with pytest.raises(ValueError, match="drift"):
            apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        db.rollback()
        assert db.query(models.GameRecord).count() == 0


def test_resealed_manifest_cannot_omit_snapshot_round(migration_fixture):
    from app.services.round_identity_migration import apply_manifest, seal_manifest

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest = approved(db, snapshot)
        manifest["games"] = []
        manifest = seal_manifest(manifest)
        with pytest.raises(ValueError, match="exactly once"):
            apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert db.query(models.GameRecord).count() == 0


def test_hold_preserves_pending_retired_and_social_rows(migration_fixture):
    from app.services.round_identity_migration import apply_manifest, seal_manifest, verify_manifest

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        db.get(models.LegacyRound, 1).status = "pending"
        db.commit()
        manifest = approved(db, snapshot)
        manifest["games"][0]["decision"]["action"] = "hold"
        for entries in manifest["inventory"].values():
            for entry in entries:
                entry["decision"]["action"] = "hold"
        manifest["approval"]["expected_standings"] = {}
        approve_deltas(manifest)
        manifest = seal_manifest(manifest)
        apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        report = verify_manifest(db, manifest)
        assert report["errors"] == []
        assert report["held_operation_keys"] == [manifest["games"][0]["operation_key"]]
        assert db.get(models.LegacyRound, 1).status == "pending"
        assert db.get(models.RoundComment, 1).game_id is None
        assert db.query(models.GameRecord).count() == 0
        assert db.query(models.RoundIssue).count() == 1


def test_forward_rollback_preserves_committed_new_evidence(migration_fixture):
    from app.services.round_cutover import forward_rollback
    from app.services.round_identity_migration import apply_manifest

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest = approved(db, snapshot)
        apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        game_id = manifest["games"][0]["game_id"]
        db.add(
            models.RoundComment(
                id=2,
                game_id=game_id,
                round_date="2026-10-01",
                round_group="A",
                location="",
                author_profile_id=1,
                body="After migration",
                created_at="fixture",
            )
        )
        db.commit()
        from app.services.round_reconciliation import observe_round

        config = db.get(models.AppConfig, "round_identity")
        config.value = {**config.value, "mode": "canonical"}
        db.commit()
        distinct = snapshot.rounds[0].draft.model_copy(deep=True)
        distinct = RoundDraft.model_validate({**distinct.model_dump(), "played_on": "2026-10-02"})
        new_game = observe_round(
            db,
            SourceRef(kind="fixture", scope="new", round_token="post-cutover"),
            distinct,
            observation_key="post-cutover",
            raw_payload={"synthetic": True},
            continuity_verified=True,
            create_without_candidate=True,
        )
        conflict = snapshot.rounds[0].draft.model_copy(deep=True)
        conflict.players[0].quarters = 4
        outcome = observe_round(
            db,
            snapshot.rounds[0].source,
            conflict,
            observation_key="new-conflict",
            raw_payload={"synthetic": "conflict"},
            continuity_verified=True,
        )
        db.commit()
        assert new_game.game_id and outcome.issue_ids
        before = db.query(models.RoundObservation).count()
        assert forward_rollback(db, expected_epoch=3, reason="Synthetic recovery") == 4
        db.commit()
    with Session(engine) as reader:
        assert reader.get(models.RoundComment, 2).game_id == game_id
        assert reader.query(models.RoundObservation).count() == before
        assert reader.query(models.GameStateModel).filter_by(game_id=new_game.game_id).one()
        assert all(reader.get(models.RoundIssue, issue_id) for issue_id in outcome.issue_ids)
        assert reader.query(models.GameStateModel).filter_by(game_id=game_id).one()
        assert reader.get(models.AppConfig, "round_identity").value["dispatch_paused"] is True


def test_crash_rolls_back_whole_game_and_rerun_uses_assigned_uuid(migration_fixture, monkeypatch):
    from app.services import round_identity_migration as migration

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest = approved(db, snapshot)
        original = migration._associate

        def crash(*args):
            original(*args)
            raise RuntimeError("Synthetic crash before checkpoint")

        monkeypatch.setattr(migration, "_associate", crash)
        with pytest.raises(RuntimeError):
            migration.apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert db.query(models.GameRecord).count() == 0
        assert db.query(models.RoundMigrationCheckpoint).count() == 0
        assert db.get(models.RoundComment, 1).game_id is None
        monkeypatch.setattr(migration, "_associate", original)
        migration.apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert db.query(models.GameRecord).one().game_id == manifest["games"][0]["game_id"]
        assert migration.verify_manifest(db, manifest)["errors"] == []


def test_physical_sqlite_guards_reject_direct_sql_and_preserve_rows(migration_fixture):
    from sqlalchemy import text

    from app.services.round_evidence_guards import install_evidence_guards
    from app.services.round_identity_migration import apply_manifest

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest = approved(db, snapshot)
        apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        install_evidence_guards(db)
        db.commit()
        original = db.query(models.RoundObservation).one().id
        for operation in ("UPDATE round_observations SET id=id", "DELETE FROM round_observations"):
            with pytest.raises(Exception, match="immutable"), db.begin_nested():
                db.execute(text(operation))
        assert db.query(models.RoundObservation).one().id == original


def test_activation_requires_stored_physical_proof_and_separate_gate_d(migration_fixture):
    from fastapi import HTTPException

    from app.schemas.round_identity import RoundModeRequest
    from app.services.round_cutover import activate_canonical, store_verification
    from app.services.round_evidence_guards import install_evidence_guards
    from app.services.round_identity_migration import apply_manifest

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest = approved(db, snapshot)
        apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        request = RoundModeRequest(
            mode="canonical",
            expected_epoch=3,
            verification_report={"passed": True, "manifest_checksum": manifest["checksum"]},
        )
        with pytest.raises(HTTPException, match="Fresh stored"):
            activate_canonical(db, request, 1)
        db.rollback()
        observation = db.query(models.RoundObservation).one()
        issue = models.RoundIssue(
            source_id=observation.source_id,
            observation_id=observation.id,
            kind="identity",
            field="identity",
            fingerprint="synthetic-proof",
        )
        db.add(issue)
        db.flush()
        db.add(
            models.RoundResolution(
                issue_id=issue.id,
                actor_profile_id=1,
                action="keep",
                reason="Synthetic proof",
                observation_ids=[observation.id],
            )
        )
        db.commit()
        # New evidence invalidates the original manifest, not merely its stored flag.
        with pytest.raises(ValueError, match="verification failed"):
            store_verification(db, manifest)
        db.rollback()
        # Prove the actual post-migration inventory through a fresh reviewed manifest.
        manifest = approved(db, snapshot)
        apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        with pytest.raises(ValueError, match="immutability"):
            store_verification(db, manifest)
        db.rollback()
        install_evidence_guards(db)
        db.commit()
        store_verification(db, manifest)
        db.commit()
        request.verification_report = {"manifest_checksum": manifest["checksum"]}
        with pytest.raises(HTTPException, match="Separate Gate D"):
            activate_canonical(db, request, 1)
        db.rollback()
        db.add(
            models.AppConfig(
                name="round_identity_gate_d",
                value={
                    "manifest_checksum": manifest["checksum"],
                    "epoch": 3,
                    "actor_profile_id": 1,
                    "reason": "Synthetic fixture approval",
                    "approved_at": "synthetic",
                },
            )
        )
        db.commit()
        assert activate_canonical(db, request, 1) == {"mode": "canonical", "epoch": 4, "dispatch_paused": True}
        db.commit()
        assert db.get(models.AppConfig, "round_identity").value["require_client_epoch"] is True


def test_source_global_participant_token_collision_refused(migration_fixture):
    from copy import deepcopy

    from app.services.round_evidence import fingerprint
    from app.services.round_identity_migration import apply_manifest, seal_manifest

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest = approved(db, snapshot)
        first = manifest["games"][0]
        first["decision"]["source_participant_tokens"] = {"slot-a": "duplicate-token"}
        second = deepcopy(first)
        second["source"]["round_token"] = "another-round"
        second["operation_key"] = fingerprint(second["source"])
        second["game_id"] = "another-issued-uuid"
        manifest["games"].append(second)
        manifest["snapshot"]["rounds"].append(
            {key: second[key] for key in ("source", "draft", "raw_payload", "observation_key", "continuity_verified")}
        )
        manifest["raw_source_checksum"] = fingerprint(manifest["snapshot"])
        manifest = seal_manifest(manifest)
        with pytest.raises(ValueError, match="token collision"):
            apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert db.query(models.GameStateModel).count() == 0


def test_tampering_fails_before_any_write(migration_fixture):
    from app.services.round_identity_migration import apply_manifest

    engine, snapshot = migration_fixture
    with Session(engine) as db:
        manifest = approved(db, snapshot)
        manifest["games"][0]["draft"]["players"][0]["quarters"] = 99
        with pytest.raises(ValueError, match="checksum"):
            apply_manifest(db, manifest, expected_checksum=manifest["checksum"])
        assert db.query(models.GameRecord).count() == 0
