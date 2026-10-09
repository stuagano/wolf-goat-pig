"""Claims: a returning player asks to be connected to their original profile.

Many players have an original profile (their history, no email, no login) from
before logins existed. On first sign-in they land on a new stray profile; when
they pick their roster name it's already held by the original. Instead of a
dead end, that becomes a claim an admin approves (see routers/account_claims.py).
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from sqlalchemy import func, or_

from ..models import AccountClaim, PlayerProfile
from ..utils.time import utc_now

logger = logging.getLogger(__name__)


def has_login(profile: PlayerProfile) -> bool:
    return bool((profile.preferences or {}).get("auth0_id"))


def find_name_holder(db: Any, canonical_name: str) -> PlayerProfile | None:
    """The active profile holding this roster name (lowest id wins)."""
    low = canonical_name.lower()
    return (
        db.query(PlayerProfile)
        .filter(
            PlayerProfile.is_active == 1,
            or_(func.lower(PlayerProfile.legacy_name) == low, func.lower(PlayerProfile.name) == low),
        )
        .order_by(PlayerProfile.id)
        .first()
    )


def pending_claim_for(db: Any, requester_profile_id: int) -> AccountClaim | None:
    return (
        db.query(AccountClaim)
        .filter(AccountClaim.requester_profile_id == requester_profile_id, AccountClaim.status == "pending")
        .order_by(AccountClaim.id.desc())
        .first()
    )


def request_claim_for_name(
    db: Any,
    requester: PlayerProfile,
    canonical_name: str,
    *,
    email: str | None,
    email_verified: bool | None,
) -> dict[str, Any]:
    """Turn "that name is taken" into a pending claim when the holder has no login. Caller commits."""
    holder = find_name_holder(db, canonical_name)
    if holder is None or holder.id == requester.id or has_login(holder):
        return {"status": "taken"}
    if email_verified is not True:
        return {"status": "unverified"}

    now = utc_now().isoformat()
    existing = pending_claim_for(db, requester.id)
    if existing and existing.target_profile_id == holder.id:
        return {"status": "pending", "claim": existing, "created": False}
    if existing:
        existing.status = "dismissed"
        existing.resolved_at = now
        existing.resolved_by = "superseded"
    claim = AccountClaim(
        requester_profile_id=requester.id,
        target_profile_id=holder.id,
        canonical_name=canonical_name,
        requester_email=email,
        status="pending",
        created_at=now,
    )
    db.add(claim)
    db.flush()
    logger.info("Claim %s: profile %s asks to be %r (profile %s)", claim.id, requester.id, canonical_name, holder.id)
    return {"status": "pending", "claim": claim, "created": True}


def notify_admins_of_claim(canonical_name: str, requester_email: str | None) -> None:
    """Best-effort, non-blocking admin email; never affects the player's request."""

    def _send() -> None:
        try:
            from ..utils.admin_auth import get_admin_emails
            from .email_service import get_email_service

            service = get_email_service()
            if not service.is_configured():
                return
            for admin_email in get_admin_emails():
                service.send_account_claim_notification(admin_email, canonical_name, requester_email)
        except Exception as exc:  # never surface to the player
            logger.warning("Failed to notify admins of claim for %r: %s", canonical_name, exc)

    threading.Thread(target=_send, daemon=True, name="account-claim-notify").start()
