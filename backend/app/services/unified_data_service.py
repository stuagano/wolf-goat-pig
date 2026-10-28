"""Unified data service that merges data from all sources.

This service provides a single view of all game data by merging:
1. Primary spreadsheet (season-of-record Google Sheet)
2. Database (games recorded directly in the app)

The old transition-era writable sheet copy is no longer read — it held prior-
season rounds and was polluting the 2026-27 leaderboard after the sheet cutover.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from ..database import get_db
from ..models import GamePlayerResult, GameRecord, GameStateModel, LegacyRound
from ..utils.time import utc_now
from .completed_game_service import round_played_at
from .round_identity import course_name, group_rounds, link_saved_cards, normalized, round_day
from .spreadsheet_sync_service import PRIMARY_SHEET_ID, RoundResult, SpreadsheetSyncService

logger = logging.getLogger(__name__)

SHEET_SOURCES = {"primary_sheet", "writable_sheet"}
DUPLICATE_WINDOW_DAYS = 6


@dataclass
class UnifiedRound:
    """A round result from any source."""

    date: str  # DD-Mon format for display
    date_sortable: str | None  # Known played date only in canonical mode
    group: str
    member: str
    score: float | None  # Unknown is not zero; retain fractional quarters
    location: str | None
    duration: str | None = None
    source: str = "unknown"  # "primary_sheet", "writable_sheet", "database"
    # Per-hole detail — only ever populated for rounds scored live in the app
    # or recorded via scorecard scan (both write real GamePlayerResult rows).
    # Legacy/sheet-only rounds never have this; it's just a running total.
    hole_scores: list[dict[str, Any]] | None = None
    # Rows from one game share a key; used to match app/member copies to the sheet.
    game_key: tuple | None = None
    # The saved game's UUID, when this round is backed by a reachable app card.
    # Sheet-only and member-posted rounds have none; linking copies it onto
    # sheet rows only when exactly one app game matches them unambiguously.
    game_id: str | None = None
    # True only when ``date_sortable`` is the date the round was played rather
    # than the date the app finished or uploaded it. Dedup trusts a known date.
    played_date_known: bool = False
    player_id: int | None = None
    participant_id: str | None = None
    score_eligible: bool = True
    detail_coverage: str | None = None

    def __hash__(self):
        """Canonical identity is the persisted UUID/participant, never labels or totals."""
        if self.source == "canonical":
            return hash((self.source, self.game_key))
        return hash((self.date, self.group, self.member, self.score))

    def __eq__(self, other):
        if not isinstance(other, UnifiedRound):
            return False
        if self.source == "canonical" or other.source == "canonical":
            return self.source == other.source and self.game_key == other.game_key
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
    quarters: float = 0  # Total quarters won/lost
    rounds: int = 0  # Number of rounds played
    average: float | None = 0.0  # None when canonical scored sample is empty
    best_round: float | None = 0  # Best single round score
    worst_round: float | None = 0  # Worst single round score
    sources: set[str] = field(default_factory=set)  # Which sources contributed data
    player_id: int | None = None
    known_participation_count: int = 0
    incomplete_round_count: int = 0

    def recalculate_average(self):
        """Recalculate average based on total and rounds."""
        if self.rounds > 0:
            self.average = self.quarters / self.rounds


def _keep_first(rounds: dict[tuple, UnifiedRound], r: UnifiedRound) -> None:
    """Remove exact cache duplicates without collapsing distinct source games."""
    rounds.setdefault((r.game_key, r.source, r.date_sortable, r.group, r.location, r.member, r.score), r)


class UnifiedDataService:
    """Service that merges data from spreadsheets and database."""

    def __init__(self, db: Session | None = None):
        self.primary_sheet = SpreadsheetSyncService(PRIMARY_SHEET_ID)
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
            game_key=(source, r.date, r.group, r.location),
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
            # Member posts may omit group/location; the API models require strings.
            group=r.group or "",
            member=r.member,
            score=r.score,
            location=r.location or "",
            duration=r.duration,
            source=r.source,
            hole_scores=r.hole_scores if isinstance(r.hole_scores, list) and r.hole_scores else None,
            game_key=(
                ("member", r.date, r.submitted_by_profile_id)
                if r.source == "member"
                else (r.source, r.date, r.group, r.location)
            ),
        )

    def _db_result_to_unified(
        self, result: GamePlayerResult, record: GameRecord, game: GameStateModel | None = None
    ) -> UnifiedRound:
        """Convert a database game result to unified format."""
        # Convert database date format to DD-Mon
        try:
            dt = datetime.fromisoformat(round_played_at(record, game).replace("Z", "+00:00"))
            date_display = dt.strftime("%-d-%b")
            date_sortable = dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            date_display = "Unknown"
            date_sortable = "1900-01-01"

        settings = record.game_settings
        explicit_date = isinstance(settings, dict) and bool(settings.get("played_at"))
        scan_date = game is not None and isinstance(game.state, dict) and game.state.get("source") == "scorecard_scan"
        played_date_known = date_display != "Unknown" and bool(explicit_date or scan_date)

        return UnifiedRound(
            date=date_display,
            date_sortable=date_sortable,
            group="A",  # Database doesn't track groups
            member=result.player_name,
            score=int(result.total_earnings),  # Convert earnings to quarters
            location=record.course_name or "Unknown",
            duration=(f"{record.game_duration_minutes}:00" if record.game_duration_minutes else None),
            source="database",
            hole_scores=result.hole_scores if isinstance(result.hole_scores, list) and result.hole_scores else None,
            game_key=("database", record.id),
            # Only a reachable saved game can be opened as a card; a GameRecord
            # whose game_state row is gone must not advertise a dead route.
            game_id=str(game.game_id) if game is not None and game.game_id else None,
            played_date_known=played_date_known,
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
        from .canonical_round_reads import accepted_rows, canonical_mode

        db = self._get_db()
        if canonical_mode(db):
            rows, eligible = accepted_rows(db)
            return sorted(
                [
                    UnifiedRound(
                        date=record.played_on.strftime("%-d-%b") if record.played_on else record.raw_date or "Unknown",
                        date_sortable=record.played_on.isoformat() if record.played_on else None,
                        group=record.group or "",
                        member=result.player_name,
                        score=result.total_earnings,
                        location=record.course_name,
                        source="canonical",
                        game_id=str(record.game_id),
                        game_key=(str(record.game_id), result.participant_id),
                        participant_id=result.participant_id,
                        player_id=result.player_profile_id,
                        played_date_known=record.played_on is not None,
                        score_eligible=record.id in eligible and record.played_on is not None,
                        detail_coverage=record.detail_coverage,
                        hole_scores=result.hole_scores,
                    )
                    for record, result in rows
                ],
                key=lambda r: (r.date_sortable or "", r.game_id, r.participant_id),
                reverse=True,
            )

        all_rounds: dict[tuple, UnifiedRound] = {}

        if use_sheet_cache:
            # Fast path: read from legacy_rounds DB cache
            try:
                db = self._get_db()
                # Exclude pending member-posted rounds — they are not
                # authoritative until a foursome member attests them. Sheet/db
                # rows default to status='attested' so they are unaffected.
                # Also skip retired writable_sheet rows from the prior season.
                for r in (
                    db.query(LegacyRound)
                    .filter(LegacyRound.status != "pending", LegacyRound.source != "writable_sheet")
                    .all()
                ):
                    unified = self._legacy_round_to_unified(r)
                    _keep_first(all_rounds, unified)
            except Exception as e:
                logger.warning(f"Failed to read legacy_rounds cache: {e}")
        else:
            # Slow path: live Sheets API — used only by the sync job itself.
            # Primary season sheet only; the old writable copy is retired.
            try:
                for r in self.primary_sheet.get_all_rounds():
                    unified = self._sheet_round_to_unified(r, "primary_sheet")
                    _keep_first(all_rounds, unified)
            except Exception as e:
                logger.warning(f"Failed to fetch primary sheet: {e}")

        # Merge in-app GameRecord results
        if include_database:
            try:
                db = self._get_db()
                records = (
                    db.query(GameRecord, GameStateModel)
                    .outerjoin(GameStateModel, GameStateModel.game_id == GameRecord.game_id)
                    .filter(GameRecord.completed_at.isnot(None))
                    .all()
                )
                for record, game in records:
                    results = db.query(GamePlayerResult).filter(GamePlayerResult.game_record_id == record.id).all()
                    for result in results:
                        unified = self._db_result_to_unified(result, record, game)
                        # Distinct participants can share both a name and a score.
                        # Sheet copies are reconciled by whole game below.
                        all_rounds[("database", result.id)] = unified
            except Exception as e:
                logger.warning(f"Failed to fetch database records: {e}")

        rounds = self._drop_sheet_duplicates(list(all_rounds.values()))
        return sorted(rounds, key=lambda r: r.date_sortable, reverse=True)

    @staticmethod
    def _drop_sheet_duplicates(rounds: list[UnifiedRound]) -> list[UnifiedRound]:
        """The sheet is authoritative: drop app/member games the sheet already has.

        App rounds are dated when finished or scanned, and scans or posts can be
        off by a few quarters or a spelling, so a game matches a sheet game within
        DUPLICATE_WINDOW_DAYS that has the same players or the same totals. A round
        whose real played date is known only matches that same day, so a foursome
        replaying later in the week keeps its own round.

        Suppressing a duplicate total is a weaker claim than identifying a card, so
        the saved game id and its per-hole detail come from ``link_saved_cards``
        instead of this approximate match.
        """
        sheet_games = group_rounds([r for r in rounds if r.source in SHEET_SOURCES])
        other_games = group_rounds([r for r in rounds if r.source not in SHEET_SOURCES])
        link_saved_cards(sheet_games, other_games)

        indexed = [
            (round_day(g), {normalized(r.member) for r in g}, sorted(r.score for r in g), g) for g in sheet_games
        ]
        kept = [r for g in sheet_games for r in g]
        for g in other_games:
            day, players, totals = round_day(g), {normalized(r.member) for r in g}, sorted(r.score for r in g)
            window = 0 if g[0].played_date_known else DUPLICATE_WINDOW_DAYS
            course = course_name(g[0].location)
            matches = [
                sheet
                for sheet_day, sheet_players, sheet_totals, sheet in indexed
                if day
                and sheet_day
                and abs((sheet_day - day).days) <= window
                and (sheet_players == players or sheet_totals == totals)
                # A known course never matches a different known course.
                and not (course and course_name(sheet[0].location) and course_name(sheet[0].location) != course)
            ]
            if not matches:
                kept.extend(g)
        return kept

    def get_unified_leaderboard(self) -> list[UnifiedLeaderboardEntry]:
        """Get the current season leaderboard, leaving all-time history intact.

        Returns:
            List of leaderboard entries sorted by total quarters (descending)
        """
        from .canonical_round_reads import canonical_mode

        if canonical_mode(self._get_db()):
            entries = {}
            for row in self.get_season_rounds():
                if row.player_id is None:
                    continue
                entry = entries.setdefault(
                    row.player_id,
                    UnifiedLeaderboardEntry(
                        member=row.member, player_id=row.player_id, average=None, best_round=None, worst_round=None
                    ),
                )
                entry.known_participation_count += 1
                entry.sources.add(row.source)
                if not row.score_eligible:
                    entry.incomplete_round_count += 1
                    continue
                entry.quarters += row.score
                entry.rounds += 1
                entry.best_round = row.score if entry.rounds == 1 else max(entry.best_round, row.score)
                entry.worst_round = row.score if entry.rounds == 1 else min(entry.worst_round, row.score)
                entry.recalculate_average()
            return sorted(entries.values(), key=lambda e: (-e.quarters, e.player_id))

        dated_rounds = self._dated_rounds()

        # ponytail: the season sheet's first round defines the cutoff; use an
        # explicit season calendar if app play must precede the first sheet round.
        season_start = min((day for day, r in dated_rounds if r.source == "primary_sheet"), default=None)
        if season_start is None:
            logger.warning("No dated season sheet rounds; withholding the leaderboard")
            return []

        # Aggregate by player
        player_stats: dict[str, UnifiedLeaderboardEntry] = {}

        for day, round_data in dated_rounds:
            if day < season_start:
                continue
            member = round_data.member
            if member not in player_stats:
                player_stats[member] = UnifiedLeaderboardEntry(member=member)

            entry = player_stats[member]
            entry.quarters += round_data.score
            entry.rounds += 1
            entry.sources.add(round_data.source)

            # Track best/worst
            if entry.best_round is None or round_data.score > entry.best_round:
                entry.best_round = round_data.score
            if entry.worst_round is None or round_data.score < entry.worst_round:
                entry.worst_round = round_data.score

        # Calculate averages
        for entry in player_stats.values():
            entry.recalculate_average()

        # Sort by total quarters (descending)
        sorted_leaderboard = sorted(player_stats.values(), key=lambda e: e.quarters, reverse=True)
        return sorted_leaderboard

    def _dated_rounds(self) -> list[tuple[date, UnifiedRound]]:
        """Rounds with a parseable ISO date, in the order get_all_rounds returns them."""
        dated: list[tuple[date, UnifiedRound]] = []
        for round_data in self.get_all_rounds():
            try:
                dated.append((date.fromisoformat(round_data.date_sortable), round_data))
            except (TypeError, ValueError):
                logger.warning("Skipping round with invalid date: %r", round_data.date_sortable)
        return dated

    def get_season_rounds(self) -> list[UnifiedRound]:
        """Current-season rounds, newest first. Empty when the season start is unknown."""
        from ..schemas.round_identity import read_round_identity_config

        config = read_round_identity_config(self._get_db())
        if config.mode != "legacy":
            return [
                r
                for r in self.get_all_rounds()
                if r.date_sortable
                and config.season is not None
                and date.fromisoformat(r.date_sortable).year == config.season
            ]
        dated = self._dated_rounds()
        start = min((day for day, r in dated if r.source == "primary_sheet"), default=None)
        if start is None:
            return []
        # get_all_rounds is newest-first, but callers may pass unsorted rows.
        season = [r for day, r in dated if day >= start]
        return sorted(season, key=lambda r: r.date_sortable, reverse=True)

    def get_profile_history(self, player_id: int) -> list[UnifiedRound]:
        """Use only persisted verified profile association, never display-name matching."""
        return [r for r in self.get_all_rounds() if r.player_id == player_id]

    def get_player_history(self, member_name: str) -> list[UnifiedRound]:
        """Get all rounds for a specific player across all sources.

        Args:
            member_name: Player name (case-insensitive match)

        Returns:
            List of rounds for the player, sorted by date (most recent first)
        """
        from ..models import PlayerProfile
        from .canonical_round_reads import canonical_mode

        if canonical_mode(self._get_db()):
            profiles = [
                p
                for p in self._get_db().query(PlayerProfile).all()
                if member_name.lower() in {(p.name or "").lower(), (p.legacy_name or "").lower()}
            ]
            return self.get_profile_history(profiles[0].id) if len(profiles) == 1 else []
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
        date_rounds = [r for r in all_rounds if r.date == date or r.date_sortable == date]
        return date_rounds

    def get_data_sources_status(self) -> dict[str, Any]:
        """Get status of all data sources.

        Returns:
            Status info for each source including record counts
        """
        from .canonical_round_reads import canonical_mode

        if canonical_mode(self._get_db()):
            rows = self.get_all_rounds()
            empty = {"available": False, "record_count": 0}
            return {
                "primary_sheet": empty.copy(),
                "writable_sheet": empty.copy(),
                "database": {"available": True, "record_count": len(rows)},
                "unified_total": len(rows),
                "deduplicated_total": len(rows),
            }
        status: dict[str, Any] = {
            "primary_sheet": {
                "available": False,
                "record_count": 0,
                "id": PRIMARY_SHEET_ID,
            },
            "writable_sheet": {
                "available": False,
                "record_count": 0,
                "id": PRIMARY_SHEET_ID,
                "note": "Same workbook as primary_sheet (season of record)",
            },
            "database": {"available": False, "record_count": 0},
            "unified_total": 0,
            "deduplicated_total": 0,
        }

        try:
            db = self._get_db()
            primary_count = db.query(LegacyRound).filter(LegacyRound.source == "primary_sheet").count()
            status["primary_sheet"]["available"] = primary_count > 0
            status["primary_sheet"]["record_count"] = primary_count
        except Exception as e:
            status["primary_sheet"]["error"] = str(e)

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

        status["unified_total"] = status["primary_sheet"]["record_count"] + status["database"]["record_count"]

        try:
            db = self._get_db()
            status["deduplicated_total"] = db.query(LegacyRound).filter(LegacyRound.source != "writable_sheet").count()
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
