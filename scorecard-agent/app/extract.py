"""Shared extraction helpers for the scorecard vision agent."""

from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_EXAMPLES_DIR = Path(__file__).parent / "data" / "scorecard_examples"

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

_STRICT_SUFFIX = """

CRITICAL OUTPUT RULE — your previous response either failed to parse as JSON or violated the zero-sum invariant. Do these:
1. Output ONLY a valid JSON object. No markdown fences, no prose, no leading or trailing text.
2. Wolf Goat Pig is ZERO-SUM. On every hole, the change in running totals across all players MUST sum to 0. If your numbers don't satisfy this, re-read the cells before answering.
3. If a value is unclear, lower its confidence — do NOT guess in a way that breaks zero-sum.
"""


def expected_players_suffix(expected_players: list[str] | None) -> str:
    if not expected_players:
        return ""
    names = ", ".join(expected_players)
    return (
        f"\n\nThe scorers are KNOWN: expect exactly {len(expected_players)} players "
        f"named: {names}. Use these exact names (one row each). Some players may be "
        f"written in a lower band below the Par row — include them. Ignore any "
        f"golf-score rows and handwritten notes; only read the quarter running totals."
    )


def bad_holes_suffix(bad_holes: dict[int, float]) -> str:
    if not bad_holes:
        return ""
    holes = ", ".join(str(h) for h in sorted(bad_holes))
    return (
        f"\n\nZERO-SUM VIOLATION on hole(s): {holes}. Re-read ONLY those columns "
        f"and fix the running totals so per-hole deltas sum to zero across players."
    )


def load_reference_examples() -> list[tuple[bytes, str, str]]:
    examples: list[tuple[bytes, str, str]] = []
    seen: set[str] = set()
    if not _EXAMPLES_DIR.is_dir():
        return examples
    for path in sorted(_EXAMPLES_DIR.glob("example_*")):
        if path.suffix.lower() not in (".jpeg", ".jpg", ".png") or path.stem in seen:
            continue
        gt_path = _EXAMPLES_DIR / f"{path.stem}_ground_truth.json"
        if not gt_path.exists():
            continue
        seen.add(path.stem)
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        examples.append((path.read_bytes(), mime, gt_path.read_text()))
    return examples


def fit_image_to_budget(
    image_bytes: bytes, content_type: str, *, max_dim: int, max_b64_chars: int
) -> tuple[bytes, str]:
    try:
        from io import BytesIO

        from PIL import Image

        fits_budget = len(base64.b64encode(image_bytes)) <= max_b64_chars
        img = Image.open(BytesIO(image_bytes))
        if fits_budget and max(img.size) <= max_dim:
            return image_bytes, content_type
        img = img.convert("RGB")
        dim = min(max_dim, max(img.size))
        data = image_bytes
        for _ in range(8):
            w, h = img.size
            scale = dim / max(w, h)
            frame = (
                img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS) if scale < 1 else img
            )
            buf = BytesIO()
            frame.save(buf, format="JPEG", quality=82)
            data = buf.getvalue()
            if len(base64.b64encode(data)) <= max_b64_chars:
                return data, "image/jpeg"
            dim = int(dim * 0.85)
        return data, "image/jpeg"
    except Exception:
        return image_bytes, content_type


def compute_per_hole_deltas(running_totals_for_player: list[dict], num_holes: int = 18) -> list[dict]:
    by_hole = {entry["hole"]: entry for entry in running_totals_for_player}
    deltas = []
    prev = 0
    for hole in range(1, num_holes + 1):
        if hole in by_hole:
            entry = by_hole[hole]
            val = -abs(entry["value"]) if entry.get("is_circled") else entry["value"]
        else:
            val = prev
        delta = val - prev
        prev = val
        deltas.append({"hole": hole, "quarters": delta})
    return deltas


def validate_zero_sum(per_hole_quarters: list[dict]) -> dict[str, Any]:
    by_hole: dict[int, float] = {}
    for entry in per_hole_quarters:
        h = entry["hole"]
        by_hole[h] = by_hole.get(h, 0) + entry["quarters"]
    bad_holes = {h: s for h, s in by_hole.items() if abs(s) > 0.5}
    return {"valid": not bad_holes, "bad_holes": bad_holes}


def shape_extraction(extracted: dict[str, Any]) -> dict[str, Any]:
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
        deltas = compute_per_hole_deltas(totals)
        for d in deltas:
            per_hole_quarters.append({"player_index": player_index, "hole": d["hole"], "quarters": d["quarters"]})

    return {
        "players": players,
        "running_totals": raw_totals,
        "per_hole_quarters": per_hole_quarters,
    }


def build_prompt(
    *,
    expected_players: list[str] | None,
    strict: bool = False,
    bad_holes: dict[int, float] | None = None,
    include_references: bool = True,
) -> tuple[str, list[tuple[bytes, str]]]:
    """Return (text prompt, reference images as (bytes, mime))."""
    references = [] if not include_references or os.getenv("SCORECARD_SKIP_REFERENCE_EXAMPLES") == "1" else load_reference_examples()
    ref_images: list[tuple[bytes, str]] = []
    if references:
        gt_blocks = []
        for idx, (ref_bytes, ref_mime, ref_gt) in enumerate(references, 1):
            sized_ref, sized_ref_mime = fit_image_to_budget(
                ref_bytes, ref_mime, max_dim=1100, max_b64_chars=900_000
            )
            ref_images.append((sized_ref, sized_ref_mime))
            gt_label = (
                "Correct extraction for the reference"
                if len(references) == 1
                else f"Correct extraction for reference #{idx}"
            )
            gt_blocks.append(f"{gt_label}:\n{ref_gt}")
        prompt = "\n\n".join(gt_blocks) + "\n\n---\n\nNow extract the NEW scorecard below:\n" + EXTRACTION_PROMPT
    else:
        prompt = EXTRACTION_PROMPT

    prompt += expected_players_suffix(expected_players)
    if strict:
        prompt += _STRICT_SUFFIX
    if bad_holes:
        prompt += bad_holes_suffix(bad_holes)
    return prompt, ref_images


def parse_vision_json(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.rsplit("```", 1)[0].strip()
    if not text.startswith("{"):
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last > first:
            text = text[first : last + 1]
    return json.loads(text)
