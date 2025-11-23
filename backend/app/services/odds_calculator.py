"""
Comprehensive odds calculation engine for Wolf Goat Pig betting system.
Provides real-time win probability calculations, expected value analysis,
and strategic betting insights.
"""

import statistics
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class TeamConfiguration(Enum):
    """Team configuration types in Wolf Goat Pig"""
    PENDING = "pending"
    SOLO = "solo"
    PARTNERS = "partners"


class ShotDifficulty(Enum):
    """Shot difficulty levels"""
    VERY_EASY = "very_easy"
    EASY = "easy"
    MODERATE = "moderate"
    DIFFICULT = "difficult"
    VERY_DIFFICULT = "very_difficult"


@dataclass
class PlayerState:
    """Current state of a player for odds calculation"""
    id: str
    name: str
    handicap: float
    current_score: int = 0
    shots_taken: int = 0
    distance_to_pin: float = 0.0
    lie_type: str = "fairway"
    is_captain: bool = False
    team_id: Optional[str] = None
    confidence_factor: float = 1.0  # Multiplier based on recent performance


@dataclass
class HoleState:
    """Current hole state for odds calculation"""
    hole_number: int
    par: int
    difficulty_rating: float = 3.0  # 1-5 scale
    weather_factor: float = 1.0  # Wind, rain, etc.
    pin_position: str = "middle"  # front, middle, back
    course_conditions: str = "normal"  # fast, normal, slow
    teams: TeamConfiguration = TeamConfiguration.PENDING
    current_wager: int = 1
    is_doubled: bool = False
    line_of_scrimmage_passed: bool = False


@dataclass
class BettingScenario:
    """A specific betting scenario with calculated odds"""
    scenario_type: str  # 'offer_double', 'accept_partnership', etc.
    win_probability: float
    expected_value: float
    risk_level: str  # 'low', 'medium', 'high'
    confidence_interval: Tuple[float, float]
    recommendation: str
    reasoning: str
    payout_matrix: Dict[str, float]


@dataclass
class OddsResult:
    """Complete odds calculation result"""
    timestamp: float
    calculation_time_ms: float
    player_probabilities: Dict[str, Any]
    team_probabilities: Dict[str, float]
    betting_scenarios: List[BettingScenario]
    optimal_strategy: str
    risk_assessment: Dict[str, Any]
    educational_insights: List[str]
    confidence_level: float


class OddsCalculator:
    """
    Core odds calculation engine for Wolf Goat Pig.
    Provides real-time probability calculations and betting analysis.
    """

    def __init__(self):
        self.cache_expiry = 30  # seconds
        self.performance_target_ms = 50
        self._shot_difficulty_cache = {}
        self._handicap_adjustments = self._initialize_handicap_adjustments()
        self._probability_cache = {}
        self._team_calculation_cache = {}
        self._last_cache_cleanup = time.time()

        # Pre-compute commonly used values
        self._distance_thresholds = [50, 100, 150, 200]
        self._lie_multipliers = self._precompute_lie_multipliers()
        self._handicap_multipliers = self._precompute_handicap_multipliers()

    def _initialize_handicap_adjustments(self) -> Dict[float, float]:
        """Initialize handicap-based probability adjustments"""
        adjustments: Dict[float, float] = {}
        for hcp in range(0, 37):
            # Convert handicap to skill multiplier (0 = best, 36 = worst)
            if hcp <= 5:
                adjustments[float(hcp)] = 1.2  # Scratch players have advantage
            elif hcp <= 10:
                adjustments[float(hcp)] = 1.1
            elif hcp <= 15:
                adjustments[float(hcp)] = 1.0
            elif hcp <= 20:
                adjustments[float(hcp)] = 0.9
            elif hcp <= 25:
                adjustments[float(hcp)] = 0.8
            else:
                adjustments[float(hcp)] = 0.7
        return adjustments

    def _precompute_lie_multipliers(self) -> Dict[str, float]:
        """Pre-compute lie type multipliers for performance"""
        return {
            "green": 1.1,
            "fringe": 1.05,
            "fairway": 1.0,
            "first_cut": 0.95,
            "rough": 0.8,
            "deep_rough": 0.6,
            "bunker": 0.5,
            "water": 0.0,
            "trees": 0.3
        }

    def _precompute_handicap_multipliers(self) -> Dict[int, float]:
        """Pre-compute handicap multipliers for common handicaps"""
        multipliers = {}
        for hcp in range(0, 37):
            if hcp <= 5:
                multipliers[hcp] = 1.2
            elif hcp <= 10:
                multipliers[hcp] = 1.1
            elif hcp <= 15:
                multipliers[hcp] = 1.0
            elif hcp <= 20:
                multipliers[hcp] = 0.9
            elif hcp <= 25:
                multipliers[hcp] = 0.8
            else:
                multipliers[hcp] = 0.7
        return multipliers

    def _cleanup_caches_if_needed(self):
        """Periodic cache cleanup to prevent memory bloat"""
        current_time = time.time()
        if current_time - self._last_cache_cleanup > 300:  # Every 5 minutes
            # Clear old probability cache entries
            expired_keys = [
                k for k, (timestamp, _) in self._probability_cache.items()
                if current_time - timestamp > self.cache_expiry
            ]
            for key in expired_keys:
                del self._probability_cache[key]

            # Clear team calculation cache
            self._team_calculation_cache.clear()

            self._last_cache_cleanup = current_time

    def _calculate_shot_success_probability(
        self,
        handicap: float,
        distance: float,
        lie_type: str,
        hole_difficulty: float
    ) -> float:
        """
        Calculate probability of a successful shot based on player skill and conditions.
        Optimized for performance with caching and pre-computed values.
        """
        # Create cache key for this calculation
        cache_key = (round(handicap, 1), round(distance, 1), lie_type, round(hole_difficulty, 1))

        # Check cache first
        current_time = time.time()
        if cache_key in self._probability_cache:
            timestamp, cached_prob = self._probability_cache[cache_key]
            if current_time - timestamp < self.cache_expiry:
                return float(cached_prob)

        # Perform cleanup if needed
        self._cleanup_caches_if_needed()

        # Base probability by distance (optimized with pre-computed thresholds)
        if distance <= self._distance_thresholds[0]:  # <= 50
            base_prob = 0.85
        elif distance <= self._distance_thresholds[1]:  # <= 100
            base_prob = 0.75
        elif distance <= self._distance_thresholds[2]:  # <= 150
            base_prob = 0.65
        elif distance <= self._distance_thresholds[3]:  # <= 200
            base_prob = 0.55
        else:
            base_prob = 0.45

        # Handicap adjustment (use pre-computed multipliers)
        hcp_key = min(36, max(0, int(handicap)))
        hcp_adjustment = self._handicap_multipliers.get(hcp_key, 0.7)

        # Lie adjustment (use pre-computed multipliers)
        lie_adj = self._lie_multipliers.get(lie_type, 1.0)

        # Hole difficulty adjustment (simplified calculation)
        difficulty_adj = 1.1 - (hole_difficulty - 3.0) * 0.05

        # Calculate final probability
        final_prob = base_prob * hcp_adjustment * lie_adj * difficulty_adj
        result = max(0.05, min(0.95, final_prob))  # Clamp between 5% and 95%

        # Cache the result
        self._probability_cache[cache_key] = (current_time, result)

        return result

    def _calculate_hole_completion_probability(
        self,
        player: PlayerState,
        hole: HoleState
    ) -> Dict[str, float]:
        """Calculate probability distribution for hole completion scores - optimized"""
        # Create cache key for team calculations
        player_key = (player.id, player.handicap, player.shots_taken,
                     round(player.distance_to_pin, 1), player.lie_type)
        hole_key = (hole.hole_number, hole.par, hole.difficulty_rating)
        cache_key = (player_key, hole_key)

        # Check cache
        if cache_key in self._team_calculation_cache:
            return dict(self._team_calculation_cache[cache_key])

        target_score = hole.par
        current_shots = player.shots_taken

        # Fast path for common scenarios
        if current_shots == 0 and player.distance_to_pin > 100:
            # On tee, use simplified calculation
            result = self._calculate_tee_shot_probabilities(player, hole)
            self._team_calculation_cache[cache_key] = result
            return result

        # Probability of making par, birdie, bogey, etc.
        probabilities = {}

        # Base expectations by handicap (pre-computed)
        expected_over_par = player.handicap * 0.055556  # / 18.0 pre-calculated

        # Optimized loop with fewer iterations for performance
        score_range = range(-2, 4) if player.handicap <= 10 else range(-1, 3)

        for score_relative_to_par in score_range:
            actual_score = target_score + score_relative_to_par

            if actual_score <= current_shots:
                probabilities[str(actual_score)] = 0.0
                continue

            remaining_shots = actual_score - current_shots

            if remaining_shots == 1:
                # Need to hole out in one shot
                prob = self._calculate_shot_success_probability(
                    player.handicap,
                    player.distance_to_pin,
                    player.lie_type,
                    hole.difficulty_rating
                )
            elif remaining_shots <= 3:
                # Simplified calculation for multiple shots
                shot_success_rate = self._calculate_shot_success_probability(
                    player.handicap,
                    player.distance_to_pin,
                    player.lie_type,
                    hole.difficulty_rating
                )
                # Optimized power calculation
                prob = shot_success_rate * (0.7 ** (remaining_shots - 1))
            else:
                # Very unlikely scenario, assign minimal probability
                prob = 0.01

            # Skill adjustment (simplified)
            skill_factor = 1.0 + (expected_over_par - score_relative_to_par) * 0.2
            prob *= skill_factor

            probabilities[str(actual_score)] = max(0.01, min(0.8, prob))

        # Fast normalization
        total = sum(probabilities.values())
        if total > 0:
            norm_factor = 1.0 / total
            probabilities = {k: v * norm_factor for k, v in probabilities.items()}

        # Cache the result
        self._team_calculation_cache[cache_key] = probabilities

        return probabilities

    def _calculate_tee_shot_probabilities(self, player: PlayerState, hole: HoleState) -> Dict[str, float]:
        """Fast calculation for tee shot scenarios"""
        par = hole.par
        hcp_strokes = player.handicap / 18.0

        # Simplified probability distribution based on par and handicap
        if par == 3:
            if player.handicap <= 10:
                return {"2": 0.1, "3": 0.6, "4": 0.25, "5": 0.05}
            else:
                return {"3": 0.3, "4": 0.5, "5": 0.15, "6": 0.05}
        elif par == 4:
            if player.handicap <= 10:
                return {"3": 0.05, "4": 0.5, "5": 0.35, "6": 0.1}
            else:
                return {"4": 0.25, "5": 0.45, "6": 0.25, "7": 0.05}
        else:  # par 5
            if player.handicap <= 10:
                return {"4": 0.03, "5": 0.4, "6": 0.4, "7": 0.15, "8": 0.02}
            else:
                return {"5": 0.15, "6": 0.35, "7": 0.35, "8": 0.1, "9": 0.05}

    def _calculate_team_win_probability(
        self,
        players: List[PlayerState],
        hole: HoleState
    ) -> Dict[str, float]:
        """Calculate win probabilities for different team configurations"""
        if hole.teams == TeamConfiguration.PENDING:
            return {"pending": 1.0}

        team_probs = {}

        if hole.teams == TeamConfiguration.SOLO:
            # Find captain and opponents
            captain = next((p for p in players if p.is_captain), None)
            opponents = [p for p in players if not p.is_captain]

            if captain and opponents:
                # Captain vs best ball of opponents
                captain_scores = self._calculate_hole_completion_probability(captain, hole)

                # Calculate opponents' best ball probability
                opponent_best_scores = {}
                for score in captain_scores.keys():
                    # Probability that at least one opponent beats this score
                    prob_all_worse = 1.0
                    for opp in opponents:
                        opp_scores = self._calculate_hole_completion_probability(opp, hole)
                        prob_this_worse = sum(
                            prob for s, prob in opp_scores.items()
                            if int(s) >= int(score)
                        )
                        prob_all_worse *= prob_this_worse

                    opponent_best_scores[score] = 1.0 - prob_all_worse

                # Calculate captain win probability
                captain_win_prob = 0.0
                for score, prob in captain_scores.items():
                    # Probability captain gets this score AND opponents don't beat it
                    prob_opponents_worse = sum(
                        opp_prob for opp_score, opp_prob in opponent_best_scores.items()
                        if int(opp_score) > int(score)
                    )
                    captain_win_prob += prob * prob_opponents_worse

                team_probs["captain"] = captain_win_prob
                team_probs["opponents"] = 1.0 - captain_win_prob

        elif hole.teams == TeamConfiguration.PARTNERS:
            # Team play - best ball of each team
            team1_players = [p for p in players if p.team_id == "team1"]
            team2_players = [p for p in players if p.team_id == "team2"]

            if team1_players and team2_players:
                # Calculate best ball probabilities for each team
                score_range: List[int] = list(range(hole.par - 2, hole.par + 4))

                team1_scores: Dict[int, float] = {}
                team2_scores: Dict[int, float] = {}

                for score_val in score_range:
                    # Team 1 probability of making this score or better
                    team1_prob = 1.0
                    for player in team1_players:
                        player_scores = self._calculate_hole_completion_probability(player, hole)
                        player_prob_worse = sum(
                            prob for s, prob in player_scores.items()
                            if int(s) > score_val
                        )
                        team1_prob *= player_prob_worse
                    team1_scores[score_val] = 1.0 - team1_prob

                    # Team 2 probability
                    team2_prob = 1.0
                    for player in team2_players:
                        player_scores = self._calculate_hole_completion_probability(player, hole)
                        player_prob_worse = sum(
                            prob for s, prob in player_scores.items()
                            if int(s) > score_val
                        )
                        team2_prob *= player_prob_worse
                    team2_scores[score_val] = 1.0 - team2_prob

                # Calculate team win probabilities
                team1_win_prob = 0.0
                for score_val in score_range:
                    team1_score_prob = team1_scores[score_val]
                    team2_worse_prob = sum(
                        team2_scores[s_val] for s_val in score_range if s_val > score_val
                    )
                    team1_win_prob += team1_score_prob * team2_worse_prob

                team_probs["team1"] = team1_win_prob
                team_probs["team2"] = 1.0 - team1_win_prob

        return team_probs

    def _calculate_expected_value(
        self,
        scenario: str,
        win_prob: float,
        current_wager: int,
        players: List[PlayerState]
    ) -> float:
        """Calculate expected value for a betting scenario"""
        if scenario == "offer_double":
            # EV of offering double
            prob_accept = 0.7  # Typical acceptance rate
            if prob_accept > 0:
                ev_if_accepted = win_prob * (current_wager * 2) - (1 - win_prob) * (current_wager * 2)
                ev_if_declined = current_wager  # Win at current stakes
                return prob_accept * ev_if_accepted + (1 - prob_accept) * ev_if_declined
            else:
                return current_wager

        elif scenario == "accept_double":
            # EV of accepting double
            return win_prob * (current_wager * 2) - (1 - win_prob) * (current_wager * 2)

        elif scenario == "go_solo":
            # EV of going solo (wager doubles automatically)
            return win_prob * (current_wager * 2 * 3) - (1 - win_prob) * (current_wager * 2)

        elif scenario == "accept_partnership":
            # EV of accepting partnership vs staying in opponents group
            return win_prob * current_wager - (1 - win_prob) * current_wager

        return 0.0

    def _assess_risk_level(self, win_prob: float, expected_value: float) -> str:
        """Assess risk level of a betting scenario"""
        if win_prob >= 0.6 and expected_value > 0:
            return "low"
        elif win_prob >= 0.4 and expected_value >= -0.5:
            return "medium"
        else:
            return "high"

    def _generate_educational_insights(
        self,
        players: List[PlayerState],
        hole: HoleState,
        scenarios: List[BettingScenario]
    ) -> List[str]:
        """Generate educational insights about the current betting situation"""
        insights = []

        # Handicap analysis
        handicaps = [p.handicap for p in players]
        hcp_range = max(handicaps) - min(handicaps)
        if hcp_range > 10:
            insights.append(
                f"Large handicap spread ({hcp_range:.1f} strokes) creates significant skill differences. "
                "Lower handicap players have better odds on approach shots."
            )

        # Position analysis
        distances = [p.distance_to_pin for p in players if p.distance_to_pin > 0]
        if distances:
            closest = min(distances)
            furthest = max(distances)
            if furthest - closest > 50:
                insights.append(
                    f"Large position spread ({furthest - closest:.0f} yards). "
                    "Players closer to pin have significant advantage."
                )

        # Team configuration insights
        if hole.teams == TeamConfiguration.PENDING:
            insights.append(
                "Team formation pending. Captain should consider handicap differences "
                "and current positions when choosing strategy."
            )
        elif hole.teams == TeamConfiguration.SOLO:
            insights.append(
                "Solo play doubles the base wager but requires beating best ball of three opponents. "
                "Success rate typically ranges from 15-35% depending on skill differential."
            )

        # Hole-specific insights
        if hole.hole_number >= 17:
            insights.append(
                "Late in round - consider overall match position, not just this hole. "
                "Conservative play may be optimal if leading."
            )

        # Betting scenario insights
        for scenario in scenarios:
            if scenario.scenario_type == "offer_double" and scenario.risk_level == "low":
                insights.append(
                    f"Favorable doubling opportunity detected. {scenario.reasoning}"
                )

        return insights

    def calculate_real_time_odds(
        self,
        players: List[PlayerState],
        hole: HoleState,
        game_context: Optional[Dict[str, Any]] = None
    ) -> OddsResult:
        """
        Main method to calculate comprehensive real-time odds.
        Optimized for 50ms performance target.
        """
        start_time = time.time()

        try:
            # Calculate individual player probabilities
            player_probs = {}
            for player in players:
                completion_probs = self._calculate_hole_completion_probability(player, hole)
                # Convert to win probability vs field
                avg_score = sum(float(score) * prob for score, prob in completion_probs.items())
                player_probs[player.id] = {
                    "win_probability": self._calculate_player_win_vs_field(player, players, hole),
                    "expected_score": avg_score,
                    "score_distribution": completion_probs
                }

            # Calculate team probabilities
            team_probs = self._calculate_team_win_probability(players, hole)

            # Generate betting scenarios
            scenarios = self._generate_betting_scenarios(players, hole, team_probs)

            # Determine optimal strategy
            optimal_strategy = self._determine_optimal_strategy(scenarios, team_probs)

            # Risk assessment
            risk_assessment = {
                "overall_uncertainty": self._calculate_uncertainty_level(player_probs),
                "volatility_factors": self._identify_volatility_factors(players, hole),
                "recommendation_confidence": self._calculate_recommendation_confidence(scenarios)
            }

            # Educational insights
            insights = self._generate_educational_insights(players, hole, scenarios)

            # Calculate confidence level
            confidence = self._calculate_overall_confidence(player_probs, team_probs, hole)

            calculation_time = (time.time() - start_time) * 1000

            return OddsResult(
                timestamp=time.time(),
                calculation_time_ms=calculation_time,
                player_probabilities=player_probs,
                team_probabilities=team_probs,
                betting_scenarios=scenarios,
                optimal_strategy=optimal_strategy,
                risk_assessment=risk_assessment,
                educational_insights=insights,
                confidence_level=confidence
            )

        except Exception:
            # Fallback to simple calculation if complex fails
            calculation_time = (time.time() - start_time) * 1000
            return self._simple_fallback_calculation(players, hole, calculation_time)

    def _calculate_player_win_vs_field(
        self,
        target_player: PlayerState,
        all_players: List[PlayerState],
        hole: HoleState
    ) -> float:
        """Calculate probability of a player winning vs the field"""
        target_scores = self._calculate_hole_completion_probability(target_player, hole)

        win_prob = 0.0
        for score, score_prob in target_scores.items():
            # Probability all other players score worse
            prob_others_worse = 1.0
            for other_player in all_players:
                if other_player.id != target_player.id:
                    other_scores = self._calculate_hole_completion_probability(other_player, hole)
                    prob_this_worse = sum(
                        prob for s, prob in other_scores.items()
                        if int(s) > int(score)
                    )
                    prob_others_worse *= prob_this_worse

            win_prob += score_prob * prob_others_worse

        return win_prob

    def _generate_betting_scenarios(
        self,
        players: List[PlayerState],
        hole: HoleState,
        team_probs: Dict[str, float]
    ) -> List[BettingScenario]:
        """Generate all relevant betting scenarios with analysis"""
        scenarios = []

        # Offer double scenario
        if not hole.is_doubled and hole.teams != TeamConfiguration.PENDING:
            primary_team = "captain" if hole.teams == TeamConfiguration.SOLO else "team1"
            win_prob = team_probs.get(primary_team, 0.5)

            ev = self._calculate_expected_value("offer_double", win_prob, hole.current_wager, players)
            risk = self._assess_risk_level(win_prob, ev)

            scenarios.append(BettingScenario(
                scenario_type="offer_double",
                win_probability=win_prob,
                expected_value=ev,
                risk_level=risk,
                confidence_interval=(win_prob - 0.1, win_prob + 0.1),
                recommendation="offer" if ev > 0.5 else "pass",
                reasoning=f"Win probability {win_prob:.1%} with EV of {ev:.2f} quarters",
                payout_matrix={
                    "win": hole.current_wager * 2,
                    "lose": -hole.current_wager * 2,
                    "declined": hole.current_wager
                }
            ))

        # Accept partnership scenario (if pending)
        if hole.teams == TeamConfiguration.PENDING:
            # Calculate EV of accepting vs declining partnership
            for player in players:
                if not player.is_captain:
                    # Simulate both scenarios
                    accept_ev = self._calculate_expected_value("accept_partnership", 0.5, hole.current_wager, players)

                    scenarios.append(BettingScenario(
                        scenario_type="accept_partnership",
                        win_probability=0.5,  # Simplified for now
                        expected_value=accept_ev,
                        risk_level="medium",
                        confidence_interval=(0.4, 0.6),
                        recommendation="accept" if accept_ev > 0 else "decline",
                        reasoning=f"Partnership EV: {accept_ev:.2f} quarters",
                        payout_matrix={
                            "win": hole.current_wager,
                            "lose": -hole.current_wager
                        }
                    ))
                    break

        # Go solo scenario
        if hole.teams == TeamConfiguration.PENDING:
            captain = next((p for p in players if p.is_captain), None)
            if captain:
                solo_win_prob = self._calculate_player_win_vs_field(captain, players, hole)
                solo_ev = self._calculate_expected_value("go_solo", solo_win_prob, hole.current_wager, players)

                scenarios.append(BettingScenario(
                    scenario_type="go_solo",
                    win_probability=solo_win_prob,
                    expected_value=solo_ev,
                    risk_level=self._assess_risk_level(solo_win_prob, solo_ev),
                    confidence_interval=(solo_win_prob - 0.15, solo_win_prob + 0.15),
                    recommendation="go_solo" if solo_ev > 1.0 else "find_partner",
                    reasoning=f"Solo odds: {solo_win_prob:.1%}, high risk/reward scenario",
                    payout_matrix={
                        "win": hole.current_wager * 2 * 3,
                        "lose": -hole.current_wager * 2
                    }
                ))

        return scenarios

    def _determine_optimal_strategy(
        self,
        scenarios: List[BettingScenario],
        team_probs: Dict[str, float]
    ) -> str:
        """Determine the optimal betting strategy based on scenarios"""
        if not scenarios:
            return "continue_play"

        # Find scenario with highest expected value
        best_scenario = max(scenarios, key=lambda s: s.expected_value)

        if best_scenario.expected_value > 0.5:
            return f"recommend_{best_scenario.scenario_type}"
        elif best_scenario.risk_level == "low":
            return f"consider_{best_scenario.scenario_type}"
        else:
            return "play_conservatively"

    def _calculate_uncertainty_level(self, player_probs: Dict[str, Any]) -> float:
        """Calculate overall uncertainty in the current situation"""
        win_probs = [data["win_probability"] for data in player_probs.values()]
        if not win_probs:
            return 0.5

        # Higher uncertainty when probabilities are closer together
        prob_variance = statistics.variance(win_probs) if len(win_probs) > 1 else 0
        return 1.0 - prob_variance  # Invert so high variance = high uncertainty

    def _identify_volatility_factors(
        self,
        players: List[PlayerState],
        hole: HoleState
    ) -> List[str]:
        """Identify factors that increase outcome volatility"""
        factors = []

        # Distance factors
        distances = [p.distance_to_pin for p in players if p.distance_to_pin > 0]
        if distances and max(distances) > 200:
            factors.append("long_shots_remaining")

        # Lie factors
        difficult_lies = ["bunker", "deep_rough", "trees", "water"]
        if any(p.lie_type in difficult_lies for p in players):
            factors.append("difficult_lies")

        # Hole factors
        if hole.difficulty_rating >= 4.0:
            factors.append("difficult_hole")

        if hole.weather_factor < 0.9:
            factors.append("adverse_weather")

        return factors

    def _calculate_recommendation_confidence(self, scenarios: List[BettingScenario]) -> float:
        """Calculate confidence in recommendations"""
        if not scenarios:
            return 0.5

        # Higher confidence when scenarios have clear winners
        ev_values = [s.expected_value for s in scenarios]
        if not ev_values:
            return 0.5

        max_ev = max(ev_values)
        ev_spread = max_ev - min(ev_values) if len(ev_values) > 1 else max_ev

        # Normalize to 0-1 scale
        confidence = min(1.0, max(0.1, ev_spread / 2.0))
        return confidence

    def _calculate_overall_confidence(
        self,
        player_probs: Dict[str, Any],
        team_probs: Dict[str, float],
        hole: HoleState
    ) -> float:
        """Calculate overall confidence in the odds calculation"""
        factors = []

        # Data quality factors
        if len(player_probs) >= 4:
            factors.append(0.9)  # Good player data
        else:
            factors.append(0.6)  # Limited player data

        # Hole completion factor
        shots_taken = sum(1 for p in player_probs if player_probs[p].get("shots_taken", 0) > 0)
        completion_factor = min(1.0, shots_taken / len(player_probs))
        factors.append(0.5 + completion_factor * 0.4)

        # Team formation factor
        if hole.teams != TeamConfiguration.PENDING:
            factors.append(0.9)  # Teams formed, clear scenarios
        else:
            factors.append(0.7)  # Teams pending, more uncertainty

        return statistics.mean(factors)

    def _simple_fallback_calculation(
        self,
        players: List[PlayerState],
        hole: HoleState,
        calculation_time: float
    ) -> OddsResult:
        """Simplified fallback calculation for error cases"""
        # Equal probabilities as fallback
        equal_prob = 1.0 / len(players)
        player_probs = {
            p.id: {
                "win_probability": equal_prob,
                "expected_score": hole.par + p.handicap / 18.0,
                "score_distribution": {str(hole.par): 0.5, str(hole.par + 1): 0.3, str(hole.par + 2): 0.2}
            }
            for p in players
        }

        team_probs = {"team1": 0.5, "team2": 0.5} if hole.teams == TeamConfiguration.PARTNERS else {"captain": 0.3, "opponents": 0.7}

        return OddsResult(
            timestamp=time.time(),
            calculation_time_ms=calculation_time,
            player_probabilities=player_probs,
            team_probabilities=team_probs,
            betting_scenarios=[],
            optimal_strategy="insufficient_data",
            risk_assessment={"error": True},
            educational_insights=["Calculation error - using simplified model"],
            confidence_level=0.3
        )


# Utility functions for API integration
def create_player_state_from_game_data(player_data: Dict[str, Any]) -> PlayerState:
    """Convert game state player data to PlayerState object"""
    return PlayerState(
        id=player_data.get("id", ""),
        name=player_data.get("name", "Unknown"),
        handicap=float(player_data.get("handicap", 18)),
        current_score=player_data.get("current_score", 0),
        shots_taken=player_data.get("shots_taken", 0),
        distance_to_pin=float(player_data.get("distance_to_pin", 0)),
        lie_type=player_data.get("lie_type", "fairway"),
        is_captain=player_data.get("is_captain", False),
        team_id=player_data.get("team_id"),
        confidence_factor=player_data.get("confidence_factor", 1.0)
    )


def create_hole_state_from_game_data(hole_data: Dict[str, Any]) -> HoleState:
    """Convert game state hole data to HoleState object"""
    teams_map = {
        "pending": TeamConfiguration.PENDING,
        "solo": TeamConfiguration.SOLO,
        "partners": TeamConfiguration.PARTNERS
    }

    return HoleState(
        hole_number=hole_data.get("hole_number", 1),
        par=hole_data.get("par", 4),
        difficulty_rating=float(hole_data.get("difficulty_rating", 3.0)),
        weather_factor=float(hole_data.get("weather_factor", 1.0)),
        pin_position=hole_data.get("pin_position", "middle"),
        course_conditions=hole_data.get("course_conditions", "normal"),
        teams=teams_map.get(hole_data.get("teams", "pending"), TeamConfiguration.PENDING),
        current_wager=hole_data.get("current_wager", 1),
        is_doubled=hole_data.get("is_doubled", False),
        line_of_scrimmage_passed=hole_data.get("line_of_scrimmage_passed", False)
    )


