"""Unit tests for SimplifiedScoring — the lightweight in-memory scoring engine."""

import pytest

from app.simplified_scoring import SimplifiedScoring, SimpleHoleResult


PLAYERS = [
    {"id": "p1", "name": "Stuart"},
    {"id": "p2", "name": "Jeff"},
    {"id": "p3", "name": "Gregg"},
    {"id": "p4", "name": "Allen"},
]


def make_game(players=None):
    return SimplifiedScoring(players or PLAYERS)


# ── Initialization ────────────────────────────────────────────────────────────

class TestInit:
    def test_players_start_at_zero_points(self):
        game = make_game()
        for pid, data in game.players.items():
            assert data["points"] == 0

    def test_player_names_mapped_correctly(self):
        game = make_game()
        assert game.players["p1"]["name"] == "Stuart"
        assert game.players["p4"]["name"] == "Allen"

    def test_no_hole_results_initially(self):
        game = make_game()
        assert len(game.hole_results) == 0


# ── Partners scoring ──────────────────────────────────────────────────────────

class TestPartnersScoring:
    def _teams(self):
        return {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]}

    def test_team1_wins(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 4, "p2": 4, "p3": 5, "p4": 5}, self._teams(), wager=1
        )
        assert result["success"] is True
        assert result["points_changes"]["p1"] == 1
        assert result["points_changes"]["p2"] == 1
        assert result["points_changes"]["p3"] == -1
        assert result["points_changes"]["p4"] == -1

    def test_team2_wins(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 5, "p2": 5, "p3": 4, "p4": 3}, self._teams(), wager=1
        )
        assert result["points_changes"]["p1"] == -1
        assert result["points_changes"]["p2"] == -1
        assert result["points_changes"]["p3"] == 1
        assert result["points_changes"]["p4"] == 1

    def test_tie_no_points_awarded(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 4, "p2": 5, "p3": 3, "p4": 5}, self._teams(), wager=2
        )
        # Team1 best = 4, Team2 best = 3 → Team2 wins
        assert result["points_changes"]["p3"] == 2
        assert result["points_changes"]["p4"] == 2
        assert result["points_changes"]["p1"] == -2
        assert result["points_changes"]["p2"] == -2

    def test_exact_tie_produces_zero_points(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 4, "p2": 5, "p3": 4, "p4": 5}, self._teams(), wager=2
        )
        for change in result["points_changes"].values():
            assert change == 0

    def test_wager_multiplies_points(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 3, "p2": 4, "p3": 5, "p4": 5}, self._teams(), wager=4
        )
        assert result["points_changes"]["p1"] == 4
        assert result["points_changes"]["p2"] == 4
        assert result["points_changes"]["p3"] == -4
        assert result["points_changes"]["p4"] == -4

    def test_best_ball_used_not_average(self):
        """Team score is best ball (min), not average."""
        game = make_game()
        # Team1: p1=3, p2=9 → best=3. Team2: p3=4, p4=4 → best=4. Team1 wins.
        result = game.enter_hole_scores(
            1, {"p1": 3, "p2": 9, "p3": 4, "p4": 4}, self._teams(), wager=1
        )
        assert result["points_changes"]["p1"] == 1
        assert result["points_changes"]["p2"] == 1

    def test_zero_sum_partners(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 4, "p2": 4, "p3": 5, "p4": 5}, self._teams(), wager=3
        )
        assert sum(result["points_changes"].values()) == 0

    def test_invalid_team_type_returns_error(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 4}, {"type": "invalid"}, wager=1
        )
        assert "error" in result

    def test_empty_teams_returns_error(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 4, "p2": 4}, {"type": "partners", "team1": [], "team2": []}, wager=1
        )
        assert "error" in result


# ── Solo scoring ──────────────────────────────────────────────────────────────

class TestSoloScoring:
    def _solo_teams(self, solo="p1"):
        return {"type": "solo", "solo_player": solo}

    def test_solo_player_wins(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 3, "p2": 5, "p3": 5, "p4": 5}, self._solo_teams("p1"), wager=1
        )
        assert result["points_changes"]["p1"] == 3   # wins 1 from each of 3 opponents
        assert result["points_changes"]["p2"] == -1
        assert result["points_changes"]["p3"] == -1
        assert result["points_changes"]["p4"] == -1

    def test_solo_player_loses(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 5, "p2": 4, "p3": 4, "p4": 4}, self._solo_teams("p1"), wager=1
        )
        assert result["points_changes"]["p1"] == -3
        assert result["points_changes"]["p2"] == 1
        assert result["points_changes"]["p3"] == 1
        assert result["points_changes"]["p4"] == 1

    def test_solo_tie_no_points(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 4, "p2": 4, "p3": 4, "p4": 5}, self._solo_teams("p1"), wager=1
        )
        # Solo ties best opponent (4=4) → no points
        for change in result["points_changes"].values():
            assert change == 0

    def test_solo_wager_multiplies(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 3, "p2": 5, "p3": 5, "p4": 5}, self._solo_teams("p1"), wager=2
        )
        assert result["points_changes"]["p1"] == 6
        assert result["points_changes"]["p2"] == -2

    def test_zero_sum_solo(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 3, "p2": 5, "p3": 5, "p4": 5}, self._solo_teams("p1"), wager=1
        )
        assert sum(result["points_changes"].values()) == 0

    def test_missing_solo_player_returns_error(self):
        game = make_game()
        result = game.enter_hole_scores(
            1, {"p1": 4}, {"type": "solo"}, wager=1
        )
        assert "error" in result

    def test_empty_scores_returns_error(self):
        game = make_game()
        result = game.enter_hole_scores(1, {}, self._solo_teams("p1"), wager=1)
        assert "error" in result


# ── Cumulative state ──────────────────────────────────────────────────────────

class TestCumulativeState:
    def test_points_accumulate_across_holes(self):
        game = make_game()
        teams = {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]}
        # Hole 1: Team1 wins
        game.enter_hole_scores(1, {"p1": 3, "p2": 4, "p3": 5, "p4": 5}, teams, wager=1)
        # Hole 2: Team2 wins
        game.enter_hole_scores(2, {"p1": 5, "p2": 5, "p3": 3, "p4": 4}, teams, wager=1)
        # Net: all back to 0
        assert game.players["p1"]["points"] == 0
        assert game.players["p3"]["points"] == 0

    def test_hole_results_stored(self):
        game = make_game()
        teams = {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]}
        game.enter_hole_scores(1, {"p1": 3, "p2": 4, "p3": 5, "p4": 5}, teams, wager=1)
        assert 1 in game.hole_results
        assert isinstance(game.hole_results[1], SimpleHoleResult)

    def test_get_game_summary_after_holes(self):
        game = make_game()
        teams = {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]}
        game.enter_hole_scores(1, {"p1": 3, "p2": 4, "p3": 5, "p4": 5}, teams, wager=1)
        game.enter_hole_scores(2, {"p1": 3, "p2": 4, "p3": 5, "p4": 5}, teams, wager=1)
        summary = game.get_game_summary()
        assert summary["holes_played"] == 2
        assert summary["last_hole_result"] == 2

    def test_leaderboard_sorted_by_points_descending(self):
        game = make_game()
        teams = {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]}
        game.enter_hole_scores(1, {"p1": 3, "p2": 4, "p3": 5, "p4": 5}, teams, wager=2)
        lb = game.get_game_summary()["leaderboard"]
        scores = [entry[2] for entry in lb]
        assert scores == sorted(scores, reverse=True)

    def test_get_hole_history_ordered(self):
        game = make_game()
        teams = {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]}
        game.enter_hole_scores(3, {"p1": 3, "p2": 4, "p3": 5, "p4": 5}, teams, wager=1)
        game.enter_hole_scores(1, {"p1": 3, "p2": 4, "p3": 5, "p4": 5}, teams, wager=1)
        history = game.get_hole_history()
        assert [h["hole"] for h in history] == [1, 3]

    def test_hole_history_has_winner_names(self):
        game = make_game()
        teams = {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]}
        game.enter_hole_scores(1, {"p1": 3, "p2": 4, "p3": 5, "p4": 5}, teams, wager=1)
        history = game.get_hole_history()
        assert "Stuart" in history[0]["winners"]
        assert "Jeff" in history[0]["winners"]


# ── Edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_game_summary_no_holes_played(self):
        game = make_game()
        summary = game.get_game_summary()
        assert summary["holes_played"] == 0
        assert summary["last_hole_result"] is None

    def test_single_player_solo_error(self):
        game = SimplifiedScoring([{"id": "p1", "name": "Stuart"}])
        result = game.enter_hole_scores(
            1, {"p1": 4}, {"type": "solo", "solo_player": "p1"}, wager=1
        )
        assert "error" in result  # No opponents
