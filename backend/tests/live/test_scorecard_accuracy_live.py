"""Live accuracy eval for the scorecard scanner against a known 5-man card.

FRONT NINE ONLY (back nine excluded — unusual betting). Hits the real Groq
Vision API (read-only, costs tokens, non-deterministic), so it's an on-demand
eval rather than a CI unit test — it SKIPS unless GROQ_API_KEY is set.

It scans the fixture card, aligns the extracted players to the ground truth by
name, scores each front-nine cell (signed running total), prints a full per-cell
diff, and asserts a conservative accuracy floor so a catastrophic regression
fails loudly while the inherently-hard card doesn't flake.
"""

import asyncio
import json
import re
from pathlib import Path

import pytest

from app.services.scorecard_scan_service import scan_scorecard
from tests.live._helpers import require_env

pytestmark = pytest.mark.live

_DATA = Path(__file__).parent / "data"
_IMAGE = _DATA / "scorecard_5man_001.jpeg"
_GROUND_TRUTH = _DATA / "scorecard_5man_001_ground_truth.json"

# Conservative front-nine cell-accuracy floor for this hard, low-res 5-man card.
# Tighten once real numbers are observed; the printed diff is the primary value.
_ACCURACY_FLOOR = 0.5


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _signed(entry: dict) -> int:
    value = abs(entry["value"])
    return -value if entry.get("is_circled") else value


def test_scorecard_scan_front_nine_accuracy():
    require_env("GROQ_API_KEY")
    ground_truth = json.loads(_GROUND_TRUTH.read_text())
    image_bytes = _IMAGE.read_bytes()

    result = asyncio.run(scan_scorecard(image_bytes, "image/jpeg"))

    scan_names = {i: _norm(p.get("name", "")) for i, p in enumerate(result.get("players", []))}
    scan_signed = {(e["player_index"], e["hole"]): _signed(e) for e in result.get("running_totals", [])}

    gt_names = {i: _norm(p["name"]) for i, p in enumerate(ground_truth["players"])}
    gt_signed = {(e["player_index"], e["hole"]): _signed(e) for e in ground_truth["running_totals"]}
    holes = ground_truth["holes_covered"]

    def match_scan_index(gt_norm: str):
        for si, sn in scan_names.items():
            if sn == gt_norm:
                return si
        for si, sn in scan_names.items():
            if sn and (sn in gt_norm or gt_norm in sn):
                return si
        return None

    total = 0
    correct = 0
    lines = []
    for gi, gnorm in gt_names.items():
        si = match_scan_index(gnorm)
        lines.append(
            f"  {ground_truth['players'][gi]['name']} -> scan[{si}] ({'matched' if si is not None else 'NO MATCH'})"
        )
        for h in holes:
            total += 1
            expected = gt_signed[(gi, h)]
            got = scan_signed.get((si, h)) if si is not None else None
            if got == expected:
                correct += 1
            else:
                lines.append(f"      h{h}: expected {expected:+d}, got {got}")

    accuracy = correct / total if total else 0.0
    report = (
        f"\nScorecard front-nine accuracy: {correct}/{total} = {accuracy:.0%}\n"
        "Player mapping + cell misses:\n" + "\n".join(lines) + "\n"
    )
    print(report)

    assert accuracy >= _ACCURACY_FLOOR, report
