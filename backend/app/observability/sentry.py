"""Sentry initialization for the backend.

No-op unless SENTRY_DSN is set, so local/CI/test runs never touch Sentry and
no data leaves the process. Errors-only (no performance tracing); PII is not
sent and auth/secret fields are scrubbed before send.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import sentry_sdk

logger = logging.getLogger(__name__)

_SECRET_KEY_HINTS = ("authorization", "api_key", "apikey", "token", "password", "secret")

# Set by init_sentry() so diagnostics can explain a failed init (e.g. a malformed
# DSN) without crashing the app. None means "no init error this run".
last_init_error: str | None = None


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: ("[scrubbed]" if any(h in k.lower() for h in _SECRET_KEY_HINTS) else _redact(v)) for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj


def _scrub(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """before_send hook: strip auth headers and redact secret-ish fields."""
    request = event.get("request")
    if isinstance(request, dict):
        headers = request.get("headers")
        if isinstance(headers, dict):
            for key in list(headers):
                if key.lower() in ("authorization", "cookie"):
                    headers[key] = "[scrubbed]"
    if "extra" in event:
        event["extra"] = _redact(event["extra"])
    return event


def init_sentry() -> bool:
    """Initialize Sentry iff SENTRY_DSN is configured. Returns True if initialized.

    sentry-sdk[fastapi] auto-enables the FastAPI/Starlette integration, so every
    route's unhandled exceptions and 500s are captured once this runs.
    """
    global last_init_error
    last_init_error = None
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return False
    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("ENVIRONMENT", "development"),
            release=os.getenv("RENDER_GIT_COMMIT") or os.getenv("GIT_SHA") or None,
            send_default_pii=False,
            traces_sample_rate=0.0,
            before_send=_scrub,
        )
        return True
    except Exception as e:  # a bad DSN must not crash app startup
        last_init_error = f"{type(e).__name__}: {e}"
        logger.error("Sentry init failed: %s", last_init_error)
        return False
