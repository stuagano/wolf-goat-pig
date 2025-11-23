"""
Simplified scoring system for Wolf Goat Pig game.

This module provides a streamlined alternative to the complex scoring logic
in the main WolfGoatPigGame class. It focuses on essential scoring
mechanics while reducing the serialization overhead.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

@dataclass
class SimpleHoleResult:
    """Simplified hole result with just essential data"""
    hole_number: int
    scores: Dict[str, int]  # player_id -> score
    wager: int
    team_type: str  # "solo" or "partners"
    winners: List[str]
    points_awarded: Dict[str, int]  # player_id -> points change

class SimplifiedScoring:
    """
    Simplified scoring system that reduces complexity while maintaining
    core Wolf Goat Pig game mechanics.
    """

    def __init__(self, players: List[Dict[str, Any]]):
        """Initialize with basic player information"""
        self.players = {p["id"]: {"name": p["name"], "points": 0} for p in players}
        self.hole_results: Dict[int, SimpleHoleResult] = {}

    def enter_hole_scores(self, hole_number: int, scores: Dict[str, int],
                         teams: Dict[str, Any], wager: int = 1) -> Dict[str, Any]:
        """
        Simplified hole scoring that focuses on core mechanics.
        
        Args:
            hole_number: Current hole number
            scores: Dict mapping player_id to their score for this hole
            teams: Team configuration for this hole
            wager: Wager amount (default 1)
            
        Returns:
            Dict with scoring results and point changes
        """
        try:
            # Validate inputs
            if not scores:
                return {"error": "No scores provided"}

            # Determine winners and calculate points
            if teams.get("type") == "solo":
                result = self._calculate_solo_points(scores, teams, wager)
            elif teams.get("type") == "partners":
                result = self._calculate_partners_points(scores, teams, wager)
            else:
                return {"error": f"Invalid team type: {teams.get('type')}"}

            # Update player points
            for player_id, point_change in result["points_changes"].items():
                if player_id in self.players:
                    self.players[player_id]["points"] += point_change

            # Store simplified hole result
            hole_result = SimpleHoleResult(
                hole_number=hole_number,
                scores=scores,
                wager=wager,
                team_type=teams.get("type", "solo"),
                winners=result.get("winners", []),
                points_awarded=result["points_changes"]
            )
            self.hole_results[hole_number] = hole_result

            return {
                "success": True,
                "message": result.get("message", "Hole scored successfully"),
                "points_changes": result["points_changes"],
                "current_standings": {pid: p["points"] for pid, p in self.players.items()},
                "hole_summary": {
                    "hole": hole_number,
                    "winners": [self.players[pid]["name"] for pid in result.get("winners", [])],
                    "wager": wager
                }
            }

        except Exception as e:
            logger.error(f"Error in simplified hole scoring: {e}")
            return {"error": f"Scoring failed: {str(e)}"}

    def _calculate_solo_points(self, scores: Dict[str, int], teams: Dict[str, Any],
                              wager: int) -> Dict[str, Any]:
        """Calculate points for solo play (one vs all others)"""
        solo_player = teams.get("solo_player")
        if not solo_player or solo_player not in scores:
            return {"error": "Invalid solo player configuration"}

        solo_score = scores[solo_player]
        other_players = [pid for pid in scores if pid != solo_player]

        if not other_players:
            return {"error": "No opponent players found"}

        # Best opponent score
        best_opponent_score = min(scores[pid] for pid in other_players)

        points_changes = dict.fromkeys(scores.keys(), 0)

        if solo_score < best_opponent_score:
            # Solo player wins
            points_changes[solo_player] = wager * len(other_players)
            for opponent in other_players:
                points_changes[opponent] = -wager
            winners = [solo_player]
            message = f"{solo_player} wins solo against {len(other_players)} opponents!"

        elif solo_score > best_opponent_score:
            # Opponents win
            points_changes[solo_player] = -wager * len(other_players)
            for opponent in other_players:
                points_changes[opponent] = wager
            winners = other_players
            message = f"Opponents defeat solo player {solo_player}"

        else:
            # Tie - no points awarded
            winners = []
            message = "Hole tied - no points awarded"

        return {
            "points_changes": points_changes,
            "winners": winners,
            "message": message,
            "halved": len(winners) == 0
        }

    def _calculate_partners_points(self, scores: Dict[str, int], teams: Dict[str, Any],
                                  wager: int) -> Dict[str, Any]:
        """Calculate points for partner play (two teams of two)"""
        team1 = teams.get("team1", [])
        team2 = teams.get("team2", [])

        if not team1 or not team2:
            return {"error": "Invalid team configuration"}

        # Best ball scoring for each team
        team1_score = min(scores[pid] for pid in team1 if pid in scores)
        team2_score = min(scores[pid] for pid in team2 if pid in scores)

        points_changes = dict.fromkeys(scores.keys(), 0)

        if team1_score < team2_score:
            # Team 1 wins
            for player in team1:
                points_changes[player] = wager
            for player in team2:
                points_changes[player] = -wager
            winners = team1
            message = "Team 1 wins the hole"

        elif team2_score < team1_score:
            # Team 2 wins
            for player in team2:
                points_changes[player] = wager
            for player in team1:
                points_changes[player] = -wager
            winners = team2
            message = "Team 2 wins the hole"

        else:
            # Tie - no points awarded
            winners = []
            message = "Hole tied - no points awarded"

        return {
            "points_changes": points_changes,
            "winners": winners,
            "message": message,
            "halved": len(winners) == 0
        }

    def get_game_summary(self) -> Dict[str, Any]:
        """Get a simple game summary with current standings"""
        return {
            "players": self.players,
            "holes_played": len(self.hole_results),
            "last_hole_result": max(self.hole_results.keys()) if self.hole_results else None,
            "leaderboard": sorted(
                [(pid, p["name"], p["points"]) for pid, p in self.players.items()],
                key=lambda x: x[2],  # Sort by points
                reverse=True
            )
        }

    def get_hole_history(self) -> List[Dict[str, Any]]:
        """Get simplified hole-by-hole results"""
        history = []
        for hole_num in sorted(self.hole_results.keys()):
            result = self.hole_results[hole_num]
            history.append({
                "hole": hole_num,
                "scores": result.scores,
                "team_type": result.team_type,
                "wager": result.wager,
                "winners": [self.players[pid]["name"] for pid in result.winners],
                "points_awarded": result.points_awarded
            })
        return history
