"""Unit tests for external_checks: each checker maps good/error/absent to
ok/down/not_configured. All HTTP mocked — no real network."""

import httpx
import pytest
import respx

from app.observability import external_checks as ec


@pytest.fixture(autouse=True)
def _no_proxy(monkeypatch):
    for v in ("ALL_PROXY", "all_proxy", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"):
        monkeypatch.delenv(v, raising=False)


# --------------------------------------------------------------------------
# groq
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_groq_not_configured(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    s = await ec.check_groq()
    assert s.status == "not_configured"


@pytest.mark.asyncio
@respx.mock
async def test_groq_ok(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "x"}}]})
    )
    s = await ec.check_groq()
    assert s.status == "ok"
    assert s.latency_ms is not None


@pytest.mark.asyncio
@respx.mock
async def test_groq_down_on_error(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "k")
    respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(500, json={"error": "boom"})
    )
    s = await ec.check_groq()
    assert s.status == "down"


# --------------------------------------------------------------------------
# auth0
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_auth0_not_configured(monkeypatch):
    monkeypatch.delenv("AUTH0_DOMAIN", raising=False)
    s = await ec.check_auth0()
    assert s.status == "not_configured"


@pytest.mark.asyncio
@respx.mock
async def test_auth0_ok(monkeypatch):
    monkeypatch.setenv("AUTH0_DOMAIN", "x.auth0.com")
    respx.get("https://x.auth0.com/.well-known/jwks.json").mock(
        return_value=httpx.Response(200, json={"keys": [{"kid": "test", "kty": "RSA"}]})
    )
    s = await ec.check_auth0()
    assert s.status == "ok"
    assert "1 signing key" in s.detail


@pytest.mark.asyncio
@respx.mock
async def test_auth0_down_when_no_keys(monkeypatch):
    monkeypatch.setenv("AUTH0_DOMAIN", "x.auth0.com")
    respx.get("https://x.auth0.com/.well-known/jwks.json").mock(return_value=httpx.Response(200, json={"keys": []}))
    s = await ec.check_auth0()
    assert s.status == "down"


@pytest.mark.asyncio
@respx.mock
async def test_auth0_down_on_http_error(monkeypatch):
    monkeypatch.setenv("AUTH0_DOMAIN", "x.auth0.com")
    respx.get("https://x.auth0.com/.well-known/jwks.json").mock(return_value=httpx.Response(500))
    s = await ec.check_auth0()
    assert s.status == "down"


# --------------------------------------------------------------------------
# resend
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_resend_not_configured(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    s = await ec.check_resend()
    assert s.status == "not_configured"


@pytest.mark.asyncio
@respx.mock
async def test_resend_ok(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "k")
    respx.get("https://api.resend.com/domains").mock(return_value=httpx.Response(200, json={"data": []}))
    s = await ec.check_resend()
    assert s.status == "ok"


@pytest.mark.asyncio
@respx.mock
async def test_resend_401_is_ok_send_scoped(monkeypatch):
    # A send-scoped key 401s on /domains but can still send — treat as ok, not down.
    monkeypatch.setenv("RESEND_API_KEY", "k")
    respx.get("https://api.resend.com/domains").mock(return_value=httpx.Response(401, json={"error": "restricted"}))
    s = await ec.check_resend()
    assert s.status == "ok"
    assert "send-scoped" in s.detail


@pytest.mark.asyncio
@respx.mock
async def test_resend_down_on_500(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "k")
    respx.get("https://api.resend.com/domains").mock(return_value=httpx.Response(500, json={"error": "boom"}))
    s = await ec.check_resend()
    assert s.status == "down"


# --------------------------------------------------------------------------
# groupme
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_groupme_not_configured(monkeypatch):
    monkeypatch.delenv("GROUPME_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GROUPME_GROUP_ID", raising=False)
    s = await ec.check_groupme()
    assert s.status == "not_configured"


@pytest.mark.asyncio
@respx.mock
async def test_groupme_ok(monkeypatch):
    monkeypatch.setenv("GROUPME_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("GROUPME_GROUP_ID", "123")
    respx.get(url__startswith="https://api.groupme.com/v3/groups").mock(
        return_value=httpx.Response(200, json={"response": [], "meta": {"code": 200}})
    )
    s = await ec.check_groupme()
    assert s.status == "ok"


@pytest.mark.asyncio
@respx.mock
async def test_groupme_down_on_401(monkeypatch):
    monkeypatch.setenv("GROUPME_ACCESS_TOKEN", "tok")
    monkeypatch.setenv("GROUPME_GROUP_ID", "123")
    respx.get(url__startswith="https://api.groupme.com/v3/groups").mock(return_value=httpx.Response(401))
    s = await ec.check_groupme()
    assert s.status == "down"


# --------------------------------------------------------------------------
# ghin
# --------------------------------------------------------------------------
GHIN_LOGIN_URL = "https://api2.ghin.com/api/v1/golfer_login.json"


@pytest.mark.asyncio
async def test_ghin_not_configured(monkeypatch):
    monkeypatch.delenv("GHIN_API_USER", raising=False)
    monkeypatch.delenv("GHIN_API_PASS", raising=False)
    s = await ec.check_ghin()
    assert s.status == "not_configured"


@pytest.mark.asyncio
@respx.mock
async def test_ghin_ok(monkeypatch):
    monkeypatch.setenv("GHIN_API_USER", "golfer@example.com")
    monkeypatch.setenv("GHIN_API_PASS", "secret")
    respx.post(GHIN_LOGIN_URL).mock(
        return_value=httpx.Response(200, json={"golfer_user": {"golfer_user_token": "tok-abc"}})
    )
    s = await ec.check_ghin()
    assert s.status == "ok"
    assert s.detail == "authenticated"


@pytest.mark.asyncio
@respx.mock
async def test_ghin_down_when_no_token(monkeypatch):
    monkeypatch.setenv("GHIN_API_USER", "golfer@example.com")
    monkeypatch.setenv("GHIN_API_PASS", "secret")
    respx.post(GHIN_LOGIN_URL).mock(return_value=httpx.Response(200, json={"golfer_user": {}}))
    s = await ec.check_ghin()
    assert s.status == "down"


@pytest.mark.asyncio
@respx.mock
async def test_ghin_down_on_401(monkeypatch):
    monkeypatch.setenv("GHIN_API_USER", "golfer@example.com")
    monkeypatch.setenv("GHIN_API_PASS", "wrong")
    respx.post(GHIN_LOGIN_URL).mock(return_value=httpx.Response(401, json={"error": "invalid"}))
    s = await ec.check_ghin()
    assert s.status == "down"


# --------------------------------------------------------------------------
# foretees
# --------------------------------------------------------------------------
FT_LOGIN_URL = "https://www.wingpointgolf.com/public/member-login-465.html"
FT_TEE_PAGE_URL = "https://www.wingpointgolf.com/members/golf/make-a-tee-time-703.html"
FT_SSO_PREFIX = "https://ftapp.wingpointgolf.com/v5/wingpointgcc_flxrez0_m30/Member_select"
FT_TEE_PAGE_OK = "<html><body><script>var ftSSOKey = 'sso-key-abc'; var ftSSOIV = 'sso-iv-def';</script></body></html>"
FT_TEE_PAGE_BAD = "<html><body><p>Invalid username or password.</p></body></html>"


@pytest.mark.asyncio
async def test_foretees_not_configured(monkeypatch):
    monkeypatch.delenv("FORETEES_USERNAME", raising=False)
    monkeypatch.delenv("FORETEES_PASSWORD", raising=False)
    s = await ec.check_foretees()
    assert s.status == "not_configured"


@pytest.mark.asyncio
@respx.mock
async def test_foretees_ok(monkeypatch):
    monkeypatch.setenv("FORETEES_USERNAME", "u")
    monkeypatch.setenv("FORETEES_PASSWORD", "p")
    respx.get(FT_LOGIN_URL).mock(return_value=httpx.Response(200, text="<html>login</html>"))
    respx.post(FT_LOGIN_URL).mock(return_value=httpx.Response(200, text="<html>ok</html>"))
    respx.get(FT_TEE_PAGE_URL).mock(return_value=httpx.Response(200, text=FT_TEE_PAGE_OK))
    respx.get(url__startswith=FT_SSO_PREFIX).mock(return_value=httpx.Response(200, text="<html>sso</html>"))
    s = await ec.check_foretees()
    assert s.status == "ok"
    assert s.detail == "session established"


@pytest.mark.asyncio
@respx.mock
async def test_foretees_down_on_bad_login(monkeypatch):
    # Login succeeds but the tee page lacks SSO markers → handshake fails → down.
    monkeypatch.setenv("FORETEES_USERNAME", "u")
    monkeypatch.setenv("FORETEES_PASSWORD", "p")
    respx.get(FT_LOGIN_URL).mock(return_value=httpx.Response(200, text="<html>login</html>"))
    respx.post(FT_LOGIN_URL).mock(return_value=httpx.Response(200, text="<html>ok</html>"))
    respx.get(FT_TEE_PAGE_URL).mock(return_value=httpx.Response(200, text=FT_TEE_PAGE_BAD))
    s = await ec.check_foretees()
    assert s.status == "down"


# --------------------------------------------------------------------------
# google (urllib seam — patched at _sheets_api_get)
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_google_not_configured(monkeypatch):
    monkeypatch.delenv("GOOGLE_OAUTH_CREDENTIALS", raising=False)
    monkeypatch.delenv("LIVE_TEST_SHEET_ID", raising=False)
    s = await ec.check_google()
    assert s.status == "not_configured"


@pytest.mark.asyncio
async def test_google_ok(monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CREDENTIALS", "{}")
    monkeypatch.setenv("LIVE_TEST_SHEET_ID", "sheet-id")
    from app.services import spreadsheet_sync_service

    monkeypatch.setattr(
        spreadsheet_sync_service,
        "_sheets_api_get",
        lambda sheet_id, range_spec: {"values": [["x"]]},
    )
    s = await ec.check_google()
    assert s.status == "ok"
    assert s.detail == "sheet readable"


@pytest.mark.asyncio
async def test_google_down_when_no_data(monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CREDENTIALS", "{}")
    monkeypatch.setenv("LIVE_TEST_SHEET_ID", "sheet-id")
    from app.services import spreadsheet_sync_service

    # _sheets_api_get returns None on any failure (bad token, HTTP error, etc.).
    monkeypatch.setattr(
        spreadsheet_sync_service,
        "_sheets_api_get",
        lambda sheet_id, range_spec: None,
    )
    s = await ec.check_google()
    assert s.status == "down"


# --------------------------------------------------------------------------
# tee_sheet (no not_configured case — always configured)
# --------------------------------------------------------------------------
# The probe reads the real .cgi endpoint (the bare base path 301-redirects).
TEE_SHEET_URL = "https://thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi"


@pytest.mark.asyncio
@respx.mock
async def test_tee_sheet_ok():
    respx.get(TEE_SHEET_URL).mock(return_value=httpx.Response(200, text="<html>ok</html>"))
    s = await ec.check_tee_sheet()
    assert s.status == "ok"


@pytest.mark.asyncio
@respx.mock
async def test_tee_sheet_down_on_500():
    respx.get(TEE_SHEET_URL).mock(return_value=httpx.Response(500))
    s = await ec.check_tee_sheet()
    assert s.status == "down"


@pytest.mark.asyncio
@respx.mock
async def test_tee_sheet_down_on_connect_error():
    respx.get(TEE_SHEET_URL).mock(side_effect=httpx.ConnectError("no route to host"))
    s = await ec.check_tee_sheet()
    assert s.status == "down"


# --------------------------------------------------------------------------
# check_all
# --------------------------------------------------------------------------
@pytest.mark.asyncio
@respx.mock
async def test_check_all_returns_all_eight(monkeypatch):
    for n in (
        "GROQ_API_KEY",
        "AUTH0_DOMAIN",
        "RESEND_API_KEY",
        "GHIN_API_USER",
        "GHIN_API_PASS",
        "GROUPME_ACCESS_TOKEN",
        "GROUPME_GROUP_ID",
        "FORETEES_USERNAME",
        "FORETEES_PASSWORD",
        "GOOGLE_OAUTH_CREDENTIALS",
        "LIVE_TEST_SHEET_ID",
    ):
        monkeypatch.delenv(n, raising=False)
    # tee_sheet has no creds gate, so it always fires a real GET — mock it so the
    # suite makes no live network call. The other seven short-circuit to
    # not_configured and make no HTTP request.
    respx.get(TEE_SHEET_URL).mock(return_value=httpx.Response(200, text="<html>ok</html>"))

    results = await ec.check_all()
    names = {r.name for r in results}
    assert names == {"groq", "auth0", "google", "ghin", "groupme", "foretees", "resend", "tee_sheet"}
    by = {r.name: r.status for r in results}
    assert by["groq"] == "not_configured"
    assert by["ghin"] == "not_configured"
    assert by["tee_sheet"] == "ok"
