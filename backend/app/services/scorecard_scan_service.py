"""
Scorecard Photo Scan Service

Uses Gemini Vision (via Vercel proxy) to extract running quarter totals
from a photo of a physical Wolf Goat Pig scorecard. Circles = negative values.
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

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


async def scan_scorecard(image_bytes: bytes, content_type: str) -> dict[str, Any]:
    """
    Send scorecard image to Gemini Vision (via Vercel proxy) and return
    extracted running totals plus computed per-hole quarter deltas.
    """
    proxy_url = os.getenv(
        "GEMINI_PROXY_URL",
        "https://wolf-goat-pig.vercel.app/api/gemini-proxy",
    )

    try:
        # Encode image as base64 for the Gemini REST API
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Build contents array with inline image data
        parts = []

        # Add reference image if available (few-shot)
        ref = _load_reference_image()
        if ref:
            ref_bytes, ref_mime = ref
            ref_b64 = base64.b64encode(ref_bytes).decode("utf-8")
            ref_gt_path = _EXAMPLES_DIR / "example_001_ground_truth.json"
            ref_gt = ref_gt_path.read_text() if ref_gt_path.exists() else ""
            parts.append({"text": "REFERENCE SCORECARD — this is a known example. Study the handwriting style."})
            parts.append({"inline_data": {"mime_type": ref_mime, "data": ref_b64}})
            parts.append({"text": f"The correct extraction for the reference scorecard above (H1-H6 confirmed):\n{ref_gt}\n\n---\n\nNow extract the NEW scorecard below using the same conventions and handwriting awareness:\n{EXTRACTION_PROMPT}"})
        else:
            parts.append({"text": EXTRACTION_PROMPT})

        # Add the actual scorecard image
        parts.append({"inline_data": {"mime_type": content_type, "data": image_b64}})

        payload = {
            "model": "gemini-flash-latest",
            "contents": [{"parts": parts}],
        }

        headers = {}
        proxy_secret = os.getenv("GEMINI_PROXY_SECRET")
        if proxy_secret:
            headers["x-proxy-secret"] = proxy_secret

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(proxy_url, json=payload, headers=headers)

        if resp.status_code == 429:
            raise ValueError("Scorecard scanner is rate-limited. Try again in a minute.")
        if resp.status_code != 200:
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            err_msg = body.get("error", {}).get("message", "unknown error")
            logger.error("Gemini Vision API %d: %s", resp.status_code, err_msg)
            raise ValueError(f"Vision API error: {err_msg}")

        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini returned no candidates")
        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

        # Strip markdown code fences if present
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        extracted = json.loads(raw_text)

    except json.JSONDecodeError as e:
        logger.error("Gemini returned non-JSON: %s", e)
        raise ValueError(f"Failed to parse Gemini response: {e}")
    except ValueError:
        raise
    except Exception as e:
        logger.error("Gemini Vision error: %s", e)
        raise

    players = extracted.get("players", [])
    raw_totals = extracted.get("running_totals", [])

    # Apply circle = negative to values
    for entry in raw_totals:
        if entry.get("is_circled"):
            entry["value"] = -abs(entry["value"])

    # Group running totals by player_index
    by_player: dict[int, list] = {}
    for entry in raw_totals:
        pi = entry["player_index"]
        by_player.setdefault(pi, []).append(entry)

    # Ensure all players have entries (even if Gemini missed some)
    for i in range(len(players)):
        by_player.setdefault(i, [])

    # Compute per-hole deltas for each player, filling carry-overs as delta=0
    per_hole_quarters = []
    for player_index, totals in by_player.items():
        deltas = _compute_per_hole_deltas(totals)
        for d in deltas:
            per_hole_quarters.append(
                {
                    "player_index": player_index,
                    "hole": d["hole"],
                    "quarters": d["quarters"],
                }
            )

    return {
        "players": players,
        "running_totals": raw_totals,
        "per_hole_quarters": per_hole_quarters,
    }
