"""Live probe for Google Sheets: read a designated test sheet with real creds.

Skips unless GOOGLE_OAUTH_CREDENTIALS + LIVE_TEST_SHEET_ID are set. Read-only —
calls SpreadsheetSyncService.get_all_rounds(), which only GETs the Details range
and never writes.

The read path is synchronous (plain ``def``), so this is a plain test, not async.

NOTE: the configured LIVE_TEST_SHEET_ID must point at a sheet with the WGP
``Details`` tab shape (columns Date/Group/Member/Score/Location/Duration).
get_all_rounds() returns [] for any read failure AND for an empty/wrong-shaped
sheet, so a non-empty result is the only unambiguous "live read works" signal.
"""

import pytest
from ctk import expect

from tests.live._helpers import require_env

pytestmark = pytest.mark.live


def test_google_sheet_readable():
    env = require_env("GOOGLE_OAUTH_CREDENTIALS", "LIVE_TEST_SHEET_ID")

    from app.services.spreadsheet_sync_service import SpreadsheetSyncService

    service = SpreadsheetSyncService(env["LIVE_TEST_SHEET_ID"])
    rounds = service.get_all_rounds()

    # Non-empty list of RoundResult proves token exchange + values read worked.
    expect(rounds, label="google sheet rounds").nonempty().verify()
    first = rounds[0]
    expect(first.member, label="round member").nonempty().verify()
    expect(first.date, label="round date").nonempty().verify()
