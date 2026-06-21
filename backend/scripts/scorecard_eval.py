"""Repeatable accuracy eval for the scorecard scanner (needs GROQ_API_KEY).

Runs the real production scan (scan_scorecard) N times and reports a VARIANCE
BAND, not a single sample — single prod scans are dominated by temp-0.3 noise.

Two cards, two metrics:
  * 5-man (hard) : front-nine per-hole CELL accuracy vs ground truth. Stays ~1-16%
    (model can't read dense circled handwriting) — review-and-correct does the work.
  * 4-man (clear): FINAL TOTALS only — the legible total column the model DOES read
    reliably, and the number that matters for settle-up.

Usage (key NOT echoed):
  GROQ_API_KEY=$(cat /path/to/keyfile) backend/venv/bin/python backend/scripts/scorecard_eval.py [N]
"""

import asyncio
import json
import re
import sys
import time
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))

from app.services.scorecard_scan_service import _PREPROCESS_MAX_DIM, scan_scorecard  # noqa: E402

_DATA = _BACKEND / "tests/live/data"
_IMAGE = _DATA / "scorecard_5man_001.jpeg"
_GT = json.loads((_DATA / "scorecard_5man_001_ground_truth.json").read_text())
_EXPECTED = [p["name"] for p in _GT["players"]]
_HOLES = _GT["holes_covered"]

# Clear 4-man card — graded on FINAL TOTALS only (the model reads the legible
# total column reliably even when it can't read the dense per-hole grid).
_IMAGE_4MAN = _DATA / "scorecard_4man_002.jpeg"
_FINALS_4MAN = json.loads((_DATA / "scorecard_4man_002_finaltotals.json").read_text())


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _signed(e):
    v = abs(e["value"])
    return -v if e.get("is_circled") else v


_GT_SIGNED = {(_norm(_GT["players"][e["player_index"]]["name"]), e["hole"]): _signed(e) for e in _GT["running_totals"]}


def _score(result):
    """Front-nine cell accuracy + players-found, aligning scan players to GT by name."""
    scan = {}
    names = {i: _norm(p.get("name", "")) for i, p in enumerate(result.get("players", []))}
    for e in result.get("running_totals", []):
        scan[(names.get(e["player_index"]), e["hole"])] = _signed(e)
    found = {_norm(n) for n in names.values()}
    correct = total = 0
    for n in (_norm(x) for x in _EXPECTED):
        for h in _HOLES:
            total += 1
            if scan.get((n, h)) == _GT_SIGNED[(n, h)]:
                correct += 1
    n_found = sum(1 for n in _EXPECTED if _norm(n) in found)
    return correct, total, n_found


def _final_per_player(result):
    """player_norm -> signed running total at that player's highest hole."""
    names = {i: _norm(p.get("name", "")) for i, p in enumerate(result.get("players", []))}
    last: dict = {}  # player_index -> (hole, signed)
    for e in result.get("running_totals", []):
        pi, h = e["player_index"], e["hole"]
        if pi not in last or h > last[pi][0]:
            last[pi] = (h, _signed(e))
    return {names.get(pi): sv for pi, (_, sv) in last.items()}


def _score_finals(result, final_totals):
    got = _final_per_player(result)
    correct = sum(1 for name, val in final_totals.items() if got.get(_norm(name)) == val)
    return correct, len(final_totals)


def _pct(c, t):
    return f"{c}/{t}={c / t:.0%}" if t else "n/a"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    image_bytes = _IMAGE.read_bytes()
    cells = []
    print(f"Eval: {n} runs on {_IMAGE.name} — per-hole CELLS (PREPROCESS_MAX_DIM={_PREPROCESS_MAX_DIM})\n")
    for i in range(1, n + 1):
        res = asyncio.run(scan_scorecard(image_bytes, "image/jpeg", expected_players=_EXPECTED))
        c, t, nf = _score(res)
        cells.append(c)
        print(
            f"run {i}: per-hole {_pct(c, t):>10} | players {nf}/{len(_EXPECTED)} "
            f"| method={res.get('method')} valid={res.get('validation', {}).get('valid')}"
        )
        time.sleep(8)  # ease Groq's per-minute limit between scans
    lo, hi, mean = min(cells), max(cells), sum(cells) / len(cells)
    print(f"\n--- 5-man per-hole CELLS: mean {mean:.1f}/45 ({mean / 45:.0%}) | range {lo}-{hi} | runs {cells} ---")

    # ---- clear 4-man card: FINAL TOTALS accuracy over N runs ----
    expected_4 = _FINALS_4MAN["players"]
    finals_gt = _FINALS_4MAN["final_totals"]
    img4 = _IMAGE_4MAN.read_bytes()
    finals_correct = []
    print(f"\nEval: {n} runs on {_IMAGE_4MAN.name} (graded on FINAL TOTALS only)\n")
    for i in range(1, n + 1):
        res = asyncio.run(scan_scorecard(img4, "image/jpeg", expected_players=expected_4))
        c, t = _score_finals(res, finals_gt)
        finals_correct.append(c)
        got = _final_per_player(res)
        print(f"run {i} 4-man finals: {c}/{t} correct | " + ", ".join(f"{p}={got.get(_norm(p))}" for p in expected_4))
        time.sleep(8)
    lo, hi, mean = min(finals_correct), max(finals_correct), sum(finals_correct) / len(finals_correct)
    print(f"\n--- 4-man FINAL TOTALS: mean {mean:.1f}/4 | range {lo}-{hi} | runs {finals_correct} ---")


if __name__ == "__main__":
    main()
