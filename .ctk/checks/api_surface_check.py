"""API surface-drift check (caps).

Builds the live set of (METHOD, path) operations from the FastAPI app and
compares it to a committed baseline. Fails if any baseline endpoint is missing
(removed or renamed) — the "the API silently shrank" guard. New endpoints are
fine; regenerate the baseline with --update when a removal is intentional.

Run from the backend dir with backend on the path:
    cd backend && PYTHONPATH=. venv/bin/python ../.ctk/checks/api_surface_check.py
    (add --update to (re)write the baseline)

Exit 0 = no drift, 1 = endpoints removed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("ENVIRONMENT", "test")

from app.main import app  # noqa: E402

_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def operations() -> list[str]:
    ops = set()
    for route in app.routes:
        methods = getattr(route, "methods", None) or set()
        path = getattr(route, "path", None)
        if not path:
            continue
        for m in methods:
            if m in _METHODS:
                ops.add(f"{m} {path}")
    return sorted(ops)


def main() -> int:
    baseline_path = Path(__file__).resolve().parent / "api_surface_baseline.json"
    current = operations()

    if "--update" in sys.argv or not baseline_path.exists():
        baseline_path.write_text(json.dumps(current, indent=2) + "\n")
        print(f"baseline written: {len(current)} operations -> {baseline_path.name}")
        return 0

    baseline = json.loads(baseline_path.read_text())
    cur, base = set(current), set(baseline)
    missing = sorted(base - cur)
    added = sorted(cur - base)

    if missing:
        print(f"API SURFACE DRIFT — {len(missing)} endpoint(s) REMOVED/renamed:")
        for op in missing:
            print(f"  - {op}")
        if added:
            print(f"  ({len(added)} added; if the removal is intended, regenerate: "
                  f"... api_surface_check.py --update)")
        return 1

    msg = f"OK: all {len(base)} baseline operations present"
    if added:
        msg += f" (+{len(added)} new — baseline still valid)"
    print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
