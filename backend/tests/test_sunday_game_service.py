"""Tests for Sunday game pairing logic and related randomization helpers."""

import copy

from backend.app.services import sunday_game_service
from backend.app.services.team_formation_service import TeamFormationService


def _make_players(count: int):
    """Create synthetic signup payloads for testing team formation."""
    players = []
    for idx in range(count):
        players.append({
            "id": idx + 1,
            "player_profile_id": idx + 1,
            "player_name": f"Player {idx + 1}",
            "preferred_start_time": None,
            "notes": None,
            "signup_time": f"2024-04-{(idx % 9) + 1:02d}T08:00:00"
        })
    return players


def _extract_team_signatures(teams):
    """Build comparable signatures for generated teams ignoring metadata fields."""
    signatures = []
    for team in teams:
        player_ids = sorted(player["player_profile_id"] for player in team["players"])
        signatures.append(tuple(player_ids))
    return sorted(signatures)


def test_generate_random_teams_is_deterministic_with_seed():
    players = _make_players(8)

    first_result = TeamFormationService.generate_random_teams(players, seed=42)
    second_result = TeamFormationService.generate_random_teams(players, seed=42)

    assert _extract_team_signatures(first_result) == _extract_team_signatures(second_result)


def test_sunday_pairings_respect_explicit_seed():
    players = _make_players(8)

    first = sunday_game_service.generate_sunday_pairings(players, num_rotations=5, seed=101)
    second = sunday_game_service.generate_sunday_pairings(players, num_rotations=5, seed=101)

    assert first["total_rotations"] == 5
    assert first["selected_rotation"] in first["rotations"]
    assert _extract_team_signatures(second["selected_rotation"]["teams"]) == _extract_team_signatures(first["selected_rotation"]["teams"])


def test_sunday_pairings_uses_environment_seed(monkeypatch):
    players = _make_players(12)
    monkeypatch.setenv(sunday_game_service.SUNDAY_GAME_SEED_ENV, "7")

    first = sunday_game_service.generate_sunday_pairings(players, num_rotations=4)
    second = sunday_game_service.generate_sunday_pairings(copy.deepcopy(players), num_rotations=4)

    assert _extract_team_signatures(first["selected_rotation"]["teams"]) == _extract_team_signatures(second["selected_rotation"]["teams"])
    assert first["total_rotations"] == 4

    monkeypatch.delenv(sunday_game_service.SUNDAY_GAME_SEED_ENV, raising=False)


def test_sunday_pairings_handles_insufficient_players():
    players = _make_players(3)

    result = sunday_game_service.generate_sunday_pairings(players)

    assert result["total_rotations"] == 0
    assert result["selected_rotation"] is None
    assert result["remaining_players"] == 3
