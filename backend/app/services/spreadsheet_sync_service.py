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

The service uses Google Sheets API v4 with OAuth credentials.

To enable write access:
1. Share the writable spreadsheet with stuagano@gmail.com as Editor
2. Ensure gcloud is authenticated with that account:
   gcloud auth application-default login --scopes="openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive"
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Spreadsheet IDs
PRIMARY_SHEET_ID = "1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM"  # The real/primary dashboard (read-only)
WRITABLE_SHEET_ID = "19AabC4vx0jRXHIAmz8QJfqTIBxxvMfFUplB0abg8mdA"  # Stuart's writable copy for app sync

# GCP quota project for API calls (stuagano@gmail.com's project)
QUOTA_PROJECT = "stuartgano-n8n"


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
    """Get OAuth access token.

    Tries in order:
    1. GOOGLE_OAUTH_CREDENTIALS env var (for production - contains refresh token)
    2. gcloud CLI (for local development)
    """
    # Try environment variable first (production)
    oauth_creds_json = os.environ.get("GOOGLE_OAUTH_CREDENTIALS")
    if oauth_creds_json:
        try:
            creds = json.loads(oauth_creds_json)
            refresh_token = creds.get("refresh_token")
            client_id = creds.get("client_id")
            client_secret = creds.get("client_secret")

            if refresh_token and client_id and client_secret:
                # Exchange refresh token for access token
                token_url = "https://oauth2.googleapis.com/token"
                data = urllib.parse.urlencode(
                    {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    }
                ).encode("utf-8")

                req = urllib.request.Request(token_url, data=data, method="POST")
                with urllib.request.urlopen(req, timeout=10) as response:
                    result = json.loads(response.read())
                    access_token = result.get("access_token")
                    if access_token:
                        logger.info("Got access token from GOOGLE_OAUTH_CREDENTIALS")
                        return access_token
        except Exception as e:
            logger.error(f"Failed to get token from GOOGLE_OAUTH_CREDENTIALS: {e}")

    # Fall back to gcloud CLI (local development)
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


@dataclass
class ReconciliationResult:
    """Result of comparing two spreadsheets."""

    primary_only: List[RoundResult]  # Rounds only in primary (real) sheet
    writable_only: List[RoundResult]  # Rounds only in writable (app) sheet
    matched: int  # Count of matching rounds
    primary_total: int
    writable_total: int

    @property
    def is_synced(self) -> bool:
        return len(self.primary_only) == 0 and len(self.writable_only) == 0


class ReconciliationService:
    """Service for reconciling data between primary and writable spreadsheets.

    During the transition period, scores may be entered in either:
    - The primary spreadsheet (legacy manual entry)
    - The writable copy (via the app)

    This service helps identify discrepancies and sync them.
    """

    def __init__(self):
        self.primary = SpreadsheetSyncService(PRIMARY_SHEET_ID)
        self.writable = SpreadsheetSyncService(WRITABLE_SHEET_ID)

    def _round_key(self, r: RoundResult) -> str:
        """Create a unique key for a round result."""
        return f"{r.date}|{r.group}|{r.member}|{r.score}"

    def compare_sheets(self) -> ReconciliationResult:
        """Compare primary and writable sheets to find differences."""
        primary_rounds = self.primary.get_all_rounds()
        writable_rounds = self.writable.get_all_rounds()

        primary_keys = {self._round_key(r): r for r in primary_rounds}
        writable_keys = {self._round_key(r): r for r in writable_rounds}

        primary_only = [r for k, r in primary_keys.items() if k not in writable_keys]
        writable_only = [r for k, r in writable_keys.items() if k not in primary_keys]
        matched = len(set(primary_keys.keys()) & set(writable_keys.keys()))

        return ReconciliationResult(
            primary_only=primary_only,
            writable_only=writable_only,
            matched=matched,
            primary_total=len(primary_rounds),
            writable_total=len(writable_rounds),
        )

    def sync_primary_to_writable(self, dry_run: bool = True) -> Dict[str, Any]:
        """Copy missing rounds from primary to writable sheet.

        Args:
            dry_run: If True, only report what would be synced without making changes.

        Returns:
            Summary of sync operation.
        """
        result = self.compare_sheets()

        if not result.primary_only:
            return {
                "status": "already_synced",
                "message": "Writable sheet already has all rounds from primary",
                "matched": result.matched,
            }

        if dry_run:
            return {
                "status": "dry_run",
                "message": f"Would copy {len(result.primary_only)} rounds from primary to writable",
                "rounds_to_copy": [
                    {"date": r.date, "group": r.group, "member": r.member, "score": r.score}
                    for r in result.primary_only
                ],
            }

        # Actually sync
        success = self.writable.add_round_results(result.primary_only)

        if success:
            return {
                "status": "success",
                "message": f"Copied {len(result.primary_only)} rounds from primary to writable",
                "rounds_copied": len(result.primary_only),
            }
        else:
            return {
                "status": "error",
                "message": "Failed to copy rounds to writable sheet",
            }

    def sync_writable_to_primary(self, dry_run: bool = True) -> Dict[str, Any]:
        """Copy missing rounds from writable to primary sheet.

        NOTE: This requires write access to the primary sheet.

        Args:
            dry_run: If True, only report what would be synced.

        Returns:
            Summary of sync operation.
        """
        result = self.compare_sheets()

        if not result.writable_only:
            return {
                "status": "already_synced",
                "message": "Primary sheet already has all rounds from writable",
                "matched": result.matched,
            }

        if dry_run:
            return {
                "status": "dry_run",
                "message": f"Would copy {len(result.writable_only)} rounds from writable to primary",
                "rounds_to_copy": [
                    {"date": r.date, "group": r.group, "member": r.member, "score": r.score}
                    for r in result.writable_only
                ],
            }

        # Actually sync - this may fail if we don't have write access to primary
        success = self.primary.add_round_results(result.writable_only)

        if success:
            return {
                "status": "success",
                "message": f"Copied {len(result.writable_only)} rounds from writable to primary",
                "rounds_copied": len(result.writable_only),
            }
        else:
            return {
                "status": "error",
                "message": "Failed to copy rounds to primary sheet (may need write access)",
            }

    def get_sync_status(self) -> Dict[str, Any]:
        """Get a summary of sync status between the two sheets."""
        result = self.compare_sheets()

        return {
            "is_synced": result.is_synced,
            "primary_sheet": {
                "id": PRIMARY_SHEET_ID,
                "total_rounds": result.primary_total,
                "unique_rounds": len(result.primary_only),
            },
            "writable_sheet": {
                "id": WRITABLE_SHEET_ID,
                "total_rounds": result.writable_total,
                "unique_rounds": len(result.writable_only),
            },
            "matched_rounds": result.matched,
            "primary_only_sample": [
                {"date": r.date, "member": r.member, "score": r.score} for r in result.primary_only[:5]
            ],
            "writable_only_sample": [
                {"date": r.date, "member": r.member, "score": r.score} for r in result.writable_only[:5]
            ],
        }


_reconciliation_service: Optional[ReconciliationService] = None


def get_reconciliation_service() -> ReconciliationService:
    """Get the singleton reconciliation service."""
    global _reconciliation_service
    if _reconciliation_service is None:
        _reconciliation_service = ReconciliationService()
    return _reconciliation_service
