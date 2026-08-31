"""Unit tests for UnifiedDataService — date parsing, dedup, leaderboard aggregation."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.unified_data_service import (
    UnifiedDataService,
    UnifiedLeaderboardEntry,
    UnifiedRound,
)


def make_service():
    """Create a UnifiedDataService with mocked sheet clients."""
    with patch("app.services.unified_data_service.SpreadsheetSyncService"):
        svc = UnifiedDataService(db=MagicMock())
    return svc


# ── UnifiedRound dataclass ────────────────────────────────────────────────────


class TestUnifiedRound:
    def test_equal_rounds_are_deduplicated(self):
        r1 = UnifiedRound("6-Apr", "2026-04-06", "A", "Stuart", 4, "Wing Point")
        r2 = UnifiedRound("6-Apr", "2026-04-06", "A", "Stuart", 4, "Wing Point")
        assert r1 == r2
        assert len({r1, r2}) == 1  # Set dedup

    def test_different_scores_are_not_equal(self):
        r1 = UnifiedRound("6-Apr", "2026-04-06", "A", "Stuart", 4, "Wing Point")
        r2 = UnifiedRound("6-Apr", "2026-04-06", "A", "Stuart", 8, "Wing Point")
        assert r1 != r2

    def test_different_members_are_not_equal(self):
        r1 = UnifiedRound("6-Apr", "2026-04-06", "A", "Stuart", 4, "Wing Point")
        r2 = UnifiedRound("6-Apr", "2026-04-06", "A", "Jeff", 4, "Wing Point")
        assert r1 != r2

    def test_hole_scores_defaults_to_none(self):
        assert UnifiedRound("6-Apr", "2026-04-06", "A", "Stuart", 4, "Wing Point").hole_scores is None


# ── hole-by-hole detail: only real for in-app/scanned rounds, never legacy sheet ──


class TestHoleScoresPlumbing:
    def test_legacy_round_with_empty_dict_hole_scores_has_none(self):
        """The model default (and every real writer) leaves this as {} — never
        a populated list — so it must come through as None, not a truthy {}."""
        svc = make_service()
        row = MagicMock(
            date="2026-04-06", group="A", member="Stuart", score=4, location="Wing Point", duration=None, hole_scores={}
        )

        unified = svc._legacy_round_to_unified(row)

        assert unified.hole_scores is None

    def test_legacy_round_with_populated_list_passes_through(self):
        svc = make_service()
        holes = [{"hole": 1, "quarters": 2}]
        row = MagicMock(
            date="2026-04-06",
            group="A",
            member="Stuart",
            score=4,
            location="Wing Point",
            duration=None,
            hole_scores=holes,
        )

        unified = svc._legacy_round_to_unified(row)

        assert unified.hole_scores == holes

    def test_db_result_with_real_hole_scores_passes_through(self):
        svc = make_service()
        holes = [{"hole": 1, "quarters": 2, "gross_score": 5}, {"hole": 2, "quarters": -1, "gross_score": 4}]
        result = MagicMock(player_name="Stuart", total_earnings=1.0, hole_scores=holes)
        record = MagicMock(
            completed_at="2026-04-06T12:00:00", created_at=None, course_name="Wing Point", game_duration_minutes=None
        )

        unified = svc._db_result_to_unified(result, record)

        assert unified.hole_scores == holes
        assert unified.source == "database"

    def test_db_result_with_empty_hole_scores_has_none(self):
        svc = make_service()
        result = MagicMock(player_name="Stuart", total_earnings=1.0, hole_scores=[])
        record = MagicMock(
            completed_at="2026-04-06T12:00:00", created_at=None, course_name="Wing Point", game_duration_minutes=None
        )

        unified = svc._db_result_to_unified(result, record)

        assert unified.hole_scores is None


# ── UnifiedLeaderboardEntry ───────────────────────────────────────────────────


class TestUnifiedLeaderboardEntry:
    def test_recalculate_average_basic(self):
        entry = UnifiedLeaderboardEntry(member="Stuart", quarters=30, rounds=3)
        entry.recalculate_average()
        assert entry.average == 10.0

    def test_recalculate_average_zero_rounds(self):
        entry = UnifiedLeaderboardEntry(member="Stuart", quarters=0, rounds=0)
        entry.recalculate_average()
        assert entry.average == 0.0

    def test_recalculate_average_negative_quarters(self):
        entry = UnifiedLeaderboardEntry(member="Jeff", quarters=-20, rounds=4)
        entry.recalculate_average()
        assert entry.average == -5.0

    def test_sources_is_set(self):
        entry = UnifiedLeaderboardEntry(member="Gregg")
        assert isinstance(entry.sources, set)


# ── _parse_sheet_date ─────────────────────────────────────────────────────────


class TestParseSheetDate:
    def setup_method(self):
        self.svc = make_service()

    def test_parses_valid_dd_mon_format(self):
        with patch("app.services.unified_data_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 7)
            mock_dt.strptime.side_effect = datetime.strptime
            result = self.svc._parse_sheet_date("06-Apr")
        assert result == "2026-04-06"

    def test_invalid_format_returns_original(self):
        result = self.svc._parse_sheet_date("not-a-date")
        assert result == "not-a-date"

    def test_empty_string_returns_empty(self):
        result = self.svc._parse_sheet_date("")
        assert result == ""

    def test_future_date_shifts_to_last_year(self):
        """Dates >30 days in the future are assumed to be last year."""
        with patch("app.services.unified_data_service.datetime") as mock_dt:
            # "current date" is Jan 5 — so Dec 25 would be ~340 days in the future
            mock_dt.now.return_value = datetime(2026, 1, 5)
            mock_dt.strptime.side_effect = datetime.strptime
            result = self.svc._parse_sheet_date("25-Dec")
        assert result == "2025-12-25"

    def test_recent_past_date_stays_current_year(self):
        with patch("app.services.unified_data_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 15)
            mock_dt.strptime.side_effect = datetime.strptime
            result = self.svc._parse_sheet_date("10-Apr")
        assert result == "2026-04-10"

    def test_result_is_iso_format(self):
        result = self.svc._parse_sheet_date("06-Apr")
        # Should be parseable as a date or return original
        if result != "06-Apr":
            parts = result.split("-")
            assert len(parts) == 3


# ── get_unified_leaderboard (mocked data sources) ────────────────────────────


class TestGetUnifiedLeaderboard:
    @pytest.mark.parametrize("year", [2026, 2027])
    def test_season_cutoff_preserves_current_results_and_all_time_history(self, year):
        svc = make_service()
        rows = [
            UnifiedRound("20-Jul", f"{year}-07-20", "A", "Stuart", -27, "Wing Point", source="primary_sheet"),
            UnifiedRound("30-Aug", f"{year}-08-30", "A", "Stuart", 525, "Wing Point", source="primary_sheet"),
            UnifiedRound("26-Jun", f"{year}-06-26", "A", "Stuart", -257, "Wing Point", source="database"),
            UnifiedRound("19-Jul", f"{year}-07-19", "A", "Old Player", 999, "Wing Point", source="database"),
            UnifiedRound("19-Jul", f"{year}-07-19", "A", "Old Member", 999, "Wing Point", source="member"),
            UnifiedRound("20-Jul", f"{year}-07-20", "B", "Stuart", 2, "Wing Point", source="database"),
            UnifiedRound("31-Aug", f"{year}-08-31", "A", "Stuart", 4, "Wing Point", source="member"),
            UnifiedRound("1-Jan", f"{year + 1}-01-01", "A", "Stuart", 8, "Wing Point", source="database"),
            UnifiedRound("30-Aug", f"{year}-08-30", "A", "Jeff", -10, "Wing Point", source="primary_sheet"),
            UnifiedRound("bad", "not-a-date", "A", "Bad Sheet Date", 999, "Wing Point", source="primary_sheet"),
            UnifiedRound("bad", "2026-99-99", "A", "Bad App Date", 999, "Wing Point", source="database"),
        ]
        with patch.object(svc, "get_all_rounds", return_value=rows):
            leaderboard = svc.get_unified_leaderboard()
            assert [entry.member for entry in leaderboard] == ["Stuart", "Jeff"]
            stuart = leaderboard[0]
            assert (stuart.quarters, stuart.rounds, stuart.average) == (512, 5, 102.4)
            assert (stuart.best_round, stuart.worst_round) == (525, -27)
            assert stuart.sources == {"primary_sheet", "database", "member"}
            # Season filtering must not change the all-time history API.
            assert len(svc.get_player_history("Stuart")) == 6
            assert svc.get_player_history("Old Player")[0].score == 999

    @pytest.mark.parametrize("sheet_date", [None, "", "not-a-date"])
    def test_missing_season_dates_does_not_fall_back_to_all_time(self, sheet_date):
        svc = make_service()
        rows = [UnifiedRound("26-Jun", "2026-06-26", "A", "Stuart", -257, "Wing Point", source="database")]
        if sheet_date is not None:
            rows.append(UnifiedRound("bad", sheet_date, "A", "Jeff", 257, "Wing Point", source="primary_sheet"))
        with patch.object(svc, "get_all_rounds", return_value=rows):
            assert svc.get_unified_leaderboard() == []

    def test_live_fetch_skips_writable_sheet(self):
        """Prior-season writable copy must not be merged into season-of-record data."""
        svc = make_service()
        svc.primary_sheet = MagicMock()
        svc.primary_sheet.get_all_rounds.return_value = []
        svc._db = MagicMock()
        # Would fail AttributeError if code still called writable_sheet
        assert not hasattr(svc, "writable_sheet")
        rounds = svc.get_all_rounds(include_database=False, use_sheet_cache=False)
        assert rounds == []
        svc.primary_sheet.get_all_rounds.assert_called_once()


def test_writable_sheet_is_season_primary():
    """App→sheet writes must target the same 2026-27 workbook as reads."""
    from app.services.spreadsheet_sync_service import PRIMARY_SHEET_ID, WRITABLE_SHEET_ID

    assert WRITABLE_SHEET_ID == PRIMARY_SHEET_ID
    assert PRIMARY_SHEET_ID == "141s8V_UACdBc8Xg17W0UhWxd08BMbEImkXOSPa66RfQ"
