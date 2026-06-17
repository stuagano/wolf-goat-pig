"""Admin authentication dependency for FastAPI routes."""

import os

from fastapi import Header, HTTPException

# Fallback to hardcoded set if env var not set, but prefer env var for flexibility
_DEFAULT_ADMIN_EMAILS = {"stuagano@gmail.com", "admin@wgp.com"}


def get_admin_emails() -> set[str]:
    """Return the set of allowed admin emails (env-configured or default)."""
    env = os.getenv("ADMIN_EMAILS")
    if env:
        return {e.strip() for e in env.split(",") if e.strip()}
    return _DEFAULT_ADMIN_EMAILS


# Backwards-compatible private alias for existing internal callers.
_get_admin_emails = get_admin_emails


def require_admin(x_admin_email: str | None = Header(None)) -> None:
    """FastAPI dependency that restricts access to admin email addresses.

    Callers pass the email in the X-Admin-Email request header.
    Configure allowed emails via the ADMIN_EMAILS env var (comma-separated)
    or fall back to the hardcoded default set.
    """
    if not x_admin_email or x_admin_email not in _get_admin_emails():
        raise HTTPException(status_code=403, detail="Admin access required")
