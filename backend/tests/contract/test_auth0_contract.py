"""Contract tests for the Auth0 integration (JWT verification).

Mocks the tenant's JWKS endpoint at the httpx boundary and verifies
`AuthService.verify_token` fetches+uses the JWKS, rejects bad tokens, and
surfaces JWKS-fetch failures.

`verify_token(credentials)` is a FastAPI dependency taking
`HTTPAuthorizationCredentials`; the JWKS path only runs when
`ENVIRONMENT == "production"`. It does a *sync* `httpx.get` to the JWKS URL,
calls `raise_for_status()`, `resp.json()`, then `jwt.decode(...)`.

Behavior pinned to what the code actually does (read auth_service.py):
- bogus token (no matching key) -> jose raises JWTError, caught -> HTTPException 401
- missing config in production  -> HTTPException 500 (raised directly)
- JWKS 500 -> `raise_for_status()` -> httpx.HTTPStatusError (NOT caught -> propagates)
- JWKS timeout -> httpx.ConnectTimeout (propagates)
- malformed JWKS body -> `resp.json()` -> json.JSONDecodeError (propagates)

The `except` in verify_token only catches JWTError, so JWKS fetch/parse
failures propagate as their raw httpx/json types — mirroring how the Groq
reference pins httpx.ConnectTimeout / json.JSONDecodeError rather than a
wrapped type.

`ENVIRONMENT` is read live via os.getenv inside the function (setenv works),
but `AUTH0_DOMAIN`/`AUTH0_API_AUDIENCE` are module-level constants captured at
import — they must be patched via monkeypatch.setattr on the module, not setenv.
"""

import json

import httpx
import pytest
import respx
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.services import auth_service as auth_service_module

DOMAIN = "test.example.com"
AUDIENCE = "https://api.test/"
JWKS_URL = f"https://{DOMAIN}/.well-known/jwks.json"

# Success-shape JWKS: a single RSA signing key. A bogus token can't be validated
# against this (no matching kid / signature), which is the correct rejection.
_JWKS_BODY = {"keys": [{"kid": "test", "kty": "RSA", "use": "sig", "n": "abc", "e": "AQAB"}]}

# Syntactically-bogus bearer token (not a real JWT).
BOGUS_TOKEN = "not.a.realtoken"


def _creds(token: str = BOGUS_TOKEN) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.fixture
def _production_auth0(monkeypatch):
    """Put verify_token on the production JWKS path with valid-looking config."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setattr(auth_service_module, "AUTH0_DOMAIN", DOMAIN)
    monkeypatch.setattr(auth_service_module, "AUTH0_API_AUDIENCE", AUDIENCE)


@respx.mock
def test_success_shape_jwks_bogus_token_raises_401(_production_auth0):
    # JWKS fetch succeeds; the bogus token can't be validated -> jose JWTError
    # -> caught -> HTTPException 401. Proves we fetch+use the JWKS and reject.
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, json=_JWKS_BODY))
    with pytest.raises(HTTPException) as exc:
        auth_service_module.AuthService.verify_token(_creds())
    assert exc.value.status_code == 401


@respx.mock
def test_jwks_endpoint_500_raises(_production_auth0):
    # resp.raise_for_status() fires before decode; only JWTError is caught, so
    # this propagates as a raw httpx.HTTPStatusError (would be an unhandled 500).
    respx.get(JWKS_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        auth_service_module.AuthService.verify_token(_creds())


@respx.mock
def test_jwks_timeout_raises(_production_auth0):
    # Pin the injected type: a bare Exception would green-wash a client-build
    # failure (e.g. local SOCKS proxy) instead of asserting the timeout path.
    respx.get(JWKS_URL).mock(side_effect=httpx.ConnectTimeout("x"))
    with pytest.raises(httpx.ConnectTimeout):
        auth_service_module.AuthService.verify_token(_creds())


@respx.mock
def test_malformed_jwks_body_raises(_production_auth0):
    # resp.json() on a non-JSON 200 body raises JSONDecodeError before decode.
    respx.get(JWKS_URL).mock(return_value=httpx.Response(200, text="not json"))
    with pytest.raises(json.JSONDecodeError):
        auth_service_module.AuthService.verify_token(_creds())


def test_missing_config_raises_500(monkeypatch):
    # Production branch with no domain configured -> the guard raises directly.
    # AUTH0_DOMAIN is a module constant captured at import, so clear it via
    # setattr (delenv on the env var can't touch the already-captured value).
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setattr(auth_service_module, "AUTH0_DOMAIN", "")
    monkeypatch.setattr(auth_service_module, "AUTH0_API_AUDIENCE", "")
    with pytest.raises(HTTPException) as exc:
        auth_service_module.AuthService.verify_token(_creds())
    assert exc.value.status_code == 500
