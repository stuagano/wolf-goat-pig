"""Scoring for WolfGoatPigGame — hole scores, points calculation, Karl Marx rule, game finish."""

import logging
from typing import Any, cast

from ..domain.game_types import BettingState, HoleState, TeamFormation
from ..services.post_hole_analysis_service import (
    get_post_hole_analysis as _get_post_hole_analysis,
)

logger = logging.getLogger(__name__)


class ScoringMixin:
    """Hole scoring, quarter distribution (incl. Karl Marx rule), and game completion."""

    def enter_hole_scores(self, scores: dict[str, int]) -> dict[str, Any]:
        """Enter scores for the hole and calculate points"""
        hole_state = self.hole_states[self.current_hole]

        # Validate all scores are provided
        for player_id in [p.id for p in self.players]:
            if player_id not in scores:
                raise ValueError(f"Score missing for player {self._get_player_name(player_id)}")

        hole_state.scores = {k: cast("int | None", v) for k, v in scores.items()}

        # Calculate and distribute points
        points_result = self._calculate_hole_points(hole_state)

        # Store points awarded in hole state for hole_history
        hole_state.points_awarded = points_result["points_changes"].copy()

        # Update player points
        for player_id, points_change in points_result["points_changes"].items():
            player = next(p for p in self.players if p.id == player_id)
            player.points += points_change

        # Check for carry-over
        if points_result["halved"]:
            hole_state.betting.carry_over = True

        return points_result

    def apply_hole_events(self, events: list[dict[str, Any]]) -> None:
        """Recompute player points from the full hole-event log.

        Accepts a list of per-player-per-hole dicts with keys:
          hole_number, player_id, score (optional), quarters.
        Resets all player points to zero, then sums quarters from each event.
        Also restores hole_state.scores / .points_awarded for initialized holes.
        """
        from collections import defaultdict

        for player in self.players:
            player.points = 0

        by_hole: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for event in events:
            by_hole[event["hole_number"]].append(event)

        for hole_number in sorted(by_hole.keys()):
            hole_events = by_hole[hole_number]
            hole_state = self.hole_states.get(hole_number)
            if hole_state:
                hole_state.scores = {e["player_id"]: e["score"] for e in hole_events if e.get("score") is not None}
                hole_state.points_awarded = {e["player_id"]: e["quarters"] for e in hole_events}

            for event in hole_events:
                player = next((p for p in self.players if p.id == event["player_id"]), None)
                if player:
                    player.points += event["quarters"]

    def get_post_hole_analysis(self, hole_number: int) -> dict[str, Any]:
        """Generate comprehensive post-hole analysis"""
        return _get_post_hole_analysis(
            hole_states=self.hole_states,
            game_phase=self.game_phase,
            players=self.players,
            get_player_name_fn=self._get_player_name,
            hole_number=hole_number,
            calculate_hole_points_fn=self._calculate_hole_points,
        )

    def advance_to_next_hole(self) -> dict[str, Any]:
        """Advance to the next hole"""
        if self.current_hole >= 18:
            return self._finish_game()

        self.current_hole += 1
        self._initialize_hole(self.current_hole)

        return {
            "status": "hole_advanced",
            "current_hole": self.current_hole,
            "game_phase": self.game_phase.value,
            "hole_state": self._get_hole_state_summary(),
        }

    def _calculate_hole_points(self, hole_state: HoleState) -> dict[str, Any]:
        """Calculate points for the hole based on scores and betting"""
        scores = hole_state.scores
        betting = hole_state.betting
        teams = hole_state.teams

        # Filter out None values from scores
        valid_scores: dict[str, int] = {pid: score for pid, score in scores.items() if score is not None}

        if teams.type == "partners":
            return self._calculate_partners_points(valid_scores, teams, betting)
        if teams.type == "solo":
            return self._calculate_solo_points(valid_scores, teams, betting)
        raise ValueError(f"Invalid team type for points calculation: {teams.type}")

    def _calculate_partners_points(
        self, scores: dict[str, int], teams: TeamFormation, betting: BettingState
    ) -> dict[str, Any]:
        """Calculate points for partners format"""
        team1_score = min(scores[pid] for pid in teams.team1)
        team2_score = min(scores[pid] for pid in teams.team2)

        wager = betting.current_wager

        if team1_score < team2_score:
            winners = teams.team1
            losers = teams.team2
        elif team2_score < team1_score:
            winners = teams.team2
            losers = teams.team1
        else:
            # Hole halved
            return {
                "halved": True,
                "message": "Hole halved. No points awarded.",
                "points_changes": {p.id: 0 for p in self.players},
            }

        points_changes = self._apply_karl_marx_rule(winners, losers, wager)

        # Apply special rule multipliers
        if betting.duncan_invoked or betting.tunkarri_invoked:
            # 3 for 2 rule - winner gets 3 quarters for every 2 wagered
            for winner in winners:
                if points_changes[winner] > 0:
                    points_changes[winner] = int(points_changes[winner] * 1.5)

        return {
            "halved": False,
            "winners": winners,
            "losers": losers,
            "points_changes": points_changes,
            "message": f"Team {winners} wins the hole",
        }

    def _calculate_solo_points(
        self, scores: dict[str, int], teams: TeamFormation, betting: BettingState
    ) -> dict[str, Any]:
        """Calculate points for solo format"""
        solo_player = teams.solo_player
        opponents = teams.opponents

        if solo_player is None:
            raise ValueError("Solo player cannot be None")
        solo_score = scores[solo_player]
        opponent_score = min(scores[pid] for pid in opponents)

        wager = betting.current_wager

        if solo_score < opponent_score:
            # Solo player wins
            points_changes = {solo_player: wager * len(opponents)}
            for opp in opponents:
                points_changes[opp] = -wager

            winners = [solo_player]
            message = f"{self._get_player_name(solo_player)} wins solo!"

        elif opponent_score < solo_score:
            # Opponents win
            points_changes = {solo_player: -wager * len(opponents)}
            for opp in opponents:
                points_changes[opp] = wager

            winners_list: list[str] = list(opponents)
            message = f"Opponents defeat {self._get_player_name(solo_player)}"

        else:
            # Hole halved
            return {
                "halved": True,
                "message": "Hole halved. No points awarded.",
                "points_changes": {p.id: 0 for p in self.players},
            }

        # Apply special rule multipliers
        if betting.duncan_invoked or betting.tunkarri_invoked:
            # 3 for 2 rule
            # Use winners_list if defined, otherwise use winners
            winner_ids = winners_list if "winners_list" in locals() else winners
            for winner in winner_ids:
                if points_changes[winner] > 0:
                    points_changes[winner] = int(points_changes[winner] * 1.5)

        # Return with correct winners variable
        final_winners = winners_list if "winners_list" in locals() else winners
        return {
            "halved": False,
            "winners": final_winners,
            "points_changes": points_changes,
            "message": message,
        }

    def _apply_karl_marx_rule(self, winners: list[str], losers: list[str], wager: int) -> dict[str, int]:
        """
        Apply Karl Marx rule: "from each according to his ability, to each according to his need"
        Player furthest down pays/receives less
        """
        points_changes = {}

        # Initialize all players to 0
        for p in self.players:
            points_changes[p.id] = 0

        total_owed = wager * len(winners)
        total_won = wager * len(losers)

        # Winners get points
        if len(winners) == 1:
            points_changes[winners[0]] = total_won
        else:
            points_per_winner = total_won // len(winners)
            remainder = total_won % len(winners)

            # Sort winners by current points (ascending - furthest down gets less)
            sorted_winners = sorted(
                winners,
                key=lambda pid: next(p.points for p in self.players if p.id == pid),
            )

            for i, winner in enumerate(sorted_winners):
                points_changes[winner] = points_per_winner
                if i >= len(sorted_winners) - remainder:  # Last few get extra
                    points_changes[winner] += 1

        # Losers lose points
        if len(losers) == 1:
            points_changes[losers[0]] = -total_owed
        else:
            points_per_loser = total_owed // len(losers)
            remainder = total_owed % len(losers)

            # Sort losers by current points (ascending - furthest down pays less)
            sorted_losers = sorted(
                losers,
                key=lambda pid: next(p.points for p in self.players if p.id == pid),
            )

            for i, loser in enumerate(sorted_losers):
                points_changes[loser] = -points_per_loser
                if i >= len(sorted_losers) - remainder:  # Last few pay extra
                    points_changes[loser] -= 1

        return points_changes

    def _finish_game(self) -> dict[str, Any]:
        """Finish the game and determine final results"""
        final_scores = {p.id: p.points for p in self.players}

        # Determine winner(s)
        max_points = max(final_scores.values())
        winners = [pid for pid, points in final_scores.items() if points == max_points]

        # Persist completed game to database
        self.complete_game()

        return {
            "status": "game_finished",
            "final_scores": final_scores,
            "winners": winners,
            "winner_names": [self._get_player_name(pid) for pid in winners],
            "game_summary": {
                "total_holes": 18,
                "final_phase": self.game_phase.value,
                "player_performances": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "final_points": p.points,
                        "solo_count": p.solo_count,
                        "float_used": p.float_used,
                    }
                    for p in self.players
                ],
            },
        }
