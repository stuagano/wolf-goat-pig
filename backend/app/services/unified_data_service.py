"""Unified data service that merges data from all sources.

This service provides a single view of all game data by merging:
1. Primary spreadsheet (read-only legacy data)
2. Writable spreadsheet (app-entered data during transition)
3. Render database (games recorded directly in the app)

The service deduplicates data and provides a unified leaderboard and round history.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from ..utils.time import utc_now
from typing import Any

from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GamePlayerResult, GameRecord, LegacyRound
from .spreadsheet_sync_service import PRIMARY_SHEET_ID, WRITABLE_SHEET_ID, RoundResult, SpreadsheetSyncService

logger = logging.getLogger(__name__)


@dataclass
class UnifiedRound:
    """A round result from any source."""

    date: str  # DD-Mon format for display
    date_sortable: str  # YYYY-MM-DD for sorting
    group: str
    member: str
    score: int  # Quarters (positive = won, negative = lost)
    location: str
    duration: str | None = None
    source: str = "unknown"  # "primary_sheet", "writable_sheet", "database"

    def __hash__(self):
        """Hash for deduplication - same date/group/member/score is same round."""
        return hash((self.date, self.group, self.member, self.score))

    def __eq__(self, other):
        if not isinstance(other, UnifiedRound):
            return False
        return (
            self.date == other.date
            and self.group == other.group
            and self.member == other.member
            and self.score == other.score
        )


@dataclass
class UnifiedLeaderboardEntry:
    """A player's aggregated stats across all sources."""

    member: str
    quarters: int = 0  # Total quarters won/lost
    rounds: int = 0  # Number of rounds played
    average: float = 0.0  # Average quarters per round
    best_round: int = 0  # Best single round score
    worst_round: int = 0  # Worst single round score
    sources: set[str] = field(default_factory=set)  # Which sources contributed data

    def recalculate_average(self):
        """Recalculate average based on total and rounds."""
        if self.rounds > 0:
            self.average = self.quarters / self.rounds


class UnifiedDataService:
    """Service that merges data from spreadsheets and database."""

    def __init__(self, db: Session | None = None):
        self.primary_sheet = SpreadsheetSyncService(PRIMARY_SHEET_ID)
        self.writable_sheet = SpreadsheetSyncService(WRITABLE_SHEET_ID)
        self._db = db

    def _get_db(self) -> Session:
        """Get database session."""
        if self._db:
            return self._db
        return next(get_db())

    def _parse_sheet_date(self, date_str: str) -> str:
        """Convert DD-Mon format to YYYY-MM-DD for sorting.

        Assumes current year for dates, adjusting for year boundary.
        """
        try:
            # Try parsing with current year
            current_year = utc_now().year
            dt = datetime.strptime(f"{date_str}-{current_year}", "%d-%b-%Y")

            # If date is in the future by more than a month, it's probably last year
            if dt > utc_now() and (dt - utc_now()).days > 30:
                dt = dt.replace(year=current_year - 1)

            return dt.strftime("%Y-%m-%d")
        except ValueError:
            # If parsing fails, return original
            return date_str

    def _sheet_round_to_unified(self, r: RoundResult, source: str) -> UnifiedRound:
        """Convert a spreadsheet round to unified format."""
        return UnifiedRound(
            date=r.date,
            date_sortable=self._parse_sheet_date(r.date),
            group=r.group,
            member=r.member,
            score=r.score,
            location=r.location,
            duration=r.duration,
            source=source,
        )

    def _legacy_round_to_unified(self, r: LegacyRound) -> UnifiedRound:
        """Convert a legacy_rounds DB row to unified format."""
        try:
            dt = datetime.strptime(r.date, "%Y-%m-%d")
            date_display = dt.strftime("%-d-%b")
        except ValueError:
            date_display = r.date
        return UnifiedRound(
            date=date_display,
            date_sortable=r.date,
            group=r.group,
            member=r.member,
            score=r.score,
            location=r.location,
            duration=r.duration,
            source=r.source,
        )

    def _db_result_to_unified(self, result: GamePlayerResult, record: GameRecord) -> UnifiedRound:
        """Convert a database game result to unified format."""
        # Convert database date format to DD-Mon
        try:
            if record.completed_at:
                dt = datetime.fromisoformat(record.completed_at.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(record.created_at.replace("Z", "+00:00"))
            date_display = dt.strftime("%-d-%b")
            date_sortable = dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            date_display = "Unknown"
            date_sortable = "1900-01-01"

        return UnifiedRound(
            date=date_display,
            date_sortable=date_sortable,
            group="A",  # Database doesn't track groups
            member=result.player_name,
            score=int(result.total_earnings),  # Convert earnings to quarters
            location=record.course_name or "Unknown",
            duration=(f"{record.game_duration_minutes}:00" if record.game_duration_minutes else None),
            source="database",
        )

    def get_all_rounds(
        self,
        include_database: bool = True,
        use_sheet_cache: bool = True,
    ) -> list[UnifiedRound]:
        """Get all rounds from all sources, deduplicated.

        Args:
            include_database: Whether to include in-app GameRecord results.
            use_sheet_cache: When True (default), read sheet data from the
                legacy_rounds DB cache (synced every 2h) instead of calling
                the Sheets API live. Pass False only when populating that cache.

        Returns:
            List of unified rounds, sorted by date (most recent first).
        """
        all_rounds: dict[tuple, UnifiedRound] = {}

        if use_sheet_cache:
            # Fast path: read from legacy_rounds DB cache
            try:
                db = self._get_db()
                for r in db.query(LegacyRound).all():
                    unified = self._legacy_round_to_unified(r)
                    key = (unified.date_sortable, unified.group, unified.member, unified.score)
                    if key not in all_rounds:
                        all_rounds[key] = unified
            except Exception as e:
                logger.warning(f"Failed to read legacy_rounds cache: {e}")
        else:
            # Slow path: live Sheets API — used only by the sync job itself
            try:
                for r in self.primary_sheet.get_all_rounds():
                    unified = self._sheet_round_to_unified(r, "primary_sheet")
                    key = (unified.date_sortable, unified.group, unified.member, unified.score)
                    if key not in all_rounds:
                        all_rounds[key] = unified
            except Exception as e:
                logger.warning(f"Failed to fetch primary sheet: {e}")

            try:
                for r in self.writable_sheet.get_all_rounds():
                    unified = self._sheet_round_to_unified(r, "writable_sheet")
                    key = (unified.date_sortable, unified.group, unified.member, unified.score)
                    if key not in all_rounds:
                        all_rounds[key] = unified
            except Exception as e:
                logger.warning(f"Failed to fetch writable sheet: {e}")

        # Merge in-app GameRecord results
        if include_database:
            try:
                db = self._get_db()
                records = db.query(GameRecord).filter(GameRecord.completed_at.isnot(None)).all()
                for record in records:
                    results = db.query(GamePlayerResult).filter(
                        GamePlayerResult.game_record_id == record.id
                    ).all()
                    for result in results:
                        unified = self._db_result_to_unified(result, record)
                        key = (unified.date_sortable, unified.group, unified.member, unified.score)
                        if key not in all_rounds:
                            all_rounds[key] = unified
            except Exception as e:
                logger.warning(f"Failed to fetch database records: {e}")

        return sorted(all_rounds.values(), key=lambda r: r.date_sortable, reverse=True)

    def get_unified_leaderboard(self) -> list[UnifiedLeaderboardEntry]:
        """Get unified leaderboard aggregating all sources.

        Returns:
            List of leaderboard entries sorted by total quarters (descending)
        """
        all_rounds = self.get_all_rounds()

        # Aggregate by player
        player_stats: dict[str, UnifiedLeaderboardEntry] = {}

        for round_data in all_rounds:
            member = round_data.member
            if member not in player_stats:
                player_stats[member] = UnifiedLeaderboardEntry(member=member)

            entry = player_stats[member]
            entry.quarters += round_data.score
            entry.rounds += 1
            entry.sources.add(round_data.source)

            # Track best/worst
            if round_data.score > entry.best_round:
                entry.best_round = round_data.score
            if round_data.score < entry.worst_round:
                entry.worst_round = round_data.score

        # Calculate averages
        for entry in player_stats.values():
            entry.recalculate_average()

        # Sort by total quarters (descending)
        sorted_leaderboard = sorted(player_stats.values(), key=lambda e: e.quarters, reverse=True)
        return sorted_leaderboard

    def get_player_history(self, member_name: str) -> list[UnifiedRound]:
        """Get all rounds for a specific player across all sources.

        Args:
            member_name: Player name (case-insensitive match)

        Returns:
            List of rounds for the player, sorted by date (most recent first)
        """
        all_rounds = self.get_all_rounds()
        player_rounds = [r for r in all_rounds if r.member.lower() == member_name.lower()]
        return player_rounds

    def get_rounds_by_date(self, date: str) -> list[UnifiedRound]:
        """Get all rounds for a specific date.

        Args:
            date: Date in DD-Mon format (e.g., "27-Jan")

        Returns:
            List of rounds for that date
        """
        all_rounds = self.get_all_rounds()
        date_rounds = [r for r in all_rounds if r.date == date]
        return date_rounds

    def get_data_sources_status(self) -> dict[str, Any]:
        """Get status of all data sources.

        Returns:
            Status info for each source including record counts
        """
        status = {
            "primary_sheet": {
                "available": False,
                "record_count": 0,
                "id": PRIMARY_SHEET_ID,
            },
            "writable_sheet": {
                "available": False,
                "record_count": 0,
                "id": WRITABLE_SHEET_ID,
            },
            "database": {"available": False, "record_count": 0},
            "unified_total": 0,
            "deduplicated_total": 0,
        }

        try:
            db = self._get_db()
            primary_count = db.query(LegacyRound).filter(
                LegacyRound.source == "primary_sheet"
            ).count()
            writable_count = db.query(LegacyRound).filter(
                LegacyRound.source == "writable_sheet"
            ).count()
            status["primary_sheet"]["available"] = primary_count > 0  # type: ignore[index]
            status["primary_sheet"]["record_count"] = primary_count  # type: ignore[index]
            status["writable_sheet"]["available"] = writable_count > 0  # type: ignore[index]
            status["writable_sheet"]["record_count"] = writable_count  # type: ignore[index]
        except Exception as e:
            status["primary_sheet"]["error"] = str(e)  # type: ignore[index]
            status["writable_sheet"]["error"] = str(e)  # type: ignore[index]

        try:
            db = self._get_db()
            db_count = (
                db.query(GamePlayerResult)
                .join(GameRecord, GamePlayerResult.game_record_id == GameRecord.id)
                .filter(GameRecord.completed_at.isnot(None))
                .count()
            )
            status["database"]["available"] = True  # type: ignore[index]
            status["database"]["record_count"] = db_count  # type: ignore[index]
        except Exception as e:
            status["database"]["error"] = str(e)  # type: ignore[index]

        # Calculate totals
        status["unified_total"] = (
            status["primary_sheet"]["record_count"]  # type: ignore[index]
            + status["writable_sheet"]["record_count"]  # type: ignore[index]
            + status["database"]["record_count"]  # type: ignore[index]
        )

        try:
            db = self._get_db()
            status["deduplicated_total"] = db.query(LegacyRound).count()
        except Exception:
            pass

        return status


# Singleton instance
_unified_service: UnifiedDataService | None = None


def get_unified_data_service(db: Session | None = None) -> UnifiedDataService:
    """Get the unified data service.

    Args:
        db: Optional database session. If not provided, uses global singleton.

    Returns:
        UnifiedDataService instance
    """
    global _unified_service
    if db:
        # If db provided, return a new instance with that session
        return UnifiedDataService(db=db)
    if _unified_service is None:
        _unified_service = UnifiedDataService()
    return _unified_service
