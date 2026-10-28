"""Transactional round alert outbox using the existing notification/email services.

Email `accepted` means provider acceptance, NOT inbox delivery. Boolean failures
and expired pre-send claims are uncertain: only proven pre-acceptance failures
may retry. No source session is ever committed by this dispatcher.
"""

import logging
from datetime import datetime, timedelta
from hashlib import sha256
from urllib.parse import quote, unquote, urlsplit
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import or_

from app import models
from app.database import SessionLocal
from app.schemas.round_identity import read_round_identity_config
from app.services.email_service import RoundEmailRejectedError, get_email_service
from app.services.notification_service import get_notification_service
from app.utils.admin_auth import is_admin_profile
from app.utils.time import utc_now

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 5
LEASE_SECONDS = 120


def safe_round_path(path):
    """Only an unambiguous local absolute path; never protocol-relative URLs."""
    if not isinstance(path, str) or not path.startswith("/"):
        return None
    decoded = unquote(path)
    if decoded.startswith("//") or "\\" in decoded or any(ord(c) < 33 for c in decoded):
        return None
    parts = urlsplit(decoded)
    return path if not parts.scheme and not parts.netloc else None


def confirmed_recipient(db):
    """Validate the confirmed profile/account/email snapshot, not admin lists.

    The evidence is recorded by an authorized operator from a verified account
    claim. A changed subject/email or duplicate subject invalidates confirmation.
    No email address or credential is stored in delivery diagnostics.
    """
    from app.services.round_recipient import fresh_config, fresh_profile, valid_attestation

    row, config = fresh_config(db)
    profile = fresh_profile(db, config.reviewer_profile_id) if config.reviewer_profile_id else None
    actor = (
        fresh_profile(db, config.routing_confirmed_by_profile_id) if config.routing_confirmed_by_profile_id else None
    )
    evidence = config.routing_linkage_evidence
    try:
        stamp = datetime.fromisoformat(config.routing_confirmed_at or "")
        from datetime import UTC

        stamp = stamp.astimezone(UTC).replace(tzinfo=None) if stamp.tzinfo else stamp
        valid_time = stamp <= utc_now()
    except ValueError:
        valid_time = False
    subject = (profile.preferences or {}).get("auth0_id") if profile else None
    if not (
        config.routing_confirmed
        and valid_time
        and actor
        and actor.is_active
        and is_admin_profile(actor)
        and profile
        and profile.is_active
        and not profile.is_ai
        and profile.email
        and subject
        and evidence.get("auth0_id") == subject
        and evidence.get("email_verified") is True
        and evidence.get("email_sha256") == sha256(profile.email.strip().lower().encode()).hexdigest()
    ):
        return None
    proof_id = (row.value or {}).get("routing_attestation_id") if row else None
    if not valid_attestation(db, proof_id, profile):
        return None
    linked = (
        db.query(models.PlayerProfile)
        .filter(models.PlayerProfile.preferences["auth0_id"].as_string() == subject)
        .populate_existing()
        .all()
    )
    return profile if len(linked) == 1 and linked[0].id == profile.id else None


def enqueue_round_deliveries(db, issue):
    """Called within the source transaction; retain both intents if unconfigured."""
    recipient = confirmed_recipient(db)
    config = read_round_identity_config(db)
    for channel in ("email", "in_app"):
        key = f"{issue.id}:{issue.generation}:{channel}:routing-{config.epoch}"
        if db.query(models.RoundDelivery).filter_by(delivery_key=key).first():
            continue
        db.add(
            models.RoundDelivery(
                issue_id=issue.id,
                issue_event_key=f"{issue.id}:{issue.generation}",
                recipient_profile_id=recipient.id if recipient else None,
                channel=channel,
                delivery_key=key,
                status="pending" if recipient else "unconfigured",
            )
        )
    db.flush()


def requeue_round_deliveries(db, issue_ids, *, actor_profile_id, reason):
    """Explicit admin selection only; never replay history on a config change.

    Preserve original deliveries (including uncertain sends) and append an
    immutable resolution audit. Same recipient/channel successes never replay.
    The caller owns this transaction.
    """
    actor = db.get(models.PlayerProfile, actor_profile_id)
    if not actor or not actor.is_active or not is_admin_profile(actor):
        raise HTTPException(403, "Administrator required")
    recipient = confirmed_recipient(db)
    if not recipient or not reason.strip():
        raise HTTPException(409, "Confirmed routing and a reason are required")
    count = 0
    for issue_id in sorted(set(issue_ids)):
        issue = db.query(models.RoundIssue).filter_by(id=issue_id).with_for_update().one_or_none()
        if not issue or issue.status != "open":
            raise HTTPException(409, "Only selected outstanding issues may be requeued")
        rows = db.query(models.RoundDelivery).filter_by(issue_id=issue.id).with_for_update().all()
        if any(
            r.status == "sending" and r.lease_expires_at and r.lease_expires_at > utc_now().isoformat() for r in rows
        ):
            raise HTTPException(409, "Delivery currently claimed; retry after lease expiry")
        for row in rows:
            if row.recipient_profile_id != recipient.id and row.status in {"pending", "unconfigured", "failed"}:
                row.status = "replaced"
        for channel in ("email", "in_app"):
            existing = next((r for r in rows if r.channel == channel and r.recipient_profile_id == recipient.id), None)
            if existing:
                # Replaced intents came only from unsent states. Never reset
                # acceptance/uncertainty, or an exhausted attempt budget.
                if existing.status in {"unconfigured", "replaced"} and existing.attempts < MAX_ATTEMPTS:
                    existing.status, existing.error = "pending", None
                    existing.lease_expires_at = None
                    count += 1
                continue
            db.add(
                models.RoundDelivery(
                    issue_id=issue.id,
                    issue_event_key=f"{issue.id}:{issue.generation}",
                    recipient_profile_id=recipient.id,
                    channel=channel,
                    delivery_key=f"{issue.id}:{issue.generation}:{channel}:recipient-{recipient.id}",
                    status="pending",
                )
            )
            count += 1
        db.add(
            models.RoundResolution(
                issue_id=issue.id,
                actor_profile_id=actor.id,
                action="routing_requeue",
                reason=reason,
                issue_revision=issue.revision,
                head_revision=issue.head_revision,
                value_present=True,
                value={
                    "recipient_profile_id": recipient.id,
                    "previous_delivery_ids": [r.id for r in rows],
                    "routing_confirmed_at": read_round_identity_config(db).routing_confirmed_at,
                },
            )
        )
    db.flush()
    return count


def _path(issue):
    return (
        f"/game/{quote(issue.game_id, safe='')}"
        if issue.game_id
        else f"/rounds/reconciliation?issue={quote(issue.id, safe='')}"
    )


def _retry(row, code):
    row.error = code
    row.status = "failed" if row.attempts >= MAX_ATTEMPTS else "pending"
    row.lease_owner = None
    row.lease_expires_at = (utc_now() + timedelta(seconds=min(3600, 30 * 2**row.attempts))).isoformat()


def _dispatch_one():
    with SessionLocal() as db:
        now = utc_now().isoformat()
        row = (
            db.query(models.RoundDelivery)
            .filter(
                models.RoundDelivery.status.in_(["pending", "sending"]),
                or_(models.RoundDelivery.lease_expires_at.is_(None), models.RoundDelivery.lease_expires_at <= now),
            )
            .order_by(models.RoundDelivery.created_at, models.RoundDelivery.id)
            .with_for_update(skip_locked=True)
            .first()
        )
        if row is None:
            return None
        # A sending email claim was committed BEFORE invoking the provider. Even
        # a crash just before that invocation is conservatively held uncertain.
        if row.status == "sending":
            row.status, row.error = "uncertain", "expired_email_claim"
            db.commit()
            return "uncertain"
        recipient = confirmed_recipient(db)
        if not recipient or row.recipient_profile_id != recipient.id:
            row.status, row.error = "unconfigured", "routing_confirmation_required"
            db.commit()
            return "unconfigured"
        issue = db.get(models.RoundIssue, row.issue_id)
        if not issue or issue.status != "open":
            row.status = "obsolete"
            db.commit()
            return "obsolete"
        path = safe_round_path(_path(issue))
        if not path:
            row.status, row.error = "failed", "unsafe_path"
            db.commit()
            return "failed"
        row.attempts += 1
        if row.channel == "in_app":
            try:
                # The row lock predates this savepoint. A failed notification
                # rolls back only its insert, never releases the owning lock.
                # Attempt accounting and backoff commit under that same lock.
                with db.begin_nested():
                    get_notification_service().send_notification(
                        recipient.id,
                        "round_conflict",
                        "A round needs review",
                        db,
                        data={"path": path, "issue_id": issue.id},
                        delivery_key=row.delivery_key,
                        commit=False,
                    )
                row.status, row.delivered_at = "delivered", now
                row.error = None
            except Exception:
                _retry(row, "notification_transaction_failed")
            status = row.status
            db.commit()
            return status
        if row.channel != "email":
            row.status, row.error = "failed", "unsupported_channel"
            db.commit()
            return "failed"
        service = get_email_service()
        if not service.is_configured():
            _retry(row, "provider_unconfigured_before_send")
            status = row.status
            db.commit()
            return status
        # Pre-send durable claim. Never hold a DB transaction across network I/O.
        row.status, row.lease_owner = "sending", str(uuid4())
        row.lease_expires_at = (utc_now() + timedelta(seconds=LEASE_SECONDS)).isoformat()
        row_id, owner, email, issue_id = row.id, row.lease_owner, recipient.email, issue.id
        db.commit()
    try:
        accepted = service.send_round_conflict_notification(to_email=email, issue_id=issue_id, path=path)
        status = "accepted" if accepted is True else "uncertain"
    except RoundEmailRejectedError:
        status = "rejected"
    except Exception:
        status = "uncertain"
    with SessionLocal() as db:
        row = db.query(models.RoundDelivery).filter_by(id=row_id).with_for_update().one()
        if row.status == "sending" and row.lease_owner == owner:
            if status == "rejected":
                _retry(row, "provider_rejected_before_acceptance")
            else:
                row.status = status
                row.error = None if status == "accepted" else "provider_acceptance_unknown"
                row.delivered_at = utc_now().isoformat() if status == "accepted" else None
                row.lease_owner, row.lease_expires_at = None, None
            db.commit()
        return row.status


def dispatch_round_deliveries(*, limit: int = 50) -> dict[str, int]:
    """One bounded drain, also callable by the authenticated scheduler job."""
    counts = {}
    for _ in range(max(0, min(limit, 500))):
        status = _dispatch_one()
        if status is None:
            break
        counts[status] = counts.get(status, 0) + 1
    return counts
