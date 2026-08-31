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

  * each matching profile, including missing email/Auth0/legacy-name evidence
  * duplicate email/Auth0 identities (without printing Auth0 subjects)
  * profiles that SHARE a legacy_name (the classic "everyone is Steve" symptom)
  * profiles whose legacy_name is not a canonical roster name
  * orphan/misattributed DailySignup rows, plus all signups for audited players

Missing links and name mismatches are investigation leads, NOT proof of a
test signup or of the correct account owner. This script never changes Auth0
subjects, emails, signup rows, or the external tee sheet.

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
from backend.app.services.legacy_player_service import (  # noqa: E402
    get_canonical_name,
    is_canonical_name_claimed,
    link_profile_to_canonical_name,
)

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
        for name in names:
            if not any(_match(p, [name]) for p in profiles):
                print(f"  {name!r}: no matching profile — identity unverified")
                anomalies += 1
        for p in matched:
            canonical = get_canonical_name(p.legacy_name, db) if p.legacy_name else None
            flag = ""
            if p.legacy_name and canonical is None:
                flag = "  <-- legacy_name NOT in canonical roster"
                anomalies += 1
            canonical_profile_name = get_canonical_name(p.name, db) if p.name else None
            if canonical and canonical_profile_name and canonical != canonical_profile_name:
                flag += "  <-- legacy_name disagrees with canonical profile name; investigate ownership"
                anomalies += 1
            auth0_id = (p.preferences or {}).get("auth0_id")
            missing = [
                key
                for key, value in (("legacy_name", p.legacy_name), ("email", p.email), ("auth0_id", auth0_id))
                if not value or not str(value).strip()
            ]
            if missing:
                flag += f"  <-- missing {', '.join(missing)}; identity unverified"
                anomalies += 1
            print(
                f"  id={p.id:<5} name={p.name!r:<24} email={p.email!r:<32} "
                f"legacy_name={p.legacy_name!r} auth0_id_present={bool(auth0_id)}{flag}"
            )

        for field in ("email", "auth0_id"):
            by_identity: dict[str, list[int]] = {}
            for p in profiles:
                value = p.email if field == "email" else (p.preferences or {}).get("auth0_id")
                if value:
                    # Email comparison is case-insensitive; Auth0 subjects are opaque.
                    key = value.strip().casefold() if field == "email" else value
                    by_identity.setdefault(key, []).append(p.id)
            for ids in by_identity.values():
                if len(ids) > 1:
                    anomalies += 1
                    print(f"  SHARED {field}: profile ids={ids}; ownership requires investigation")

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
        signups = db.query(DailySignup).order_by(DailySignup.id).all()
        for s in signups:
            owner = profile_by_id.get(s.player_profile_id)
            if owner is None:
                mismatches += 1
                anomalies += 1
                print(
                    f"  signup id={s.id} date={s.date} player_name={s.player_name!r} "
                    f"status={s.status!r}: missing profile id={s.player_profile_id}"
                )
                continue
            expected = owner.legacy_name or owner.name
            if expected and s.player_name and s.player_name.lower() != expected.lower():
                mismatches += 1
                anomalies += 1
                print(
                    f"  signup id={s.id} date={s.date} player_name={s.player_name!r} "
                    f"status={s.status!r} but profile id={owner.id} name={owner.name!r} "
                    f"legacy_name={owner.legacy_name!r}"
                )
        if not mismatches:
            print("  (none — every signup matches its profile's linked name)")

        print("\nSIGNUPS FOR AUDITED PLAYERS (including cancelled; not automatically test rows)")
        matched_ids = {p.id for p in matched}
        for s in signups:
            if s.player_profile_id in matched_ids or any(n.lower() in (s.player_name or "").lower() for n in names):
                print(
                    f"  signup id={s.id} date={s.date} player_name={s.player_name!r} "
                    f"profile id={s.player_profile_id} status={s.status!r} created_at={s.created_at!r}"
                )
        print("  Reconcile exact dates/rows with the live sheet and tester evidence before any cleanup.")

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
        raise SystemExit(f'--set-legacy-name expects ID="Name", got {spec!r}')

    db = SessionLocal()
    try:
        canonical = get_canonical_name(new_name, db)
        if canonical is None:
            raise SystemExit(f"{new_name!r} is not a canonical roster name; refusing to write.")
        profile = db.query(PlayerProfile).filter(PlayerProfile.id == profile_id).first()
        if profile is None:
            raise SystemExit(f"No profile with id={profile_id}")
        if is_canonical_name_claimed(db, canonical, exclude_profile_id=profile_id):
            raise SystemExit(f"{canonical!r} is already claimed by another profile; refusing to write.")
        print(f"profile id={profile_id}: legacy_name {profile.legacy_name!r} -> {canonical!r}")
        if not confirmed:
            print("  (dry run — pass --yes to apply)")
            return
        result = link_profile_to_canonical_name(db, profile_id, canonical, allow_relink=True)
        if not result["linked"]:
            raise SystemExit(f"Cannot repair profile id={profile_id}: {result['status']}")
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
