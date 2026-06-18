"""Contract tests for the Groq integration (Commissioner chat).

Mocks api.groq.com at the httpx boundary and verifies _llm_generate handles
success, auth failure, rate limit, server error, timeout, and malformed JSON.

`_llm_generate(prompt, system_instruction)` takes two strings (NOT a messages
list) and returns the assistant message *content string*. Error paths raise:
ValueError for the missing-key/429/non-200 branches; httpx/JSON exceptions
propagate for timeout/malformed-JSON.
"""

import json

import httpx
import pytest
import respx

from app.routers import commissioner

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
PROMPT = "hi"
SYSTEM = "be brief"


def _ok_body(content: str = "Hello from Groq") -> dict:
    # OpenAI-compatible shape Groq returns.
    return {
        "id": "chatcmpl-test",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}],
        "usage": {"total_tokens": 3},
    }


def _err_body(message: str) -> dict:
    # Groq's real error envelope: nested error.message.
    return {"error": {"message": message, "type": "invalid_request_error"}}


@pytest.mark.asyncio
@respx.mock
async def test_success_returns_usable_content(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    respx.post(GROQ_URL).mock(return_value=httpx.Response(200, json=_ok_body("pong")))
    result = await commissioner._llm_generate(PROMPT, SYSTEM)
    assert "pong" in (result if isinstance(result, str) else str(result))


@pytest.mark.asyncio
async def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError):
        await commissioner._llm_generate(PROMPT, SYSTEM)


@pytest.mark.asyncio
@respx.mock
async def test_rate_limit_429_raises(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    respx.post(GROQ_URL).mock(return_value=httpx.Response(429, json=_err_body("rate")))
    with pytest.raises(ValueError):
        await commissioner._llm_generate(PROMPT, SYSTEM)


@pytest.mark.asyncio
@respx.mock
async def test_server_error_500_raises(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    respx.post(GROQ_URL).mock(return_value=httpx.Response(500, json=_err_body("boom")))
    with pytest.raises(ValueError):
        await commissioner._llm_generate(PROMPT, SYSTEM)


@pytest.mark.asyncio
@respx.mock
async def test_timeout_raises(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    respx.post(GROQ_URL).mock(side_effect=httpx.ConnectTimeout("timed out"))
    # Specific type: a bare `Exception` here would silently green-wash an
    # ImportError if the httpx client failed to build (e.g. local SOCKS proxy),
    # asserting nothing about the timeout path. Pin to the injected type.
    with pytest.raises(httpx.ConnectTimeout):
        await commissioner._llm_generate(PROMPT, SYSTEM)


@pytest.mark.asyncio
@respx.mock
async def test_malformed_json_raises(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    respx.post(GROQ_URL).mock(return_value=httpx.Response(200, text="not json"))
    # Specific type: assert the JSON-decode path actually fired (resp.json() on
    # the 200 body), not just "some exception".
    with pytest.raises(json.JSONDecodeError):
        await commissioner._llm_generate(PROMPT, SYSTEM)
