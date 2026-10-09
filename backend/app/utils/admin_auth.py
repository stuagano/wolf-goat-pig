"""Admin authorization dependencies for FastAPI routes.

A caller is an admin if their login email is on the ``SUPER_ADMIN_EMAILS`` env
allowlist, or if their linked player profile carries an in-app admin grant
(``player_profiles.is_admin``). Both kinds have the same powers.
"""

import os
from typing import Any, Literal

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PlayerProfile
from ..services.auth_service import get_current_auth0_user

_DEFAULT_SUPER_ADMIN_EMAILS = {"stuagano@gmail.com"}


def get_super_admin_emails() -> set[str]:
    """Return normalized super-admin login emails.

    ``ADMIN_EMAILS`` remains a temporary compatibility fallback for existing
    deployments. New environments should configure ``SUPER_ADMIN_EMAILS``.
    """
    env = os.getenv("SUPER_ADMIN_EMAILS") or os.getenv("ADMIN_EMAILS")
    if env:
        return {email.strip().casefold() for email in env.split(",") if email.strip()}
    return _DEFAULT_SUPER_ADMIN_EMAILS


def get_admin_emails() -> set[str]:
    """Compatibility alias for notification recipients."""
    return get_super_admin_emails()


def is_super_admin_email(email: str | None) -> bool:
    """Return whether a verified login email has super-admin access."""
    email = (email or "").strip().casefold()
    return bool(email and email in get_super_admin_emails())


def is_profile_admin(db: Session, auth0_sub: str | None) -> bool:
    """True only for exactly one active, flagged profile linked to this Auth0 subject."""
    if not auth0_sub:
        return False
    matches = (
        db.query(PlayerProfile).filter(PlayerProfile.preferences["auth0_id"].as_string() == auth0_sub).limit(2).all()
    )
    return len(matches) == 1 and bool(matches[0].is_active) and bool(matches[0].admin_granted)


def admin_role(db: Session, auth0_user: dict[str, Any]) -> Literal["super_admin", "admin", "normal"]:
    """Env allowlist first (no DB hit), then the stored profile flag."""
    if is_super_admin_email(auth0_user.get("email")):
        return "super_admin"
    if is_profile_admin(db, auth0_user.get("sub")):
        return "admin"
    return "normal"


def is_admin_profile(profile: Any) -> bool:
    """Admin check for an already-resolved signed-in profile (from ``get_current_user``).

    Same rules as ``admin_role``: the env allowlist by the profile's email, or an
    in-app grant on this (active) profile. Use when a route resolves the player
    profile rather than raw token claims.
    """
    return is_super_admin_email(getattr(profile, "email", None)) or bool(
        getattr(profile, "admin_granted", 0) and getattr(profile, "is_active", 1)
    )


def require_admin(
    auth0_user: dict[str, Any] = Depends(get_current_auth0_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Require an env-allowlisted email or an in-app admin grant."""
    if admin_role(db, auth0_user) == "normal":
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth0_user


# Compatibility name; dependency overrides keyed on either name hit the same object.
require_super_admin = require_admin
