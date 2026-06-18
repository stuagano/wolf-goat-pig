"""Live probe for GHIN: real credentials authenticate. Skips unless
GHIN_API_USER + GHIN_API_PASS are set. Read-only (login + optional lookup).

GHINService.initialize() returns True / sets self.initialized on success; on
any failure it returns False (never raises). We pin the real success signal.

If LIVE_TEST_GHIN_ID is set, additionally fetch that golfer's handicap. The
by-id lookup (_fetch_handicap_from_ghin) is gated behind ENABLE_GHIN_INTEGRATION
== "true", so we set that env inside the guarded block. The lookup is skipped
(not failed) when LIVE_TEST_GHIN_ID is absent.
"""

import os

import pytest
from ctk import claim_vs_reality, expect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.live._helpers import require_env

pytestmark = pytest.mark.live

# The live dir has no DB fixture; GHINService(db) needs a real Session, so set
# up a minimal sqlite session locally (read-only as far as GHIN auth goes).
_TEST_DATABASE_URL = "sqlite:///./test_ghin_live.db"
_engine = create_engine(_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture
def db():
    from app.models import Base

    Base.metadata.create_all(bind=_engine)
    session = _TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.mark.asyncio
async def test_ghin_authenticates(db, monkeypatch):
    require_env("GHIN_API_USER", "GHIN_API_PASS")
    from app.services.ghin_service import GHINService

    service = GHINService(db)
    ok = await service.initialize()  # True on success; sets self.initialized + jwt_token

    claim_vs_reality(
        claimed_success=bool(ok),
        verifier=lambda: (_ for _ in ()).throw(AssertionError("GHIN auth failed"))
        if not (service.initialized and service.jwt_token)
        else None,
        claim_label="ghin initialize",
    )

    # Optional read-only by-id lookup, guarded on LIVE_TEST_GHIN_ID.
    ghin_id = os.environ.get("LIVE_TEST_GHIN_ID")
    if ghin_id:
        # The by-id fetch is gated behind this flag; enable it for the probe.
        monkeypatch.setenv("ENABLE_GHIN_INTEGRATION", "true")
        handicap_data = await service._fetch_handicap_from_ghin(ghin_id)
        expect(handicap_data, label="ghin handicap lookup").nonempty().verify()
        expect(handicap_data.get("handicap_index"), label="handicap_index").nonempty().verify()
