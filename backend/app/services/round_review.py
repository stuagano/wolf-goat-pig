"""Safe HTTP projections and routing confirmation on existing round records."""

from fastapi import HTTPException

from app import models
from app.schemas.round_identity import read_round_identity_config
from app.services.round_delivery import confirmed_recipient
from app.services.round_identity import acquire_reconciliation_lock
from app.utils.admin_auth import is_admin_profile
from app.utils.time import utc_now


def require_reviewer(db, actor):
    from app.services.round_recipient import fresh_profile

    actor = fresh_profile(db, actor.id)
    recipient = confirmed_recipient(db)
    if not actor or not actor.is_active or not (is_admin_profile(actor) or (recipient and recipient.id == actor.id)):
        raise HTTPException(403, "Active confirmed reviewer or administrator required")
    return actor


def public_round(db, game_id):
    # Existing game state and detail endpoints are public. A final record is
    # required here; aliases must not advertise dangling or unfinished rounds.
    game = db.query(models.GameStateModel).filter_by(game_id=game_id).one_or_none()
    record = db.query(models.GameRecord).filter_by(game_id=game_id).one_or_none()
    if not game or not record:
        raise HTTPException(404, "Round unavailable")
    return game, record


def detail_agrees(record, rows, history):
    if record.detail_coverage != "per_hole_complete" or (record.game_settings or {}).get("detail_discrepancies"):
        return False
    slots = {row.participant_id for row in rows}
    if not slots or None in slots or len(history) != 18 or {h.get("hole") for h in history} != set(range(1, 19)):
        return False
    if any(set(h.get("points_delta") or {}) != slots for h in history):
        return False
    return all(
        row.total_earnings is not None
        and abs(sum(h["points_delta"][row.participant_id] for h in history) - row.total_earnings) <= 1e-9
        for row in rows
    )


def round_summary(db, game_id):
    game, record = public_round(db, game_id)
    rows = (
        db.query(models.GamePlayerResult).filter_by(game_record_id=record.id).order_by(models.GamePlayerResult.id).all()
    )
    history = (game.state or {}).get("hole_history") or []
    # Allowlist detail cells rather than leaking arbitrary state/source metadata.
    holes = [
        {key: hole[key] for key in ("hole", "points_delta", "gross_scores", "par") if key in hole} for hole in history
    ]
    return {
        "game_id": game_id,
        "revision": game.revision,
        "accepted_label": "accepted",
        "played_on": record.played_on,
        "raw_date": record.raw_date,
        "course_name": record.course_name,
        "detail_coverage": record.detail_coverage,
        "roster_complete": record.roster_complete,
        "score_eligible": bool(record.score_eligible and not record.is_retracted),
        "is_retracted": record.is_retracted,
        "players": [
            {
                "participant_id": row.participant_id,
                "name": row.player_name,
                "profile_id": row.player_profile_id,
                "quarters": row.total_earnings,
                "is_retracted": row.is_retracted,
            }
            for row in rows
        ],
        "hole_history": holes,
        "detail_label": "accepted_recorded_detail",
        "detail_discrepancies": {
            slot: {"accepted": values.get("accepted"), "computed_detail": values.get("computed")}
            for slot, values in (record.game_settings or {}).get("detail_discrepancies", {}).items()
            if slot in {row.participant_id for row in rows}
        },
        "detail_reconciled": detail_agrees(record, rows, history),
        "proposed_detail": {
            "label": "proposed",
            "available_to_reviewer": db.query(models.RoundIssue)
            .filter_by(game_id=game_id, field="detail", status="open")
            .count()
            > 0,
        },
        "conflict_count": db.query(models.RoundIssue).filter_by(game_id=game_id, status="open").count(),
        "capabilities": {
            "recorded_holes": bool(holes),
            "complete_detail": record.detail_coverage == "per_hole_complete",
            "photo": bool(game.scorecard_image),
            "discussion": True,
        },
    }


def confirm_routing(db, request, actor, claims):
    """Explicit admin selection of a current, trusted self-attestation."""
    from app.services.round_recipient import attest_recipient, fresh_profile, valid_attestation

    acquire_reconciliation_lock(db)
    actor = fresh_profile(db, actor.id)
    if not actor or not actor.is_active or not is_admin_profile(actor):
        raise HTTPException(403, "Active administrator required")
    row = (
        db.query(models.AppConfig).filter_by(name="round_identity").populate_existing().with_for_update().one_or_none()
    )
    profile = fresh_profile(db, request.profile_id)
    proof_id = request.attestation_id
    if not proof_id and actor.id == request.profile_id:
        proof_id = attest_recipient(db, actor.id, claims)["attestation_id"]
    evidence = valid_attestation(db, proof_id, profile, for_selection=True) if profile else None
    if not evidence:
        raise HTTPException(422, "Recipient requires a current matching self-attestation")
    old = dict(row.value or {}) if row else {}
    config = read_round_identity_config(db)
    stamp = utc_now().isoformat()
    audit = list(old.get("routing_audit", []))
    audit.append(
        {
            "actor_profile_id": actor.id,
            "previous_profile_id": config.reviewer_profile_id,
            "profile_id": profile.id,
            "reason": request.reason,
            "confirmed_at": stamp,
            "attestation_id": proof_id,
        }
    )
    value = {
        **old,
        "reviewer_profile_id": profile.id,
        "routing_confirmed": True,
        "routing_confirmed_by_profile_id": actor.id,
        "routing_confirmed_at": stamp,
        "routing_linkage_evidence": evidence,
        "routing_attestation_id": proof_id,
        "routing_audit": audit,
    }
    if row:
        row.value = value
    else:
        db.add(models.AppConfig(name="round_identity", value=value))
    db.flush()
    if not confirmed_recipient(db):
        raise HTTPException(422, "Recipient confirmation could not be validated")
    return {"profile_id": profile.id, "configured": True}
