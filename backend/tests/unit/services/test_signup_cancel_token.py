"""Signed cancel links are bound to one signup and are not guessable ids."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.services.signup_cancel_token import (
    CancelTokenError,
    cancel_signup_url,
    issue_cancel_token,
    read_cancel_token,
)

CLUB = ZoneInfo("America/Los_Angeles")
SECRET = "test-cancel-secret"


@pytest.fixture(autouse=True)
def signing_secret(monkeypatch):
    monkeypatch.setenv("SIGNUP_CANCEL_SECRET", SECRET)
    monkeypatch.delenv("FORETEES_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)


def _issue(**overrides):
    fields = {"signup_id": 42, "player_profile_id": 7, "signup_date": "2026-11-27"}
    fields.update(overrides)
    return issue_cancel_token(**fields)


def test_round_trip_binds_signup_player_and_date():
    token = _issue()
    claims = read_cancel_token(token, now=datetime(2026, 11, 23, tzinfo=CLUB))

    assert claims.signup_id == 42
    assert claims.player_profile_id == 7
    assert claims.signup_date == "2026-11-27"
    assert token != "42"


def test_bare_signup_id_is_not_a_token():
    with pytest.raises(CancelTokenError) as caught:
        read_cancel_token("42")
    assert caught.value.code == "invalid"


def test_tampered_payload_is_rejected():
    token = _issue()
    body, signature = token.split(".", 1)
    other = _issue(signup_id=43)
    swapped = f"{other.split('.', 1)[0]}.{signature}"

    with pytest.raises(CancelTokenError) as caught:
        read_cancel_token(swapped)
    assert caught.value.code == "invalid"
    assert body != other.split(".", 1)[0]


def test_token_from_another_secret_is_rejected(monkeypatch):
    token = _issue()
    monkeypatch.setenv("SIGNUP_CANCEL_SECRET", "different-secret")

    with pytest.raises(CancelTokenError) as caught:
        read_cancel_token(token)
    assert caught.value.code == "invalid"


def test_token_expires_after_the_day_following_the_game():
    token = _issue(signup_date="2026-11-27")

    still_good = read_cancel_token(token, now=datetime(2026, 11, 28, 23, 0, tzinfo=CLUB))
    assert still_good.signup_date == "2026-11-27"

    with pytest.raises(CancelTokenError) as caught:
        read_cancel_token(token, now=datetime(2026, 11, 29, 0, 30, tzinfo=CLUB))
    assert caught.value.code == "expired"


def test_cancel_url_uses_the_frontend_and_hides_the_signup_id(monkeypatch):
    monkeypatch.setenv("FRONTEND_URL", "https://wolfgoatpig.com/")
    token = _issue()
    url = cancel_signup_url(token)

    assert url == f"https://wolfgoatpig.com/signup/cancel/{token}"
    assert "/signups/42" not in url
    assert url.endswith(token)
