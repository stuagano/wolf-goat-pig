"""Shared-secret auth for scheduled jobs, and the admin-or-job route guard.

Cron callers (GitHub Actions, Cloud Scheduler) send ``X-Internal-Job-Token``
matching the ``INTERNAL_JOB_TOKEN`` env var. Routes that both a cron job and an
admin in the UI trigger use :func:`require_admin_or_job_token`.
"""

import os
from typing import Any

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import auth_service as auth_module
from .admin_auth import admin_role

_optional_bearer = HTTPBearer(auto_error=False)


def verify_job_token(supplied: str | None) -> None:
    """Authorize an internal-job request, or raise. Fail-closed when unset."""
    expected = os.getenv("INTERNAL_JOB_TOKEN")
    if not expected:
        # No token configured → job endpoints are disabled (safe default).
        raise HTTPException(status_code=503, detail="internal jobs disabled (INTERNAL_JOB_TOKEN unset)")
    if supplied != expected:
        raise HTTPException(status_code=403, detail="forbidden")


def require_job_token(x_internal_job_token: str | None = Header(default=None)) -> None:
    """Route dependency: only a caller holding the job token gets through."""
    verify_job_token(x_internal_job_token)


def require_admin_or_job_token(
    x_internal_job_token: str | None = Header(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Let through a cron caller with the job token, or a signed-in admin.

    A request that sends the job-token header is judged on the token alone, so a
    wrong token is a 403 even if a bearer token is also present.
    """
    if x_internal_job_token is not None:
        verify_job_token(x_internal_job_token)
        return {"job": True}
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    auth0_user = auth_module.get_current_auth0_user(credentials)
    if admin_role(db, auth0_user) == "normal":
        raise HTTPException(status_code=403, detail="Admin access required")
    return auth0_user
