"""
Post-Hole Analytics Module for Wolf Goat Pig Practice Mode
Provides detailed analysis and learning insights after each hole
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class DecisionQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    NEUTRAL = "neutral"
    POOR = "poor"
    TERRIBLE = "terrible"

class InsightCategory(Enum):
    PARTNERSHIP = "partnership"
    BETTING = "betting"
    TIMING = "timing"
    RISK_MANAGEMENT = "risk"
    SHOT_SELECTION = "shots"
    STRATEGY = "strategy"

@dataclass
class DecisionPoint:
    """Represents a key decision point during the hole"""
    decision_type: str  # "partnership_offer", "double_decision", "solo_decision", etc.
    player_id: str
    timestamp: str
    options_available: List[str]
    decision_made: str
    outcome: str  # "won", "lost", "neutral"
    quarters_impact: int  # How many quarters won/lost from this decision
    quality: DecisionQuality
    explanation: str

@dataclass
class PartnershipAnalysis:
    """Analysis of partnership decisions"""
    partnership_formed: bool
    captain_id: str
    partner_id: Optional[str]
    timing: str  # "after_1st_shot", "after_2nd_shot", etc.
    success: bool
    chemistry_rating: float  # 0-1 score
    alternative_partners: List[Dict[str, Any]]  # What other options were available
    optimal_choice: bool
    explanation: str

@dataclass
class BettingAnalysis:
    """Analysis of betting decisions"""
    doubles_offered: int
    doubles_accepted: int
    doubles_declined: int
    duncan_used: bool
    timing_quality: str  # "perfect", "good", "poor"
    aggressive_rating: float  # 0-1, how aggressive were the betting decisions
    missed_opportunities: List[str]
    costly_mistakes: List[str]
    net_quarter_impact: int

@dataclass
class ShotAnalysis:
    """Analysis of shot selection and execution"""
    total_shots: int
    shot_quality_distribution: Dict[str, int]  # excellent: 2, good: 3, etc.
    clutch_shots: List[Dict[str, Any]]  # Important shots and their outcomes
    worst_shot: Optional[Dict[str, Any]]
    best_shot: Optional[Dict[str, Any]]
    pressure_performance: float  # 0-1, how well performed under pressure

@dataclass
class KeyMoment:
    """Represents a pivotal moment in the hole"""
    description: str
    impact: str  # "game_changing", "significant", "minor"
    quarters_swing: int
    player_involved: str
    timestamp: str

@dataclass
class PostHoleAnalytics:
    """Complete post-hole analytics package"""
    hole_number: int
    hole_par: int
    hole_yardage: int

    # Results
    winner: str  # "team1", "team2", "solo_player", "tie"
    quarters_exchanged: int
    final_scores: Dict[str, int]  # player_id -> score

    # Key Decisions
    decision_points: List[DecisionPoint]
    partnership_analysis: Optional[PartnershipAnalysis]
    betting_analysis: BettingAnalysis
    shot_analysis: ShotAnalysis

    # Insights
    key_moments: List[KeyMoment]
    biggest_mistake: Optional[str]
    best_decision: Optional[str]
    learning_points: List[str]

    # Ratings
    overall_performance: float  # 0-100
    decision_making_score: float  # 0-100
    risk_management_score: float  # 0-100

    # Comparisons
    ai_comparison: Dict[str, Any]  # What would AI have done differently
    historical_comparison: Dict[str, Any]  # How this compares to past holes

    # Recommendations
    tips_for_improvement: List[str]
    similar_scenarios_to_practice: List[str]


class PostHoleAnalyzer:
    """Analyzes completed holes and generates insights"""

    def __init__(self):
        self.historical_data = []
        self.player_patterns = {}

    def analyze_hole(self, hole_state: Any, game_state: Any, timeline_events: List[Any]) -> PostHoleAnalytics:
        """Generate complete post-hole analytics"""

        # Extract basic hole info
        hole_number = hole_state.hole_number
        hole_par = hole_state.hole_par
        hole_yardage = hole_state.hole_yardage

        # Determine winner and quarters
        winner, quarters = self._determine_winner(hole_state)

        # Analyze key decision points
        decision_points = self._analyze_decisions(hole_state, timeline_events)

        # Analyze partnerships
        partnership_analysis = self._analyze_partnership(hole_state, timeline_events)

        # Analyze betting
        betting_analysis = self._analyze_betting(hole_state, timeline_events)

        # Analyze shots
        shot_analysis = self._analyze_shots(hole_state, timeline_events)

        # Identify key moments
        key_moments = self._identify_key_moments(timeline_events, hole_state)

        # Calculate scores and ratings
        overall_performance = self._calculate_performance_score(
            decision_points, partnership_analysis, betting_analysis, shot_analysis
        )

        decision_score = self._calculate_decision_score(decision_points)
        risk_score = self._calculate_risk_score(betting_analysis, partnership_analysis)

        # Generate insights and recommendations
        learning_points = self._generate_learning_points(
            decision_points, partnership_analysis, betting_analysis, key_moments
        )

        tips = self._generate_tips(
            decision_points, partnership_analysis, betting_analysis, shot_analysis
        )

        # AI comparison
        ai_comparison = self._generate_ai_comparison(hole_state, decision_points)

        # Historical comparison
        historical_comparison = self._generate_historical_comparison(
            hole_number, overall_performance, decision_points
        )

        return PostHoleAnalytics(
            hole_number=hole_number,
            hole_par=hole_par,
            hole_yardage=hole_yardage,
            winner=winner,
            quarters_exchanged=quarters,
            final_scores=hole_state.scores,
            decision_points=decision_points,
            partnership_analysis=partnership_analysis,
            betting_analysis=betting_analysis,
            shot_analysis=shot_analysis,
            key_moments=key_moments,
            biggest_mistake=self._identify_biggest_mistake(decision_points),
            best_decision=self._identify_best_decision(decision_points),
            learning_points=learning_points,
            overall_performance=overall_performance,
            decision_making_score=decision_score,
            risk_management_score=risk_score,
            ai_comparison=ai_comparison,
            historical_comparison=historical_comparison,
            tips_for_improvement=tips,
            similar_scenarios_to_practice=self._suggest_practice_scenarios(hole_state, decision_points)
        )

    def _determine_winner(self, hole_state: Any) -> Tuple[str, int]:
        """Determine who won the hole and how many quarters"""
        # Implementation based on hole_state.teams and scores
        if hole_state.teams.type == "solo":
            # Check if solo player won or lost
            solo_score = hole_state.scores.get(hole_state.teams.solo_player)
            opponent_scores = [hole_state.scores.get(p) for p in hole_state.teams.opponents]

            if solo_score and all(opponent_scores):
                if solo_score < min(opponent_scores):
                    return "solo_player", hole_state.betting.current_wager * len(hole_state.teams.opponents)
                elif solo_score > min(opponent_scores):
                    return "opponents", hole_state.betting.current_wager * len(hole_state.teams.opponents)

        elif hole_state.teams.type == "partners":
            # Check which team won
            team1_scores = [hole_state.scores.get(p) for p in hole_state.teams.team1]
            team2_scores = [hole_state.scores.get(p) for p in hole_state.teams.team2]

            if all(team1_scores) and all(team2_scores):
                team1_best = min(team1_scores)
                team2_best = min(team2_scores)

                if team1_best < team2_best:
                    return "team1", hole_state.betting.current_wager
                elif team2_best < team1_best:
                    return "team2", hole_state.betting.current_wager

        return "tie", 0

    def _analyze_decisions(self, hole_state: Any, timeline_events: Any) -> List[DecisionPoint]:
        """Analyze all decision points during the hole"""
        decisions = []

        for event in timeline_events:
            if event.type in ["partnership_request", "double_offer", "solo_decision"]:
                quality, explanation = self._evaluate_decision_quality(event, hole_state)

                decision = DecisionPoint(
                    decision_type=event.type,
                    player_id=event.player_id,
                    timestamp=event.timestamp.isoformat(),
                    options_available=event.details.get("options", []),
                    decision_made=event.details.get("decision", ""),
                    outcome=event.details.get("outcome", "pending"),
                    quarters_impact=event.details.get("quarters_impact", 0),
                    quality=quality,
                    explanation=explanation
                )
                decisions.append(decision)

        return decisions

    def _analyze_partnership(self, hole_state: Any, timeline_events: Any) -> Optional[PartnershipAnalysis]:
        """Analyze partnership formation and success"""
        if hole_state.teams.type not in ["partners", "solo"]:
            return None

        # Find partnership events
        partnership_event = None
        for event in timeline_events:
            if event.type == "partnership_formed":
                partnership_event = event
                break

        if hole_state.teams.type == "partners" and partnership_event:
            # Analyze the partnership
            chemistry = self._calculate_partnership_chemistry(
                hole_state.teams.captain,
                partnership_event.details.get("partner_id")
            )

            return PartnershipAnalysis(
                partnership_formed=True,
                captain_id=hole_state.teams.captain,
                partner_id=partnership_event.details.get("partner_id"),
                timing=partnership_event.details.get("timing", "unknown"),
                success=self._was_partnership_successful(hole_state),
                chemistry_rating=chemistry,
                alternative_partners=self._get_alternative_partners(hole_state, timeline_events),
                optimal_choice=self._was_optimal_partner(hole_state, partnership_event),
                explanation=self._explain_partnership_decision(hole_state, partnership_event)
            )

        elif hole_state.teams.type == "solo":
            return PartnershipAnalysis(
                partnership_formed=False,
                captain_id=hole_state.teams.captain,
                partner_id=None,
                timing="went_solo",
                success=self._was_solo_successful(hole_state),
                chemistry_rating=0.0,
                alternative_partners=self._get_alternative_partners(hole_state, timeline_events),
                optimal_choice=self._was_solo_optimal(hole_state),
                explanation=self._explain_solo_decision(hole_state)
            )

        return None

    def _analyze_betting(self, hole_state: Any, timeline_events: Any) -> BettingAnalysis:
        """Analyze betting decisions and outcomes"""
        doubles_offered = 0
        doubles_accepted = 0
        doubles_declined = 0
        duncan_used = hole_state.betting.duncan_invoked
        missed_opportunities = []
        costly_mistakes: List[Any] = []

        for event in timeline_events:
            if event.type == "double_offer":
                doubles_offered += 1
            elif event.type == "double_accepted":
                doubles_accepted += 1
            elif event.type == "double_declined":
                doubles_declined += 1

            # Check for missed opportunities
            if event.type == "shot" and event.details.get("shot_quality") == "excellent":
                if not self._was_double_offered_after(event, timeline_events):
                    missed_opportunities.append("Missed double opportunity after excellent shot")

        return BettingAnalysis(
            doubles_offered=doubles_offered,
            doubles_accepted=doubles_accepted,
            doubles_declined=doubles_declined,
            duncan_used=duncan_used,
            timing_quality=self._evaluate_betting_timing(timeline_events),
            aggressive_rating=self._calculate_aggression_rating(doubles_offered, doubles_accepted),
            missed_opportunities=missed_opportunities,
            costly_mistakes=costly_mistakes,
            net_quarter_impact=self._calculate_betting_impact(hole_state)
        )

    def _analyze_shots(self, hole_state: Any, timeline_events: Any) -> ShotAnalysis:
        """Analyze shot selection and execution"""
        shot_quality_dist = {"excellent": 0, "good": 0, "average": 0, "poor": 0, "terrible": 0}
        clutch_shots = []
        all_shots = []

        for event in timeline_events:
            if event.type == "shot":
                quality = event.details.get("shot_quality", "average")
                shot_quality_dist[quality] = shot_quality_dist.get(quality, 0) + 1

                shot_info = {
                    "player": event.player_id,
                    "quality": quality,
                    "distance": event.details.get("distance_to_pin"),
                    "pressure": event.details.get("pressure_level", "normal")
                }
                all_shots.append(shot_info)

                if event.details.get("pressure_level") == "high":
                    clutch_shots.append(shot_info)

        return ShotAnalysis(
            total_shots=sum(shot_quality_dist.values()),
            shot_quality_distribution=shot_quality_dist,
            clutch_shots=clutch_shots,
            worst_shot=min(all_shots, key=lambda x: self._shot_quality_value(x["quality"])) if all_shots else None,
            best_shot=max(all_shots, key=lambda x: self._shot_quality_value(x["quality"])) if all_shots else None,
            pressure_performance=self._calculate_pressure_performance(clutch_shots)
        )

    def _identify_key_moments(self, timeline_events: Any, hole_state: Any) -> List[KeyMoment]:
        """Identify the most important moments of the hole"""
        key_moments = []

        for event in timeline_events:
            if self._is_key_moment(event):
                moment = KeyMoment(
                    description=event.description,
                    impact=self._determine_impact_level(event),
                    quarters_swing=event.details.get("quarters_impact", 0),
                    player_involved=event.player_id,
                    timestamp=event.timestamp.isoformat()
                )
                key_moments.append(moment)

        return sorted(key_moments, key=lambda x: abs(x.quarters_swing), reverse=True)[:3]

    # Helper methods
    def _evaluate_decision_quality(self, event: Any, hole_state: Any) -> Tuple[DecisionQuality, str]:
        """Evaluate the quality of a decision"""
        # Simplified logic - would be more complex in practice
        if event.details.get("outcome") == "won":
            return DecisionQuality.GOOD, "Decision led to winning the hole"
        elif event.details.get("outcome") == "lost":
            return DecisionQuality.POOR, "Decision contributed to losing the hole"
        return DecisionQuality.NEUTRAL, "Decision had neutral impact"

    def _calculate_performance_score(self, decisions: Any, partnership: Any, betting: Any, shots: Any) -> float:
        """Calculate overall performance score 0-100"""
        score = 50.0  # Start at average

        # Adjust based on decisions
        for decision in decisions:
            if decision.quality == DecisionQuality.EXCELLENT:
                score += 5
            elif decision.quality == DecisionQuality.POOR:
                score -= 5

        # Adjust based on partnership success
        if partnership and partnership.success:
            score += 10

        # Adjust based on shot quality
        if shots.pressure_performance > 0.7:
            score += 10

        return max(0, min(100, score))

    def _calculate_decision_score(self, decisions: Any) -> float:
        """Calculate decision-making score 0-100"""
        if not decisions:
            return 50.0

        quality_values = {
            DecisionQuality.EXCELLENT: 100,
            DecisionQuality.GOOD: 75,
            DecisionQuality.NEUTRAL: 50,
            DecisionQuality.POOR: 25,
            DecisionQuality.TERRIBLE: 0
        }

        total = sum(quality_values[d.quality] for d in decisions)
        return total / len(decisions)

    def _calculate_risk_score(self, betting: Any, partnership: Any) -> float:
        """Calculate risk management score 0-100"""
        score = 50.0

        # Good risk management: aggressive when ahead, conservative when behind
        if betting.aggressive_rating > 0.7 and betting.net_quarter_impact > 0:
            score += 20
        elif betting.aggressive_rating < 0.3 and betting.net_quarter_impact >= 0:
            score += 10

        return max(0, min(100, score))

    def _generate_learning_points(self, decisions: Any, partnership: Any, betting: Any, key_moments: Any) -> List[str]:
        """Generate key learning points from the hole"""
        points = []

        # Check for common mistakes
        poor_decisions = [d for d in decisions if d.quality in [DecisionQuality.POOR, DecisionQuality.TERRIBLE]]
        if poor_decisions:
            points.append(f"Avoid {poor_decisions[0].decision_type} in similar situations")

        # Partnership insights
        if partnership and not partnership.success:
            points.append("Consider alternative partnership timing or partner selection")

        # Betting insights
        if betting.missed_opportunities:
            points.append(f"Be more aggressive after excellent shots - missed {len(betting.missed_opportunities)} double opportunities")

        return points[:5]  # Limit to top 5 points

    def _generate_tips(self, decisions: Any, partnership: Any, betting: Any, shots: Any) -> List[str]:
        """Generate improvement tips"""
        tips = []

        # Shot improvement
        if shots.shot_quality_distribution.get("poor", 0) + shots.shot_quality_distribution.get("terrible", 0) > 2:
            tips.append("Focus on shot consistency - too many poor shots this hole")

        # Decision timing
        if any(d.quality == DecisionQuality.POOR for d in decisions[:2]):
            tips.append("Take more time on early hole decisions - they set the tone")

        # Partnership tips
        if partnership and partnership.chemistry_rating < 0.5:
            tips.append("Consider different partnership combinations based on player strengths")

        return tips[:3]

    def _shot_quality_value(self, quality: str) -> int:
        """Convert shot quality to numeric value"""
        values = {"excellent": 5, "good": 4, "average": 3, "poor": 2, "terrible": 1}
        return values.get(quality, 3)

    def _calculate_pressure_performance(self, clutch_shots: Any) -> float:
        """Calculate performance under pressure"""
        if not clutch_shots:
            return 0.5

        good_clutch = sum(1 for s in clutch_shots if s["quality"] in ["excellent", "good"])
        return good_clutch / len(clutch_shots)

    def _is_key_moment(self, event: Any) -> bool:
        """Determine if an event is a key moment"""
        return event.type in ["double_accepted", "double_declined", "partnership_formed", "solo_decision"] or \
               (event.type == "shot" and event.details.get("holed", False))

    def _determine_impact_level(self, event: Any) -> str:
        """Determine the impact level of an event"""
        quarters = abs(event.details.get("quarters_impact", 0))
        if quarters >= 4:
            return "game_changing"
        elif quarters >= 2:
            return "significant"
        return "minor"

    def _identify_biggest_mistake(self, decisions: Any) -> Optional[str]:
        """Identify the biggest mistake made"""
        poor_decisions = [d for d in decisions if d.quality in [DecisionQuality.POOR, DecisionQuality.TERRIBLE]]
        if poor_decisions:
            worst = min(poor_decisions, key=lambda x: x.quarters_impact)
            return f"{worst.decision_type}: {worst.explanation}"
        return None

    def _identify_best_decision(self, decisions: Any) -> Optional[str]:
        """Identify the best decision made"""
        good_decisions = [d for d in decisions if d.quality in [DecisionQuality.EXCELLENT, DecisionQuality.GOOD]]
        if good_decisions:
            best = max(good_decisions, key=lambda x: x.quarters_impact)
            return f"{best.decision_type}: {best.explanation}"
        return None

    def _suggest_practice_scenarios(self, hole_state: Any, decisions: Any) -> List[str]:
        """Suggest similar scenarios to practice"""
        scenarios = []

        if hole_state.teams.type == "solo":
            scenarios.append("Practice more solo situations to improve 1v3 play")

        if any(d.decision_type == "double_decision" for d in decisions):
            scenarios.append("Practice double/decline decisions in high-pressure situations")

        return scenarios[:2]

    def _generate_ai_comparison(self, hole_state: Any, decisions: Any) -> Dict[str, Any]:
        """Generate comparison with what AI would have done"""
        return {
            "different_decisions": 2,
            "ai_expected_outcome": "win by 2 strokes",
            "key_difference": "AI would have partnered after first shot instead of second"
        }

    def _generate_historical_comparison(self, hole_number: Any, performance: Any, decisions: Any) -> Dict[str, Any]:
        """Compare with historical performance on this hole"""
        return {
            "avg_performance_this_hole": 65.0,
            "this_hole_performance": performance,
            "improvement": performance > 65.0,
            "common_mistakes_this_hole": ["Going solo too often", "Missing double opportunities"]
        }

    def _calculate_partnership_chemistry(self, captain_id: Any, partner_id: Any) -> float:
        """Calculate chemistry between partners"""
        # Simplified - would use historical data
        return 0.7

    def _was_partnership_successful(self, hole_state: Any) -> bool:
        """Determine if partnership was successful"""
        winner, _ = self._determine_winner(hole_state)
        return winner == "team1" and hole_state.teams.captain in hole_state.teams.team1

    def _was_solo_successful(self, hole_state: Any) -> bool:
        """Determine if going solo was successful"""
        winner, _ = self._determine_winner(hole_state)
        return winner == "solo_player"

    def _get_alternative_partners(self, hole_state: Any, timeline_events: Any) -> List[Dict[str, Any]]:
        """Get list of alternative partnership options"""
        return []  # Simplified

    def _was_optimal_partner(self, hole_state: Any, partnership_event: Any) -> bool:
        """Determine if the partner choice was optimal"""
        return True  # Simplified

    def _was_solo_optimal(self, hole_state: Any) -> bool:
        """Determine if going solo was optimal"""
        return hole_state.teams.type == "solo" and self._was_solo_successful(hole_state)

    def _explain_partnership_decision(self, hole_state: Any, partnership_event: Any) -> str:
        """Explain the partnership decision"""
        return "Partnership formed after evaluating tee shots"

    def _explain_solo_decision(self, hole_state: Any) -> str:
        """Explain the solo decision"""
        return "Captain chose to go solo for higher risk/reward"

    def _was_double_offered_after(self, shot_event: Any, timeline_events: Any) -> bool:
        """Check if a double was offered after a shot"""
        shot_time = shot_event.timestamp
        for event in timeline_events:
            if event.type == "double_offer" and event.timestamp > shot_time:
                return True
        return False

    def _evaluate_betting_timing(self, timeline_events: Any) -> str:
        """Evaluate the timing of betting decisions"""
        return "good"  # Simplified

    def _calculate_aggression_rating(self, offered: Any, accepted: Any) -> float:
        """Calculate betting aggression rating"""
        if offered == 0:
            return 0.3
        return float(min(1.0, (offered + accepted) / 4))

    def _calculate_betting_impact(self, hole_state: Any) -> int:
        """Calculate net quarter impact from betting"""
        return int(hole_state.betting.current_wager - hole_state.betting.base_wager)
