"""
Scorecard Photo Scan Service

Uses Gemini Vision to extract running quarter totals from a photo of a
physical Wolf Goat Pig scorecard. Circles = negative values.
"""

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """This is a Wolf Goat Pig golf wagering scorecard photo.

The numbers written on it represent RUNNING TOTALS of quarters (a wagering unit) for each player across the round.

CRITICAL conventions:
- CIRCLED numbers are NEGATIVE. A circle drawn around a number means that player is DOWN by that amount. Uncircled = positive (player is UP).
- Values are RUNNING TOTALS, not per-hole amounts. Each cell shows the player's cumulative quarter balance AFTER that hole.
- Values are typically small integers (-15 to +15 range). Half-values like 0.5 are possible.
- The running total runs continuously from hole 1 through hole 18 (no reset at hole 10).
- If a cell is blank or has "E", treat it as 0 (player is even).
- If you can't read a value clearly, still make your best guess but assign low confidence.

Extract:
1. Player names (from the leftmost column or row headers)
2. For each player, for each hole 1-18: the running total value and whether it is circled (negative)

Return ONLY valid JSON in this exact format:
{
  "players": [
    {"name": "John", "confidence": 0.95}
  ],
  "running_totals": [
    {"player_index": 0, "hole": 1, "value": 2, "is_circled": false, "confidence": 0.92},
    {"player_index": 0, "hole": 2, "value": 4, "is_circled": false, "confidence": 0.90},
    {"player_index": 0, "hole": 3, "value": 3, "is_circled": true, "confidence": 0.85}
  ]
}

Only include holes you can actually read. Omit holes that are completely unreadable.
"""


def _compute_per_hole_deltas(running_totals_for_player: list[dict]) -> list[dict]:
    """Convert running totals to per-hole deltas. Hole 1 delta = value itself (starting from 0)."""
    sorted_holes = sorted(running_totals_for_player, key=lambda x: x["hole"])
    deltas = []
    prev = 0
    for entry in sorted_holes:
        val = -entry["value"] if entry["is_circled"] else entry["value"]
        delta = val - prev
        prev = val
        deltas.append({"hole": entry["hole"], "quarters": delta})
    return deltas


async def scan_scorecard(image_bytes: bytes, content_type: str) -> dict[str, Any]:
    """
    Send scorecard image to Gemini Vision and return extracted running totals
    plus computed per-hole quarter deltas.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        image_part = {"mime_type": content_type, "data": image_bytes}
        response = model.generate_content([EXTRACTION_PROMPT, image_part])

        raw_text = response.text.strip()
        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        extracted = json.loads(raw_text)

    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned non-JSON: {e}")
        raise ValueError(f"Failed to parse Gemini response: {e}")
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
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

    # Compute per-hole deltas for each player
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
