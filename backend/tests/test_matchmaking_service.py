"""
Unit tests for MatchmakingService

Tests player availability matching and group formation for 4-player golf groups.
"""

import pytest
from datetime import time
from app.services.matchmaking_service import MatchmakingService


class TestTimeStringParsing:
    """Test time string parsing"""

    def test_parse_valid_time_string(self):
        """Test parsing valid time strings"""
        result = MatchmakingService.parse_time_string("9:00 AM")
        assert result == time(9, 0)

    def test_parse_pm_time_string(self):
        """Test parsing PM time strings"""
        result = MatchmakingService.parse_time_string("2:30 PM")
        assert result == time(14, 30)

    def test_parse_invalid_time_string(self):
        """Test invalid time string returns None"""
        result = MatchmakingService.parse_time_string("invalid")
        assert result is None

    def test_parse_none_time_string(self):
        """Test None time string returns None"""
        result = MatchmakingService.parse_time_string(None)
        assert result is None


class TestTimeOverlap:
    """Test time overlap calculation"""

    def test_get_time_overlap_with_times(self):
        """Test finding overlap when players have specific times"""
        players_availability = [
            {'available_from_time': '8:00 AM', 'available_to_time': '12:00 PM'},
            {'available_from_time': '9:00 AM', 'available_to_time': '2:00 PM'},
            {'available_from_time': '10:00 AM', 'available_to_time': '1:00 PM'},
            {'available_from_time': '8:30 AM', 'available_to_time': '11:30 AM'}
        ]

        result = MatchmakingService.get_time_overlap(players_availability)

        assert result is not None
        start, end = result
        assert start == time(10, 0)  # Latest start
        assert end == time(11, 30)  # Earliest end

    def test_get_time_overlap_no_overlap(self):
        """Test when players have no overlapping time"""
        players_availability = [
            {'available_from_time': '8:00 AM', 'available_to_time': '10:00 AM'},
            {'available_from_time': '11:00 AM', 'available_to_time': '2:00 PM'}
        ]

        result = MatchmakingService.get_time_overlap(players_availability)
        assert result is None

    def test_get_time_overlap_all_day_availability(self):
        """Test when some players have all-day availability"""
        players_availability = [
            {'available_from_time': None, 'available_to_time': None},  # All day
            {'available_from_time': '10:00 AM', 'available_to_time': '2:00 PM'}
        ]

        result = MatchmakingService.get_time_overlap(players_availability)
        assert result is not None


class TestOverlapDuration:
    """Test overlap duration calculation"""

    def test_calculate_overlap_duration(self):
        """Test duration calculation in hours"""
        start = time(9, 0)
        end = time(11, 30)

        duration = MatchmakingService.calculate_overlap_duration(start, end)
        assert duration == 2.5

    def test_calculate_overlap_duration_full_day(self):
        """Test full day duration"""
        start = time(6, 0)
        end = time(20, 0)

        duration = MatchmakingService.calculate_overlap_duration(start, end)
        assert duration == 14.0


class TestFindMatches:
    """Test the core matchmaking algorithm"""

    def test_find_matches_basic(self):
        """Test basic 4-player match finding"""
        all_players_availability = [
            {
                'player_id': 1,
                'player_name': 'Player 1',
                'email': 'player1@example.com',
                'availability': [
                    {'day_of_week': 0, 'is_available': True,
                     'available_from_time': '9:00 AM', 'available_to_time': '12:00 PM'}
                ]
            },
            {
                'player_id': 2,
                'player_name': 'Player 2',
                'email': 'player2@example.com',
                'availability': [
                    {'day_of_week': 0, 'is_available': True,
                     'available_from_time': '8:00 AM', 'available_to_time': '1:00 PM'}
                ]
            },
            {
                'player_id': 3,
                'player_name': 'Player 3',
                'email': 'player3@example.com',
                'availability': [
                    {'day_of_week': 0, 'is_available': True,
                     'available_from_time': '10:00 AM', 'available_to_time': '2:00 PM'}
                ]
            },
            {
                'player_id': 4,
                'player_name': 'Player 4',
                'email': 'player4@example.com',
                'availability': [
                    {'day_of_week': 0, 'is_available': True,
                     'available_from_time': '9:30 AM', 'available_to_time': '11:30 AM'}
                ]
            }
        ]

        matches = MatchmakingService.find_matches(all_players_availability, min_overlap_hours=1.0)

        assert len(matches) >= 1
        if len(matches) > 0:
            assert matches[0]['day_of_week'] == 0
            assert len(matches[0]['players']) == 4
            assert 'overlap_start' in matches[0]
            assert 'overlap_end' in matches[0]

    def test_find_matches_insufficient_players(self):
        """Test when there aren't enough players"""
        all_players_availability = [
            {
                'player_id': 1,
                'player_name': 'Player 1',
                'email': 'player1@example.com',
                'availability': [{'day_of_week': 0, 'is_available': True}]
            }
        ]

        matches = MatchmakingService.find_matches(all_players_availability)
        assert len(matches) == 0

    def test_find_matches_min_overlap_requirement(self):
        """Test minimum overlap hours requirement"""
        all_players_availability = [
            {
                'player_id': i,
                'player_name': f'Player {i}',
                'email': f'player{i}@example.com',
                'availability': [
                    {'day_of_week': 0, 'is_available': True,
                     'available_from_time': '10:00 AM',
                     'available_to_time': '10:30 AM'}  # Only 30min overlap
                ]
            }
            for i in range(1, 5)
        ]

        matches = MatchmakingService.find_matches(
            all_players_availability,
            min_overlap_hours=2.0
        )

        # Should have no matches due to insufficient overlap
        assert len(matches) == 0


class TestTeeTimeSuggestion:
    """Test tee time suggestions"""

    def test_suggest_tee_time_morning_window(self):
        """Test suggestion within morning window"""
        start = time(8, 0)
        end = time(12, 0)

        suggested = MatchmakingService.suggest_tee_time(start, end)
        assert suggested == "9:00 AM"

    def test_suggest_tee_time_afternoon(self):
        """Test suggestion for afternoon window"""
        start = time(13, 0)
        end = time(16, 0)

        suggested = MatchmakingService.suggest_tee_time(start, end)
        assert "1:00 PM" in suggested or "01:00 PM" in suggested


class TestMatchQuality:
    """Test match quality scoring"""

    def test_calculate_match_quality_high_duration(self):
        """Test high quality for long overlap"""
        players = [
            {'available_from_time': None, 'available_to_time': None}
            for _ in range(4)
        ]

        score = MatchmakingService.calculate_match_quality(players, 5.0)
        assert score > 50  # Should be high quality

    def test_calculate_match_quality_morning_bonus(self):
        """Test bonus for morning availability"""
        players = [
            {'available_from_time': '8:00 AM', 'available_to_time': '12:00 PM'}
            for _ in range(4)
        ]

        score = MatchmakingService.calculate_match_quality(players, 3.0)
        assert score > 0


class TestMatchNotification:
    """Test match notification generation"""

    def test_create_match_notification(self):
        """Test notification content generation"""
        match = {
            'day_of_week': 5,  # Saturday
            'players': [
                {'player_name': 'Alice', 'email': 'alice@example.com'},
                {'player_name': 'Bob', 'email': 'bob@example.com'},
                {'player_name': 'Charlie', 'email': 'charlie@example.com'},
                {'player_name': 'David', 'email': 'david@example.com'}
            ],
            'overlap_start': '9:00 AM',
            'overlap_end': '12:00 PM',
            'suggested_tee_time': '9:00 AM'
        }

        notification = MatchmakingService.create_match_notification(match)

        assert notification['subject'] is not None
        assert 'Saturday' in notification['subject']
        assert notification['body'] is not None
        assert len(notification['recipients']) == 4
        assert 'alice@example.com' in notification['recipients']


class TestRecentMatchFiltering:
    """Test filtering of recent matches"""

    def test_filter_recent_matches_no_history(self):
        """Test filtering with no history"""
        matches = [
            {'players': [{'player_id': 1}, {'player_id': 2}, {'player_id': 3}, {'player_id': 4}]}
        ]

        filtered = MatchmakingService.filter_recent_matches(matches, [], days_between_matches=3)
        assert len(filtered) == 1

    def test_filter_recent_matches_with_recent_history(self):
        """Test filtering removes recent matches"""
        from datetime import datetime, timedelta

        matches = [
            {'players': [{'player_id': 1}, {'player_id': 2}, {'player_id': 3}, {'player_id': 4}]}
        ]

        recent_history = [
            {
                'players': [{'player_id': 1}, {'player_id': 2}, {'player_id': 5}, {'player_id': 6}],
                'created_at': datetime.now().isoformat()
            }
        ]

        filtered = MatchmakingService.filter_recent_matches(
            matches,
            recent_history,
            days_between_matches=3
        )

        # Match should be filtered out because player 1 and 2 were recently matched
        assert len(filtered) == 0
