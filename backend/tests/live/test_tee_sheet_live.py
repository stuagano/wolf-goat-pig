"""Live probe for the thousand-cranes WGP tee sheet: the page is reachable and
parses into slots. Read-only. Opt-in via LIVE_TEST_TEE_SHEET=1 (no creds needed,
but we don't hammer the real site unless explicitly enabled)."""

from datetime import date as date_type

import pytest
from ctk import expect

from tests.live._helpers import require_env

pytestmark = pytest.mark.live


@pytest.mark.asyncio
async def test_tee_sheet_reachable_and_parses():
    require_env("LIVE_TEST_TEE_SHEET")  # opt-in flag; skips unless set
    from app.routers import tee_sheet

    # Real GET against today's date. Reaching past this line means the request
    # succeeded — a non-2xx or connection failure raises HTTPException(502).
    result = await tee_sheet.get_tee_sheet(date=date_type.today().isoformat())

    # Real return shape is a dict with the parsed slot list under "slots".
    expect(result).has_keys("date", "slots", "signed_up", "signed_up_count").verify()
    expect(result["slots"]).satisfies(lambda s: isinstance(s, list), "slots is a list").verify()
