"""Repeatable accuracy eval for the scorecard scanner (needs GROQ_API_KEY).

Runs the held-out 5-man card through the real Groq Vision pipeline N times and
reports a VARIANCE BAND (not a single sample), measuring two configs head-to-head:

  * guided-single : one guided whole-card read (no correction, no tiling)
  * adaptive      : the full production scan_scorecard() (single -> correction -> tiled)

Front-nine cell accuracy is scored against the committed ground truth. Use this
to tell a real method gain from run-to-run noise, and to decide whether tiling
(now lower-res than the single read) still earns its extra calls.

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

from app.services.scorecard_preprocess import annotate_circles, crop_to_grid, deskew_to_card  # noqa: E402
from app.services.scorecard_scan_service import (  # noqa: E402
    _PREPROCESS_MAX_DIM,
    _call_groq_vision,
    _fit_image_to_budget,
    _shape_extraction,
    _validate_zero_sum,
    scan_scorecard,
)

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


async def _guided_single(image_bytes):
    b, ct = _fit_image_to_budget(image_bytes, "image/jpeg", max_dim=_PREPROCESS_MAX_DIM, max_b64_chars=10**12)
    db, dct, _ = deskew_to_card(b, ct)
    cb, cct, _ = crop_to_grid(db, dct)
    ab, act, _ = annotate_circles(cb, cct)
    raw = await _call_groq_vision(ab, act, expected_players=_EXPECTED)
    out = _shape_extraction(raw)
    out["validation"] = _validate_zero_sum(out["per_hole_quarters"])
    out["method"] = "guided-single"
    return out


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
    rows = {"guided-single": [], "adaptive": []}
    print(f"Eval: {n} runs/config on {_IMAGE.name} (PREPROCESS_MAX_DIM={_PREPROCESS_MAX_DIM})\n")
    for i in range(1, n + 1):
        for cfg, runner in (
            ("guided-single", lambda b: _guided_single(b)),
            ("adaptive", lambda b: scan_scorecard(b, "image/jpeg", expected_players=_EXPECTED)),
        ):
            res = asyncio.run(runner(image_bytes))
            c, t, nf = _score(res)
            rows[cfg].append(c)
            print(
                f"run {i} {cfg:>14}: acc {_pct(c, t):>10} | players {nf}/{len(_EXPECTED)} "
                f"| method={res.get('method')} valid={res.get('validation', {}).get('valid')}"
            )
            time.sleep(8)  # ease Groq's per-minute limit between scans
    print("\n--- summary (front-nine cells correct, of 45) ---")
    for cfg, vals in rows.items():
        lo, hi, mean = min(vals), max(vals), sum(vals) / len(vals)
        print(
            f"{cfg:>14}: mean {mean:.1f}/45 ({mean / 45:.0%}) | range {lo}-{hi} ({lo / 45:.0%}-{hi / 45:.0%}) | runs {vals}"
        )

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
