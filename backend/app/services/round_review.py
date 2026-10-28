"""Safe HTTP projections and routing confirmation on existing round records."""

from hashlib import sha256

from fastapi import HTTPException

from app import models
from app.schemas.round_identity import read_round_identity_config
from app.services.round_delivery import confirmed_recipient
from app.services.round_identity import acquire_reconciliation_lock
from app.utils.admin_auth import is_admin_profile
from app.utils.time import utc_now


def require_reviewer(db, actor):
    recipient = confirmed_recipient(db)
    if not actor.is_active or not (is_admin_profile(actor) or (recipient and recipient.id == actor.id)):
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
        "detail_reconciled": bool(holes) and not (record.game_settings or {}).get("detail_discrepancies"),
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
    """Only server-verified, subject-matched claims can establish linkage.

    Other profiles cannot be verified from an admin's token. Until an independent
    trusted linkage collector exists, they must not be configured by assertion.
    Caller owns transaction; selection alone never requeues or sends anything.
    """
    acquire_reconciliation_lock(db)
    row = db.query(models.AppConfig).filter_by(name="round_identity").with_for_update().one_or_none()
    profile = db.get(models.PlayerProfile, request.profile_id)
    subject = (profile.preferences or {}).get("auth0_id") if profile else None
    if not (
        profile
        and profile.is_active
        and not profile.is_ai
        and profile.email
        and subject
        and claims.get("sub") == subject
        and claims.get("email_verified") is True
        and (claims.get("email") or "").strip().lower() == profile.email.strip().lower()
    ):
        raise HTTPException(422, "Recipient requires active verified account linkage; caller claims must match")
    linked = (
        db.query(models.PlayerProfile).filter(models.PlayerProfile.preferences["auth0_id"].as_string() == subject).all()
    )
    if len(linked) != 1:
        raise HTTPException(422, "Recipient account linkage is ambiguous")
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
        }
    )
    value = {
        **old,
        "reviewer_profile_id": profile.id,
        "routing_confirmed": True,
        "routing_confirmed_by_profile_id": actor.id,
        "routing_confirmed_at": stamp,
        "routing_linkage_evidence": {
            "auth0_id": subject,
            "email_verified": True,
            "email_sha256": sha256(profile.email.strip().lower().encode()).hexdigest(),
        },
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
