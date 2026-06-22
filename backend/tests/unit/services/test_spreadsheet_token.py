"""_get_access_token: prod uses GOOGLE_OAUTH_CREDENTIALS exclusively; the dev-only
gcloud fallback must not spam Sentry (error-level) when the CLI is simply absent."""

import logging

import app.services.spreadsheet_sync_service as svc

_LOGGER = "app.services.spreadsheet_sync_service"


def test_no_creds_and_missing_gcloud_returns_none_without_error(monkeypatch, caplog):
    monkeypatch.delenv("GOOGLE_OAUTH_CREDENTIALS", raising=False)

    def missing_gcloud(*a, **k):
        raise FileNotFoundError(2, "No such file or directory", "gcloud")

    monkeypatch.setattr(svc.subprocess, "run", missing_gcloud)
    with caplog.at_level(logging.WARNING, logger=_LOGGER):
        token = svc._get_access_token()

    assert token is None
    # Missing gcloud in prod must be a WARNING, never an ERROR (no Sentry escalation).
    assert not any(r.levelname == "ERROR" for r in caplog.records)
    assert any(r.levelname == "WARNING" for r in caplog.records)


def test_incomplete_creds_errors_and_does_not_fall_back_to_gcloud(monkeypatch, caplog):
    monkeypatch.setenv("GOOGLE_OAUTH_CREDENTIALS", '{"refresh_token": "r"}')  # missing client_id/secret
    calls = {"n": 0}

    def spy_run(*a, **k):
        calls["n"] += 1
        raise AssertionError("gcloud must NOT be invoked when creds are present")

    monkeypatch.setattr(svc.subprocess, "run", spy_run)
    with caplog.at_level(logging.ERROR, logger=_LOGGER):
        token = svc._get_access_token()

    assert token is None
    assert calls["n"] == 0
    assert any(r.levelname == "ERROR" and "incomplete" in r.getMessage() for r in caplog.records)
