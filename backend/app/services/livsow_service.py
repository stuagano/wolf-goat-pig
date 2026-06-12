"""Service for reading LivSow stableford league data from Google Sheets."""

from __future__ import annotations

import csv
import io
import logging
import os
import time
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

LIVSOW_SHEET_ID = os.environ.get("LIVSOW_SHEET_ID", "1_u7RFdyDdhyG2KLgJXMMehqLLQTTCCQq4l9AnN9XnuE")
LIVSOW_ROSTER_GID = os.environ.get("LIVSOW_ROSTER_GID", "970807461")
LIVSOW_STATS_GID = os.environ.get("LIVSOW_STATS_GID", "0")

# Column offsets where each team block starts in the roster tab
_TEAM_COL_OFFSETS = [2, 5, 8, 11, 14, 17]

# Cache: refresh at most once per 15 minutes
_cache: dict[str, Any] = {}
_cache_ts: float = 0.0
_CACHE_TTL = 900


def _fetch_csv(gid: str) -> list[list[str]]:
    url = f"https://docs.google.com/spreadsheets/d/{LIVSOW_SHEET_ID}/export?format=csv&gid={gid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            return list(csv.reader(io.StringIO(content)))
    except Exception as e:
        logger.error("Failed to fetch LivSow sheet gid=%s: %s", gid, e)
        return []


def _safe_int(val: str) -> int | None:
    try:
        return int(val.strip())
    except (ValueError, TypeError):
        return None


def _parse_stats(rows: list[list[str]]) -> tuple[list[str], dict[str, dict]]:
    """Parse the stats tab. Returns (weeks, {player_name: stats_dict})."""
    if not rows:
        return [], {}

    header = rows[0]
    week_indices = [i for i, h in enumerate(header) if "/" in h]
    weeks = [header[i] for i in week_indices]

    players: dict[str, dict] = {}
    for row in rows[1:]:
        name = row[0].strip() if row else ""
        if not name:
            continue
        weekly = {}
        for col_idx, week in zip(week_indices, weeks):
            raw = row[col_idx].strip() if col_idx < len(row) else ""
            weekly[week] = _safe_int(raw)
        total = sum(v for v in weekly.values() if v is not None)
        count_raw = row[5].strip() if len(row) > 5 else "0"
        players[name] = {
            "total": total,
            "count": _safe_int(count_raw) or 0,
            "weeks": weekly,
        }
    return weeks, players


def _parse_roster(
    rows: list[list[str]],
    weeks: list[str],
    player_stats: dict[str, dict],
) -> tuple[list[dict], list[dict]]:
    """Parse the roster tab. Returns (teams, free_agents)."""
    if not rows:
        return [], []

    # Row 1: team names
    name_row = rows[1] if len(rows) > 1 else []
    team_names = [
        name_row[offset].strip() for offset in _TEAM_COL_OFFSETS if offset < len(name_row) and name_row[offset].strip()
    ]

    # Rows with roles
    role_rows = [r for r in rows[2:] if r and r[0].strip() in ("Captain", "Starter", "Alternate")]

    teams_players: dict[str, list] = {n: [] for n in team_names}
    for row in role_rows:
        role = row[0].strip()
        for i, team_name in enumerate(team_names):
            if i >= len(_TEAM_COL_OFFSETS):
                break
            offset = _TEAM_COL_OFFSETS[i]
            player_name = row[offset].strip() if offset < len(row) else ""
            if not player_name:
                continue
            s1 = _safe_int(row[offset + 1].strip() if offset + 1 < len(row) else "")
            s2 = _safe_int(row[offset + 2].strip() if offset + 2 < len(row) else "")
            best_scores = [v for v in [s1, s2] if v is not None]
            team_contribution = sum(best_scores)
            stats = player_stats.get(player_name, {"total": 0, "count": 0, "weeks": dict.fromkeys(weeks)})
            teams_players[team_name].append(
                {
                    "name": player_name,
                    "role": role,
                    "total": stats["total"],
                    "count": stats["count"],
                    "weeks": stats["weeks"],
                    "best_scores": best_scores,
                    "team_contribution": team_contribution,
                }
            )

    # Team totals row (follows "Point Totals" label row)
    team_totals: dict[str, int] = {}
    for idx, row in enumerate(rows):
        if row and len(row) > 2 and "Point Totals" in (row[2] if len(row) > 2 else ""):
            if idx + 1 < len(rows):
                total_row = rows[idx + 1]
                for i, team_name in enumerate(team_names):
                    if i >= len(_TEAM_COL_OFFSETS):
                        break
                    offset = _TEAM_COL_OFFSETS[i]
                    raw = total_row[offset + 1].strip() if offset + 1 < len(total_row) else ""
                    v = _safe_int(raw)
                    if v is not None:
                        team_totals[team_name] = v
            break

    # Free agents
    free_agents = []
    for row in rows:
        if not row or row[0].strip() != "Free Agent":
            continue
        fa_name = row[2].strip() if len(row) > 2 else ""
        if not fa_name:
            continue
        stats = player_stats.get(fa_name, {"total": 0, "count": 0, "weeks": dict.fromkeys(weeks)})
        free_agents.append(
            {
                "name": fa_name,
                "total": stats["total"],
                "count": stats["count"],
                "weeks": stats["weeks"],
            }
        )

    # Build sorted teams
    teams = []
    for name in team_names:
        total = team_totals.get(
            name,
            sum(p["total"] for p in teams_players.get(name, [])),
        )
        teams.append({"name": name, "total": total, "players": teams_players.get(name, [])})
    teams.sort(key=lambda t: t["total"], reverse=True)
    for i, t in enumerate(teams):
        t["rank"] = i + 1

    return teams, free_agents


def get_livsow_team_map() -> dict[str, dict]:
    """Return {player_name: {team, role}} for quick lookup. Uses cached leaderboard."""
    data = get_livsow_leaderboard()
    result: dict[str, dict] = {}
    for team in data.get("teams", []):
        for p in team.get("players", []):
            result[p["name"]] = {"team": team["name"], "role": p["role"]}
    return result


def get_livsow_leaderboard(force_refresh: bool = False) -> dict[str, Any]:
    """Return the LivSow leaderboard. Cached for 15 minutes."""
    global _cache, _cache_ts
    if not force_refresh and _cache and (time.time() - _cache_ts) < _CACHE_TTL:
        return _cache

    stats_rows = _fetch_csv(LIVSOW_STATS_GID)
    roster_rows = _fetch_csv(LIVSOW_ROSTER_GID)

    weeks, player_stats = _parse_stats(stats_rows)
    teams, free_agents = _parse_roster(roster_rows, weeks, player_stats)

    result: dict[str, Any] = {
        "teams": teams,
        "weeks": weeks,
        "free_agents": free_agents,
        "sheet_url": (
            f"https://docs.google.com/spreadsheets/d/{LIVSOW_SHEET_ID}"
            f"/edit?gid={LIVSOW_ROSTER_GID}#gid={LIVSOW_ROSTER_GID}"
        ),
    }
    _cache = result
    _cache_ts = time.time()
    return result
