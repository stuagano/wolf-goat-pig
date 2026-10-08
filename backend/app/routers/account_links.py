"""Explicit, admin-only links between existing player profiles and login identities."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, or_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PlayerProfile
from ..services.legacy_player_service import get_canonical_name, link_profile_to_canonical_name
from ..utils.admin_auth import require_admin
from ..utils.time import utc_now

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["players"])


class AccountLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    player_id: int = Field(..., gt=0)
    legacy_name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    auth0_id: str | None = Field(None, max_length=255, pattern=r"^[^\s|]+\|[^\s|]+$")
    expected_updated_at: str | None

    @field_validator("legacy_name", "email", "auth0_id", mode="before")
    @classmethod
    def normalize(cls, value, info):
        if isinstance(value, str):
            value = value.strip()
            if info.field_name == "email":
                value = value.lower()
            if info.field_name == "auth0_id" and not value:
                return None
        return value


def _link_details(player: PlayerProfile) -> dict[str, Any]:
    return {
        "id": player.id,
        "name": player.name,
        "legacy_name": player.legacy_name,
        "email": player.email,
        "auth0_id": (player.preferences or {}).get("auth0_id"),
        "updated_at": player.updated_at,
    }


@router.get("/account-links", dependencies=[Depends(require_admin)])
def search_account_links(
    query: str = Query(..., min_length=2, max_length=100),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Search a bounded set of existing profiles by literal name or email."""
    term = query.strip().lower()
    if len(term) < 2:
        raise HTTPException(status_code=422, detail="Enter at least two characters")
    players = (
        db.query(PlayerProfile)
        .filter(
            PlayerProfile.is_active == 1,
            or_(
                func.lower(PlayerProfile.name).contains(term, autoescape=True),
                func.lower(PlayerProfile.legacy_name).contains(term, autoescape=True),
                func.lower(PlayerProfile.email).contains(term, autoescape=True),
            ),
        )
        .order_by(PlayerProfile.id)
        .limit(51)
        .all()
    )
    return {"players": [_link_details(player) for player in players[:50]], "has_more": len(players) > 50}


@router.post("/relink-auth0")
def relink_auth0_account(
    body: AccountLinkRequest,
    admin: dict[str, Any] = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Link a selected existing profile; never merge, delete, or steal another identity."""
    canonical = get_canonical_name(body.legacy_name, db)
    if not canonical:
        raise HTTPException(status_code=400, detail="Choose an existing roster player")

    # Serialize competing admin claims, including identities that have no row yet.
    # Sorted transaction-scoped locks avoid cross-link deadlocks on PostgreSQL.
    if db.get_bind().dialect.name == "postgresql":
        identities = [f"roster:{canonical.lower()}", f"email:{body.email}"]
        if body.auth0_id:
            identities.append(f"auth0:{body.auth0_id}")
        for identity in sorted(identities):
            db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:identity))"), {"identity": f"account-link:{identity}"}
            )

    player = db.query(PlayerProfile).filter(PlayerProfile.id == body.player_id).with_for_update().first()
    if not player:
        raise HTTPException(status_code=404, detail="Player profile not found")
    if player.updated_at != body.expected_updated_at:
        raise HTTPException(
            status_code=409, detail="This profile changed since you selected it. Search again before saving."
        )

    conditions = [
        func.lower(PlayerProfile.legacy_name) == canonical.lower(),
        func.lower(PlayerProfile.name) == canonical.lower(),
        func.lower(PlayerProfile.email) == body.email,
    ]
    effective_auth0 = body.auth0_id or (player.preferences or {}).get("auth0_id")
    if effective_auth0:
        conditions.append(PlayerProfile.preferences["auth0_id"].as_string() == effective_auth0)
    conflict = db.query(PlayerProfile).filter(PlayerProfile.id != player.id, or_(*conditions)).first()
    if conflict:
        raise HTTPException(
            status_code=409,
            detail=(
                f"That roster name, email, or Auth0 ID is already linked to profile #{conflict.id} "
                f"({conflict.legacy_name or conflict.name}). Select that profile or resolve the conflict first. No links were changed."
            ),
        )

    result = link_profile_to_canonical_name(db, player.id, canonical, allow_relink=True)
    if not result["linked"]:
        raise HTTPException(status_code=409, detail="This roster player is already linked to another profile")
    player.name = canonical
    player.email = body.email
    if body.auth0_id:
        player.preferences = {**(player.preferences or {}), "auth0_id": body.auth0_id}
    player.updated_at = utc_now().isoformat()
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="An account link changed while saving. Search again; no links were changed."
        ) from exc
    db.refresh(player)
    logger.info("Admin %s updated account link for profile id=%s, roster=%s", admin.get("sub"), player.id, canonical)
    return _link_details(player)
