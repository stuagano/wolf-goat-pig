"""
Unit tests for TeamFormationService

Tests random team formation from daily player signups.
"""

import pytest
from random import Random
from app.services.team_formation_service import TeamFormationService


class TestGenerateRandomTeams:
    """Test random team generation"""

    def test_generate_teams_exact_four(self):
        """Test generating teams with exactly 4 players"""
        players = [
            {'player_id': i, 'player_name': f'Player {i}', 'email': f'player{i}@example.com'}
            for i in range(1, 5)
        ]

        teams = TeamFormationService.generate_random_teams(players, seed=42)

        assert len(teams) == 1
        assert len(teams[0]['players']) == 4
        assert teams[0]['formation_method'] == 'random'

    def test_generate_teams_eight_players(self):
        """Test generating teams with 8 players"""
        players = [
            {'player_id': i, 'player_name': f'Player {i}', 'email': f'player{i}@example.com'}
            for i in range(1, 9)
        ]

        teams = TeamFormationService.generate_random_teams(players, seed=42)

        assert len(teams) == 2
        assert all(len(team['players']) == 4 for team in teams)

    def test_generate_teams_insufficient_players(self):
        """Test with insufficient players"""
        players = [
            {'player_id': i, 'player_name': f'Player {i}', 'email': f'player{i}@example.com'}
            for i in range(1, 3)
        ]

        teams = TeamFormationService.generate_random_teams(players)

        assert len(teams) == 0

    def test_generate_teams_with_remainder(self):
        """Test with 10 players (6 left over)"""
        players = [
            {'player_id': i, 'player_name': f'Player {i}', 'email': f'player{i}@example.com'}
            for i in range(1, 11)
        ]

        teams = TeamFormationService.generate_random_teams(players, seed=42)

        assert len(teams) == 2
        # 2 players should be left over

    def test_seed_reproducibility(self):
        """Test same seed gives same teams"""
        players = [
            {'player_id': i, 'player_name': f'Player {i}', 'email': f'player{i}@example.com'}
            for i in range(1, 9)
        ]

        teams1 = TeamFormationService.generate_random_teams(players, seed=123)
        teams2 = TeamFormationService.generate_random_teams(players, seed=123)

        # Teams should be identical
        assert len(teams1) == len(teams2)
        for i, team in enumerate(teams1):
            assert [p['player_id'] for p in team['players']] == [p['player_id'] for p in teams2[i]['players']]

    def test_max_teams_limit(self):
        """Test max teams limit"""
        players = [
            {'player_id': i, 'player_name': f'Player {i}', 'email': f'player{i}@example.com'}
            for i in range(1, 13)
        ]

        teams = TeamFormationService.generate_random_teams(players, seed=42, max_teams=2)

        assert len(teams) == 2


class TestTeamPairingsWithRotations:
    """Test multiple team rotation generation"""

    def test_create_rotations(self):
        """Test creating multiple rotations"""
        players = [
            {'player_id': i, 'player_name': f'Player {i}', 'email': f'player{i}@example.com'}
            for i in range(1, 9)
        ]

        rotations = TeamFormationService.create_team_pairings_with_rotations(
            players,
            num_rotations=3,
            seed=42
        )

        assert len(rotations) == 3
        # Each rotation should have different team compositions

    def test_rotations_insufficient_players(self):
        """Test rotations with too few players"""
        players = [
            {'player_id': i, 'player_name': f'Player {i}', 'email': f'player{i}@example.com'}
            for i in range(1, 3)
        ]

        rotations = TeamFormationService.create_team_pairings_with_rotations(players)

        assert len(rotations) == 0


class TestRandomNumberGeneration:
    """Test RNG handling"""

    def test_custom_rng(self):
        """Test using custom RNG"""
        players = [
            {'player_id': i, 'player_name': f'Player {i}', 'email': f'player{i}@example.com'}
            for i in range(1, 5)
        ]

        custom_rng = Random(999)
        teams = TeamFormationService.generate_random_teams(players, rng=custom_rng)

        assert len(teams) == 1

    def test_no_seed_different_results(self):
        """Test without seed gives different results"""
        players = [
            {'player_id': i, 'player_name': f'Player {i}', 'email': f'player{i}@example.com'}
            for i in range(1, 9)
        ]

        # Run multiple times without seed
        teams_list = [
            TeamFormationService.generate_random_teams(players)
            for _ in range(5)
        ]

        # At least some should be different (highly likely)
        player_orders = [
            [p['player_id'] for team in teams for p in team['players']]
            for teams in teams_list
        ]

        # Check that not all are identical
        assert len(set(tuple(order) for order in player_orders)) > 1
