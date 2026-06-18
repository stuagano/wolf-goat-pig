"""Live probe for Groq: a real 1-token completion proves reachability + auth
+ a usable response. Skips unless GROQ_API_KEY is set. Read-only (no state)."""

import os

import httpx
import pytest
from ctk import expect

from tests.live._helpers import require_env

pytestmark = pytest.mark.live

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def test_groq_reachable_and_returns_content():
    env = require_env("GROQ_API_KEY")
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    resp = httpx.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {env['GROQ_API_KEY']}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": "reply with the word pong"}],
            "max_tokens": 5,
        },
        timeout=30.0,
    )
    assert resp.status_code == 200, f"Groq returned {resp.status_code}: {resp.text[:300]}"
    content = resp.json()["choices"][0]["message"]["content"]
    expect(content).nonempty().verify()
