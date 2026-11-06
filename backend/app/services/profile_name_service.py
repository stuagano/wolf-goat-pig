"""A golfer's display name when Auth0 only gave us their email.

Auth0 database logins set the ``name`` claim to the email address, so a new
golfer's profile (and their pending sign-up row) would otherwise be named
with an email. Onboarding asks those golfers for their real name once.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ..models import PendingLegacyPlayer, PlayerProfile
from ..utils.time import utc_now

MAX_NAME_PART = 50


def display_name_from_claims(auth0_user: dict[str, Any], email: str | None) -> str:
    """Best display name from Auth0 claims, avoiding the login email.

    Prefer a real ``name``, then ``given_name`` + ``family_name``. An email
    ``name`` is kept as-is so onboarding knows to ask for the golfer's name;
    with no name claim at all, the email's local part is used (as before).
    """
    name = str(auth0_user.get("name") or "").strip()
    if name and "@" not in name:
        return name
    parts = [str(auth0_user.get(key) or "").strip() for key in ("given_name", "family_name")]
    full = " ".join(part for part in parts if part)
    if full and "@" not in full:
        return full
    return name or (email.split("@")[0] if email else "") or "Unknown Player"


def needs_real_name(profile: PlayerProfile) -> bool:
    return "@" in str(profile.name or "") or not str(profile.name or "").strip()


def _clean_part(value: Any, label: str) -> str:
    part = re.sub(r"\s+", " ", str(value or "")).strip()
    if not part:
        raise HTTPException(status_code=400, detail=f"Enter your {label}.")
    if "@" in part:
        raise HTTPException(status_code=400, detail=f"Your {label} can't be an email address.")
    if len(part) > MAX_NAME_PART:
        raise HTTPException(status_code=400, detail=f"Your {label} must be {MAX_NAME_PART} characters or fewer.")
    return part


def set_own_name(db: Any, profile: PlayerProfile, first_name: Any, last_name: Any) -> PlayerProfile:
    """Replace an email-as-name with the golfer's real name. Commits.

    Only allowed while the profile is still named with an email; after that an
    admin changes names. Pending sign-up rows still named with the email are
    renamed too, so admins see the real name when promoting.
    """
    if not needs_real_name(profile):
        raise HTTPException(status_code=409, detail="Your name is already set. Ask a club admin to change it.")
    name = f"{_clean_part(first_name, 'first name')} {_clean_part(last_name, 'last name')}"
    taken = (
        db.query(PlayerProfile.id)
        .filter(func.lower(PlayerProfile.name) == name.lower(), PlayerProfile.id != profile.id)
        .first()
    )
    if taken:
        raise HTTPException(
            status_code=409,
            detail=f"A player named '{name}' already exists. If that's you, use Find my player history instead.",
        )

    profile.name = name
    profile.updated_at = utc_now().isoformat()
    pending = (
        db.query(PendingLegacyPlayer)
        .filter(PendingLegacyPlayer.player_profile_id == profile.id, PendingLegacyPlayer.status == "pending")
        .all()
    )
    for row in pending:
        if "@" in str(row.name or ""):
            row.name = name
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"A player named '{name}' already exists.") from exc
    db.refresh(profile)
    return profile
