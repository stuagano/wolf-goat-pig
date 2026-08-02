"""Commissioner LLM generation — Vertex Gemini (default) with optional Groq fallback."""

from __future__ import annotations

import logging
import os

import httpx
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _provider() -> str:
    return os.getenv("COMMISSIONER_LLM_PROVIDER", "vertex").strip().lower()


def commissioner_provider() -> str:
    """Public accessor for commissioner LLM provider (vertex | groq)."""
    return _provider()


async def llm_generate(prompt: str, system_instruction: str) -> str:
    """Generate commissioner text from a user prompt and system instruction."""
    if _provider() == "groq":
        return await _groq_generate(prompt, system_instruction)
    return await _vertex_generate(prompt, system_instruction)


async def _vertex_generate(prompt: str, system_instruction: str) -> str:
    project = os.getenv("GCP_PROJECT_ID", "").strip()
    if not project:
        raise ValueError("Commissioner AI is not configured (GCP_PROJECT_ID missing)")

    location = os.getenv("GCP_LOCATION", "global").strip() or "global"
    model = os.getenv("COMMISSIONER_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

    client = genai.Client(vertexai=True, project=project, location=location)
    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                max_output_tokens=2048,
            ),
        )
    except Exception as exc:
        logger.error("Vertex Commissioner LLM failed: %s", exc)
        raise ValueError(f"LLM API error: {exc}") from exc

    text = (response.text or "").strip()
    if not text:
        raise ValueError("LLM returned empty response")
    return text


async def _groq_generate(prompt: str, system_instruction: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Commissioner AI is not configured (GROQ_API_KEY missing)")

    payload = {
        "model": _GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _GROQ_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        if resp.status_code == 429:
            raise ValueError("Commissioner is getting too many questions right now. Try again in a minute.")
        if resp.status_code != 200:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            err_msg = body.get("error", {}).get("message", "unknown error")
            logger.error("Groq API %d: %s", resp.status_code, err_msg)
            raise ValueError(f"LLM API error: {err_msg}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError("LLM returned no choices")
    return choices[0].get("message", {}).get("content", "")
