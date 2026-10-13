"""
Unit tests for the Commissioner-voice intro added to league emails.

The AI only ever adds a flavor paragraph on top of the real facts; any
failure, timeout, or invented number must fall back to no intro at all.
"""

import asyncio

import pytest

from app.services import email_voice

FACTS = {
    "biggest_round": {"player": "Dan Anderson", "quarters": 370},
    "rounds": 5,
    "players": ["Dan Anderson", "Brett Saks"],
}


def fake_llm(text=None, exc=None, delay=0.0):
    calls = []

    async def generate(prompt, system_instruction):
        calls.append((prompt, system_instruction))
        if delay:
            await asyncio.sleep(delay)
        if exc:
            raise exc
        return text

    generate.calls = calls
    return generate


@pytest.fixture
def use_llm(monkeypatch):
    def install(fake):
        monkeypatch.setattr(email_voice, "llm_generate", fake)
        return fake

    return install


def test_returns_cleaned_intro_and_sends_facts_in_prompt(use_llm):
    fake = use_llm(fake_llm('  "Dan Anderson took 370 quarters off the field across 5 rounds. Brutal."  '))
    intro = email_voice.commissioner_intro("weekly_highlights", FACTS)
    assert intro == "Dan Anderson took 370 quarters off the field across 5 rounds. Brutal."
    prompt, system = fake.calls[0]
    assert "Dan Anderson" in prompt and "370" in prompt
    assert "never invent" in system.lower()


def test_negative_numbers_in_facts_allow_their_magnitude(use_llm):
    use_llm(fake_llm("Bob dropped 20 quarters. Ouch."))
    assert email_voice.commissioner_intro("x", {"worst": {"player": "Bob", "quarters": -20}}) == (
        "Bob dropped 20 quarters. Ouch."
    )


def test_invented_number_drops_the_intro(use_llm):
    use_llm(fake_llm("Dan Anderson won 400 quarters in 5 rounds."))
    assert email_voice.commissioner_intro("weekly_highlights", FACTS) is None


def test_llm_error_falls_back_to_none(use_llm):
    use_llm(fake_llm(exc=ValueError("LLM API error")))
    assert email_voice.commissioner_intro("weekly_highlights", FACTS) is None


def test_timeout_falls_back_to_none(use_llm, monkeypatch):
    monkeypatch.setattr(email_voice, "TIMEOUT_SECONDS", 0.05)
    use_llm(fake_llm("too late", delay=1))
    assert email_voice.commissioner_intro("weekly_highlights", FACTS) is None


def test_empty_or_overlong_reply_is_dropped(use_llm):
    use_llm(fake_llm("   "))
    assert email_voice.commissioner_intro("x", FACTS) is None
    use_llm(fake_llm("Dan Anderson " * 100))
    assert email_voice.commissioner_intro("x", FACTS) is None
