#!/usr/bin/env python3
"""Live CTK prove-it: multi-user daily signup on Cloud SQL + Cloud Run.

1. Authenticated POST /signups as N club-linked players (TestClient + auth override
   against live Cloud SQL — same create path as production).
2. claim_vs_reality: live Cloud Run GET /signups/weekly must show all names/ids.
3. Cleanup test rows and confirm they disappear from Cloud Run.

Does NOT hit thousand-cranes (legacy sync is monkeypatched off).

Usage:
  export DATABASE_URL=postgresql://...@127.0.0.1:PORT/wolf_goat_pig?sslmode=disable
  export API_BASE=https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app
  python scripts/live_multi_user_signup_check.py
"""

from __future__ import annotations

import os
import sys
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import DailySignup, PlayerProfile  # noqa: E402
from app.services.auth_service import get_current_user  # noqa: E402

TEST_WEEK_START = "2099-08-02"  # Monday
TEST_DATE = "2099-08-03"  # Tuesday
API_BASE = os.getenv("API_BASE", "https://wolf-goat-pig-api-i5v2shrpoa-uc.a.run.app").rstrip("/")
PLAYER_COUNT = int(os.getenv("SIGNUP_TEST_PLAYERS", "4"))


class ClaimVsReality(Exception):
    pass


def _pick_players(db: Session, n: int) -> list[PlayerProfile]:
    preferred_names = ["Stuart Gano", "Kevin Gent", "Allen Avery", "Brett Hodus", "Brent Gray"]
    picked: list[PlayerProfile] = []
    for name in preferred_names:
        row = (
            db.query(PlayerProfile)
            .filter(PlayerProfile.legacy_name == name, PlayerProfile.is_active == 1)
            .first()
        )
        if row and all(row.id != p.id for p in picked):
            picked.append(row)
        if len(picked) >= n:
            return picked

    extras = (
        db.query(PlayerProfile)
        .filter(
            PlayerProfile.legacy_name.isnot(None),
            PlayerProfile.legacy_name != "",
            PlayerProfile.is_active == 1,
        )
        .order_by(PlayerProfile.id.asc())
        .all()
    )
    for row in extras:
        if all(row.id != p.id for p in picked):
            picked.append(row)
        if len(picked) >= n:
            break
    if len(picked) < n:
        raise SystemExit(f"Need {n} club-linked players, found {len(picked)}")
    return picked


def _cleanup(db: Session, player_ids: list[int]) -> list[int]:
    rows = (
        db.query(DailySignup)
        .filter(DailySignup.date == TEST_DATE, DailySignup.player_profile_id.in_(player_ids))
        .all()
    )
    ids = [r.id for r in rows]
    if ids:
        db.query(DailySignup).filter(DailySignup.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
    return ids


def _fetch_live_weekly() -> dict:
    resp = httpx.get(
        f"{API_BASE}/signups/weekly",
        params={"week_start": TEST_WEEK_START},
        timeout=30.0,
    )
    if resp.status_code != 200:
        raise ClaimVsReality(f"GET /signups/weekly -> {resp.status_code}: {resp.text[:400]}")
    return resp.json()


def _day_signups(payload: dict, day: str) -> list[dict]:
    for summary in payload.get("daily_summaries") or []:
        if summary.get("date") == day:
            return [s for s in (summary.get("signups") or []) if s.get("status") != "cancelled"]
    return []


def _as_auth_user(player: PlayerProfile):
    return SimpleNamespace(
        id=player.id,
        legacy_name=player.legacy_name,
        name=player.name,
        email=player.email,
    )


def main() -> None:
    if not os.getenv("DATABASE_URL"):
        raise SystemExit("DATABASE_URL required (Cloud SQL via Auth Proxy TCP URL)")

    print(f"API_BASE={API_BASE}")
    print(f"TEST_DATE={TEST_DATE} week_start={TEST_WEEK_START} today={date.today().isoformat()}")

    db = SessionLocal()
    client = TestClient(app)
    created_ids: list[int] = []
    player_ids: list[int] = []

    # Avoid outbound legacy CGI writes during this prove-it.
    import app.routers.signups as signups_router

    original_legacy = signups_router.get_legacy_signup_service
    mock_legacy = MagicMock()
    mock_legacy.sync_signup_created = MagicMock(return_value=None)
    mock_legacy.sync_signup_cancelled = MagicMock(return_value=None)
    signups_router.get_legacy_signup_service = lambda: mock_legacy

    # Avoid confirmation emails during prove-it.
    original_confirm = signups_router._send_signup_confirmation
    signups_router._send_signup_confirmation = lambda *a, **k: None

    try:
        players = _pick_players(db, PLAYER_COUNT)
        player_ids = [p.id for p in players]
        print("Players under test:")
        for p in players:
            print(f"  id={p.id} name={p.name!r} legacy={p.legacy_name!r}")

        removed = _cleanup(db, player_ids)
        if removed:
            print(f"Cleared pre-existing test signups: {removed}")

        expected_names: set[str] = set()
        for p in players:
            app.dependency_overrides[get_current_user] = lambda player=p: _as_auth_user(player)
            # Spoof body identity — server must ignore and use auth profile
            resp = client.post(
                "/signups",
                json={
                    "date": TEST_DATE,
                    "player_profile_id": 999999,
                    "player_name": "SHOULD_NOT_PERSIST",
                    "preferred_start_time": None,
                    "notes": f"ctk-live-multi-user id={p.id}",
                },
            )
            if resp.status_code != 200:
                raise ClaimVsReality(f"POST /signups as {p.legacy_name} -> {resp.status_code} {resp.text[:300]}")
            body = resp.json()
            if body.get("player_profile_id") != p.id:
                raise ClaimVsReality(
                    f"Identity leak: expected profile_id={p.id}, got {body.get('player_profile_id')}"
                )
            if body.get("player_name") != p.legacy_name:
                raise ClaimVsReality(
                    f"Identity leak: expected name={p.legacy_name!r}, got {body.get('player_name')!r}"
                )
            created_ids.append(body["id"])
            expected_names.add(p.legacy_name)
            print(f"  POST ok id={body['id']} name={body['player_name']!r}")

        # Duplicate as first player must 400
        first = players[0]
        app.dependency_overrides[get_current_user] = lambda: _as_auth_user(first)
        dup = client.post("/signups", json={"date": TEST_DATE})
        if dup.status_code != 400:
            raise ClaimVsReality(f"Duplicate signup expected 400, got {dup.status_code}")
        print("  duplicate correctly rejected (400)")

        # claim vs reality against LIVE Cloud Run
        live = _fetch_live_weekly()
        live_rows = _day_signups(live, TEST_DATE)
        live_names = {r["player_name"] for r in live_rows}
        live_ids = {r["id"] for r in live_rows}
        print(f"Cloud Run names: {sorted(live_names)}")
        print(f"Expected names:  {sorted(expected_names)}")

        missing = expected_names - live_names
        if missing:
            raise ClaimVsReality(f"SILENT FAILURE: Cloud Run weekly missing names {missing}")
        missing_ids = set(created_ids) - live_ids
        if missing_ids:
            raise ClaimVsReality(f"SILENT FAILURE: Cloud Run weekly missing ids {missing_ids}")

        print("OK: multi-user signup create + Cloud Run read-after-write")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        signups_router.get_legacy_signup_service = original_legacy
        signups_router._send_signup_confirmation = original_confirm

        # Leave rows briefly for browser check if KEEP_SIGNUPS=1
        if os.getenv("KEEP_SIGNUPS") == "1":
            print(f"KEEP_SIGNUPS=1 — left ids={created_ids} on {TEST_DATE}")
        else:
            cleaned = _cleanup(db, player_ids)
            print(f"Cleaned up signup ids={cleaned or created_ids}")
            live = _fetch_live_weekly()
            leftover = {r["id"] for r in _day_signups(live, TEST_DATE)} & set(created_ids)
            if leftover:
                print(f"WARN: Cloud Run still shows cleaned ids {leftover}")
            else:
                print("OK: cleanup reflected on Cloud Run")
        db.close()


if __name__ == "__main__":
    try:
        main()
    except ClaimVsReality as e:
        print(f"FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
