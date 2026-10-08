"""Super-admin authorization dependencies for FastAPI routes."""

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
    return len(matches) == 1 and bool(matches[0].is_active) and bool(matches[0].is_admin)


def admin_role(db: Session, auth0_user: dict[str, Any]) -> Literal["super_admin", "admin", "normal"]:
    """Env allowlist first (no DB hit), then the stored profile flag."""
    if is_super_admin_email(auth0_user.get("email")):
        return "super_admin"
    if is_profile_admin(db, auth0_user.get("sub")):
        return "admin"
    return "normal"


def require_admin(
    auth0_user: dict[str, Any] = Depends(get_current_auth0_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Require an env-allowlisted email or an in-app admin grant."""
    if admin_role(db, auth0_user) == "normal":
        raise HTTPException(status_code=403, detail="Super-admin access required")
    return auth0_user


# Compatibility name; dependency overrides keyed on either name hit the same object.
require_super_admin = require_admin
