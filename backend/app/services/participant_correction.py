"""Legacy-only single-link repair. Caller owns transaction; no derived writes."""

from copy import deepcopy

from fastapi import HTTPException
from sqlalchemy import text

from app import models
from app.services.round_cutover import guard_client_epoch, guard_writer
from app.services.round_evidence import fingerprint
from app.utils.admin_auth import is_admin_profile


def administrator(db, user):
    actor = db.query(models.PlayerProfile).filter_by(id=user.id).populate_existing().with_for_update().one_or_none()
    if actor is None or not actor.is_active or not is_admin_profile(actor):
        raise HTTPException(403, "Active administrator required")
    return actor


def result_values(row):
    return {c.name: deepcopy(getattr(row, c.name)) for c in row.__table__.columns}


def context(db, result_id, replacement_id):
    # Also protects absence/duplicate checks from legacy callers lacking the
    # advisory fence. These locks live through audit+link commit, never network IO.
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("LOCK TABLE game_records, game_player_results IN SHARE ROW EXCLUSIVE MODE"))
    result = (
        db.query(models.GamePlayerResult).filter_by(id=result_id).populate_existing().with_for_update().one_or_none()
    )
    if result is None:
        raise HTTPException(404, "Saved result unavailable")
    record = (
        db.query(models.GameRecord)
        .filter_by(id=result.game_record_id)
        .populate_existing()
        .with_for_update()
        .one_or_none()
    )
    if record is None or not record.game_id:
        raise HTTPException(409, "Saved game UUID unavailable")
    profiles = {
        p.id: p
        for p in db.query(models.PlayerProfile)
        .filter(models.PlayerProfile.id.in_([replacement_id, result.player_profile_id]))
        .populate_existing()
        .with_for_update()
        .all()
    }
    replacement = profiles.get(replacement_id)
    if replacement is None or not replacement.is_active:
        raise HTTPException(409, "Replacement must be an active existing profile")
    if result.player_profile_id is not None and result.player_profile_id not in profiles:
        raise HTTPException(409, "Current profile is missing; separate identity review required")
    rows = (
        db.query(models.GamePlayerResult)
        .filter_by(game_record_id=record.id)
        .order_by(models.GamePlayerResult.id)
        .populate_existing()
        .all()
    )
    game = db.query(models.GameStateModel).filter_by(game_id=record.game_id).populate_existing().one_or_none()
    unsupported = (
        record.accepted_revision
        or record.is_retracted
        or any(r.participant_id is not None or r.is_retracted for r in rows)
        or db.query(models.RoundSource).filter_by(game_id=record.game_id).first()
        or db.query(models.RoundIssue).filter_by(game_id=record.game_id).first()
        or db.query(models.RoundMigrationCheckpoint).filter_by(game_id=record.game_id).first()
        or db.query(models.LegacyRound).filter_by(game_id=record.game_id).first()
    )
    # A live state's mapped roster is another authority. Never silently diverge.
    if game and (
        game.revision or any(p.get("player_profile_id") is not None for p in (game.state or {}).get("players", []))
    ):
        unsupported = True
    if unsupported:
        raise HTTPException(
            409, "Canonical, mapped or conflicted game requires identity review; legacy correction refused"
        )
    name = " ".join((result.player_name or "").split()).casefold()
    if not name or sum(" ".join((r.player_name or "").split()).casefold() == name for r in rows) != 1:
        raise HTTPException(409, "Participant name is blank or ambiguous in this game")
    if any(r.id != result.id and r.player_profile_id == replacement_id for r in rows):
        raise HTTPException(409, "Replacement profile already participates in this game")

    def profile_view(profile):
        return {"id": profile.id, "name": profile.name, "legacy_name": profile.legacy_name} if profile else None

    view = {
        "game_id": record.game_id,
        "game_record_id": record.id,
        "result": result_values(result),
        "current_profile": profile_view(profiles.get(result.player_profile_id)),
        "replacement_profile": profile_view(replacement),
    }
    view["snapshot"] = fingerprint(
        {**view, "record": result_values(record), "roster": [result_values(r) for r in rows]}
    )
    return result, view


def preview(db, user, result_id, replacement_id):
    config = guard_writer(db)
    administrator(db, user)
    if config.mode != "legacy":
        raise HTTPException(409, "Only pre-canonical legacy corrections are supported")
    _, view = context(db, result_id, replacement_id)
    return {**view, "epoch": config.epoch}


def correct(db, user, result_id, request):
    config = guard_client_epoch(db, request.expected_epoch)
    actor = administrator(db, user)
    if config.mode != "legacy":
        raise HTTPException(409, "Only pre-canonical legacy corrections are supported")
    payload = {"result_id": result_id, **request.model_dump()}
    digest = fingerprint(payload)
    prior = (
        db.query(models.ParticipantCorrectionAudit)
        .filter_by(actor_profile_id=actor.id, request_key=request.request_key)
        .one_or_none()
    )
    if prior:
        if prior.fingerprint != digest:
            raise HTTPException(409, "Request key reused with different content")
        row = db.query(models.GamePlayerResult).filter_by(id=result_id).populate_existing().one_or_none()
        if row is None or result_values(row) != prior.after:
            raise HTTPException(409, "Correction has since changed; preview again")
        return prior.id
    row, view = context(db, result_id, request.replacement_profile_id)
    if row.player_profile_id != request.expected_old_profile_id or view["snapshot"] != request.expected_snapshot:
        raise HTTPException(409, "Saved participant changed; preview again before confirming")
    if row.player_profile_id == request.replacement_profile_id:
        raise HTTPException(409, "Participant already linked to this profile")
    before = result_values(row)
    row.player_profile_id = request.replacement_profile_id
    db.flush()
    db.refresh(row)
    after = result_values(row)
    if after != {**before, "player_profile_id": request.replacement_profile_id}:
        raise HTTPException(409, "Unexpected result changes; correction rolled back")
    audit = models.ParticipantCorrectionAudit(
        actor_profile_id=actor.id,
        request_key=request.request_key,
        fingerprint=digest,
        result_id=row.id,
        game_record_id=row.game_record_id,
        game_id=view["game_id"],
        old_profile_id=before["player_profile_id"],
        new_profile_id=row.player_profile_id,
        reason=request.reason,
        before=before,
        after=after,
    )
    db.add(audit)
    db.flush()
    return audit.id
