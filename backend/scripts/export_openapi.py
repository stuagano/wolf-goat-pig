#!/usr/bin/env python3
"""Export the FastAPI app's OpenAPI schema to a stable JSON file.

This makes the API contract an explicit, version-controlled artifact rather
than something that only exists at runtime on ``/openapi.json``. The committed
spec (``backend/openapi.json``) is the source of truth the frontend generates
its types from, and CI regenerates it to fail on drift (see the
``openapi-contract`` workflow).

Usage:
    python scripts/export_openapi.py            # write backend/openapi.json
    python scripts/export_openapi.py --check     # exit 1 if the file is stale
    python scripts/export_openapi.py --stdout    # print to stdout

Run from the ``backend/`` directory (so ``app`` is importable).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# The backend package root (parent of scripts/). Ensure it is importable
# regardless of the current working directory — running a script only puts the
# script's own directory on sys.path, not the backend root where ``app`` lives.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Default output path: backend/openapi.json.
DEFAULT_OUTPUT = BACKEND_ROOT / "openapi.json"


def build_spec() -> dict:
    """Build the OpenAPI schema from the FastAPI app.

    Imported lazily so ``--help`` works without the full app import cost.
    """
    from app.main import app

    return app.openapi()


def serialize(spec: dict) -> str:
    """Deterministic JSON so the committed file diffs cleanly across runs."""
    return json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write the spec to (default: backend/openapi.json).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write; exit non-zero if the committed spec is out of date.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write the spec to stdout instead of a file.",
    )
    args = parser.parse_args()

    rendered = serialize(build_spec())

    if args.stdout:
        sys.stdout.write(rendered)
        return 0

    if args.check:
        if not args.output.exists():
            print(f"❌ {args.output} does not exist — run scripts/export_openapi.py", file=sys.stderr)
            return 1
        current = args.output.read_text(encoding="utf-8")
        if current != rendered:
            print(
                f"❌ {args.output} is out of date with the app's routes/schemas.\n"
                "   Regenerate it with: python scripts/export_openapi.py",
                file=sys.stderr,
            )
            return 1
        print(f"✅ {args.output} is in sync with the app.")
        return 0

    args.output.write_text(rendered, encoding="utf-8")
    print(f"✅ Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
