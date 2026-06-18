"""Read-only health probes for the external services WGP depends on.

Each checker reaches its service with a minimal read-only request and returns a
ServiceStatus. A service with no credentials configured returns "not_configured"
(NOT a failure — must never alert). Used by GET /health/external.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Literal

import httpx

Status = Literal["ok", "down", "not_configured"]
_TIMEOUT = 8.0


@dataclass
class ServiceStatus:
    name: str
    status: Status
    latency_ms: int | None = None
    detail: str = ""


def _missing(*names: str) -> bool:
    return any(not os.environ.get(n) for n in names)


async def _timed(name: str, coro) -> ServiceStatus:
    """Run a probe coroutine, mapping success/exception to ServiceStatus."""
    start = time.monotonic()
    try:
        detail = await coro
        return ServiceStatus(name, "ok", int((time.monotonic() - start) * 1000), detail or "ok")
    except Exception as e:  # any failure (HTTP error, timeout, parse) means the dep is down
        return ServiceStatus(name, "down", int((time.monotonic() - start) * 1000), f"{type(e).__name__}: {e}")


async def check_groq() -> ServiceStatus:
    if _missing("GROQ_API_KEY"):
        return ServiceStatus("groq", "not_configured")

    async def probe() -> str:
        model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
                json={"model": model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1},
            )
            resp.raise_for_status()
            return f"HTTP {resp.status_code}"

    return await _timed("groq", probe())


async def check_auth0() -> ServiceStatus:
    if _missing("AUTH0_DOMAIN"):
        return ServiceStatus("auth0", "not_configured")

    async def probe() -> str:
        url = f"https://{os.environ['AUTH0_DOMAIN']}/.well-known/jwks.json"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            keys = resp.json().get("keys") or []
            if not keys:
                raise ValueError("JWKS returned no signing keys")
            return f"{len(keys)} signing key(s)"

    return await _timed("auth0", probe())


async def check_resend() -> ServiceStatus:
    if _missing("RESEND_API_KEY"):
        return ServiceStatus("resend", "not_configured")

    async def probe() -> str:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                "https://api.resend.com/domains",
                headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
            )
            # A send-scoped key (least-privilege, the common case) returns 401/403
            # on /domains even though it can send email — that is NOT an outage.
            # We can't read-only validate a send key without sending, so treat
            # auth-rejection as "reachable + key set" and only flag real outages
            # (5xx / timeout / connection error) as down.
            if resp.status_code in (401, 403):
                return "reachable; key set (send-scoped — not read-only verifiable)"
            resp.raise_for_status()
            return f"HTTP {resp.status_code}"

    return await _timed("resend", probe())


async def check_tee_sheet() -> ServiceStatus:
    # Public page, no creds required — always "configured".
    async def probe() -> str:
        # Probe the exact endpoint the app reads (the bare base path 301-redirects),
        # following redirects, with the same Referer the real request sends.
        from app.routers.tee_sheet import TEE_SHEET_READ_URL

        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(TEE_SHEET_READ_URL, headers={"Referer": TEE_SHEET_READ_URL})
            resp.raise_for_status()
            return f"HTTP {resp.status_code}"

    return await _timed("tee_sheet", probe())


async def check_groupme() -> ServiceStatus:
    if _missing("GROUPME_ACCESS_TOKEN", "GROUPME_GROUP_ID"):
        return ServiceStatus("groupme", "not_configured")

    async def probe() -> str:
        token = os.environ["GROUPME_ACCESS_TOKEN"]
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"https://api.groupme.com/v3/groups?token={token}")
            resp.raise_for_status()
            return f"HTTP {resp.status_code}"

    return await _timed("groupme", probe())


async def check_ghin() -> ServiceStatus:
    if _missing("GHIN_API_USER", "GHIN_API_PASS"):
        return ServiceStatus("ghin", "not_configured")

    async def probe() -> str:
        # Mirrors GHINService.initialize(): POST golfer_login.json with the
        # email_or_ghin/password user block, source "GHINcom", and a static
        # token (default "ghincom"). Read-only login handshake — no scores
        # posted, no state mutated.
        static_token = os.environ.get("GHIN_API_STATIC_TOKEN") or "ghincom"
        payload = {
            "user": {
                "email_or_ghin": os.environ["GHIN_API_USER"],
                "password": os.environ["GHIN_API_PASS"],
            },
            "source": "GHINcom",
            "token": static_token,
        }
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://www.ghin.com",
            "Referer": "https://www.ghin.com/",
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                "https://api2.ghin.com/api/v1/golfer_login.json",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            if not resp.json().get("golfer_user", {}).get("golfer_user_token"):
                raise ValueError("GHIN login returned no token")
            return "authenticated"

    return await _timed("ghin", probe())


async def check_foretees() -> ServiceStatus:
    if _missing("FORETEES_USERNAME", "FORETEES_PASSWORD"):
        return ServiceStatus("foretees", "not_configured")

    async def probe() -> str:
        from app.services.foretees_service import ForeteesConfig, ForeteesService

        # Build an explicitly-enabled config (mirrors create_user_foretees_service)
        # rather than ForeteesConfig.from_env(): from_env() couples reachability to
        # the FORETEES_ENABLED feature flag, so a creds-present-but-flag-off service
        # would falsely report "down". Keying the probe off the same creds the
        # not_configured gate uses keeps probe semantics consistent with the gate.
        # Tradeoff: if creds are set AND the flag is disabled, this reports "down" —
        # acceptable, since creds present means the operator intends it reachable.
        config = ForeteesConfig(
            enabled=True,
            username=os.environ["FORETEES_USERNAME"],
            password=os.environ["FORETEES_PASSWORD"],
        )
        service = ForeteesService(config)
        try:
            ok = await service._ensure_session()
        finally:
            await service.close()
        if not ok:
            raise ValueError("ForeTees login handshake failed")
        return "session established"

    return await _timed("foretees", probe())


async def check_google() -> ServiceStatus:
    if _missing("GOOGLE_OAUTH_CREDENTIALS", "LIVE_TEST_SHEET_ID"):
        return ServiceStatus("google", "not_configured")

    async def probe() -> str:
        from app.services import spreadsheet_sync_service

        sheet_id = os.environ["LIVE_TEST_SHEET_ID"]
        data = await asyncio.to_thread(spreadsheet_sync_service._sheets_api_get, sheet_id, "A1:A1")
        if not data:
            raise ValueError("Google Sheets read returned no data")
        return "sheet readable"

    return await _timed("google", probe())


async def check_all() -> list[ServiceStatus]:
    """Run all external checks concurrently and return their statuses."""
    return await asyncio.gather(
        check_groq(),
        check_auth0(),
        check_google(),
        check_ghin(),
        check_groupme(),
        check_foretees(),
        check_resend(),
        check_tee_sheet(),
    )
