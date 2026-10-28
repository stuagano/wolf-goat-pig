"""Transaction-scoped configuration fence and authoritative stored verification.

Old binaries bypassing this row cannot be fenced: operators must stop/revoke
those writers before pause. No function here activates external dispatch.
"""

from copy import deepcopy

from fastapi import HTTPException

from app import models
from app.schemas.round_identity import read_round_identity_config
from app.utils.time import utc_now


def configuration_lock(db, *, exclusive=False):
    # Same ordering as all converted identity writers; a cutover cannot race the
    # shared configuration lock or deadlock by taking it before reconciliation.
    from .round_identity import acquire_reconciliation_lock

    acquire_reconciliation_lock(db)
    row = (
        db.query(models.AppConfig)
        .filter_by(name="round_identity")
        .populate_existing()
        .with_for_update(read=not exclusive)
        .one_or_none()
    )
    return row


def guard_writer(db, *, expected_epoch=None):
    if db.info.get("round_migration_transaction") is True:
        return read_round_identity_config(db)
    configuration_lock(db)
    config = read_round_identity_config(db)
    if config.mode == "paused" or (expected_epoch is not None and config.epoch != expected_epoch):
        raise HTTPException(409, "Round writes paused or writer epoch advanced")
    return config


def guard_client_epoch(db, expected_epoch):
    config = guard_writer(db, expected_epoch=expected_epoch)
    row = db.get(models.AppConfig, "round_identity")
    if row and row.value.get("require_client_epoch") and expected_epoch is None:
        raise HTTPException(409, "Client writer epoch required; reload and review retained edits")
    return config


def pause_writers(db, *, expected_epoch, reason):
    """Exclusive row lock drains shared writers; outer caller commits the pause."""
    row = configuration_lock(db, exclusive=True)
    config = read_round_identity_config(db)
    if row is None or config.epoch != expected_epoch or not reason.strip():
        raise ValueError("Configuration row, current epoch and pause reason required")
    value = deepcopy(row.value)
    value.update(
        mode="paused",
        epoch=config.epoch + 1,
        dispatch_paused=True,
        paused_at=utc_now().isoformat(),
        pause_reason=reason,
    )
    value.pop("verification", None)
    row.value = value
    db.flush()
    return value["epoch"]


def forward_rollback(db, *, expected_epoch, reason):
    """Forward-only recovery: pause, never restore/delete/renumber any game."""
    return pause_writers(db, expected_epoch=expected_epoch, reason=reason)


def store_verification(db, manifest):
    """Recompute real DB evidence; no client-provided passed flag is consumed."""
    from .round_identity_migration import verify_manifest
    from .round_migration_accounting import current_inventory_digest

    row = configuration_lock(db, exclusive=True)
    report = verify_manifest(db, manifest)
    if row is None or report["errors"] or report["unaccounted_source_rows"]:
        raise ValueError("Manifest verification failed")
    config = read_round_identity_config(db)
    if config.mode != "paused" or config.epoch != manifest["epoch"]:
        raise ValueError("Verification requires matching paused epoch")
    # Authority is server-stored manifest plus fresh recomputation at activation.
    from .round_evidence_guards import prove_evidence_guards

    physical = prove_evidence_guards(db)
    value = deepcopy(row.value)
    value["verification"] = {
        "manifest": manifest,
        "inventory_digest": current_inventory_digest(db),
        "epoch": config.epoch,
        "physical_proof": physical,
        "verified_at": utc_now().isoformat(),
    }
    row.value = value
    db.flush()
    return report


def activate_canonical(db, request, actor_id):
    from .round_identity_migration import verify_manifest
    from .round_migration_accounting import current_inventory_digest

    if request.mode != "canonical":
        raise HTTPException(409, "Only canonical activation is supported; use the offline pause command")
    row = configuration_lock(db, exclusive=True)
    config = read_round_identity_config(db)
    if row is None or config.epoch != request.expected_epoch or config.mode != "paused":
        raise HTTPException(409, "Matching paused writer epoch required")
    stored = (row.value or {}).get("verification", {})
    manifest = stored.get("manifest")
    supplied_checksum = request.verification_report.get("manifest_checksum")
    gate = db.get(models.AppConfig, "round_identity_gate_d")
    auth = gate.value if gate else {}
    if (
        not manifest
        or supplied_checksum != manifest.get("checksum")
        or stored.get("epoch") != config.epoch
        or stored.get("inventory_digest") != current_inventory_digest(db)
    ):
        raise HTTPException(409, "Fresh stored manifest verification required")
    report = verify_manifest(db, manifest)
    from .round_evidence_guards import prove_evidence_guards

    try:
        physical = prove_evidence_guards(db)
    except ValueError as exc:
        raise HTTPException(409, "Physical evidence immutability verification required") from exc
    if report["errors"] or report["unaccounted_source_rows"] or physical != stored.get("physical_proof"):
        raise HTTPException(409, "Fresh authoritative verification required")
    if (
        auth.get("manifest_checksum") != manifest["checksum"]
        or auth.get("epoch") != config.epoch
        or auth.get("actor_profile_id") != actor_id
        or not auth.get("reason")
        or not auth.get("approved_at")
    ):
        raise HTTPException(409, "Separate Gate D authorization required")
    value = deepcopy(row.value)
    value.update(
        mode="canonical",
        epoch=config.epoch + 1,
        dispatch_paused=True,
        require_client_epoch=True,
        activated_at=utc_now().isoformat(),
        activated_by_profile_id=actor_id,
    )
    row.value = value
    db.flush()
    return {"mode": "canonical", "epoch": value["epoch"], "dispatch_paused": True}
