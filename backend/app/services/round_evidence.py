"""Small evidence/head helpers shared by ingestion and reviewed resolution."""

import hashlib
import json

from app import models
from app.schemas.round_identity import RoundDraft, read_round_identity_config
from app.utils.time import utc_now


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def draft_values(draft):
    values = {("", f): getattr(draft, f) for f in ("played_on", "raw_date", "course_name", "group")}
    values = {key: value.isoformat() if hasattr(value, "isoformat") else value for key, value in values.items()}
    values[("", "roster_complete")] = draft.roster_complete
    values[("", "is_retracted")] = False
    if draft.hole_history:
        values[("", "detail")] = {
            "coverage": draft.detail_coverage,
            "holes": sorted(draft.hole_history, key=lambda h: h.get("hole", 0)),
        }
    for p in draft.players:
        for field in ("name", "profile_id", "quarters"):
            values[(p.participant_id, field)] = getattr(p, field)
        values[(p.participant_id, "is_retracted")] = p.participant_id in draft.removed_participant_ids
    for path in draft.clear_fields:
        parts = path.split(".")
        values[(parts[1], parts[2]) if len(parts) == 3 else ("", path)] = None
    for slot in draft.removed_participant_ids:
        # Removal never proposes overwriting historical player values.
        for field in ("name", "profile_id", "quarters"):
            values.pop((slot, field), None)
    return values


def accepted_draft(db, game_id):
    record = db.query(models.GameRecord).filter_by(game_id=game_id).one_or_none()
    if record is None:
        return None
    rows = db.query(models.GamePlayerResult).filter_by(game_record_id=record.id).all()
    if not rows or any(r.participant_id is None for r in rows):
        return None
    # The writer retains historical detail itself. A scalar/roster correction
    # must not resubmit sparse retained cells as new complete-roster evidence.
    return RoundDraft(
        detail_coverage="totals_only",
        hole_history=[],
        **{f: getattr(record, f) for f in ("played_on", "raw_date", "course_name", "group")},
        roster_complete=bool(record.roster_complete),
        players=[
            {
                "participant_id": r.participant_id,
                "name": r.player_name,
                "profile_id": r.player_profile_id,
                "quarters": r.total_earnings,
            }
            for r in rows
        ],
        removed_participant_ids=[r.participant_id for r in rows if r.is_retracted],
    )


def patch(draft, participant, field, value):
    data = draft.model_dump(mode="json")
    data["clear_fields"] = []
    data["removed_participant_ids"] = []
    if field == "is_retracted" and type(value) is not bool:
        raise ValueError("Retraction decisions require an explicit boolean")
    if participant:
        player = next(p for p in data["players"] if p["participant_id"] == participant)
        if field == "is_retracted":
            if value:
                data["removed_participant_ids"] = [participant]
        else:
            player[field] = value
            if value is None:
                data["clear_fields"] = [f"players.{participant}.{field}"]
    elif field == "detail":
        data["detail_coverage"] = value["coverage"]
        data["hole_history"] = value["holes"]
    else:
        data[field] = value
        if value is None:
            data["clear_fields"] = [field]
    return RoundDraft.model_validate(data)


def issue_for(db, source, observation, kind, *, head=None, candidates=(), value=None):
    participant, field = (head.participant_id, head.field) if head else ("", kind)
    issues = db.query(models.RoundIssue).filter_by(source_id=source.id, participant_id=participant, field=field).all()
    digest = fingerprint(
        [source.id, participant, field, value, candidates, head.accepted_revision if head else source.revision]
    )
    for old in issues:
        if old.status == "open" and old.fingerprint == digest:
            old.last_seen_at = utc_now().isoformat()
            return old
        if old.status == "open":
            old.status = "superseded"
            old.revision += 1
    issue = models.RoundIssue(
        source_id=source.id,
        game_id=source.game_id,
        kind=kind,
        participant_id=participant,
        field=field,
        fingerprint=digest,
        generation=max([i.generation for i in issues] or [0]) + 1,
        candidate_game_ids=list(candidates),
        observation_id=observation.id,
        head_revision=head.revision if head else source.revision,
        baseline_revision=head.accepted_revision if head else source.revision,
        accepted_present=head.accepted_present if head else False,
        accepted_value=head.accepted_value if head else None,
        proposed_present=True,
        proposed_value=value,
    )
    db.add(issue)
    db.flush()
    config = read_round_identity_config(db)
    recipient = db.get(models.PlayerProfile, config.reviewer_profile_id) if config.reviewer_profile_id else None
    configured = bool(
        config.routing_confirmed
        and recipient
        and recipient.is_active
        and recipient.email
        and (recipient.preferences or {}).get("email_verified")
        and (recipient.preferences or {}).get("auth0_id")
    )
    for channel in ("email", "in_app"):
        key = f"{issue.id}:{issue.generation}:{channel}:routing-{config.epoch}"
        db.add(
            models.RoundDelivery(
                issue_id=issue.id,
                issue_event_key=f"{issue.id}:{issue.generation}",
                recipient_profile_id=recipient.id if configured else None,
                channel=channel,
                delivery_key=key,
                status="pending" if configured else "unconfigured",
            )
        )
    db.flush()
    return issue
