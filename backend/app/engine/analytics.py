"""Advanced analytics views for WolfGoatPigGame — trends, chemistry, predictions."""

from typing import Any, cast

from ..domain.game_types import Player


class AnalyticsMixin:
    """Read-only analytics derived from game state."""

    def get_advanced_analytics(self) -> dict[str, Any]:
        """Get comprehensive analytics dashboard data"""
        return {
            "performance_trends": self._get_performance_trends(),
            "betting_analysis": self._get_betting_analysis(),
            "partnership_chemistry": self._get_partnership_chemistry(),
            "game_statistics": self._get_game_statistics(),
            "risk_analysis": self._get_risk_analysis(),
            "prediction_models": self._get_prediction_models(),
        }

    def _get_performance_trends(self) -> dict[str, Any]:
        """Analyze performance trends over completed holes"""
        trends = {}

        for player in self.players:
            player_holes = []
            points_history = []
            cumulative_points = 0

            for hole_num in sorted(self.hole_states.keys()):
                hole_state = self.hole_states[hole_num]
                if hole_state.hole_complete and hole_state.points_awarded:
                    player_points = hole_state.points_awarded.get(player.id, 0)
                    cumulative_points += player_points
                    player_holes.append(
                        {
                            "hole": hole_num,
                            "points": player_points,
                            "cumulative": cumulative_points,
                            "team_type": hole_state.teams.type,
                            "was_captain": hole_state.teams.captain == player.id,
                            "wager": hole_state.betting.current_wager,
                        }
                    )
                    points_history.append(player_points)

            # Calculate trend metrics
            if len(points_history) >= 3:
                recent_avg = sum(points_history[-3:]) / 3
                early_avg = sum(points_history[:3]) / 3
                trend_direction = "improving" if recent_avg > early_avg else "declining"
            else:
                trend_direction = "insufficient_data"

            trends[player.id] = {
                "name": player.name,
                "hole_by_hole": player_holes,
                "current_points": player.points,
                "holes_played": len(player_holes),
                "average_per_hole": player.points / max(1, len(player_holes)),
                "trend_direction": trend_direction,
                "best_hole": max(points_history) if points_history else 0,
                "worst_hole": min(points_history) if points_history else 0,
                "consistency": self._calculate_consistency([float(p) for p in points_history]),
            }

        return trends

    def _get_betting_analysis(self) -> dict[str, Any]:
        """Analyze betting patterns and success rates"""
        total_wagers: list[int] = []
        special_rules_count: dict[str, int] = {}

        analysis: dict[str, Any] = {
            "wager_escalation": total_wagers,
            "special_rules_frequency": special_rules_count,
            "success_rates": {},
            "risk_reward_analysis": {},
        }

        for hole_num, hole_state in self.hole_states.items():
            if hole_state.hole_complete:
                total_wagers.append(hole_state.betting.current_wager)

                # Track special rules
                if hole_state.betting.doubled:
                    special_rules_count["doubled"] = special_rules_count.get("doubled", 0) + 1
                if hole_state.betting.duncan_invoked:
                    special_rules_count["duncan"] = special_rules_count.get("duncan", 0) + 1
                if hole_state.betting.tunkarri_invoked:
                    special_rules_count["tunkarri"] = special_rules_count.get("tunkarri", 0) + 1
                if hole_state.betting.ping_pong_count > 0:
                    special_rules_count["ping_pong"] = special_rules_count.get("ping_pong", 0) + 1

        # Calculate success rates by strategy
        for player in self.players:
            solo_wins = 0
            solo_attempts = 0
            partnership_wins = 0
            partnership_attempts = 0

            for hole_state in self.hole_states.values():
                if not hole_state.hole_complete or not hole_state.points_awarded:
                    continue

                player_points = hole_state.points_awarded.get(player.id, 0)

                if hole_state.teams.type == "solo" and hole_state.teams.solo_player == player.id:
                    solo_attempts += 1
                    if player_points > 0:
                        solo_wins += 1
                elif hole_state.teams.type == "partners":
                    if player.id in hole_state.teams.team1 or player.id in hole_state.teams.team2:
                        partnership_attempts += 1
                        if player_points > 0:
                            partnership_wins += 1

            success_rates_dict = cast("dict[str, Any]", analysis["success_rates"])
            success_rates_dict[player.id] = {
                "name": player.name,
                "solo_success_rate": solo_wins / max(1, solo_attempts),
                "partnership_success_rate": partnership_wins / max(1, partnership_attempts),
                "solo_attempts": solo_attempts,
                "partnership_attempts": partnership_attempts,
            }

        # These were already set in initialization, just update if needed
        analysis["average_wager"] = sum(total_wagers) / max(1, len(total_wagers))
        analysis["max_wager"] = max(total_wagers) if total_wagers else 0

        return analysis

    def _get_partnership_chemistry(self) -> dict[str, Any]:
        """Analyze partnership combinations and their success rates"""
        chemistry = {}
        partnerships = {}

        for hole_state in self.hole_states.values():
            if not hole_state.hole_complete or hole_state.teams.type != "partners":
                continue

            # Get team combinations
            if hole_state.teams.team1 and len(hole_state.teams.team1) == 2:
                team1_key = tuple(sorted(hole_state.teams.team1))
                if team1_key not in partnerships:
                    partnerships[team1_key] = {"attempts": 0, "wins": 0, "points": 0}
                partnerships[team1_key]["attempts"] += 1

                # Check if this team won
                if hole_state.points_awarded:
                    team1_points = sum(hole_state.points_awarded.get(p, 0) for p in hole_state.teams.team1)
                    partnerships[team1_key]["points"] += team1_points
                    if team1_points > 0:
                        partnerships[team1_key]["wins"] += 1

            if hole_state.teams.team2 and len(hole_state.teams.team2) == 2:
                team2_key = tuple(sorted(hole_state.teams.team2))
                if team2_key not in partnerships:
                    partnerships[team2_key] = {"attempts": 0, "wins": 0, "points": 0}
                partnerships[team2_key]["attempts"] += 1

                if hole_state.points_awarded:
                    team2_points = sum(hole_state.points_awarded.get(p, 0) for p in hole_state.teams.team2)
                    partnerships[team2_key]["points"] += team2_points
                    if team2_points > 0:
                        partnerships[team2_key]["wins"] += 1

        # Convert to readable format
        for partnership, stats in partnerships.items():
            player1_name = self._get_player_name(partnership[0])
            player2_name = self._get_player_name(partnership[1])
            partnership_name = f"{player1_name} & {player2_name}"

            chemistry[partnership_name] = {
                "player_ids": list(partnership),
                "attempts": stats["attempts"],
                "wins": stats["wins"],
                "success_rate": stats["wins"] / max(1, stats["attempts"]),
                "total_points": stats["points"],
                "average_points": stats["points"] / max(1, stats["attempts"]),
                "chemistry_rating": self._calculate_chemistry_rating(stats),
            }

        return chemistry

    def _get_game_statistics(self) -> dict[str, Any]:
        """Get overall game statistics"""
        completed_holes = len([h for h in self.hole_states.values() if h.hole_complete])

        return {
            "holes_completed": completed_holes,
            "current_hole": self.current_hole,
            "game_phase": self.game_phase.value,
            "player_count": len(self.players),
            "total_points_awarded": sum(p.points for p in self.players),
            "leader": (max(self.players, key=lambda p: p.points).name if self.players else None),
            "closest_competition": self._get_competition_tightness(),
            "holes_remaining": 18 - completed_holes,
            "estimated_completion_time": f"{(18 - completed_holes) * 15} minutes",
        }

    def _get_risk_analysis(self) -> dict[str, Any]:
        """Analyze risk-taking patterns and outcomes"""
        risk_analysis = {}

        for player in self.players:
            high_risk_moves = 0
            high_risk_successes = 0
            conservative_moves = 0
            conservative_successes = 0

            for hole_state in self.hole_states.values():
                if not hole_state.hole_complete:
                    continue

                player_points = hole_state.points_awarded.get(player.id, 0) if hole_state.points_awarded else 0

                # Classify moves as high-risk or conservative
                if (
                    hole_state.teams.type == "solo" and hole_state.teams.solo_player == player.id
                ) or hole_state.betting.current_wager >= hole_state.betting.base_wager * 2:
                    high_risk_moves += 1
                    if player_points > 0:
                        high_risk_successes += 1
                else:
                    conservative_moves += 1
                    if player_points > 0:
                        conservative_successes += 1

            risk_analysis[player.id] = {
                "name": player.name,
                "risk_appetite": ("high" if high_risk_moves > conservative_moves else "conservative"),
                "high_risk_success_rate": high_risk_successes / max(1, high_risk_moves),
                "conservative_success_rate": conservative_successes / max(1, conservative_moves),
                "total_high_risk_moves": high_risk_moves,
                "total_conservative_moves": conservative_moves,
                "risk_reward_ratio": (high_risk_successes * 2) / max(1, high_risk_moves + conservative_moves),
            }

        return risk_analysis

    def _get_prediction_models(self) -> dict[str, Any]:
        """Generate prediction models for game outcomes"""
        current_standings = sorted(self.players, key=lambda p: p.points, reverse=True)
        holes_remaining = 18 - len([h for h in self.hole_states.values() if h.hole_complete])

        predictions = {}
        for i, player in enumerate(current_standings):
            # Simple prediction based on current performance and position
            position_factor = (len(self.players) - i) / len(self.players)
            consistency = self._calculate_consistency(
                [
                    hole_state.points_awarded.get(player.id, 0)
                    for hole_state in self.hole_states.values()
                    if hole_state.hole_complete and hole_state.points_awarded
                ]
            )

            win_probability = (position_factor * 0.6 + consistency * 0.4) * 100

            predictions[player.id] = {
                "name": player.name,
                "current_position": i + 1,
                "current_points": player.points,
                "win_probability": min(95, max(5, win_probability)),
                "projected_final_points": player.points + (holes_remaining * 0.5),
                "key_factors": self._get_key_factors(player),
            }

        return predictions

    def _calculate_consistency(self, scores: list[float]) -> float:
        """Calculate consistency score (lower variance = higher consistency)"""
        if len(scores) < 2:
            return 0.5

        avg = sum(scores) / len(scores)
        variance = sum((x - avg) ** 2 for x in scores) / len(scores)
        return max(0, min(1, 1 - (variance / 10)))  # Normalize to 0-1

    def _calculate_chemistry_rating(self, stats: dict) -> str:
        """Calculate partnership chemistry rating"""
        success_rate = stats["wins"] / max(1, stats["attempts"])
        if success_rate >= 0.7:
            return "Excellent"
        if success_rate >= 0.5:
            return "Good"
        if success_rate >= 0.3:
            return "Average"
        return "Poor"

    def _get_competition_tightness(self) -> str:
        """Determine how close the competition is"""
        if len(self.players) < 2:
            return "N/A"

        sorted_players = sorted(self.players, key=lambda p: p.points, reverse=True)
        point_spread = sorted_players[0].points - sorted_players[-1].points

        if point_spread <= 2:
            return "Very tight"
        if point_spread <= 5:
            return "Competitive"
        if point_spread <= 10:
            return "Moderate lead"
        return "Runaway leader"

    def _get_key_factors(self, player: Player) -> list[str]:
        """Get key factors affecting player's chances"""
        factors = []

        if player.points > 0:
            factors.append("Currently ahead")
        elif player.points < -5:
            factors.append("Needs aggressive play")

        # Add more sophisticated analysis based on game state
        factors.append(
            "Consistent performer" if self._calculate_consistency([0, 1, -1, 2]) > 0.6 else "Variable performance"
        )

        return factors

    # ========== PERSISTENCE METHODS (Required by PersistenceMixin) ==========
