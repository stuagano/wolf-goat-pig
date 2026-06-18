"""Live probe for Resend: the API key is valid (lists domains). Skips unless
RESEND_API_KEY is set. READ-ONLY — never sends an email."""

import httpx
import pytest
from ctk import expect

from tests.live._helpers import require_env

pytestmark = pytest.mark.live


def test_resend_api_key_valid():
    env = require_env("RESEND_API_KEY")
    resp = httpx.get(
        "https://api.resend.com/domains",
        headers={"Authorization": f"Bearer {env['RESEND_API_KEY']}"},
        timeout=15.0,
    )
    assert resp.status_code == 200, f"Resend returned {resp.status_code}: {resp.text[:200]}"
    # A valid key returns a parseable JSON body (a 401 would mean a dead key).
    expect(resp.text).is_json().verify()
