#!/usr/bin/env python3
"""Refresh the legacy-players seed from the live tee-sheet dropdown.

The canonical roster mirrors the player ``<select>`` dropdown on Jeff Green's
legacy tee sheet (thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi). That
dropdown is the source of truth for who can sign up. This script re-reads it and
rewrites backend/app/data/legacy_players.json (the cold-start seed / read
fallback for the DB-backed roster).

Usage:
    python scripts/development/refresh_legacy_players_seed.py            # fetch live
    python scripts/development/refresh_legacy_players_seed.py --html-file page.html
    python scripts/development/refresh_legacy_players_seed.py --dry-run  # show diff only

The live DB roster also auto-reconciles from round history every 2h; this seed
is what a fresh database starts from, so refreshing it keeps cold starts current.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path

CGI_URL = "https://thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi"
SEED_PATH = Path(__file__).resolve().parents[2] / "backend" / "app" / "data" / "legacy_players.json"

# Player <select> blocks, then option values within them. The dropdown's option
# value IS the canonical player name (value="Aaron Foster").
_SELECT_RE = re.compile(r"<select[^>]*name=[\"']?\w*player\w*[\"']?[^>]*>(.*?)</select>", re.IGNORECASE | re.DOTALL)
_OPTION_RE = re.compile(r"<option[^>]*value=[\"']([^\"']*)[\"'][^>]*>", re.IGNORECASE)


def extract_players(html: str) -> list[str]:
    """Return the sorted, de-duplicated player names from the dropdown(s)."""
    names: dict[str, str] = {}  # lower -> canonical, dedup case-insensitively, keep first casing
    blocks = _SELECT_RE.findall(html)
    if not blocks:
        raise SystemExit("No player <select> dropdown found in the page — layout may have changed.")
    for block in blocks:
        for value in _OPTION_RE.findall(block):
            name = value.strip()
            if not name:  # the "Select Player..." placeholder
                continue
            names.setdefault(name.lower(), name)
    return sorted(names.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html-file", help="parse a saved HTML file instead of fetching live")
    parser.add_argument("--dry-run", action="store_true", help="print the diff but do not write")
    args = parser.parse_args()

    if args.html_file:
        html = Path(args.html_file).read_text()
    else:
        with urllib.request.urlopen(CGI_URL, timeout=30) as resp:  # noqa: S310 (trusted league URL)
            html = resp.read().decode("utf-8", errors="replace")

    players = extract_players(html)

    existing = json.loads(SEED_PATH.read_text()) if SEED_PATH.exists() else {"players": []}
    old = set(existing.get("players", []))
    new = set(players)
    added = sorted(new - old)
    removed = sorted(old - new)

    print(f"Current seed: {len(old)} players (last_updated {existing.get('last_updated', '?')})")
    print(f"Dropdown now: {len(players)} players")
    print(f"Added ({len(added)}): {', '.join(added) or '(none)'}")
    print(f"Removed ({len(removed)}): {', '.join(removed) or '(none)'}")

    if args.dry_run:
        print("\n--dry-run: seed file not written.")
        return 0
    if not added and not removed:
        print("\nNo change — seed already current.")
        return 0

    payload = {
        "source": CGI_URL,
        "last_updated": datetime.date.today().isoformat(),
        "players": players,
    }
    SEED_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nWrote {len(players)} players to {SEED_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
