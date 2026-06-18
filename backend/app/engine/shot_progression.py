"""Shot-by-shot hole progression for WolfGoatPigGame — shot order, betting opportunity analysis."""

import random
from typing import Any

from ..domain.game_types import HoleState, TeamFormation, WGPBettingOpportunity, WGPHoleProgression, WGPShotResult


class ShotProgressionMixin:
    """Shot-progression mode: per-shot state, ordering, and betting-opportunity analysis."""

    def enable_shot_progression(self) -> dict[str, Any]:
        """Enable shot-by-shot progression mode for betting analysis"""
        self.shot_simulation_mode = True
        if not self.hole_progression:
            self.hole_progression = WGPHoleProgression(hole_number=self.current_hole)
            # Initialize shot tracking for all players
            for player in self.players:
                (self.hole_progression.shots_taken if self.hole_progression is not None else {})[player.id] = []

        # Always determine shot order when enabling shot progression
        self._determine_shot_order()

        return {
            "status": "shot_progression_enabled",
            "message": "Shot-by-shot progression enabled with betting analysis",
            "current_hole": self.current_hole,
            "shot_order": self.hole_progression.current_shot_order,
        }

    def get_hole_progression_state(self) -> dict[str, Any]:
        """Get current hole progression state"""
        if not self.hole_progression:
            return {"shot_mode_enabled": False}

        return {
            "shot_mode_enabled": True,
            "hole_number": self.hole_progression.hole_number,
            "shots_taken": {
                player_id: [
                    {
                        "shot_number": shot.shot_number,
                        "lie_type": shot.lie_type,
                        "distance_to_pin": shot.distance_to_pin,
                        "shot_quality": shot.shot_quality,
                        "made_shot": shot.made_shot,
                    }
                    for shot in shots
                ]
                for player_id, shots in (
                    self.hole_progression.shots_taken if self.hole_progression is not None else {}
                ).items()
            },
            "betting_opportunities": [
                {
                    "type": opp.opportunity_type,
                    "message": opp.message,
                    "options": opp.options,
                    "recommended_action": opp.recommended_action,
                    "risk_assessment": opp.risk_assessment,
                }
                for opp in self.hole_progression.betting_opportunities
            ],
            "timeline_events": self.hole_progression.get_timeline_events(),
            "next_player": self._get_next_shot_player(),
            "hole_complete": self.hole_progression.hole_complete,
        }

    # Helper methods for shot progression
    def _determine_shot_order(self) -> None:
        """Determine order for shot-by-shot play"""
        hole_state = self.hole_states[self.current_hole]
        if self.hole_progression is not None:
            self.hole_progression.current_shot_order = hole_state.hitting_order.copy()

        # Initialize shot tracking for all players in hitting order
        for player_id in hole_state.hitting_order:
            if player_id not in (self.hole_progression.shots_taken if self.hole_progression is not None else {}):
                (self.hole_progression.shots_taken if self.hole_progression is not None else {})[player_id] = []

        # Set the initial next player to hit (first player in hitting order)
        if hole_state.hitting_order:
            hole_state.next_player_to_hit = hole_state.hitting_order[0]
            hole_state.current_order_of_play = hole_state.hitting_order.copy()

    def _analyze_betting_opportunity(self, shot_result: WGPShotResult) -> WGPBettingOpportunity | None:
        """Analyze if this shot creates a betting opportunity"""
        hole_state = self.hole_states[self.current_hole]

        # Skip if teams not formed yet
        if hole_state.teams.type == "pending":
            return None

        # Skip if already doubled
        if hole_state.betting.doubled:
            return None

        # Analyze shot for betting implications
        opportunity = None

        if shot_result.shot_quality == "excellent":
            opportunity = WGPBettingOpportunity(
                opportunity_type="double",
                message=f"💎 {self._get_player_name(shot_result.player_id)} hit an EXCELLENT shot! Perfect time to double!",
                options=["offer_double", "pass"],
                probability_analysis=self._calculate_doubling_odds(shot_result),
                recommended_action="offer_double",
                risk_assessment="low",
            )

        elif shot_result.shot_quality == "terrible":
            opportunity = WGPBettingOpportunity(
                opportunity_type="double",
                message=f"😬 {self._get_player_name(shot_result.player_id)} hit a TERRIBLE shot! Your team has the advantage!",
                options=["offer_double", "pass"],
                probability_analysis=self._calculate_doubling_odds(shot_result),
                recommended_action="offer_double",
                risk_assessment="medium",
            )

        elif shot_result.distance_to_pin < 20 and shot_result.shot_quality in [
            "good",
            "excellent",
        ]:
            opportunity = WGPBettingOpportunity(
                opportunity_type="strategic",
                message=f"🎯 {self._get_player_name(shot_result.player_id)} is close to the pin! Great doubling position!",
                options=["offer_double", "wait", "pass"],
                probability_analysis=self._calculate_doubling_odds(shot_result),
                recommended_action="offer_double",
                risk_assessment="low",
            )

        elif random.random() < 0.25:  # 25% chance for general opportunities
            opportunity = WGPBettingOpportunity(
                opportunity_type="strategic",
                message=f"🎲 Good time to press the action after {self._get_player_name(shot_result.player_id)}'s {shot_result.shot_quality} shot",
                options=["offer_double", "pass"],
                probability_analysis=self._calculate_doubling_odds(shot_result),
                recommended_action="pass",
                risk_assessment="medium",
            )

        return opportunity

    def _calculate_doubling_odds(self, shot_result: WGPShotResult) -> dict[str, float]:
        """Calculate odds for doubling based on current shot and team situation"""
        # Get current hole state
        hole_state = self.hole_states.get(self.current_hole)
        if not hole_state:
            return {
                "win_probability": 0.5,
                "confidence": 0.0,
                "shot_quality_factor": 0.0,
                "team_skill_factor": 0.0,
                "distance_factor": shot_result.distance_to_pin,
            }

        # Base shot advantage
        shot_advantage = 0.0
        if shot_result.shot_quality == "excellent":
            shot_advantage += 0.3
        elif shot_result.shot_quality == "good":
            shot_advantage += 0.2
        elif shot_result.shot_quality == "average":
            shot_advantage += 0.1
        elif shot_result.shot_quality == "poor":
            shot_advantage -= 0.1
        elif shot_result.shot_quality == "terrible":
            shot_advantage -= 0.2

        # Distance factor
        if shot_result.distance_to_pin < 20:
            shot_advantage += 0.1
        elif shot_result.distance_to_pin > 100:
            shot_advantage -= 0.1

        # Calculate team handicap advantages
        team_skill_diff = self._calculate_team_skill_difference(hole_state.teams)

        # Combine factors
        win_probability = min(0.95, max(0.05, shot_advantage + team_skill_diff))
        confidence = abs(win_probability - 0.5) * 2  # How confident we are

        return {
            "win_probability": round(win_probability, 2),
            "confidence": round(confidence, 2),
            "shot_quality_factor": shot_advantage,
            "team_skill_factor": team_skill_diff,
            "distance_factor": shot_result.distance_to_pin,
        }

    def _calculate_team_skill_difference(self, teams: TeamFormation) -> float:
        """Calculate the skill difference between teams based on handicaps"""
        if teams.type not in ["partners", "solo"]:
            return 0.0

        # Get current hole state
        hole_state = self.hole_states.get(self.current_hole)
        if not hole_state:
            return 0.0

        if teams.type == "partners":
            # Calculate average handicaps for each team
            team1_handicaps = []
            team2_handicaps = []

            for player in self.players:
                if player.id in teams.team1:
                    team1_handicaps.append(player.handicap)
                elif player.id in teams.team2:
                    team2_handicaps.append(player.handicap)

            if not team1_handicaps or not team2_handicaps:
                return 0.0

            avg_team1 = sum(team1_handicaps) / len(team1_handicaps)
            avg_team2 = sum(team2_handicaps) / len(team2_handicaps)

            # Lower handicap = better, so team1 advantage is (team2_avg - team1_avg)
            # Normalize to -1 to 1 range
            skill_diff = (avg_team2 - avg_team1) / 20.0
            return max(-1.0, min(1.0, skill_diff))

        if teams.type == "solo":
            # Solo player vs opponents
            captain = None
            opponents = []

            for player in self.players:
                if player.id == teams.captain:
                    captain = player
                elif player.id in teams.opponents:
                    opponents.append(player)

            if not captain or not opponents:
                return 0.0

            avg_opponent_handicap = sum(p.handicap for p in opponents) / len(opponents)

            # Solo advantage: (opponent_avg - captain_handicap) / 20.0
            skill_diff = (avg_opponent_handicap - captain.handicap) / 20.0
            return max(-1.0, min(1.0, skill_diff))

        return 0.0

    def _generate_betting_analysis(self, shot_result: WGPShotResult) -> dict[str, Any]:
        """Generate comprehensive betting analysis for human players"""
        analysis = {
            "shot_assessment": {
                "quality_rating": shot_result.shot_quality,
                "distance_remaining": shot_result.distance_to_pin,
                "strategic_value": ("high" if shot_result.shot_quality in ["excellent", "good"] else "low"),
            },
            "team_position": {
                "current_wager": self.hole_states[self.current_hole].betting.current_wager,
                "potential_double": self.hole_states[self.current_hole].betting.current_wager * 2,
                "momentum": ("positive" if shot_result.shot_quality in ["excellent", "good"] else "negative"),
            },
            "strategic_recommendations": self._generate_strategic_recommendations(shot_result),
            "computer_tendencies": self._analyze_computer_tendencies(),
        }

        return analysis

    def _generate_strategic_recommendations(self, shot_result: WGPShotResult) -> list[str]:
        """Generate strategic recommendations based on current situation"""
        recommendations = []

        if shot_result.shot_quality == "excellent":
            recommendations.append("🎯 Consider doubling immediately - excellent shot gives strong advantage")
            recommendations.append("💪 This is an ideal time to press the action")

        elif shot_result.shot_quality == "terrible":
            recommendations.append("🛡️ Be cautious - opponent's poor shot creates opportunity but don't overcommit")
            recommendations.append("⚖️ Evaluate team strength before doubling")

        elif shot_result.distance_to_pin < 20:
            recommendations.append("🥅 Close to pin - high probability scoring opportunity")
            recommendations.append("🎲 Good position for strategic doubling")

        return recommendations

    def _analyze_computer_tendencies(self) -> dict[str, Any]:
        """Analyze computer player tendencies for strategic insight"""
        if not hasattr(self, "computer_players"):
            return {}

        tendencies = {}
        for player_id, computer_player in self.computer_players.items():
            personality = computer_player.personality
            tendencies[player_id] = {
                "personality": personality,
                "betting_style": self._get_personality_betting_style(personality),
                "double_acceptance": self._get_personality_double_tendency(personality),
            }

        return tendencies

    def _get_personality_betting_style(self, personality: str) -> str:
        """Get betting style description for personality"""
        styles = {
            "aggressive": "High risk, frequent doubling",
            "conservative": "Low risk, selective doubling",
            "balanced": "Moderate risk, situational doubling",
            "strategic": "Calculated risk, position-based doubling",
        }
        return styles.get(personality, "Unknown")

    def _get_personality_double_tendency(self, personality: str) -> str:
        """Get double acceptance tendency for personality"""
        tendencies = {
            "aggressive": "Accepts most doubles",
            "conservative": "Declines risky doubles",
            "balanced": "Situational acceptance",
            "strategic": "Analyzes before accepting",
        }
        return tendencies.get(personality, "Unknown")

    def _update_next_player_to_hit(self, hole_state: HoleState, shot_result: WGPShotResult) -> None:
        """Update the next player to hit based on game state"""
        if shot_result.made_shot or hole_state.hole_complete:
            hole_state.next_player_to_hit = None
            return

        # Check if all tee shots have been completed
        all_tee_shots_complete = all(player_id in hole_state.ball_positions for player_id in hole_state.hitting_order)

        if not all_tee_shots_complete:
            # Still in tee shot phase - follow hitting order
            for player_id in hole_state.hitting_order:
                if player_id not in hole_state.ball_positions:
                    hole_state.next_player_to_hit = player_id
                    return
            hole_state.next_player_to_hit = None
        else:
            # All tee shots complete - find player farthest from pin who hasn't holed out and hasn't exceeded shot limit
            farthest_distance: float = 0.0
            next_player = None

            for player_id in hole_state.hitting_order:
                ball = hole_state.ball_positions.get(player_id)
                if (
                    ball and ball.distance_to_pin > 0 and ball.shot_count < 8
                ):  # Player hasn't holed out and under shot limit
                    if ball.distance_to_pin > farthest_distance:
                        farthest_distance = ball.distance_to_pin
                        next_player = player_id

            hole_state.next_player_to_hit = next_player

    def _get_next_shot_player(self) -> str | None:
        """Get the next player to hit based on current ball positions"""
        hole_state = self.hole_states[self.current_hole]

        # Check if all tee shots have been completed
        all_tee_shots_complete = all(player_id in hole_state.ball_positions for player_id in hole_state.hitting_order)

        if not all_tee_shots_complete:
            # Still in tee shot phase - follow hitting order
            for player_id in hole_state.hitting_order:
                if player_id not in hole_state.ball_positions:
                    return player_id
            return None
        # All tee shots complete - use distance-based order
        return hole_state.next_player_to_hit

    def _check_hole_completion(self) -> bool:
        """Check if hole is complete (all players holed out or max shots reached)"""
        if not self.hole_progression:
            return False

        for player_id in self.hole_progression.current_shot_order:
            shots = (self.hole_progression.shots_taken if self.hole_progression is not None else {})[player_id]
            if not shots:
                return False

            last_shot = shots[-1]
            # Continue if player hasn't holed out and hasn't reached max shots
            if not last_shot.made_shot and len(shots) < 8:
                return False

        return True

    def _get_comprehensive_hole_state(self) -> dict[str, Any]:
        """Get comprehensive hole state including all ball positions and game state"""
        hole_state = self.hole_states[self.current_hole]

        return {
            "hole_number": hole_state.hole_number,
            "current_shot_number": hole_state.current_shot_number,
            "hole_complete": hole_state.hole_complete,
            "wagering_closed": hole_state.wagering_closed,
            # Ball positions for all players
            "ball_positions": {
                player_id: (
                    {
                        "distance_to_pin": ball.distance_to_pin,
                        "lie_type": ball.lie_type,
                        "shot_count": ball.shot_count,
                        "holed": ball.holed,
                        "conceded": ball.conceded,
                        "penalty_strokes": ball.penalty_strokes,
                    }
                    if ball
                    else None
                )
                for player_id in [p.id for p in self.players]
                for ball in [hole_state.get_player_ball_position(player_id)]
            },
            # Order of play and line of scrimmage
            "current_order_of_play": hole_state.current_order_of_play,
            "line_of_scrimmage": hole_state.line_of_scrimmage,
            "next_player_to_hit": hole_state.next_player_to_hit,
            # Stroke advantages for all players
            "stroke_advantages": {
                player_id: (
                    {
                        "handicap": stroke_adv.handicap,
                        "strokes_received": stroke_adv.strokes_received,
                        "net_score": stroke_adv.net_score,
                        "stroke_index": stroke_adv.stroke_index,
                    }
                    if stroke_adv
                    else None
                )
                for player_id in [p.id for p in self.players]
                for stroke_adv in [hole_state.get_player_stroke_advantage(player_id)]
            },
            "hole_par": hole_state.hole_par,
            "stroke_index": hole_state.stroke_index,
            # Team information
            "teams": {
                "type": hole_state.teams.type,
                "captain": hole_state.teams.captain,
                "team1": hole_state.teams.team1,
                "team2": hole_state.teams.team2,
                "solo_player": hole_state.teams.solo_player,
                "opponents": hole_state.teams.opponents,
            },
            # Betting state
            "betting": {
                "base_wager": hole_state.betting.base_wager,
                "current_wager": hole_state.betting.current_wager,
                "doubled": hole_state.betting.doubled,
                "redoubled": hole_state.betting.redoubled,
                "carry_over": hole_state.betting.carry_over,
                "float_invoked": hole_state.betting.float_invoked,
                "option_invoked": hole_state.betting.option_invoked,
                "duncan_invoked": hole_state.betting.duncan_invoked,
                "tunkarri_invoked": hole_state.betting.tunkarri_invoked,
                "joes_special_value": hole_state.betting.joes_special_value,
                "wagering_closed": hole_state.wagering_closed,
            },
            # Completion tracking
            "balls_in_hole": hole_state.balls_in_hole,
            "concessions": hole_state.concessions,
            "scores": hole_state.scores,
        }

    # Utility functions for AI decision making
