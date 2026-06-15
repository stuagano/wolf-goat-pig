"""Tests for backend Sentry init + scrubbing. No real DSN / network."""

import sentry_sdk

from app.observability import sentry


def test_init_sentry_noop_without_dsn(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    calls = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: calls.append(kw))
    assert sentry.init_sentry() is False
    assert calls == []


def test_init_sentry_inits_with_dsn(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://k@o123.ingest.sentry.io/1")
    captured = {}
    monkeypatch.setattr(sentry_sdk, "init", lambda **kw: captured.update(kw))
    assert sentry.init_sentry() is True
    assert captured["send_default_pii"] is False
    assert captured["traces_sample_rate"] == 0.0
    assert captured["before_send"] is sentry._scrub


def test_scrub_strips_auth_and_secret_fields():
    event = {
        "request": {"headers": {"Authorization": "Bearer abc", "X-Fine": "ok"}},
        "extra": {"resend_api_key": "re_123", "nested": {"token": "t", "keep": "v"}},
    }
    out = sentry._scrub(event, {})
    assert out["request"]["headers"]["Authorization"] == "[scrubbed]"
    assert out["request"]["headers"]["X-Fine"] == "ok"
    assert out["extra"]["resend_api_key"] == "[scrubbed]"
    assert out["extra"]["nested"]["token"] == "[scrubbed]"
    assert out["extra"]["nested"]["keep"] == "v"
