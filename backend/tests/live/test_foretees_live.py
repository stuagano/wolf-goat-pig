"""Live probe for ForeTees: real credentials complete the login handshake.
Skips unless FORETEES_USERNAME + FORETEES_PASSWORD are set. Read-only — auth
only, never books a tee time."""

import pytest
from ctk import claim_vs_reality

from tests.live._helpers import require_env

pytestmark = pytest.mark.live


@pytest.mark.asyncio
async def test_foretees_login_handshake(monkeypatch):
    require_env("FORETEES_USERNAME", "FORETEES_PASSWORD")
    from app.services.foretees_service import ForeteesConfig, ForeteesService

    # from_env() reads FORETEES_ENABLED (a config flag, not a secret); without
    # it a configured run short-circuits to False before attempting login.
    monkeypatch.setenv("FORETEES_ENABLED", "true")

    config = ForeteesConfig.from_env()
    service = ForeteesService(config)
    try:
        ok = await service._ensure_session()

        claim_vs_reality(
            claimed_success=bool(ok),
            verifier=lambda: None
            if service._session_valid()
            else (_ for _ in ()).throw(AssertionError("ForeTees session not valid after login")),
            claim_label="foretees login handshake",
        )
    finally:
        await service.close()
