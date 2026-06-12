"""LivSow transaction tracking — roster snapshots and auto-derived moves.

The LivSow Google Sheet only shows *current* rosters. This module derives a
baseball-reference-style transaction log (signings, releases, trades, role
changes, free-agency moves) by snapshotting the compacted roster and diffing
consecutive confirmed snapshots.

Design notes (see plan for full rationale):
- Snapshots are compacted to names + roles ONLY — weekly stats churn must not
  create "changed" snapshots.
- Debounce: a changed roster is stored as a 'pending' snapshot; transactions
  are emitted only when the same roster hash is observed again >=30 minutes
  later. Hand-edited sheets have transient mid-edit states.
- Guards: empty fetches are refused outright; a >50% player-count drop or a
  >15-transaction diff is never auto-confirmed (force=True overrides).
- Rename detection: an organizer fixing a typo must not produce a fake
  departed+joined pair. A departed/joined pair occupying the same team+role
  slot with high name similarity becomes a single 'renamed' row.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.orm import Session

from .. import models
from ..utils.time import utc_now

logger = logging.getLogger(__name__)

LIVSOW_SEASON = os.environ.get("LIVSOW_SEASON", "2026")

MIN_CONFIRM_SECONDS = 30 * 60  # debounce window
MAX_TXNS_PER_DIFF = 15  # circuit breaker (~1/3 of the league)
MIN_PLAYER_RATIO = 0.5  # shrinkage guard
RENAME_SIMILARITY = 0.85

_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Pure functions (no DB) — unit-tested directly
# ---------------------------------------------------------------------------


def compact_roster(leaderboard: dict[str, Any]) -> dict[str, Any]:
    """Reduce a leaderboard payload to a canonical names+roles roster."""
    teams: dict[str, list[dict[str, str]]] = {}
    for t in leaderboard.get("teams", []):
        teams[t["name"]] = sorted(
            ({"name": p["name"], "role": p["role"]} for p in t.get("players", [])),
            key=lambda p: (p["role"], p["name"]),
        )
    return {
        "teams": dict(sorted(teams.items())),
        "free_agents": sorted(fa["name"] for fa in leaderboard.get("free_agents", [])),
    }


def roster_hash(roster: dict[str, Any]) -> str:
    canonical = json.dumps(roster, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def player_count(roster: dict[str, Any]) -> int:
    return sum(len(v) for v in roster.get("teams", {}).values()) + len(roster.get("free_agents", []))


def _norm(name: str) -> str:
    return " ".join(name.casefold().split())


def _index(roster: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """norm_name -> {display, team, role}. team=None means free agent."""
    idx: dict[str, dict[str, Any]] = {}
    for team, players in roster.get("teams", {}).items():
        for p in players:
            k = _norm(p["name"])
            if k in idx:
                logger.warning("LivSow roster: duplicate player %r — keeping first occurrence", p["name"])
                continue
            idx[k] = {"display": p["name"], "team": team, "role": p["role"]}
    for name in roster.get("free_agents", []):
        idx.setdefault(_norm(name), {"display": name, "team": None, "role": "Free Agent"})
    return idx


def _txn(type_: str, player: str, **kw: Any) -> dict[str, Any]:
    return {
        "type": type_,
        "player_name": player,
        "from_team": kw.get("from_team"),
        "to_team": kw.get("to_team"),
        "from_role": kw.get("from_role"),
        "to_role": kw.get("to_role"),
        "details": kw.get("details"),
    }


def diff_rosters(prev: dict[str, Any], curr: dict[str, Any]) -> list[dict[str, Any]]:
    """Diff two compact rosters into a list of transaction dicts. Pure."""
    p_idx, c_idx = _index(prev), _index(curr)
    txns: list[dict[str, Any]] = []
    departed = set(p_idx) - set(c_idx)
    joined = set(c_idx) - set(p_idx)

    # Rename detection: same team+role slot, similar name → one 'renamed' row
    for d in sorted(departed):
        candidates = [
            j
            for j in sorted(joined)
            if p_idx[d]["team"] == c_idx[j]["team"]
            and p_idx[d]["role"] == c_idx[j]["role"]
            and SequenceMatcher(None, d, j).ratio() >= RENAME_SIMILARITY
        ]
        if len(candidates) == 1:
            j = candidates[0]
            txns.append(
                _txn(
                    "renamed",
                    c_idx[j]["display"],
                    from_team=p_idx[d]["team"],
                    to_team=c_idx[j]["team"],
                    from_role=p_idx[d]["role"],
                    to_role=c_idx[j]["role"],
                    details={"from_name": p_idx[d]["display"], "to_name": c_idx[j]["display"]},
                )
            )
            departed.discard(d)
            joined.discard(j)

    # Players present in both: movement / role changes
    for k in sorted(set(p_idx) & set(c_idx)):
        p, c = p_idx[k], c_idx[k]
        if (p["team"], p["role"]) == (c["team"], c["role"]):
            continue
        if p["team"] is None:
            type_ = "signed"  # FA -> team
        elif c["team"] is None:
            type_ = "released"  # team -> FA
        elif p["team"] != c["team"]:
            type_ = "traded"  # team -> team
        else:
            type_ = "role_change"
        txns.append(
            _txn(
                type_,
                c["display"],
                from_team=p["team"],
                to_team=c["team"],
                from_role=p["role"],
                to_role=c["role"],
            )
        )

    for k in sorted(departed):
        txns.append(_txn("departed", p_idx[k]["display"], from_team=p_idx[k]["team"], from_role=p_idx[k]["role"]))
    for k in sorted(joined):
        c = c_idx[k]
        if c["team"] is None:
            txns.append(_txn("joined", c["display"], to_role="Free Agent"))
        else:
            txns.append(
                _txn(
                    "signed",
                    c["display"],
                    to_team=c["team"],
                    to_role=c["role"],
                    details={"source": "new_to_league"},
                )
            )
    return txns


def describe_transaction(t: dict[str, Any]) -> str:
    """Human-readable one-liner per transaction (baseball-reference style)."""
    p = t["player_name"]
    type_ = t["type"]
    if type_ == "signed":
        return f"{p} signed by {t['to_team']} as {t['to_role']}"
    if type_ == "released":
        return f"{p} released by {t['from_team']} to free agency"
    if type_ == "traded":
        role = f" ({t['to_role']})" if t.get("to_role") and t.get("to_role") != t.get("from_role") else ""
        return f"{p} moves from {t['from_team']} to {t['to_team']}{role}"
    if type_ == "role_change":
        return f"{p} changes role on {t['to_team']}: {t['from_role']} → {t['to_role']}"
    if type_ == "joined":
        return f"{p} joins the league as a free agent"
    if type_ == "departed":
        origin = t.get("from_team") or "free agency"
        return f"{p} leaves the league (was with {origin})"
    if type_ == "renamed":
        d = t.get("details") or {}
        return f"Roster name corrected: {d.get('from_name')} → {d.get('to_name')}"
    return f"{p}: {type_}"


# ---------------------------------------------------------------------------
# Stateful snapshot check (DB)
# ---------------------------------------------------------------------------


def _latest(db: Session, status: str) -> models.LivSowRosterSnapshot | None:
    return (
        db.query(models.LivSowRosterSnapshot)
        .filter(
            models.LivSowRosterSnapshot.season == LIVSOW_SEASON,
            models.LivSowRosterSnapshot.status == status,
        )
        .order_by(models.LivSowRosterSnapshot.id.desc())
        .first()
    )


def _seconds_since(iso_ts: str) -> float:
    from datetime import datetime

    try:
        then = datetime.fromisoformat(iso_ts)
        now = datetime.fromisoformat(utc_now().isoformat())
        return (now - then).total_seconds()
    except (ValueError, TypeError):
        return float("inf")


def check_and_record_snapshot(db: Session, leaderboard: dict[str, Any], force: bool = False) -> dict[str, Any]:
    """Compare current roster against stored snapshots; record transactions.

    Returns a status dict (never raises for data issues — guards skip instead).
    """
    with _lock:
        roster = compact_roster(leaderboard)
        count = player_count(roster)

        # Guard: empty/failed fetch must never be stored
        if not roster["teams"] or count == 0:
            return {"status": "skipped", "reason": "empty_fetch"}

        h = roster_hash(roster)
        now = utc_now().isoformat()
        confirmed = _latest(db, "confirmed")

        if confirmed is None:
            # First run: baseline, no transactions
            db.add(
                models.LivSowRosterSnapshot(
                    taken_at=now,
                    season=LIVSOW_SEASON,
                    status="confirmed",
                    roster_hash=h,
                    player_count=count,
                    roster=roster,
                )
            )
            db.commit()
            return {"status": "baseline", "players": count}

        if h == confirmed.roster_hash:
            # No change — clear any stale pending candidate
            db.query(models.LivSowRosterSnapshot).filter(
                models.LivSowRosterSnapshot.season == LIVSOW_SEASON,
                models.LivSowRosterSnapshot.status == "pending",
            ).delete(synchronize_session=False)
            db.commit()
            return {"status": "no_change"}

        # Guard: suspicious shrinkage (partial CSV / parse drift)
        if count < MIN_PLAYER_RATIO * (confirmed.player_count or 0) and not force:
            logger.warning("LivSow snapshot skipped: player count %s vs confirmed %s", count, confirmed.player_count)
            return {"status": "skipped", "reason": "player_count_drop", "players": count}

        pending = _latest(db, "pending")
        if force:
            # Explicit human override: record immediately, no debounce.
            # Materialize/replace the candidate so it can be confirmed below.
            db.query(models.LivSowRosterSnapshot).filter(
                models.LivSowRosterSnapshot.season == LIVSOW_SEASON,
                models.LivSowRosterSnapshot.status == "pending",
            ).delete(synchronize_session=False)
            pending = models.LivSowRosterSnapshot(
                taken_at=now,
                season=LIVSOW_SEASON,
                status="pending",
                roster_hash=h,
                player_count=count,
                roster=roster,
            )
            db.add(pending)
            db.flush()  # assign id for snapshot_id linkage
        elif pending is None or pending.roster_hash != h:
            # New candidate (or organizer still editing) — restart the clock
            db.query(models.LivSowRosterSnapshot).filter(
                models.LivSowRosterSnapshot.season == LIVSOW_SEASON,
                models.LivSowRosterSnapshot.status == "pending",
            ).delete(synchronize_session=False)
            db.add(
                models.LivSowRosterSnapshot(
                    taken_at=now,
                    season=LIVSOW_SEASON,
                    status="pending",
                    roster_hash=h,
                    player_count=count,
                    roster=roster,
                )
            )
            db.commit()
            return {"status": "pending", "reason": "new_candidate"}
        elif _seconds_since(pending.taken_at) < MIN_CONFIRM_SECONDS:
            return {"status": "pending", "reason": "awaiting_confirmation"}

        txns = diff_rosters(confirmed.roster, roster)

        # Guard: mass change — likely a season restructure, needs human eyes
        if len(txns) > MAX_TXNS_PER_DIFF and not force:
            logger.warning("LivSow snapshot needs review: %d transactions in one diff", len(txns))
            return {"status": "needs_review", "transaction_count": len(txns)}

        pending.status = "confirmed"
        week_label = (leaderboard.get("weeks") or [None])[-1]
        for t in txns:
            db.add(
                models.LivSowTransaction(
                    detected_at=now,
                    season=LIVSOW_SEASON,
                    week_label=week_label,
                    snapshot_id=pending.id,
                    type=t["type"],
                    player_name=t["player_name"],
                    from_team=t["from_team"],
                    to_team=t["to_team"],
                    from_role=t["from_role"],
                    to_role=t["to_role"],
                    details=t["details"],
                    deleted=False,
                )
            )
        db.commit()
        return {"status": "recorded", "transactions": len(txns)}
