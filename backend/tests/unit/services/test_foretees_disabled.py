from unittest.mock import patch

import pytest

from app.services.foretees_service import create_user_foretees_service


@pytest.mark.asyncio
async def test_saved_credentials_cannot_bypass_disabled_integration(monkeypatch):
    monkeypatch.setenv("FORETEES_ENABLED", "false")
    with patch("app.services.foretees_service.httpx.AsyncClient") as client:
        service = create_user_foretees_service("member", "password")
        assert service.config.enabled is False
        assert await service._ensure_session() is False
        client.assert_not_called()


def test_saved_credentials_work_when_explicitly_enabled(monkeypatch):
    monkeypatch.setenv("FORETEES_ENABLED", "true")
    service = create_user_foretees_service("member", "password")
    assert service.config.enabled is True
    assert service.config.username == "member"
