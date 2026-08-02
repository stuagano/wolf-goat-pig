"""Contract tests for Commissioner LLM generation (Vertex default, Groq fallback)."""

import json

import httpx
import pytest
import respx

from app.services import commissioner_llm_service as llm

PROMPT = "hi"
SYSTEM = "be brief"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _ok_body(content: str = "Hello") -> dict:
    return {
        "id": "chatcmpl-test",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}],
        "usage": {"total_tokens": 3},
    }


@pytest.mark.asyncio
async def test_vertex_success(monkeypatch):
    monkeypatch.setenv("COMMISSIONER_LLM_PROVIDER", "vertex")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")

    class _Resp:
        text = "pong"

    class _Models:
        async def generate_content(self, **kwargs):
            return _Resp()

    class _Aio:
        models = _Models()

    class _Client:
        aio = _Aio()

    monkeypatch.setattr(llm.genai, "Client", lambda **kwargs: _Client())
    result = await llm.llm_generate(PROMPT, SYSTEM)
    assert "pong" in result


@pytest.mark.asyncio
async def test_vertex_missing_project_raises(monkeypatch):
    monkeypatch.setenv("COMMISSIONER_LLM_PROVIDER", "vertex")
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    with pytest.raises(ValueError, match="GCP_PROJECT_ID"):
        await llm.llm_generate(PROMPT, SYSTEM)


@pytest.mark.asyncio
@respx.mock
async def test_groq_success(monkeypatch):
    monkeypatch.setenv("COMMISSIONER_LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    respx.post(GROQ_URL).mock(return_value=httpx.Response(200, json=_ok_body("pong")))
    result = await llm.llm_generate(PROMPT, SYSTEM)
    assert "pong" in result


@pytest.mark.asyncio
async def test_groq_missing_api_key_raises(monkeypatch):
    monkeypatch.setenv("COMMISSIONER_LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        await llm.llm_generate(PROMPT, SYSTEM)


@pytest.mark.asyncio
@respx.mock
async def test_groq_rate_limit_raises(monkeypatch):
    monkeypatch.setenv("COMMISSIONER_LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    respx.post(GROQ_URL).mock(return_value=httpx.Response(429, json={"error": {"message": "rate"}}))
    with pytest.raises(ValueError, match="too many questions"):
        await llm.llm_generate(PROMPT, SYSTEM)


@pytest.mark.asyncio
@respx.mock
async def test_groq_malformed_json_raises(monkeypatch):
    monkeypatch.setenv("COMMISSIONER_LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    respx.post(GROQ_URL).mock(return_value=httpx.Response(200, text="not json"))
    with pytest.raises(json.JSONDecodeError):
        await llm.llm_generate(PROMPT, SYSTEM)
