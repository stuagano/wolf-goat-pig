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
- BLANK cells mean CARRY-OVER: the hole was tied and carried over, so the running total is the same as the previous hole. DO NOT omit blank holes — include them with the same value as the previous hole and confidence 1.0.
- "E" means the player is exactly even (running total = 0).
- If you can't read a value clearly, still make your best guess but assign low confidence.
- You MUST include all 18 holes for every player. Never omit a hole.

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
    Send scorecard image to Gemini Vision and return extracted running totals
    plus computed per-hole quarter deltas.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured")

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-flash-latest")

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
