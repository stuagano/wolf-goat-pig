"""Unit tests for PairingSchedulerService — Sunday game pairing generation."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.pairing_scheduler_service import PairingSchedulerService


# ── get_next_sunday ───────────────────────────────────────────────────────────

class TestGetNextSunday:
    def test_returns_next_sunday_from_monday(self):
        # Monday 2026-04-06 → next Sunday 2026-04-12
        monday = datetime(2026, 4, 6)  # weekday() == 0
        result = PairingSchedulerService.get_next_sunday(monday)
        assert result == "2026-04-12"

    def test_returns_next_sunday_from_saturday(self):
        # Saturday 2026-04-11 → next Sunday 2026-04-12
        saturday = datetime(2026, 4, 11)
        result = PairingSchedulerService.get_next_sunday(saturday)
        assert result == "2026-04-12"

    def test_returns_same_sunday_when_given_sunday(self):
        # Sunday 2026-04-12 → same day 2026-04-12
        sunday = datetime(2026, 4, 12)
        result = PairingSchedulerService.get_next_sunday(sunday)
        assert result == "2026-04-12"

    def test_returns_next_sunday_from_friday(self):
        friday = datetime(2026, 4, 10)
        result = PairingSchedulerService.get_next_sunday(friday)
        assert result == "2026-04-12"

    def test_result_format_is_yyyy_mm_dd(self):
        result = PairingSchedulerService.get_next_sunday(datetime(2026, 1, 1))
        parts = result.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4  # year
        assert len(parts[1]) == 2  # month
        assert len(parts[2]) == 2  # day

    def test_uses_datetime_now_when_no_from_date(self):
        with patch("app.services.pairing_scheduler_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 6)  # Monday
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = PairingSchedulerService.get_next_sunday()
        assert result == "2026-04-12"

    def test_crosses_month_boundary(self):
        # Friday Jan 30 2026 → Sunday Feb 1 2026
        result = PairingSchedulerService.get_next_sunday(datetime(2026, 1, 30))
        assert result == "2026-02-01"

    def test_crosses_year_boundary(self):
        # Tuesday Dec 29 2026 → Sunday Jan 3 2027
        result = PairingSchedulerService.get_next_sunday(datetime(2026, 12, 29))
        assert result == "2027-01-03"


# ── get_signups_for_date ──────────────────────────────────────────────────────

class TestGetSignupsForDate:
    def test_returns_active_signups_only(self):
        db = MagicMock()
        active_signup = MagicMock(date="2026-04-12", status="signed_up")
        withdrawn = MagicMock(date="2026-04-12", status="withdrawn")

        query_chain = db.query.return_value.filter.return_value.filter.return_value
        query_chain.all.return_value = [active_signup]

        result = PairingSchedulerService.get_signups_for_date(db, "2026-04-12")
        assert result == [active_signup]

    def test_returns_empty_when_no_signups(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = PairingSchedulerService.get_signups_for_date(db, "2026-04-12")
        assert result == []


# ── get_existing_pairing ──────────────────────────────────────────────────────

class TestGetExistingPairing:
    def test_returns_pairing_when_exists(self):
        db = MagicMock()
        existing = MagicMock(game_date="2026-04-12")
        db.query.return_value.filter.return_value.first.return_value = existing
        result = PairingSchedulerService.get_existing_pairing(db, "2026-04-12")
        assert result == existing

    def test_returns_none_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = PairingSchedulerService.get_existing_pairing(db, "2026-04-12")
        assert result is None


# ── build_player_list ─────────────────────────────────────────────────────────

class TestBuildPlayerList:
    def test_uses_handicap_from_profile_when_available(self):
        db = MagicMock()
        signup = MagicMock(player_name="Stuart", player_profile_id=1)
        profile = MagicMock(handicap=10.5)
        db.query.return_value.filter.return_value.first.return_value = profile

        result = PairingSchedulerService.build_player_list(db, [signup])
        assert result[0]["handicap"] == 10.5
        assert result[0]["player_name"] == "Stuart"

    def test_defaults_to_18_when_no_profile(self):
        db = MagicMock()
        signup = MagicMock(player_name="Jeff", player_profile_id=None)

        result = PairingSchedulerService.build_player_list(db, [signup])
        assert result[0]["handicap"] == 18.0

    def test_defaults_to_18_when_profile_has_no_handicap(self):
        db = MagicMock()
        signup = MagicMock(player_name="Gregg", player_profile_id=2)
        profile = MagicMock(handicap=None)
        db.query.return_value.filter.return_value.first.return_value = profile

        result = PairingSchedulerService.build_player_list(db, [signup])
        assert result[0]["handicap"] == 18.0

    def test_builds_all_players(self):
        db = MagicMock()
        signups = [
            MagicMock(player_name=f"Player {i}", player_profile_id=None)
            for i in range(6)
        ]
        result = PairingSchedulerService.build_player_list(db, signups)
        assert len(result) == 6

    def test_player_dict_has_required_keys(self):
        db = MagicMock()
        signup = MagicMock(player_name="Allen", player_profile_id=None)
        result = PairingSchedulerService.build_player_list(db, [signup])
        assert "player_name" in result[0]
        assert "player_profile_id" in result[0]
        assert "handicap" in result[0]


# ── find_player_team ──────────────────────────────────────────────────────────

class TestFindPlayerTeam:
    def _teams(self):
        return [
            {"players": [{"player_name": "Stuart"}, {"player_name": "Jeff"}]},
            {"players": [{"player_name": "Gregg"}, {"player_name": "Allen"}]},
        ]

    def test_finds_player_in_team_1(self):
        assert PairingSchedulerService.find_player_team("Stuart", self._teams()) == 1

    def test_finds_player_in_team_2(self):
        assert PairingSchedulerService.find_player_team("Allen", self._teams()) == 2

    def test_returns_none_for_unknown_player(self):
        assert PairingSchedulerService.find_player_team("Unknown", self._teams()) is None

    def test_returns_none_for_empty_teams(self):
        assert PairingSchedulerService.find_player_team("Stuart", []) is None


# ── generate_pairings ─────────────────────────────────────────────────────────

class TestGeneratePairings:
    def _mock_db_with_signups(self, n_players: int, existing_pairing=None):
        """Build a DB mock that returns n_players signups."""
        db = MagicMock()

        # get_existing_pairing → filter().first()
        db.query.return_value.filter.return_value.first.return_value = existing_pairing

        # get_signups_for_date → filter().filter().all()
        signups = [
            MagicMock(player_name=f"Player {i}", player_profile_id=None)
            for i in range(n_players)
        ]
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = signups

        return db

    def test_returns_message_when_insufficient_players(self):
        db = self._mock_db_with_signups(3)  # < 4 players
        pairing, msg = PairingSchedulerService.generate_pairings(db, "2026-04-12")
        assert pairing is None
        assert "Not enough" in msg

    def test_returns_existing_pairing_without_force(self):
        existing = MagicMock(game_date="2026-04-12")
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        pairing, msg = PairingSchedulerService.generate_pairings(db, "2026-04-12", force_regenerate=False)
        assert pairing == existing
        assert "already exist" in msg

    def test_generates_pairing_with_enough_players(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        signups = [
            MagicMock(player_name=f"Player {i}", player_profile_id=None)
            for i in range(8)
        ]
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = signups

        with patch("app.services.pairing_scheduler_service.TeamFormationService") as mock_tfs:
            mock_tfs.generate_random_teams.return_value = [
                {"players": [{"player_name": "Player 0"}, {"player_name": "Player 1"},
                              {"player_name": "Player 2"}, {"player_name": "Player 3"}]},
                {"players": [{"player_name": "Player 4"}, {"player_name": "Player 5"},
                              {"player_name": "Player 6"}, {"player_name": "Player 7"}]},
            ]
            pairing, msg = PairingSchedulerService.generate_pairings(db, "2026-04-12")

        assert pairing is not None
        assert "Generated" in msg
        assert db.add.called
        assert db.commit.called

    def test_returns_none_when_team_formation_fails(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        signups = [MagicMock(player_name=f"P{i}", player_profile_id=None) for i in range(4)]
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = signups

        with patch("app.services.pairing_scheduler_service.TeamFormationService") as mock_tfs:
            mock_tfs.generate_random_teams.return_value = []
            pairing, msg = PairingSchedulerService.generate_pairings(db, "2026-04-12")

        assert pairing is None
        assert "Failed" in msg
