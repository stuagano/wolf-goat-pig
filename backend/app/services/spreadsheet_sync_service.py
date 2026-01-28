"""Service for syncing game data with the WGP Dashboard Google Sheet.

This service provides two-way sync between the Wolf Goat Pig app and the
legacy Google Sheets dashboard at:
- Primary (read-only): https://docs.google.com/spreadsheets/d/19AabC4vx0jRXHIAmz8QJfqTIBxxvMfFUplB0abg8mdA
- Writable copy: https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM

Sheet Structure:
- Dashboard: Leaderboard summary (auto-calculated from Details)
- Details: Raw round data with columns:
  - A: Date (DD-Mon format, e.g., "21-Jul")
  - B: Group (A, B, C, D - for multiple groups on same day)
  - C: Member (player name)
  - D: Score (quarters won/lost, e.g., 153 or -78)
  - E: Location (e.g., "Wing Point")
  - F: Duration (e.g., "3:55:00")

The service uses Google Sheets API v4 with service account or OAuth credentials.
"""

from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Spreadsheet IDs
PRIMARY_SHEET_ID = "19AabC4vx0jRXHIAmz8QJfqTIBxxvMfFUplB0abg8mdA"  # Read-only original
WRITABLE_SHEET_ID = "1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM"  # Writable copy

# GCP quota project for API calls
QUOTA_PROJECT = "gcp-sandbox-field-eng"


@dataclass
class RoundResult:
    """A single player's result from a round."""

    date: str  # DD-Mon format (e.g., "21-Jul")
    group: str  # A, B, C, D
    member: str  # Player name
    score: int  # Quarters (positive = won, negative = lost)
    location: str  # Course name
    duration: Optional[str] = None  # HH:MM:SS format


@dataclass
class RoundSummary:
    """Summary of a complete round (all players in a group)."""

    date: str
    group: str
    location: str
    duration: Optional[str]
    players: List[RoundResult]

    @property
    def player_count(self) -> int:
        return len(self.players)

    @property
    def total_score(self) -> int:
        """Should sum to 0 for a valid round."""
        return sum(p.score for p in self.players)


def _get_access_token() -> Optional[str]:
    """Get OAuth access token using gcloud CLI."""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
        logger.error(f"gcloud token failed: {result.stderr}")
        return None
    except Exception as e:
        logger.error(f"Failed to get access token: {e}")
        return None


def _sheets_api_get(sheet_id: str, range_spec: str) -> Optional[Dict[str, Any]]:
    """Make a GET request to the Sheets API."""
    import json
    import urllib.request

    token = _get_access_token()
    if not token:
        return None

    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_spec}"

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "x-goog-user-project": QUOTA_PROJECT,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read())
    except Exception as e:
        logger.error(f"Sheets API GET failed: {e}")
        return None


def _sheets_api_append(sheet_id: str, range_spec: str, values: List[List[Any]]) -> bool:
    """Append rows to a sheet."""
    import json
    import urllib.request

    token = _get_access_token()
    if not token:
        return False

    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_spec}:append"
    url += "?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS"

    data = json.dumps({"values": values}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "x-goog-user-project": QUOTA_PROJECT,
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read())
            logger.info(f"Appended {len(values)} rows to {range_spec}")
            return True
    except Exception as e:
        logger.error(f"Sheets API append failed: {e}")
        return False


class SpreadsheetSyncService:
    """Service for syncing game data with Google Sheets."""

    def __init__(self, sheet_id: str = WRITABLE_SHEET_ID):
        self.sheet_id = sheet_id

    def get_all_rounds(self) -> List[RoundResult]:
        """Fetch all round results from the Details sheet."""
        data = _sheets_api_get(self.sheet_id, "Details!A2:F5000")
        if not data or "values" not in data:
            return []

        results = []
        for row in data["values"]:
            if len(row) < 4:
                continue

            try:
                result = RoundResult(
                    date=row[0] if len(row) > 0 else "",
                    group=row[1] if len(row) > 1 else "A",
                    member=row[2] if len(row) > 2 else "",
                    score=int(row[3]) if len(row) > 3 and row[3] else 0,
                    location=row[4] if len(row) > 4 else "Wing Point",
                    duration=row[5] if len(row) > 5 else None,
                )
                if result.date and result.member:
                    results.append(result)
            except (ValueError, IndexError) as e:
                logger.warning(f"Skipping invalid row: {row} - {e}")
                continue

        return results

    def get_rounds_by_date(self, date: str) -> List[RoundSummary]:
        """Get all rounds for a specific date, grouped by group letter."""
        all_results = self.get_all_rounds()

        # Filter by date
        date_results = [r for r in all_results if r.date == date]

        # Group by group letter
        groups: Dict[str, List[RoundResult]] = {}
        for result in date_results:
            if result.group not in groups:
                groups[result.group] = []
            groups[result.group].append(result)

        # Build summaries
        summaries = []
        for group_letter, players in sorted(groups.items()):
            if players:
                summaries.append(
                    RoundSummary(
                        date=date,
                        group=group_letter,
                        location=players[0].location,
                        duration=players[0].duration,
                        players=players,
                    )
                )

        return summaries

    def get_player_history(self, member_name: str) -> List[RoundResult]:
        """Get all rounds for a specific player."""
        all_results = self.get_all_rounds()
        return [r for r in all_results if r.member.lower() == member_name.lower()]

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Fetch the current leaderboard from Dashboard sheet."""
        data = _sheets_api_get(self.sheet_id, "Dashboard!B3:F100")
        if not data or "values" not in data:
            return []

        leaderboard = []
        for i, row in enumerate(data["values"]):
            if len(row) < 5:
                continue

            try:
                # Skip header-like rows
                if row[0] == "Member" or not row[0]:
                    continue

                entry = {
                    "rank": i + 1,
                    "member": row[0],
                    "quarters": int(row[1].replace(",", "")) if row[1] else 0,
                    "average": int(row[2]) if row[2] else 0,
                    "rounds": int(row[3]) if row[3] else 0,
                    "qb": int(row[4].replace(",", "")) if row[4] else 0,
                }
                leaderboard.append(entry)
            except (ValueError, IndexError) as e:
                logger.warning(f"Skipping leaderboard row: {row} - {e}")
                continue

        return leaderboard

    def add_round_results(self, results: List[RoundResult]) -> bool:
        """Add new round results to the Details sheet.

        Args:
            results: List of RoundResult objects for all players in the round

        Returns:
            True if successful, False otherwise
        """
        if not results:
            return False

        # Validate: scores should sum to 0
        total = sum(r.score for r in results)
        if total != 0:
            logger.warning(f"Round scores sum to {total}, not 0. Adding anyway.")

        # Convert to sheet rows
        rows = []
        for r in results:
            rows.append(
                [
                    r.date,
                    r.group,
                    r.member,
                    r.score,
                    r.location,
                    r.duration or "",
                ]
            )

        return _sheets_api_append(self.sheet_id, "Details!A:F", rows)

    def format_date_for_sheet(self, dt: datetime) -> str:
        """Convert datetime to sheet format (DD-Mon)."""
        return dt.strftime("%-d-%b")

    def sync_completed_game(
        self,
        game_date: datetime,
        group: str,
        location: str,
        player_scores: Dict[str, int],
        duration: Optional[str] = None,
    ) -> bool:
        """Sync a completed game from the app to the spreadsheet.

        Args:
            game_date: Date of the game
            group: Group letter (A, B, C, D)
            location: Course name
            player_scores: Dict mapping player name to their score (quarters)
            duration: Optional game duration in HH:MM:SS format

        Returns:
            True if sync successful
        """
        date_str = self.format_date_for_sheet(game_date)

        results = [
            RoundResult(
                date=date_str,
                group=group,
                member=name,
                score=score,
                location=location,
                duration=duration,
            )
            for name, score in player_scores.items()
        ]

        return self.add_round_results(results)


# Singleton instance
_sync_service: Optional[SpreadsheetSyncService] = None


def get_spreadsheet_sync_service() -> SpreadsheetSyncService:
    """Get the singleton spreadsheet sync service."""
    global _sync_service
    if _sync_service is None:
        _sync_service = SpreadsheetSyncService()
    return _sync_service
