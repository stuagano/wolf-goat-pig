"""HTTP write coordination on the existing UUID/evidence root; caller commits."""

from datetime import date
from uuid import uuid4

from fastapi import HTTPException

from app import models
from app.schemas.round_identity import RoundDraft, SourceRef, read_round_identity_config

from .round_evidence import fingerprint
from .round_identity import acquire_reconciliation_lock
from .round_reconciliation import observe_round


def writer_mode(db):
    # Shared lock orders every writer before config/candidate/game reads. A
    # cutover must acquire this same lock before changing mode/epoch.
    acquire_reconciliation_lock(db)
    db.query(models.AppConfig).filter_by(name="round_identity").populate_existing().with_for_update().first()
    config = read_round_identity_config(db)
    if config.mode == "paused":
        raise HTTPException(409, "Round writes are paused for cutover")
    return config.mode


def request_receipt(db, actor_id, key, payload, *, required=True):
    if not key or not key.strip() or len(key) > 200:
        if required:
            raise HTTPException(400, "Idempotency-Key is required (maximum 200 characters)")
        return None
    digest = fingerprint(payload)
    row = db.query(models.RoundRequest).filter_by(actor_profile_id=actor_id, request_key=key).one_or_none()
    if row:
        if row.fingerprint != digest:
            raise HTTPException(409, "Idempotency-Key reused with different content")
        return row
    row = models.RoundRequest(actor_profile_id=actor_id, request_key=key, fingerprint=digest)
    db.add(row)
    db.flush()
    return row


def create_observation(db, actor_id, key, payload, draft, kind):
    receipt = request_receipt(db, actor_id, key, {"kind": kind, "body": payload})
    if receipt.outcome is not None:
        return receipt, receipt.outcome
    outcome = observe_round(
        db,
        SourceRef(kind=kind, scope=f"actor:{actor_id}", round_token=key),
        draft,
        observation_key=key,
        raw_payload=payload,
        continuity_verified=True,
    )
    result = outcome.model_dump()
    receipt.game_id = outcome.game_id
    receipt.outcome = result
    return receipt, result


def stale_round(db, game):
    return {
        "code": "stale_round",
        "game_id": game.game_id,
        "revision": game.revision,
        "issue_ids": [r.id for r in db.query(models.RoundIssue).filter_by(game_id=game.game_id, status="open")],
    }


def check_revision(db, game, expected, *, required=False):
    if (required and expected is None) or (expected is not None and expected != game.revision):
        raise HTTPException(409, stale_round(db, game))


def detailed_draft(game, history, actor_id=None):
    state = game.state or {}
    played = state.get("played_at")
    return RoundDraft(
        played_on=date.fromisoformat(played[:10]) if played else None,
        course_name=state.get("course_name"),
        group=state.get("group"),
        roster_complete=True,
        players=[
            {"participant_id": p["id"], "name": p["name"], "profile_id": p.get("player_profile_id")}
            for p in state.get("players", [])
        ],
        detail_coverage="per_hole_complete" if len(history) == 18 else "partial",
        hole_history=history,
        actor_profile_id=actor_id,
    )


def propose_completed(db, game, history, actor_id=None):
    """Explicit UUID targeting establishes identity, never scoring permission.

    Caller already authorized participant/admin and validated the full snapshot.
    Values and detail are observations, not accepted projection writes.
    """
    source = SourceRef(kind="card_edit", scope=f"game:{game.game_id}", round_token=str(actor_id or "participant"))
    row = db.query(models.RoundSource).filter_by(**source.model_dump()).one_or_none()
    if row is None:
        row = models.RoundSource(
            **source.model_dump(), game_id=game.game_id, revision=1, binding_evidence={"kind": "authorized_uuid_target"}
        )
        db.add(row)
        db.flush()
    draft = detailed_draft(game, history, actor_id)
    if len(history) == 18:
        for p in draft.players:
            p.quarters = sum(h["points_delta"][p.participant_id] for h in history)
    outcome = observe_round(
        db,
        source,
        draft,
        observation_key=str(uuid4()),
        raw_payload={"target_game_id": game.game_id, "draft": draft.model_dump(mode="json")},
        continuity_verified=True,
    )
    result = stale_round(db, game)
    result["issue_ids"] = outcome.issue_ids
    return result
