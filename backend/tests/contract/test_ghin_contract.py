"""Contract tests for the GHIN integration (handicap sync).

Mocks api2.ghin.com at the httpx boundary and verifies GHINService.initialize()
handles success, bad-creds (401), server error (500), connection timeout, and
missing credentials.

Unlike the Groq reference, GHINService NEVER raises on failure: every error
path is swallowed by a broad `except` / status-code guard and returns ``False``
with ``self.initialized = False``. So all error cases assert the *same* shape
(``is False``) and must additionally pin *which* code path fired (did the HTTP
request actually happen?) — otherwise a client-construction failure or the
missing-creds short-circuit would green-wash a test that proves nothing.

IMPORTANT: credentials are read in ``__init__`` (``os.getenv``), not in
``initialize()``. So env must be set/unset BEFORE constructing the service.
"""

import httpx
import pytest
import respx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.services.ghin_service import GHINService

GHIN_LOGIN_URL = "https://api2.ghin.com/api/v1/golfer_login.json"
FAKE_TOKEN = "fake-golfer-user-token-abc123"

TEST_DATABASE_URL = "sqlite:///./test_ghin_contract.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Minimal sqlite Session so GHINService(db) can be constructed."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _login_ok_body(token: str = FAKE_TOKEN) -> dict:
    # Real-shaped GHIN login body: token at golfer_user.golfer_user_token.
    return {
        "golfer_user": {
            "golfer_user_token": token,
            "id": 12345,
            "email": "golfer@example.com",
        }
    }


@pytest.mark.asyncio
@respx.mock
async def test_success_login_authenticates(monkeypatch, db):
    monkeypatch.setenv("GHIN_API_USER", "golfer@example.com")
    monkeypatch.setenv("GHIN_API_PASS", "secret")
    route = respx.post(GHIN_LOGIN_URL).mock(return_value=httpx.Response(200, json=_login_ok_body()))

    service = GHINService(db)  # reads creds from env in __init__
    ok = await service.initialize()

    assert ok is True
    assert route.called  # the login request actually fired
    assert service.initialized is True
    # Prove the golfer_user.golfer_user_token extraction ran.
    assert service.jwt_token == FAKE_TOKEN


@pytest.mark.asyncio
@respx.mock
async def test_bad_creds_401_disables_gracefully(monkeypatch, db):
    monkeypatch.setenv("GHIN_API_USER", "golfer@example.com")
    monkeypatch.setenv("GHIN_API_PASS", "wrong")
    route = respx.post(GHIN_LOGIN_URL).mock(return_value=httpx.Response(401, json={"error": "invalid"}))

    service = GHINService(db)
    ok = await service.initialize()

    # Real behavior: status != 200 → log + return False, no raise.
    assert ok is False
    assert route.called  # not the missing-creds short-circuit
    assert service.initialized is False
    assert service.jwt_token is None


@pytest.mark.asyncio
@respx.mock
async def test_server_error_500_disables_gracefully(monkeypatch, db):
    monkeypatch.setenv("GHIN_API_USER", "golfer@example.com")
    monkeypatch.setenv("GHIN_API_PASS", "secret")
    route = respx.post(GHIN_LOGIN_URL).mock(return_value=httpx.Response(500, json={"error": "boom"}))

    service = GHINService(db)
    ok = await service.initialize()

    assert ok is False
    assert route.called
    assert service.initialized is False
    assert service.jwt_token is None


@pytest.mark.asyncio
@respx.mock
async def test_connect_timeout_disables_gracefully(monkeypatch, db):
    monkeypatch.setenv("GHIN_API_USER", "golfer@example.com")
    monkeypatch.setenv("GHIN_API_PASS", "secret")
    route = respx.post(GHIN_LOGIN_URL).mock(side_effect=httpx.ConnectTimeout("timed out"))

    service = GHINService(db)
    ok = await service.initialize()

    # Broad `except Exception` swallows the timeout → False (no raise).
    assert ok is False
    assert route.called  # the request was attempted before timing out
    assert service.initialized is False
    assert service.jwt_token is None


@pytest.mark.asyncio
@respx.mock
async def test_missing_creds_disables_without_http_call(monkeypatch, db):
    monkeypatch.delenv("GHIN_API_USER", raising=False)
    monkeypatch.delenv("GHIN_API_PASS", raising=False)
    # Register the route but expect it to be untouched: the guard must
    # short-circuit before any httpx call.
    route = respx.post(GHIN_LOGIN_URL).mock(return_value=httpx.Response(200, json=_login_ok_body()))

    service = GHINService(db)  # __init__ sees no creds
    ok = await service.initialize()

    assert ok is False
    assert route.call_count == 0  # no network attempt at all
    assert service.initialized is False
    assert service.jwt_token is None
