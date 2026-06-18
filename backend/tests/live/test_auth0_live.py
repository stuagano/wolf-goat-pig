"""Live probe for Auth0: the tenant's JWKS endpoint is reachable and serves
signing keys. Skips unless AUTH0_DOMAIN is set. Read-only."""

import httpx
import pytest
from ctk import expect

from tests.live._helpers import require_env

pytestmark = pytest.mark.live


def test_auth0_jwks_reachable():
    env = require_env("AUTH0_DOMAIN")
    url = f"https://{env['AUTH0_DOMAIN']}/.well-known/jwks.json"
    resp = httpx.get(url, timeout=10.0)
    assert resp.status_code == 200, f"Auth0 JWKS returned {resp.status_code}: {resp.text[:200]}"
    data = resp.json()
    expect(data).has_keys("keys").verify()
    assert len(data["keys"]) > 0, "Auth0 JWKS returned no signing keys"
