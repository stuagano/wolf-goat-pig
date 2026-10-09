"""Admin: approve or dismiss returning players' claims on their original profile."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
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


def _pending(db: Session, claim_id: int) -> AccountClaim:
    claim = db.query(AccountClaim).filter(AccountClaim.id == claim_id).with_for_update().first()
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


@router.post("/{claim_id}/approve")
def approve_claim(
    claim_id: int, admin: dict[str, Any] = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Move the requester's login onto the original profile and retire the stray, atomically."""
    claim = _pending(db, claim_id)
    requester = db.query(PlayerProfile).filter(PlayerProfile.id == claim.requester_profile_id).with_for_update().first()
    target = db.query(PlayerProfile).filter(PlayerProfile.id == claim.target_profile_id).with_for_update().first()
    subject = (requester.preferences or {}).get("auth0_id") if requester else None
    email = (requester.email if requester else None) or claim.requester_email

    # Same identity locks as relink-auth0, so a concurrent relink can't interleave.
    if db.get_bind().dialect.name == "postgresql":
        identities = [f"roster:{claim.canonical_name.lower()}"] + [
            value for value in (f"auth0:{subject}" if subject else None, f"email:{email}" if email else None) if value
        ]
        for identity in sorted(identities):
            db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:identity))"), {"identity": f"account-link:{identity}"}
            )

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

    release_identity_and_retire(requester)  # frees the email + login before the original takes them
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
