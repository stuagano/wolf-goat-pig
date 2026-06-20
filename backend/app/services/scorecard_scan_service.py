"""
Scorecard Photo Scan Service

Uses Groq Vision (Llama 4 Scout) to extract running quarter totals
from a photo of a physical Wolf Goat Pig scorecard. Circles = negative values.
"""

import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import httpx

from .scorecard_preprocess import annotate_circles, crop_to_grid, deskew_to_card

logger = logging.getLogger(__name__)

_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
_GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

# Path to reference scorecard examples for few-shot prompting
_EXAMPLES_DIR = Path(__file__).parent.parent / "data" / "scorecard_examples"


def _norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _expected_players_suffix(expected_players: list[str] | None) -> str:
    if not expected_players:
        return ""
    names = ", ".join(expected_players)
    return (
        f"\n\nThe scorers are KNOWN: expect exactly {len(expected_players)} players "
        f"named: {names}. Use these exact names (one row each). Some players may be "
        f"written in a lower band below the Par row — include them. Ignore any "
        f"golf-score rows and handwritten notes; only read the quarter running totals."
    )


def _missing_expected(result: dict, expected_players: list[str] | None) -> list[str]:
    if not expected_players:
        return []
    found = {_norm_name(p.get("name", "")) for p in result.get("players", [])}
    return [n for n in expected_players if _norm_name(n) not in found]


def _load_reference_examples() -> list[tuple[bytes, str, str]]:
    """Load few-shot reference scorecards for prompting: (image bytes, mime, ground-truth JSON text).

    Any ``example_<name>.{jpeg,jpg,png}`` in the examples dir that has a matching
    ``example_<name>_ground_truth.json`` is used, sorted by name for a stable
    prompt. Drop a new card pair here to improve calibration. (The held-out
    accuracy fixture lives under ``tests/live/data`` and is deliberately NOT a
    reference, so the eval never tests on its own training data.)
    """
    examples: list[tuple[bytes, str, str]] = []
    seen: set[str] = set()
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


# Groq Vision caps a request at ~4MB. We spend that budget across the (small)
# reference image(s) + the main scorecard, maximizing the MAIN image's
# resolution so the dense handwritten cells on a ~4000px phone pic stay legible
# (downscaling the whole card to ~1800px made them unreadable).
_GROQ_REQUEST_B64_BUDGET = 3_900_000  # total base64 chars for all images in one request
_REFERENCE_MAX_DIM = 1100  # references only calibrate handwriting style — don't need full res
_REFERENCE_B64_BUDGET = 900_000
_MAIN_MAX_DIM = 4096  # effectively only budget-limited
# Cap the working image BEFORE the classical CV preprocessing (Hough circle
# detection, corner/grid detection) — those run at full resolution and are
# far too slow on a raw ~4000px phone pic (the scan would hang). The model
# still receives this size, which is already plenty more legible than the old
# 1800px. Going meaningfully higher needs tiled per-region scanning, not a
# bigger whole-card image.
_PREPROCESS_MAX_DIM = 2048


def _fit_image_to_budget(
    image_bytes: bytes, content_type: str, *, max_dim: int, max_b64_chars: int
) -> tuple[bytes, str]:
    """Re-encode an image to the HIGHEST resolution that still fits a base64 char
    budget and a max longest-side. Degrades gracefully: returns the original bytes
    unchanged if PIL can't read them (e.g. the ``b"fake"`` stub in unit tests)."""
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


def _split_horizontal_halves(
    image_bytes: bytes, content_type: str
) -> tuple[tuple[bytes, str], tuple[bytes, str]] | None:
    """Split an image at width/2 into (left, right) JPEGs. None if unreadable."""
    try:
        from io import BytesIO

        from PIL import Image

        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        w, h = img.size
        mid = w // 2

        def _enc(box):
            buf = BytesIO()
            img.crop(box).save(buf, format="JPEG", quality=85)
            return buf.getvalue()

        return (_enc((0, 0, mid, h)), "image/jpeg"), (_enc((mid, 0, w, h)), "image/jpeg")
    except Exception:
        return None


async def _call_groq_vision(
    image_bytes: bytes,
    content_type: str,
    *,
    strict: bool = False,
    expected_players: list[str] | None = None,
    hole_range: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """One round-trip to Groq Vision. Strict mode tightens the prompt and lowers temp."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured")

    user_content: list[dict[str, Any]] = []

    references = _load_reference_examples()
    ref_b64_used = 0
    if references:
        gt_blocks = []
        for idx, (ref_bytes, ref_mime, ref_gt) in enumerate(references, 1):
            sized_ref, sized_ref_mime = _fit_image_to_budget(
                ref_bytes, ref_mime, max_dim=_REFERENCE_MAX_DIM, max_b64_chars=_REFERENCE_B64_BUDGET
            )
            ref_b64 = base64.b64encode(sized_ref).decode("utf-8")
            ref_b64_used += len(ref_b64)
            label = "REFERENCE SCORECARD" if len(references) == 1 else f"REFERENCE SCORECARD #{idx}"
            user_content.append({"type": "text", "text": f"{label} — study the handwriting style:"})
            user_content.append({"type": "image_url", "image_url": {"url": f"data:{sized_ref_mime};base64,{ref_b64}"}})
            gt_label = (
                "Correct extraction for the reference"
                if len(references) == 1
                else f"Correct extraction for reference #{idx}"
            )
            gt_blocks.append(f"{gt_label}:\n{ref_gt}")
        prompt = "\n\n".join(gt_blocks) + "\n\n---\n\nNow extract the NEW scorecard below:\n" + EXTRACTION_PROMPT
    else:
        prompt = EXTRACTION_PROMPT
    prompt += _expected_players_suffix(expected_players)
    if hole_range:
        lo, hi = hole_range
        half = "FRONT nine" if lo == 1 else "BACK nine"
        prompt += (
            f"\n\nThis image is the {half} only. Read running totals for holes "
            f"{lo} through {hi} only; do not invent other holes."
        )
    if strict:
        prompt += _STRICT_SUFFIX

    # Give the main scorecard the entire remaining request budget so it goes in
    # at the highest resolution that fits — that detail is what makes the cells readable.
    main_budget = max(600_000, _GROQ_REQUEST_B64_BUDGET - ref_b64_used - len(prompt) - 4000)
    main_bytes, main_ct = _fit_image_to_budget(
        image_bytes, content_type, max_dim=_MAIN_MAX_DIM, max_b64_chars=main_budget
    )
    image_b64 = base64.b64encode(main_bytes).decode("utf-8")

    user_content.append({"type": "text", "text": prompt})
    user_content.append({"type": "image_url", "image_url": {"url": f"data:{main_ct};base64,{image_b64}"}})

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


def _merge_tile_results(expected_players: list[str], left_raw: dict, right_raw: dict) -> dict:
    """Combine left (holes 1-9) and right (holes 10-18) raw extractions into one
    raw extraction keyed by the player's position in expected_players."""
    exp_index = {_norm_name(n): i for i, n in enumerate(expected_players)}
    unified = [{"name": n, "confidence": 1.0} for n in expected_players]
    merged: list[dict] = []
    for raw, lo, hi in ((left_raw, 1, 9), (right_raw, 10, 18)):
        tile_players = raw.get("players", []) if raw else []
        idx_map: dict[int, int] = {}
        for ti, tp in enumerate(tile_players):
            ei = exp_index.get(_norm_name(tp.get("name", "")))
            if ei is None and ti < len(expected_players):
                ei = ti  # positional fallback
            if ei is not None:
                idx_map[ti] = ei
        for rt in raw.get("running_totals", []) if raw else []:
            if not (lo <= rt.get("hole", 0) <= hi):
                continue
            ei = idx_map.get(rt.get("player_index"))
            if ei is None:
                continue
            merged.append({**rt, "player_index": ei})
    return {"players": unified, "running_totals": merged}


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
            per_hole_quarters.append({"player_index": player_index, "hole": d["hole"], "quarters": d["quarters"]})

    return {
        "players": players,
        "running_totals": raw_totals,
        "per_hole_quarters": per_hole_quarters,
    }


async def scan_scorecard(
    image_bytes: bytes, content_type: str, expected_players: list[str] | None = None
) -> dict[str, Any]:
    """Single guided Groq call; if it fails zero-sum or is missing an expected
    player, fall back to a tiled (left=holes 1-9 / right=holes 10-18) scan and
    merge by player. Returns the usual shape plus result["method"]."""
    # Cap working size before the (full-res) CV preprocessing — see _PREPROCESS_MAX_DIM.
    image_bytes, content_type = _fit_image_to_budget(
        image_bytes, content_type, max_dim=_PREPROCESS_MAX_DIM, max_b64_chars=10**12
    )
    deskewed_bytes, deskewed_ct, deskew_diag = deskew_to_card(image_bytes, content_type)
    cropped_bytes, cropped_ct, grid_diag = crop_to_grid(deskewed_bytes, deskewed_ct)
    annotated_bytes, annotated_ct, circle_diag = annotate_circles(cropped_bytes, cropped_ct)
    preprocessing_diag = {"deskew": deskew_diag, "grid_crop": grid_diag, "circles": circle_diag}

    def _finalize(raw: dict, method: str) -> dict:
        out = _shape_extraction(raw)
        out["validation"] = _validate_zero_sum(out["per_hole_quarters"])
        out["preprocessing"] = preprocessing_diag
        out["method"] = method
        return out

    # ---- single guided attempt (with one strict retry on bad JSON) ----
    try:
        single_raw = await _call_groq_vision(
            annotated_bytes, annotated_ct, strict=False, expected_players=expected_players
        )
    except json.JSONDecodeError:
        try:
            single_raw = await _call_groq_vision(
                annotated_bytes, annotated_ct, strict=True, expected_players=expected_players
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse vision response: {e}")

    single = _finalize(single_raw, "single")
    if single["validation"]["valid"] and not _missing_expected(single_raw, expected_players):
        return single

    # ---- tiled fallback ----
    halves = _split_horizontal_halves(deskewed_bytes, deskewed_ct)
    if not halves:
        return single  # can't tile — return best single attempt
    (left_b, left_ct), (right_b, right_ct) = halves
    try:
        left_b, left_ct, _ = annotate_circles(left_b, left_ct)
        right_b, right_ct, _ = annotate_circles(right_b, right_ct)
        left_raw = await _call_groq_vision(left_b, left_ct, expected_players=expected_players, hole_range=(1, 9))
        right_raw = await _call_groq_vision(right_b, right_ct, expected_players=expected_players, hole_range=(10, 18))
        merged_raw = _merge_tile_results(expected_players or [], left_raw, right_raw)
        tiled = _finalize(merged_raw, "tiled")
    except Exception as e:
        logger.warning("Tiled scan failed (%s); using single-call result", e)
        return single

    # Keep whichever attempt is balanced; prefer tiled when both/neither are.
    if tiled["validation"]["valid"] or not single["validation"]["valid"]:
        return tiled
    return single
