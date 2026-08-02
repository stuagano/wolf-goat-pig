"""Vertex Gemini multimodal vision for scorecard extraction."""

from __future__ import annotations

import logging
from typing import Any

from google import genai
from google.genai import types

from .config import Settings, get_settings
from .extract import build_prompt, fit_image_to_budget, parse_vision_json

logger = logging.getLogger("scorecard_agent.vision")

_REFERENCE_MAX_DIM = 4096


def _client(settings: Settings) -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=settings.gcp_project_id,
        location=settings.gcp_location,
    )


async def extract_scorecard(
    image_bytes: bytes,
    content_type: str,
    *,
    expected_players: list[str] | None = None,
    strict: bool = False,
    bad_holes: dict[int, float] | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """One Vertex Gemini vision call with optional reference examples."""
    settings = settings or get_settings()
    prompt, ref_images = build_prompt(
        expected_players=expected_players,
        strict=strict,
        bad_holes=bad_holes,
        include_references=not settings.skip_reference_examples,
    )

    main_bytes, main_ct = fit_image_to_budget(
        image_bytes, content_type, max_dim=_REFERENCE_MAX_DIM, max_b64_chars=10**12
    )

    parts: list[types.Part] = []
    for idx, (ref_bytes, ref_mime) in enumerate(ref_images, 1):
        label = "REFERENCE SCORECARD" if len(ref_images) == 1 else f"REFERENCE SCORECARD #{idx}"
        parts.append(types.Part.from_text(text=f"{label} — study the handwriting style:"))
        parts.append(types.Part.from_bytes(data=ref_bytes, mime_type=ref_mime))

    parts.append(types.Part.from_text(text=prompt))
    parts.append(types.Part.from_bytes(data=main_bytes, mime_type=main_ct))

    client = _client(settings)
    response = await client.aio.models.generate_content(
        model=settings.vision_model,
        contents=parts,
        config=types.GenerateContentConfig(
            temperature=0.0 if strict else 0.2,
            response_mime_type="application/json",
            max_output_tokens=8192,
        ),
    )

    raw_text = (response.text or "").strip()
    if not raw_text:
        raise ValueError("Vertex returned empty vision response")
    return parse_vision_json(raw_text)
