#!/usr/bin/env python3
"""
Scorecard scan evaluation harness.

Runs the scorecard scan pipeline against a directory of fixture images
with ground-truth JSON, and reports cell-level accuracy. Use this to
validate preprocessing changes (Hough param tweaks, prompt edits) don't
regress accuracy.

Usage:
    cd backend
    python scripts/eval_scorecard_scan.py [fixtures_dir]

If fixtures_dir is omitted, defaults to backend/tests/fixtures/scorecard_scans/,
falling back to backend/app/data/scorecard_examples/.

Each fixture is a pair: <name>.{jpeg,jpg,png} + <name>_ground_truth.json.
Ground truth JSON has the same shape as scan_scorecard() output:
{"players": [...], "running_totals": [{player_index, hole, value, is_circled}, ...]}.

Hits the real Groq Vision API — costs $$ per run. Not a unit test.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.scorecard_scan_service import scan_scorecard  # noqa: E402


def load_fixtures(directory: Path) -> list[tuple[Path, Path]]:
    pairs: list[tuple[Path, Path]] = []
    for ext in ("jpeg", "jpg", "png"):
        for img in sorted(directory.glob(f"*.{ext}")):
            gt = directory / f"{img.stem}_ground_truth.json"
            if gt.exists():
                pairs.append((img, gt))
    return pairs


def compare_cells(extracted: dict, ground_truth: dict) -> dict:
    gt_cells = {
        (e["player_index"], e["hole"]): e
        for e in ground_truth.get("running_totals", [])
    }
    ex_cells = {
        (e["player_index"], e["hole"]): e
        for e in extracted.get("running_totals", [])
    }

    correct = 0
    wrong_value = 0
    wrong_circle = 0
    missing = 0
    mismatches: list[dict] = []

    for key, gt_entry in gt_cells.items():
        if key not in ex_cells:
            missing += 1
            mismatches.append({"cell": key, "kind": "missing"})
            continue
        ex = ex_cells[key]
        gt_signed = -abs(gt_entry["value"]) if gt_entry.get("is_circled") else gt_entry["value"]
        ex_signed = ex["value"]  # service already applied sign in _shape_extraction
        if ex_signed == gt_signed:
            correct += 1
            continue
        if abs(ex_signed) != abs(gt_entry["value"]):
            wrong_value += 1
            mismatches.append(
                {"cell": key, "kind": "value", "expected": gt_signed, "got": ex_signed}
            )
        else:
            wrong_circle += 1
            mismatches.append(
                {"cell": key, "kind": "circle", "expected": gt_signed, "got": ex_signed}
            )

    return {
        "total": len(gt_cells),
        "correct": correct,
        "wrong_value": wrong_value,
        "wrong_circle": wrong_circle,
        "missing": missing,
        "mismatches": mismatches,
    }


def content_type_for(path: Path) -> str:
    return "image/png" if path.suffix.lower() == ".png" else "image/jpeg"


async def evaluate(fixtures: list[tuple[Path, Path]]) -> list[dict]:
    results: list[dict] = []
    for img_path, gt_path in fixtures:
        print(f"\n=== {img_path.stem} ===")
        image_bytes = img_path.read_bytes()
        ground_truth = json.loads(gt_path.read_text())

        try:
            extracted = await scan_scorecard(image_bytes, content_type_for(img_path))
        except Exception as e:
            print(f"  scan failed: {e}")
            results.append({"fixture": img_path.stem, "error": str(e)})
            continue

        gt_names = [p["name"].lower().strip() for p in ground_truth.get("players", [])]
        ex_names = [p["name"].lower().strip() for p in extracted.get("players", [])]
        names_match = gt_names == ex_names
        print(f"  Players: {ex_names}")
        if not names_match:
            print(f"    expected: {gt_names}")

        cells = compare_cells(extracted, ground_truth)
        acc = (cells["correct"] / cells["total"] * 100) if cells["total"] else 0
        print(f"  Cells: {cells['correct']}/{cells['total']} ({acc:.1f}%)")
        if cells["wrong_value"]:
            print(f"    wrong value: {cells['wrong_value']}")
        if cells["wrong_circle"]:
            print(f"    wrong circle: {cells['wrong_circle']}")
        if cells["missing"]:
            print(f"    missing: {cells['missing']}")
        for m in cells["mismatches"][:10]:
            print(f"    {m}")
        if len(cells["mismatches"]) > 10:
            print(f"    ... +{len(cells['mismatches']) - 10} more")

        validation = extracted.get("validation", {})
        if validation.get("valid"):
            print("  Zero-sum: pass")
        else:
            bad = validation.get("bad_holes", {})
            print(f"  Zero-sum: FAIL holes={sorted(bad.keys())}")

        preproc = extracted.get("preprocessing", {})
        deskew = preproc.get("deskew", {})
        circles = preproc.get("circles", {})
        print(
            f"  Preprocessing: deskew={deskew.get('deskew_applied', False)} "
            f"circles={circles.get('circles_detected', '?')} "
            f"annotated={circles.get('preprocessing_applied', False)}"
        )

        results.append(
            {
                "fixture": img_path.stem,
                "cells": cells,
                "names_match": names_match,
                "validation": validation,
                "preprocessing": preproc,
            }
        )
    return results


def print_aggregate(results: list[dict]) -> None:
    runnable = [r for r in results if "cells" in r]
    if not runnable:
        print("\n=== Aggregate ===\nNo fixtures evaluated successfully.")
        return
    total = sum(r["cells"]["total"] for r in runnable)
    correct = sum(r["cells"]["correct"] for r in runnable)
    zs_pass = sum(1 for r in runnable if r["validation"].get("valid"))
    names_pass = sum(1 for r in runnable if r["names_match"])
    print("\n=== Aggregate ===")
    print(f"Fixtures evaluated:  {len(runnable)}/{len(results)}")
    print(f"Cell accuracy:       {correct}/{total} ({correct/total*100:.1f}%)")
    print(f"Zero-sum passing:    {zs_pass}/{len(runnable)}")
    print(f"Player names match:  {names_pass}/{len(runnable)}")


async def main() -> int:
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])
    else:
        primary = backend_dir / "tests" / "fixtures" / "scorecard_scans"
        fallback = backend_dir / "app" / "data" / "scorecard_examples"
        directory = primary if primary.exists() and any(primary.iterdir()) else fallback

    if not directory.exists():
        print(f"Fixtures directory not found: {directory}", file=sys.stderr)
        return 1

    fixtures = load_fixtures(directory)
    if not fixtures:
        print(f"No fixtures (image + *_ground_truth.json) found in {directory}", file=sys.stderr)
        return 1

    print(f"Evaluating {len(fixtures)} fixture(s) from {directory}")
    results = await evaluate(fixtures)
    print_aggregate(results)

    runnable = [r for r in results if "cells" in r]
    if not runnable:
        return 1
    total = sum(r["cells"]["total"] for r in runnable)
    correct = sum(r["cells"]["correct"] for r in runnable)
    return 0 if total and correct / total >= 0.85 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
