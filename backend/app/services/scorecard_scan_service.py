"""
Scorecard Photo Scan Service

Uses Groq Vision (Llama 4 Scout) to extract running quarter totals
from a photo of a physical Wolf Goat Pig scorecard. Circles = negative values.
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

from .scorecard_preprocess import annotate_circles

logger = logging.getLogger(__name__)

_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

# Path to reference scorecard examples for few-shot prompting
_EXAMPLES_DIR = Path(__file__).parent.parent / "data" / "scorecard_examples"


def _load_reference_image() -> tuple[bytes, str] | None:
    """Load the reference scorecard image for few-shot prompting, if available."""
    for ext, mime in [("jpeg", "image/jpeg"), ("jpg", "image/jpeg"), ("png", "image/png")]:
        path = _EXAMPLES_DIR / f"example_001.{ext}"
        if path.exists():
            return path.read_bytes(), mime
    return None

EXTRACTION_PROMPT = """This is a Wolf Goat Pig golf wagering scorecard photo.

The numbers written on it represent RUNNING TOTALS of quarters (a wagering unit) for each player across the round.

CRITICAL conventions:
- CIRCLED numbers are NEGATIVE. A circle drawn around a number means that player is DOWN by that amount. Uncircled = positive (player is UP).
- Values are RUNNING TOTALS, not per-hole amounts. Each cell shows the player's cumulative quarter balance AFTER that hole.
- Values can be LARGE — running totals of ±50 to ±200 are normal. Do NOT assume values are small. Read multi-digit numbers carefully.
- HANDWRITING WARNING: A handwritten "6" often looks like a "u" or "U". The digit sequence "96" may appear to read "9u" or "9U" — always interpret trailing u/U as the digit 6. Similarly "16" may look like "1U", "36" like "3U", etc.
- The running total runs continuously from hole 1 through hole 18 (no reset at hole 10).
- BLANK cells or a slash "/" mean CARRY-OVER: the hole was tied and the running total is the same as the previous hole. DO NOT omit blank holes — include them with the same value as the previous hole and confidence 1.0.
- "E" means the player is exactly even (running total = 0).
- If you can't read a value clearly, still make your best guess but assign low confidence.
- You MUST include all 18 holes for every player. Never omit a hole.

REFERENCE EXAMPLE — use this to calibrate your reading of this scorer's handwriting:
The image you are about to analyze is from the same scorer. In a previous scorecard:
- Holes 1-2: all players at 0 (blank/carry)
- Hole 3: two players went to +96 (uncircled), two players went to -96 (circled) — what appeared to be "9u" or "9U" was actually 96
- Holes 4-5: carry-overs (blank)
- Hole 6: one player went from -96 to -36 (+60 delta), others adjusted accordingly

Key takeaway: "9u" in this handwriting = 96. Always read trailing lowercase u or U as the digit 6.

Extract:
1. Player names (from the leftmost column or row headers)
2. For each player, for ALL 18 holes: the running total value and whether it is circled (negative)

Return ONLY valid JSON in this exact format:
{
  "players": [
    {"name": "John", "confidence": 0.95}
  ],
  "running_totals": [
    {"player_index": 0, "hole": 1, "value": 2, "is_circled": false, "confidence": 0.92},
    {"player_index": 0, "hole": 2, "value": 4, "is_circled": false, "confidence": 0.90},
    {"player_index": 0, "hole": 3, "value": 4, "is_circled": false, "confidence": 1.0}
  ]
}

CRITICAL — CIRCLE DETECTION HINTS:
Bright red rectangles have been pre-drawn around cells whose values are
CIRCLED on the original card. Treat any value inside a red rectangle as
is_circled: true. Cells WITHOUT a red rectangle are uncircled (positive).
The red rectangles are pre-processing markers — ignore them when reading
the value itself, only use them to determine the sign.
"""


def _compute_per_hole_deltas(running_totals_for_player: list[dict], num_holes: int = 18) -> list[dict]:
    """Convert running totals to per-hole deltas, filling missing holes as carry-overs (delta=0)."""
    by_hole = {entry["hole"]: entry for entry in running_totals_for_player}
    deltas = []
    prev = 0
    for hole in range(1, num_holes + 1):
        if hole in by_hole:
            entry = by_hole[hole]
            val = -abs(entry["value"]) if entry.get("is_circled") else entry["value"]
        else:
            # Missing hole = carry-over, running total unchanged
            val = prev
        delta = val - prev
        prev = val
        deltas.append({"hole": hole, "quarters": delta})
    return deltas


_STRICT_SUFFIX = """

CRITICAL OUTPUT RULE — your previous response either failed to parse as JSON or violated the zero-sum invariant. Do these:
1. Output ONLY a valid JSON object. No markdown fences, no prose, no leading or trailing text.
2. Wolf Goat Pig is ZERO-SUM. On every hole, the change in running totals across all players MUST sum to 0. If your numbers don't satisfy this, re-read the cells before answering.
3. If a value is unclear, lower its confidence — do NOT guess in a way that breaks zero-sum.
"""


def _validate_zero_sum(per_hole_quarters: list[dict]) -> dict[str, Any]:
    """Per-hole deltas must sum to zero across players. Returns {valid, bad_holes}."""
    by_hole: dict[int, float] = {}
    for entry in per_hole_quarters:
        h = entry["hole"]
        by_hole[h] = by_hole.get(h, 0) + entry["quarters"]
    # Allow small rounding noise (we store ints, so anything non-zero is real).
    bad_holes = {h: s for h, s in by_hole.items() if abs(s) > 0.5}
    return {"valid": not bad_holes, "bad_holes": bad_holes}


async def _call_groq_vision(
    image_bytes: bytes,
    content_type: str,
    *,
    strict: bool = False,
) -> dict[str, Any]:
    """One round-trip to Groq Vision. Strict mode tightens the prompt and lowers temp."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    user_content: list[dict[str, Any]] = []

    ref = _load_reference_image()
    if ref:
        ref_bytes, ref_mime = ref
        ref_b64 = base64.b64encode(ref_bytes).decode("utf-8")
        ref_gt_path = _EXAMPLES_DIR / "example_001_ground_truth.json"
        ref_gt = ref_gt_path.read_text() if ref_gt_path.exists() else ""
        user_content.append({"type": "text", "text": "REFERENCE SCORECARD — study the handwriting style:"})
        user_content.append({"type": "image_url", "image_url": {"url": f"data:{ref_mime};base64,{ref_b64}"}})
        prompt = (
            f"Correct extraction for the reference (H1-H6 confirmed):\n{ref_gt}\n\n"
            f"---\n\nNow extract the NEW scorecard below:\n{EXTRACTION_PROMPT}"
        )
    else:
        prompt = EXTRACTION_PROMPT
    if strict:
        prompt += _STRICT_SUFFIX
    user_content.append({"type": "text", "text": prompt})
    user_content.append({"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_b64}"}})

    payload = {
        "model": _GROQ_VISION_MODEL,
        "messages": [{"role": "user", "content": user_content}],
        "temperature": 0.0 if strict else 0.3,
        "max_tokens": 4096,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            _GROQ_API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )

    if resp.status_code == 429:
        raise ValueError("Scorecard scanner is rate-limited. Try again in a minute.")
    if resp.status_code != 200:
        body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        err_msg = body.get("error", {}).get("message", "unknown error")
        logger.error("Groq Vision API %d: %s", resp.status_code, err_msg)
        raise ValueError(f"Vision API error: {err_msg}")

    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError("Groq returned no choices")
    raw_text = (choices[0].get("message", {}).get("content") or "").strip()

    # Strip markdown fences and any surrounding prose so a stray ```json block
    # or "Here is the JSON:" preamble doesn't blow up the parse.
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```", 2)[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.rsplit("```", 1)[0].strip()
    # Last-ditch: take the substring from the first { to the last }.
    if not raw_text.startswith("{"):
        first = raw_text.find("{")
        last = raw_text.rfind("}")
        if first != -1 and last > first:
            raw_text = raw_text[first : last + 1]

    return json.loads(raw_text)


def _shape_extraction(extracted: dict[str, Any]) -> dict[str, Any]:
    """Apply circle=negative, group by player, compute per-hole deltas."""
    players = extracted.get("players", [])
    raw_totals = extracted.get("running_totals", [])

    for entry in raw_totals:
        if entry.get("is_circled"):
            entry["value"] = -abs(entry["value"])

    by_player: dict[int, list] = {}
    for entry in raw_totals:
        pi = entry["player_index"]
        by_player.setdefault(pi, []).append(entry)
    for i in range(len(players)):
        by_player.setdefault(i, [])

    per_hole_quarters: list[dict] = []
    for player_index, totals in by_player.items():
        deltas = _compute_per_hole_deltas(totals)
        for d in deltas:
            per_hole_quarters.append(
                {"player_index": player_index, "hole": d["hole"], "quarters": d["quarters"]}
            )

    return {
        "players": players,
        "running_totals": raw_totals,
        "per_hole_quarters": per_hole_quarters,
    }


async def scan_scorecard(image_bytes: bytes, content_type: str) -> dict[str, Any]:
    """
    Send scorecard image to Groq Vision and return extracted running totals
    plus computed per-hole quarter deltas. Retries once if the first attempt
    returns malformed JSON or violates the zero-sum invariant — these are
    the dominant failure modes in practice and a stricter retry catches
    most of them without doubling latency on the happy path.

    Preprocessing: classical circle detection draws red rectangles around
    each detected hand-drawn circle once at the top of the function. The
    annotated bytes are reused for both the initial call and the strict
    retry. Annotation failures degrade gracefully — original bytes are sent.
    """
    annotated_bytes, annotated_ct, preprocessing_diag = annotate_circles(
        image_bytes, content_type
    )

    parse_error: Exception | None = None
    try:
        extracted = await _call_groq_vision(annotated_bytes, annotated_ct, strict=False)
    except json.JSONDecodeError as e:
        logger.warning("First scan returned non-JSON, retrying strict: %s", e)
        parse_error = e
        extracted = None

    if extracted is not None:
        result = _shape_extraction(extracted)
        validation = _validate_zero_sum(result["per_hole_quarters"])
        if validation["valid"]:
            result["validation"] = validation
            result["preprocessing"] = preprocessing_diag
            return result
        logger.warning("Zero-sum violated on first scan: %s — retrying strict", validation["bad_holes"])

    try:
        extracted = await _call_groq_vision(annotated_bytes, annotated_ct, strict=True)
    except json.JSONDecodeError as e:
        if parse_error is not None:
            logger.error("Both scan attempts returned non-JSON")
        raise ValueError(f"Failed to parse vision response: {e}")

    result = _shape_extraction(extracted)
    result["validation"] = _validate_zero_sum(result["per_hole_quarters"])
    result["preprocessing"] = preprocessing_diag
    return result
