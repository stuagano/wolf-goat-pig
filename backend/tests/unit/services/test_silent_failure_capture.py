"""Each known silent-failure swallow site must report to Sentry while still
returning its swallowed value (False / None). Mirrors the Phase-1 contract
error mocks; spies on sentry_sdk.capture_exception."""

import httpx
import pytest
import respx
import sentry_sdk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.services import spreadsheet_sync_service
from app.services.foretees_service import (
    FORETEES_APP_BASE,
    ForeteesConfig,
    ForeteesService,
)
from app.services.ghin_service import GHINService

TEST_DB = "sqlite:///./test_silent_capture.db"
_engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# Proxy env vars httpx honors at client construction. This module lives outside
# tests/contract/, so the contract conftest's proxy-clearing fixture does not
# apply — clear them locally so httpx never tries to load `socksio` on a
# SOCKS-proxied dev machine (same failure mode as the local-only startup test).
_PROXY_ENV_VARS = (
    "ALL_PROXY",
    "all_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "HTTPS_PROXY",
    "https_proxy",
)


@pytest.fixture(autouse=True)
def _no_proxy(monkeypatch):
    for var in _PROXY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=_engine)
    s = _Session()
    try:
        yield s
    finally:
        s.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def capture_spy(monkeypatch):
    calls = []
    monkeypatch.setattr(sentry_sdk, "capture_exception", lambda e: calls.append(e))
    return calls


@pytest.mark.asyncio
@respx.mock
async def test_ghin_reports_and_still_returns_false(db, capture_spy, monkeypatch):
    monkeypatch.setenv("GHIN_API_USER", "u")
    monkeypatch.setenv("GHIN_API_PASS", "p")
    respx.post("https://api2.ghin.com/api/v1/golfer_login.json").mock(side_effect=httpx.ConnectError("down"))
    service = GHINService(db)
    result = await service.initialize()
    assert result is False
    assert len(capture_spy) >= 1


def test_sheets_reports_and_still_returns_none(capture_spy, monkeypatch):
    monkeypatch.setattr(spreadsheet_sync_service, "_get_access_token", lambda: "tok")

    def boom(*a, **k):
        raise TimeoutError("down")

    monkeypatch.setattr(spreadsheet_sync_service.urllib.request, "urlopen", boom)
    result = spreadsheet_sync_service._sheets_api_get("sheet123", "A1:B2")
    assert result is None
    assert len(capture_spy) >= 1


@pytest.mark.asyncio
@respx.mock
async def test_foretees_reports_and_still_returns_false(capture_spy):
    respx.get(url__startswith="https://www.wingpointgolf.com").mock(side_effect=httpx.ConnectError("down"))
    config = ForeteesConfig(
        enabled=True,
        username="u",
        password="p",
        base_url=FORETEES_APP_BASE,
        timeout_seconds=15.0,
    )
    service = ForeteesService(config)
    try:
        ok = await service._ensure_session()
    finally:
        await service.close()
    assert ok is False
    assert len(capture_spy) >= 1
