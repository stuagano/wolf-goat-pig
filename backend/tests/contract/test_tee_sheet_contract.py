"""Contract tests for the thousand-cranes.com WGP tee-sheet integration.

Mocks the thousand-cranes.com CGI endpoint at the httpx boundary and verifies
`tee_sheet.get_tee_sheet` parses the real page shape and maps failures to the
contract our callers rely on.

`get_tee_sheet(date)` is async, GETs wgp_tee_sheet.cgi, runs the HTML through
`_parse_slots`, and returns a dict:
    {"date", "slots", "signed_up_count", "signed_up"}.
On httpx.HTTPStatusError (raise_for_status) or any connection error it raises
HTTPException(status_code=502). The success HTML below mirrors what the parser
expects: each occupied slot is a `<tr><td align="center">N</td>...` row whose
name lives in a `color:#001bbf` span and notes in a `color:#800000` span.
"""

import httpx
import pytest
import respx
from fastapi import HTTPException

from app.routers import tee_sheet

DATE = "2026-06-15"

# Realistic fragment: slot 1 occupied (name + notes), slot 2 empty. The
# `<tr><td align="center">` must be literally adjacent — the row regex has no
# wildcard there even under DOTALL, so a stray newline would kill the match.
SLOTS_HTML = (
    "<html><body><table>"
    '<tr><td align="center">1</td>'
    '<td><span style="color:#001bbf;font-weight:bold">John Doe</span></td>'
    '<td><span style="color:#800000">Guest</span></td></tr>'
    '<tr><td align="center">2</td><td>&nbsp;</td><td>&nbsp;</td></tr>'
    "</table></body></html>"
)

# Valid page, no sign-up rows the parser recognizes.
EMPTY_HTML = "<html><body><table><tr><th>No signups yet</th></tr></table></body></html>"


@pytest.mark.asyncio
@respx.mock
async def test_success_parses_slots():
    respx.get(url__startswith="https://thousand-cranes.com").mock(return_value=httpx.Response(200, text=SLOTS_HTML))
    result = await tee_sheet.get_tee_sheet(date=DATE)

    assert result["date"] == DATE
    # Both slots parsed (one occupied, one empty placeholder).
    occupied = [s for s in result["slots"] if s["name"]]
    assert len(occupied) == 1
    slot = occupied[0]
    assert slot["slot"] == 1
    assert slot["name"] == "John Doe"
    assert slot["notes"] == "Guest"
    # Derived fields stay consistent with the parsed slots.
    assert result["signed_up_count"] == 1
    assert result["signed_up"] == occupied


@pytest.mark.asyncio
@respx.mock
async def test_empty_but_valid_page_returns_no_signups():
    respx.get(url__startswith="https://thousand-cranes.com").mock(return_value=httpx.Response(200, text=EMPTY_HTML))
    result = await tee_sheet.get_tee_sheet(date=DATE)

    assert result["slots"] == []
    assert result["signed_up"] == []
    assert result["signed_up_count"] == 0


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("status", [502, 500])
async def test_upstream_http_error_maps_to_502(status):
    respx.get(url__startswith="https://thousand-cranes.com").mock(return_value=httpx.Response(status))
    with pytest.raises(HTTPException) as exc_info:
        await tee_sheet.get_tee_sheet(date=DATE)
    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
@respx.mock
async def test_connection_error_maps_to_502():
    respx.get(url__startswith="https://thousand-cranes.com").mock(side_effect=httpx.ConnectError("no route to host"))
    # Pin to HTTPException(502), not a bare Exception: a bare assert would
    # green-wash a client-construction failure that never exercised the handler.
    with pytest.raises(HTTPException) as exc_info:
        await tee_sheet.get_tee_sheet(date=DATE)
    assert exc_info.value.status_code == 502
