from pathlib import Path

import httpx
import pytest
import respx

from app.config import Settings
from app.tee_sheet import ForeteesAuthError, ForeteesSheetError, fetch_tee_times

settings = Settings(
    wingpoint_base="https://www.wingpointgolf.com",
    login_page="/public/member-login-465.html",
    tee_time_page="/members/golf/make-a-tee-time-703.html",
    foretees_base="https://ftapp.example/v5/club",
)


@pytest.mark.asyncio
@respx.mock
async def test_fetch_tee_times_happy_path(tmp_path):
    html = (Path(__file__).parent / "fixtures" / "member_sheet_sample.html").read_text()
    respx.get("https://www.wingpointgolf.com/public/member-login-465.html").mock(
        return_value=httpx.Response(200, text="login")
    )
    respx.post("https://www.wingpointgolf.com/public/member-login-465.html").mock(
        return_value=httpx.Response(200, text="ok")
    )
    respx.get("https://www.wingpointgolf.com/members/golf/make-a-tee-time-703.html").mock(
        return_value=httpx.Response(
            200,
            text="var ftSSOKey = 'KEY'; var ftSSOIV = 'IV';",
        )
    )
    respx.get("https://ftapp.example/v5/club/Member_select").mock(
        return_value=httpx.Response(200, text="sso")
    )
    respx.get("https://ftapp.example/v5/club/Member_sheet").mock(
        return_value=httpx.Response(200, text=html)
    )

    slots = await fetch_tee_times("u", "p", "2026-07-28", settings=settings)
    assert len(slots) == 1
    assert slots[0]["time"] == "11:00 AM"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_tee_times_auth_fails_without_sso():
    respx.get("https://www.wingpointgolf.com/public/member-login-465.html").mock(
        return_value=httpx.Response(200, text="login")
    )
    respx.post("https://www.wingpointgolf.com/public/member-login-465.html").mock(
        return_value=httpx.Response(200, text="ok")
    )
    respx.get("https://www.wingpointgolf.com/members/golf/make-a-tee-time-703.html").mock(
        return_value=httpx.Response(200, text="no sso vars here")
    )
    with pytest.raises(ForeteesAuthError):
        await fetch_tee_times("u", "p", "2026-07-28", settings=settings)


@pytest.mark.asyncio
async def test_fetch_tee_times_rejects_invalid_date():
    with pytest.raises(ValueError):
        await fetch_tee_times("u", "p", "07/28/2026", settings=settings)


@pytest.mark.asyncio
@respx.mock
async def test_fetch_tee_times_sheet_http_error_is_typed():
    respx.get("https://www.wingpointgolf.com/public/member-login-465.html").mock(
        return_value=httpx.Response(200, text="login")
    )
    respx.post("https://www.wingpointgolf.com/public/member-login-465.html").mock(
        return_value=httpx.Response(200, text="ok")
    )
    respx.get("https://www.wingpointgolf.com/members/golf/make-a-tee-time-703.html").mock(
        return_value=httpx.Response(
            200,
            text="var ftSSOKey = 'KEY'; var ftSSOIV = 'IV';",
        )
    )
    respx.get("https://ftapp.example/v5/club/Member_select").mock(
        return_value=httpx.Response(200, text="sso")
    )
    respx.get("https://ftapp.example/v5/club/Member_sheet").mock(
        return_value=httpx.Response(500, text="down")
    )

    with pytest.raises(ForeteesSheetError):
        await fetch_tee_times("u", "p", "2026-07-28", settings=settings)
