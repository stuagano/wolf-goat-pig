#!/usr/bin/env python3
"""Audit (and optionally repair) player signup identities — issue #319.

Background: during July 2026 testing, Brett Saks and Jeff Green were both
treated as "Steve" and Steve's name was written to the live tee sheet. The
client-controlled signup-identity bug was fixed in ae6a0cb (identity is now
derived from the authenticated server profile), but existing profile links and
erroneous tee-sheet / DailySignup rows may still need cleanup.

This script is READ-ONLY by default. It connects to whatever database
``backend.app.database`` is configured for (set ``DATABASE_URL`` to point at
production), and reports:

  * each PlayerProfile matching the audited names/emails, with its legacy_name
  * profiles that SHARE a legacy_name (the classic "everyone is Steve" symptom)
  * profiles whose legacy_name is not a canonical roster name
  * DailySignup rows whose player_name disagrees with the owning profile's
    legacy_name (a signup attributed to the wrong golfer)

Examples::

    # Report against production (read-only)
    DATABASE_URL=postgres://... python scripts/diagnostics/audit_signup_identities.py

    # Narrow to specific names
    python scripts/diagnostics/audit_signup_identities.py --names "Brett Saks" "Jeff Green" "Steve Sutorius"

    # Repair one profile's legacy_name (writes; requires --yes)
    python scripts/diagnostics/audit_signup_identities.py --set-legacy-name 42="Brett Saks" --yes

The repair path never merges distinct users — it only rewrites a single
profile's legacy_name, validated against the canonical roster.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.database import SessionLocal  # noqa: E402
from backend.app.models import DailySignup, PlayerProfile  # noqa: E402
from backend.app.services.legacy_player_service import get_canonical_name  # noqa: E402

DEFAULT_NAMES = ["Brett Saks", "Jeff Green", "Steve Sutorius"]


def _match(profile: PlayerProfile, needles: list[str]) -> bool:
    hay = " ".join(str(x or "").lower() for x in (profile.name, profile.email, profile.legacy_name))
    return any(n.lower() in hay for n in needles)


def audit(names: list[str]) -> int:
    """Print the audit report. Returns the number of anomalies found."""
    db = SessionLocal()
    anomalies = 0
    try:
        profiles = db.query(PlayerProfile).all()
        matched = [p for p in profiles if _match(p, names)]

        print("=" * 72)
        print(f"AUDITED PROFILES (matching {names})")
        print("=" * 72)
        if not matched:
            print("  (no matching profiles found)")
        for p in matched:
            canonical = get_canonical_name(p.legacy_name, db) if p.legacy_name else None
            flag = ""
            if p.legacy_name and canonical is None:
                flag = "  <-- legacy_name NOT in canonical roster"
                anomalies += 1
            print(f"  id={p.id:<5} name={p.name!r:<24} email={p.email!r:<32} legacy_name={p.legacy_name!r}{flag}")

        # Profiles sharing a legacy_name — the "everyone is Steve" symptom.
        by_legacy: dict[str, list[PlayerProfile]] = {}
        for p in profiles:
            if p.legacy_name:
                by_legacy.setdefault(p.legacy_name.lower(), []).append(p)
        shared = {k: v for k, v in by_legacy.items() if len(v) > 1}
        print("\n" + "=" * 72)
        print("LEGACY NAMES SHARED BY MULTIPLE PROFILES (should normally be unique)")
        print("=" * 72)
        if not shared:
            print("  (none — every legacy_name maps to at most one profile)")
        for legacy, ps in sorted(shared.items()):
            anomalies += 1
            ids = ", ".join(f"id={p.id}({p.email})" for p in ps)
            print(f"  {ps[0].legacy_name!r}: {ids}")

        # DailySignup rows whose player_name disagrees with the profile link.
        print("\n" + "=" * 72)
        print("SIGNUPS WHOSE player_name DISAGREES WITH THE OWNING PROFILE")
        print("=" * 72)
        profile_by_id = {p.id: p for p in profiles}
        mismatches = 0
        for s in db.query(DailySignup).all():
            owner = profile_by_id.get(s.player_profile_id)
            if owner is None:
                continue
            expected = owner.legacy_name or owner.name
            if expected and s.player_name and s.player_name.lower() != expected.lower():
                mismatches += 1
                anomalies += 1
                print(
                    f"  signup id={s.id} date={s.date} player_name={s.player_name!r} "
                    f"but profile id={owner.id} legacy_name={owner.legacy_name!r}"
                )
        if not mismatches:
            print("  (none — every signup matches its profile's linked name)")

        print("\n" + "=" * 72)
        print(f"DONE. {anomalies} anomaly(ies) found.")
        print("=" * 72)
        return anomalies
    finally:
        db.close()


def repair_legacy_name(spec: str, confirmed: bool) -> None:
    """Rewrite a single profile's legacy_name. spec is 'ID=Canonical Name'."""
    try:
        raw_id, _, raw_name = spec.partition("=")
        profile_id = int(raw_id.strip())
        new_name = raw_name.strip().strip('"').strip("'")
    except ValueError:
        raise SystemExit(f"--set-legacy-name expects ID=\"Name\", got {spec!r}")

    db = SessionLocal()
    try:
        canonical = get_canonical_name(new_name, db)
        if canonical is None:
            raise SystemExit(f"{new_name!r} is not a canonical roster name; refusing to write.")
        profile = db.query(PlayerProfile).filter(PlayerProfile.id == profile_id).first()
        if profile is None:
            raise SystemExit(f"No profile with id={profile_id}")
        print(f"profile id={profile_id}: legacy_name {profile.legacy_name!r} -> {canonical!r}")
        if not confirmed:
            print("  (dry run — pass --yes to apply)")
            return
        profile.legacy_name = canonical
        db.commit()
        print("  applied.")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit/repair player signup identities (issue #319).")
    parser.add_argument("--names", nargs="*", default=DEFAULT_NAMES, help="Name/email substrings to audit.")
    parser.add_argument("--set-legacy-name", metavar='ID="Name"', help="Repair one profile's legacy_name.")
    parser.add_argument("--yes", action="store_true", help="Actually apply a --set-legacy-name repair.")
    args = parser.parse_args()

    if args.set_legacy_name:
        repair_legacy_name(args.set_legacy_name, args.yes)
        return

    anomalies = audit(args.names)
    sys.exit(1 if anomalies else 0)


if __name__ == "__main__":
    main()
