"""Contract tests for the Resend email integration.

Resend sends via the `resend` Python SDK (`resend.Emails.send(params)`), so we
mock at that SDK seam rather than the HTTP boundary. Tests exercise the
provider directly (`ResendEmailProvider.send_email`), the analog of testing the
Groq provider seam.

Key interface facts (read from resend_provider.py):
- `send_email(...)` returns a plain `bool` — it discards the SDK return value,
  so success is `True` (NOT the email id) and any exception is swallowed
  (`except Exception: return False`).
- `is_configured()` checks the module global `resend.api_key` (set in
  `__init__`) AND `self.from_email` — it does NOT read the `RESEND_API_KEY`
  env var. The env var only gates the factory `create_resend_provider()`.
"""

import resend

from app.services.providers.resend_provider import (
    ResendEmailProvider,
    create_resend_provider,
)


def test_success_returns_true(monkeypatch):
    # Constructor sets resend.api_key, so is_configured() passes without env.
    provider = ResendEmailProvider(api_key="test-key", from_email="t@example.com", from_name="T")
    monkeypatch.setattr(resend.Emails, "send", lambda params: {"id": "email_123"})

    # Pin to True, not the id: the provider returns a bool, discarding the SDK result.
    assert provider.send_email("to@example.com", "Subj", "<p>hi</p>") is True


def test_provider_error_swallowed_returns_false(monkeypatch):
    provider = ResendEmailProvider(api_key="test-key", from_email="t@example.com", from_name="T")

    def _boom(params):
        raise Exception("resend: invalid API key")

    monkeypatch.setattr(resend.Emails, "send", _boom)

    # Broad except Exception -> return False is the intended design for email:
    # a failed send must not crash the calling request.
    assert provider.send_email("to@example.com", "Subj", "<p>hi</p>") is False


def test_not_configured_provider_is_noop(monkeypatch):
    # resend.api_key is a module global that leaks across tests; null it so a
    # prior test's key cannot mask the falsy path.
    monkeypatch.setattr(resend, "api_key", None)
    provider = ResendEmailProvider(api_key="", from_email="", from_name="T")

    sent = {"called": False}

    def _spy(params):
        sent["called"] = True
        return {"id": "should_not_happen"}

    monkeypatch.setattr(resend.Emails, "send", _spy)

    assert provider.is_configured() is False
    assert provider.send_email("to@example.com", "Subj", "<p>hi</p>") is False
    # Prove the no-op: send must never be attempted when unconfigured.
    assert sent["called"] is False


def test_factory_returns_none_without_api_key(monkeypatch):
    # The env var is the real gate at the factory layer (not at is_configured).
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("FROM_EMAIL", "t@example.com")
    assert create_resend_provider() is None
