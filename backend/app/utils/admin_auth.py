"""Super-admin authorization dependencies for FastAPI routes."""

import os
from typing import Any

from fastapi import Depends, HTTPException

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


def require_super_admin(
    auth0_user: dict[str, Any] = Depends(get_current_auth0_user),
) -> dict[str, Any]:
    """Require verified Auth0 claims whose login email is allowlisted."""
    if not is_super_admin_email(auth0_user.get("email")):
        raise HTTPException(status_code=403, detail="Super-admin access required")
    return auth0_user


# Compatibility name used by existing route declarations.
require_admin = require_super_admin
