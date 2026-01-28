"""Unified data service that merges data from all sources.

This service provides a single view of all game data by merging:
1. Primary spreadsheet (read-only legacy data)
2. Writable spreadsheet (app-entered data during transition)
3. Render database (games recorded directly in the app)

The service deduplicates data and provides a unified leaderboard and round history.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GamePlayerResult, GameRecord, PlayerProfile
from .spreadsheet_sync_service import (
    PRIMARY_SHEET_ID,
    WRITABLE_SHEET_ID,
    RoundResult,
    SpreadsheetSyncService,
)

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
    duration: Optional[str] = None
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
    sources: Set[str] = field(default_factory=set)  # Which sources contributed data

    def recalculate_average(self):
        """Recalculate average based on total and rounds."""
        if self.rounds > 0:
            self.average = self.quarters / self.rounds


class UnifiedDataService:
    """Service that merges data from spreadsheets and database."""

    def __init__(self, db: Optional[Session] = None):
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
            current_year = datetime.now().year
            dt = datetime.strptime(f"{date_str}-{current_year}", "%d-%b-%Y")

            # If date is in the future by more than a month, it's probably last year
            if dt > datetime.now() and (dt - datetime.now()).days > 30:
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
            duration=f"{record.game_duration_minutes}:00" if record.game_duration_minutes else None,
            source="database",
        )

    def get_all_rounds(self, include_database: bool = True) -> List[UnifiedRound]:
        """Get all rounds from all sources, deduplicated.

        Args:
            include_database: Whether to include database records (default True)

        Returns:
            List of unified rounds, sorted by date (most recent first)
        """
        all_rounds: Dict[Tuple, UnifiedRound] = {}

        # 1. Get primary spreadsheet data
        try:
            primary_rounds = self.primary_sheet.get_all_rounds()
            for r in primary_rounds:
                unified = self._sheet_round_to_unified(r, "primary_sheet")
                key = (unified.date, unified.group, unified.member, unified.score)
                if key not in all_rounds:
                    all_rounds[key] = unified
        except Exception as e:
            logger.warning(f"Failed to fetch primary sheet: {e}")

        # 2. Get writable spreadsheet data (may overlap with primary)
        try:
            writable_rounds = self.writable_sheet.get_all_rounds()
            for r in writable_rounds:
                unified = self._sheet_round_to_unified(r, "writable_sheet")
                key = (unified.date, unified.group, unified.member, unified.score)
                if key not in all_rounds:
                    all_rounds[key] = unified
                # If already exists from primary, keep primary as source of truth
        except Exception as e:
            logger.warning(f"Failed to fetch writable sheet: {e}")

        # 3. Get database records
        if include_database:
            try:
                db = self._get_db()
                records = db.query(GameRecord).filter(GameRecord.completed_at.isnot(None)).all()

                for record in records:
                    results = db.query(GamePlayerResult).filter(GamePlayerResult.game_record_id == record.id).all()
                    for result in results:
                        unified = self._db_result_to_unified(result, record)
                        key = (unified.date, unified.group, unified.member, unified.score)
                        if key not in all_rounds:
                            all_rounds[key] = unified
            except Exception as e:
                logger.warning(f"Failed to fetch database records: {e}")

        # Sort by date (most recent first)
        sorted_rounds = sorted(all_rounds.values(), key=lambda r: r.date_sortable, reverse=True)
        return sorted_rounds

    def get_unified_leaderboard(self) -> List[UnifiedLeaderboardEntry]:
        """Get unified leaderboard aggregating all sources.

        Returns:
            List of leaderboard entries sorted by total quarters (descending)
        """
        all_rounds = self.get_all_rounds()

        # Aggregate by player
        player_stats: Dict[str, UnifiedLeaderboardEntry] = {}

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

    def get_player_history(self, member_name: str) -> List[UnifiedRound]:
        """Get all rounds for a specific player across all sources.

        Args:
            member_name: Player name (case-insensitive match)

        Returns:
            List of rounds for the player, sorted by date (most recent first)
        """
        all_rounds = self.get_all_rounds()
        player_rounds = [r for r in all_rounds if r.member.lower() == member_name.lower()]
        return player_rounds

    def get_rounds_by_date(self, date: str) -> List[UnifiedRound]:
        """Get all rounds for a specific date.

        Args:
            date: Date in DD-Mon format (e.g., "27-Jan")

        Returns:
            List of rounds for that date
        """
        all_rounds = self.get_all_rounds()
        date_rounds = [r for r in all_rounds if r.date == date]
        return date_rounds

    def get_data_sources_status(self) -> Dict[str, Any]:
        """Get status of all data sources.

        Returns:
            Status info for each source including record counts
        """
        status = {
            "primary_sheet": {"available": False, "record_count": 0, "id": PRIMARY_SHEET_ID},
            "writable_sheet": {"available": False, "record_count": 0, "id": WRITABLE_SHEET_ID},
            "database": {"available": False, "record_count": 0},
            "unified_total": 0,
            "deduplicated_total": 0,
        }

        try:
            primary_rounds = self.primary_sheet.get_all_rounds()
            status["primary_sheet"]["available"] = True
            status["primary_sheet"]["record_count"] = len(primary_rounds)
        except Exception as e:
            status["primary_sheet"]["error"] = str(e)

        try:
            writable_rounds = self.writable_sheet.get_all_rounds()
            status["writable_sheet"]["available"] = True
            status["writable_sheet"]["record_count"] = len(writable_rounds)
        except Exception as e:
            status["writable_sheet"]["error"] = str(e)

        try:
            db = self._get_db()
            db_count = (
                db.query(GamePlayerResult)
                .join(GameRecord, GamePlayerResult.game_record_id == GameRecord.id)
                .filter(GameRecord.completed_at.isnot(None))
                .count()
            )
            status["database"]["available"] = True
            status["database"]["record_count"] = db_count
        except Exception as e:
            status["database"]["error"] = str(e)

        # Calculate totals
        status["unified_total"] = (
            status["primary_sheet"]["record_count"]
            + status["writable_sheet"]["record_count"]
            + status["database"]["record_count"]
        )

        try:
            unified_rounds = self.get_all_rounds()
            status["deduplicated_total"] = len(unified_rounds)
        except Exception:
            pass

        return status


# Singleton instance
_unified_service: Optional[UnifiedDataService] = None


def get_unified_data_service(db: Optional[Session] = None) -> UnifiedDataService:
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
