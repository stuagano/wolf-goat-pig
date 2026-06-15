"""Contract tests for the ForeTees integration (Wing Point tee-time auth).

Mocks the multi-step login handshake at the httpx boundary and verifies
`ForeteesService._ensure_session()` drives its real success/failure branches.

The login flow (foretees_service._ensure_session) makes FOUR HTTP calls:
1. GET  https://www.wingpointgolf.com/public/member-login-465.html  (login page)
2. POST https://www.wingpointgolf.com/public/member-login-465.html  (credentials)
3. GET  https://www.wingpointgolf.com/members/golf/make-a-tee-time-703.html
        (tee page — must embed `ftSSOKey = '...'` and `ftSSOIV = '...'`)
4. GET  {base_url}/Member_select?sso_uid=...&sso_iv=...  (SSO → JSESSIONID)

Success requires both SSO markers in the tee page (single-quoted — the regex
is `ftSSOKey\\s*=\\s*'([^']+)'`); the JSESSIONID cookie check is best-effort and
returns True regardless. Every error branch (HTTPStatusError, RequestError,
bare Exception) is swallowed and returns `False` — never raises. Because we
cannot pin a raised exception type, we assert `route.called` to prove the
False came from the real error branch (not a client-construction failure that
never exercised the handler), mirroring the "specific type" guard the other
contract modules use.
"""

import httpx
import pytest
import respx

from app.services.foretees_service import (
    FORETEES_APP_BASE,
    ForeteesConfig,
    ForeteesService,
)

LOGIN_URL = "https://www.wingpointgolf.com/public/member-login-465.html"
TEE_PAGE_URL = "https://www.wingpointgolf.com/members/golf/make-a-tee-time-703.html"
SSO_URL_PREFIX = f"{FORETEES_APP_BASE}/Member_select"

# Tee page with both SSO markers — single quotes, both keys present, so the
# `if not sso_key_match or not sso_iv_match` guard passes and login succeeds.
TEE_PAGE_OK_HTML = (
    "<html><body><script>var ftSSOKey = 'sso-key-abc123'; var ftSSOIV = 'sso-iv-def456';</script></body></html>"
)

# Tee page WITHOUT the SSO markers — drives the bad-credentials failure branch
# ("Could not find ftSSOKey/ftSSOIV") which returns False.
TEE_PAGE_BAD_HTML = "<html><body><p>Invalid username or password.</p></body></html>"


def _config(enabled: bool = True) -> ForeteesConfig:
    return ForeteesConfig(
        enabled=enabled,
        username="u",
        password="p",
        base_url=FORETEES_APP_BASE,
        timeout_seconds=15.0,
    )


@pytest.mark.asyncio
@respx.mock
async def test_successful_login_establishes_session():
    respx.get(LOGIN_URL).mock(return_value=httpx.Response(200, text="<html>login</html>"))
    respx.post(LOGIN_URL).mock(return_value=httpx.Response(200, text="<html>ok</html>"))
    respx.get(TEE_PAGE_URL).mock(return_value=httpx.Response(200, text=TEE_PAGE_OK_HTML))
    respx.get(url__startswith=SSO_URL_PREFIX).mock(return_value=httpx.Response(200, text="<html>sso</html>"))

    service = ForeteesService(_config())
    try:
        ok = await service._ensure_session()
        assert ok is True
        assert service._session_valid() is True
    finally:
        await service.close()


@pytest.mark.asyncio
@respx.mock
async def test_failed_login_bad_credentials_returns_false():
    # Login page + POST succeed, but the tee page lacks the SSO markers, so the
    # handshake can't complete. No crash, returns False, session not valid.
    respx.get(LOGIN_URL).mock(return_value=httpx.Response(200, text="<html>login</html>"))
    respx.post(LOGIN_URL).mock(return_value=httpx.Response(200, text="<html>ok</html>"))
    tee_route = respx.get(TEE_PAGE_URL).mock(return_value=httpx.Response(200, text=TEE_PAGE_BAD_HTML))

    service = ForeteesService(_config())
    try:
        ok = await service._ensure_session()
        assert ok is False
        assert service._session_valid() is False
        # The boundary was hit — the False came from the missing-marker branch,
        # not from a client-construction failure that never ran the handler.
        assert tee_route.called is True
    finally:
        await service.close()


@pytest.mark.asyncio
@respx.mock
async def test_non_200_from_login_returns_false():
    # raise_for_status() on the login GET → HTTPStatusError → swallowed → False.
    login_route = respx.get(LOGIN_URL).mock(return_value=httpx.Response(500, text="boom"))

    service = ForeteesService(_config())
    try:
        ok = await service._ensure_session()
        assert ok is False
        assert service._session_valid() is False
        assert login_route.called is True
    finally:
        await service.close()


@pytest.mark.asyncio
@respx.mock
async def test_timeout_during_login_returns_false():
    # ConnectTimeout is an httpx.RequestError → swallowed → False.
    login_route = respx.get(LOGIN_URL).mock(side_effect=httpx.ConnectTimeout("timed out"))

    service = ForeteesService(_config())
    try:
        ok = await service._ensure_session()
        assert ok is False
        assert service._session_valid() is False
        assert login_route.called is True
    finally:
        await service.close()


@pytest.mark.asyncio
@respx.mock
async def test_disabled_config_short_circuits_without_http():
    # enabled=False: the guard at the top of _ensure_session returns False
    # before any HTTP call is made.
    login_route = respx.get(LOGIN_URL).mock(return_value=httpx.Response(200, text="<html>login</html>"))

    service = ForeteesService(_config(enabled=False))
    try:
        ok = await service._ensure_session()
        assert ok is False
        assert service._session_valid() is False
        # No HTTP boundary touched — the short-circuit fired first.
        assert login_route.called is False
    finally:
        await service.close()
