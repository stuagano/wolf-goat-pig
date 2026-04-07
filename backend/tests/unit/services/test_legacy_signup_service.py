from types import SimpleNamespace

import pytest

from backend.app.services import legacy_signup_service as legacy_sync


class DummyResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("legacy CGI returned error status")


class DummyClient:
    def __init__(self, record: dict, *, status_code: int = 200, **kwargs) -> None:
        self._record = record
        self._status_code = status_code
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, data=None, json=None, headers=None):
        self._record["url"] = url
        self._record["data"] = data
        self._record["json"] = json
        self._record["headers"] = headers or {}
        self._record["timeout"] = self.kwargs.get("timeout")
        return DummyResponse(status_code=self._status_code)


def test_sync_disabled_short_circuits(monkeypatch):
    """Sync is skipped entirely when the feature flag is disabled."""

    config = legacy_sync.LegacySignupConfig(enabled=False, create_url="http://legacy")
    service = legacy_sync.LegacySignupSyncService(config)

    def _fail_client(*args, **kwargs):  # pragma: no cover - defensive guard
        raise AssertionError("Legacy client should not be instantiated when disabled")

    monkeypatch.setattr(legacy_sync.httpx, "Client", _fail_client)

    signup = SimpleNamespace(id=1, date="2024-05-01", player_name="Test")
    assert service.sync_signup_created(signup) is False


def test_sync_builds_form_payload(monkeypatch):
    """Payload uses configured mappings and headers for form submissions."""

    record: dict = {}

    def _client_factory(**kwargs):
        return DummyClient(record, **kwargs)

    monkeypatch.setattr(legacy_sync.httpx, "Client", _client_factory)

    config = legacy_sync.LegacySignupConfig(
        enabled=True,
        create_url="http://legacy",
        timeout_seconds=5.5,
        api_key="secret-token",
        payload_format="form",
        field_map={"player_name": "golfer", "date": "tee_date", "action": "mode"},
        extra_fields={"sheet_id": "wing"},
        create_action_field="action",
        create_action_value="register",
    )

    service = legacy_sync.LegacySignupSyncService(config)
    signup = SimpleNamespace(
        id=7,
        date="2024-05-01",
        player_name="Test Golfer",
        player_profile_id=99,
        preferred_start_time="07:30",
        notes="Bring balls",
        status="signed_up",
    )

    assert service.sync_signup_created(signup) is True
    assert record["url"] == "http://legacy"
    assert record["timeout"] == 5.5
    assert record["data"]["golfer"] == "Test Golfer"
    assert record["data"]["tee_date"] == "2024-05-01"
    assert record["data"]["sheet_id"] == "wing"
    assert record["data"]["mode"] == "register"
    assert record["data"]["player_profile_id"] == 99
    assert "Authorization" in record["headers"]
    assert record["json"] is None


def test_config_from_env_parses_json(monkeypatch):
    """Environment variables feed through to the runtime config."""

    monkeypatch.setenv("LEGACY_SIGNUP_SYNC_ENABLED", "true")
    monkeypatch.setenv("LEGACY_SIGNUP_CREATE_URL", "http://legacy")
    monkeypatch.setenv("LEGACY_SIGNUP_FIELD_MAP", '{"player_name": "name"}')
    monkeypatch.setenv("LEGACY_SIGNUP_EXTRA_FIELDS", '{"sheet_id": "wing"}')
    monkeypatch.setenv("LEGACY_SIGNUP_PAYLOAD_FORMAT", "json")
    monkeypatch.setenv("LEGACY_SIGNUP_TIMEOUT_SECONDS", "12.5")

    legacy_sync.reset_legacy_signup_service()
    config = legacy_sync.LegacySignupConfig.from_env()

    assert config.enabled is True
    assert config.create_url == "http://legacy"
    assert config.payload_format == "json"
    assert config.field_map["player_name"] == "name"
    assert config.extra_fields["sheet_id"] == "wing"
    assert config.timeout_seconds == pytest.approx(12.5)

    # Cleanup to avoid polluting other tests
    monkeypatch.delenv("LEGACY_SIGNUP_SYNC_ENABLED", raising=False)
    monkeypatch.delenv("LEGACY_SIGNUP_CREATE_URL", raising=False)
    monkeypatch.delenv("LEGACY_SIGNUP_FIELD_MAP", raising=False)
    monkeypatch.delenv("LEGACY_SIGNUP_EXTRA_FIELDS", raising=False)
    monkeypatch.delenv("LEGACY_SIGNUP_PAYLOAD_FORMAT", raising=False)
    monkeypatch.delenv("LEGACY_SIGNUP_TIMEOUT_SECONDS", raising=False)


def test_sync_uses_json_payload_when_configured(monkeypatch):
    """JSON payloads are emitted when requested."""

    record: dict = {}

    def _client_factory(**kwargs):
        return DummyClient(record, **kwargs)

    monkeypatch.setattr(legacy_sync.httpx, "Client", _client_factory)

    config = legacy_sync.LegacySignupConfig(
        enabled=True,
        update_url="http://legacy/update",
        payload_format="json",
        field_map={"status": "state"},
        extra_fields={"sheet_id": "wing"},
        update_action_field="action",
        update_action_value="modify",
    )

    service = legacy_sync.LegacySignupSyncService(config)
    signup = SimpleNamespace(id=12, status="signed_up", date="2024-05-01", player_name="Tester")

    assert service.sync_signup_updated(signup) is True
    assert record["url"] == "http://legacy/update"
    assert record["data"] is None
    assert record["json"]["state"] == "signed_up"
    assert record["json"]["sheet_id"] == "wing"
    assert record["json"]["action"] == "modify"
