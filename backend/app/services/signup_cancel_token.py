"""Signed links that let the person who signed up cancel that signup.

The confirmation email is the only place the token is handed out. A signup id
on its own is not a credential: the token is an HMAC over the signup, the
player, the date, and an expiry. Mail scanners that prefetch the link must
not cancel anything; this module only checks the token.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from ..utils.time import CLUB_TZ

_MAX_TOKEN_LENGTH = 512
_DEV_SECRET = "dev-signup-cancel-secret"
_DEFAULT_FRONTEND = "https://seventh-country-232522.web.app"


class CancelTokenError(Exception):
    """A cancel link is missing, forged, or past its expiry."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class CancelTokenClaims:
    signup_id: int
    player_profile_id: int
    signup_date: str
    expires_at: int


def signing_secret() -> bytes:
    """Key for cancel links. Production refuses to sign with a known default."""
    raw = (
        os.getenv("SIGNUP_CANCEL_SECRET") or os.getenv("FORETEES_ENCRYPTION_KEY") or os.getenv("JWT_SECRET_KEY") or ""
    ).strip()
    if not raw:
        if os.getenv("ENVIRONMENT", "").lower() == "production":
            raise RuntimeError(
                "SIGNUP_CANCEL_SECRET is not set. FORETEES_ENCRYPTION_KEY or JWT_SECRET_KEY is also accepted."
            )
        raw = _DEV_SECRET
    return raw.encode()


def issue_cancel_token(
    *,
    signup_id: int,
    player_profile_id: int,
    signup_date: str,
    now: datetime | None = None,
) -> str:
    """Build a URL-safe token for one signup. Valid through the day after the game."""
    if int(signup_id) < 1 or int(player_profile_id) < 1 or not signup_date:
        raise ValueError("signup id, player id, and date are required")
    moment = _as_utc(now)
    payload = {
        "v": 1,
        "sid": int(signup_id),
        "pid": int(player_profile_id),
        "date": signup_date,
        "exp": _expiry(signup_date, moment),
    }
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    signature = hmac.new(signing_secret(), body, hashlib.sha256).digest()
    return f"{_b64encode(body)}.{_b64encode(signature)}"


def read_cancel_token(token: str, *, now: datetime | None = None) -> CancelTokenClaims:
    """Return the signed claims, or raise CancelTokenError."""
    if not isinstance(token, str) or not token or len(token) > _MAX_TOKEN_LENGTH or token.count(".") != 1:
        raise CancelTokenError("invalid")
    body_b64, signature_b64 = token.split(".", 1)
    try:
        body = _b64decode(body_b64)
        signature = _b64decode(signature_b64)
        expected = hmac.new(signing_secret(), body, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise CancelTokenError("invalid")
        payload = json.loads(body)
        if payload.get("v") != 1:
            raise CancelTokenError("invalid")
        claims = CancelTokenClaims(
            signup_id=int(payload["sid"]),
            player_profile_id=int(payload["pid"]),
            signup_date=str(payload["date"]),
            expires_at=int(payload["exp"]),
        )
    except CancelTokenError:
        raise
    except Exception:
        raise CancelTokenError("invalid") from None
    if claims.signup_id < 1 or claims.player_profile_id < 1 or not claims.signup_date:
        raise CancelTokenError("invalid")
    if claims.expires_at <= int(_as_utc(now).timestamp()):
        raise CancelTokenError("expired")
    return claims


def cancel_signup_url(token: str) -> str:
    """Public page that previews the signup and asks before cancelling."""
    base = os.getenv("FRONTEND_URL", _DEFAULT_FRONTEND).strip().rstrip("/")
    return f"{base}/signup/cancel/{token}"


def _expiry(signup_date: str, now: datetime) -> int:
    """Unix time when the link dies: midnight Pacific, two days after the game date."""
    try:
        start = datetime.strptime(signup_date, "%Y-%m-%d").replace(tzinfo=CLUB_TZ)
    except ValueError:
        start = now.astimezone(CLUB_TZ)
    return int((start + timedelta(days=2)).timestamp())


def _as_utc(moment: datetime | None) -> datetime:
    if moment is None:
        return datetime.now(UTC)
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)
