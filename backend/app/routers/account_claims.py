"""Admin: approve or dismiss returning players' claims on their original profile."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AccountClaim, PlayerProfile
from ..services.account_claim_service import has_login
from ..services.player_service import release_identity_and_retire
from ..utils.admin_auth import require_admin
from ..utils.time import utc_now

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/claims", tags=["players"])


def _summary(player: PlayerProfile | None) -> dict[str, Any] | None:
    if player is None:
        return None
    login = (player.preferences or {}).get("auth0_id") or ""
    return {
        "id": player.id,
        "name": player.name,
        "legacy_name": player.legacy_name,
        "email": player.email,
        "login": login.split("|")[0] or None,
        "is_active": bool(player.is_active),
        "updated_at": player.updated_at,
    }


def _row(db: Session, claim: AccountClaim) -> dict[str, Any]:
    return {
        "id": claim.id,
        "canonical_name": claim.canonical_name,
        "requester_email": claim.requester_email,
        "status": claim.status,
        "created_at": claim.created_at,
        "resolved_at": claim.resolved_at,
        "resolved_by": claim.resolved_by,
        "requester": _summary(db.get(PlayerProfile, claim.requester_profile_id)),
        "target": _summary(db.get(PlayerProfile, claim.target_profile_id)),
    }


def _pending(db: Session, claim_id: int, lock: bool = True) -> AccountClaim:
    query = db.query(AccountClaim).filter(AccountClaim.id == claim_id)
    if lock:
        query = query.with_for_update().populate_existing()
    claim = query.first()
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status != "pending":
        raise HTTPException(status_code=409, detail=f"This claim is already {claim.status}.")
    return claim


@router.get("", dependencies=[Depends(require_admin)])
def list_claims(
    status: str = Query("pending", pattern="^(pending|approved|dismissed)$"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    claims = (
        db.query(AccountClaim).filter(AccountClaim.status == status).order_by(AccountClaim.id.desc()).limit(100).all()
    )
    return {"claims": [_row(db, claim) for claim in claims]}


def _lock_identities(db: Session, identities: list[str]) -> None:
    """Take sorted transaction-scoped advisory locks (PostgreSQL only), as relink-auth0 does."""
    if db.get_bind().dialect.name != "postgresql":
        return
    for identity in sorted(identities):
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:identity))"), {"identity": f"account-link:{identity}"})


@router.post("/{claim_id}/approve")
def approve_claim(
    claim_id: int, admin: dict[str, Any] = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Move the requester's login onto the original profile and retire the stray, atomically."""
    # Read without row locks first: the advisory locks must come before any row lock
    # (relink-auth0's order), or two admins touching the same profile can deadlock.
    claim = _pending(db, claim_id, lock=False)
    peek = db.get(PlayerProfile, claim.requester_profile_id)
    peek_subject = (peek.preferences or {}).get("auth0_id") if peek else None
    peek_email = (peek.email if peek else None) or claim.requester_email
    canonical = claim.canonical_name

    # Serialize against relink-auth0 and other approvals touching the same identities.
    # Lock keys match relink-auth0's; sorted so lock order is consistent across callers.
    identities = [f"roster:{canonical.lower()}"]
    if peek_subject:
        identities.append(f"auth0:{peek_subject}")
    if peek_email:
        identities.append(f"email:{peek_email.lower()}")
    _lock_identities(db, identities)

    # Now take row locks and re-validate: what we locked on must still be true.
    claim = _pending(db, claim_id)
    # populate_existing: with_for_update alone returns stale identity-map objects.
    requester = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.id == claim.requester_profile_id)
        .with_for_update()
        .populate_existing()
        .first()
    )
    target = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.id == claim.target_profile_id)
        .with_for_update()
        .populate_existing()
        .first()
    )
    subject = (requester.preferences or {}).get("auth0_id") if requester else None
    email = (requester.email if requester else None) or claim.requester_email
    if requester is None or not requester.is_active or subject != peek_subject or email != peek_email:
        raise HTTPException(status_code=409, detail="This claim changed while approving. Try again.")

    if target is None or not target.is_active:
        raise HTTPException(
            status_code=409,
            detail=f"The original profile #{claim.target_profile_id} is no longer active. Dismiss this claim.",
        )
    if has_login(target):
        raise HTTPException(status_code=409, detail=f"Profile #{target.id} already has a login. Dismiss this claim.")
    if requester is None or not requester.is_active or not subject:
        raise HTTPException(
            status_code=409, detail="The requesting sign-in no longer has an active profile. Dismiss this claim."
        )

    conditions = [
        func.lower(PlayerProfile.legacy_name) == canonical.lower(),
        func.lower(PlayerProfile.name) == canonical.lower(),
        PlayerProfile.preferences["auth0_id"].as_string() == subject,
    ]
    conflict = (
        db.query(PlayerProfile)
        .filter(
            PlayerProfile.is_active == 1,
            PlayerProfile.id.notin_([target.id, requester.id]),
            or_(*conditions),
        )
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=(
                f"That roster name or login is already linked to profile #{conflict.id} "
                f"({conflict.legacy_name or conflict.name}). Resolve the conflict first. Nothing was changed."
            ),
        )

    release_identity_and_retire(requester)  # frees the email + login before the original takes them
    if (requester.name or "").lower() == canonical.lower():
        requester.name = f"retired-profile-{requester.id}"  # frees the unique name for the original
    db.flush()
    now = utc_now().isoformat()
    target.email = email
    target.preferences = {**(target.preferences or {}), "auth0_id": subject}
    target.legacy_name = claim.canonical_name
    target.name = claim.canonical_name
    target.updated_at = now
    claim.status = "approved"
    claim.resolved_at = now
    claim.resolved_by = admin.get("email")
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="That email or name already belongs to another profile. Resolve it in Account links, then try again.",
        ) from exc
    logger.info(
        "Claim %s approved by %s: profile %s -> %s", claim.id, admin.get("email"), claim.requester_profile_id, target.id
    )
    return _row(db, claim)


@router.post("/{claim_id}/dismiss")
def dismiss_claim(
    claim_id: int, admin: dict[str, Any] = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, Any]:
    claim = _pending(db, claim_id)
    claim.status = "dismissed"
    claim.resolved_at = utc_now().isoformat()
    claim.resolved_by = admin.get("email")
    db.commit()
    logger.info("Claim %s dismissed by %s", claim.id, admin.get("email"))
    return _row(db, claim)
