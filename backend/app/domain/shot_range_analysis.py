"""
Shot Range Analysis - Poker-style risk/reward calculations for shot selection

This module implements a hand range analysis system for golf shots, treating
shot selection like poker hand ranges with equity calculations, bluff frequencies,
and expected value (EV) calculations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ShotType(Enum):
    """Shot types with associated risk profiles"""
    # Conservative plays (tight range)
    LAY_UP = "lay_up"  # Safe shot, low risk/low reward
    SAFE_APPROACH = "safe_approach"  # Center of green target

    # Standard plays (balanced range)
    STANDARD_APPROACH = "standard_approach"  # Pin seeking but safe
    FAIRWAY_FINDER = "fairway_finder"  # Safe tee shot

    # Aggressive plays (loose range)
    PIN_SEEKER = "pin_seeker"  # Attacking tucked pins
    RISK_REWARD = "risk_reward"  # Cut corners, carry hazards

    # Bluff plays (polarized range)
    HERO_SHOT = "hero_shot"  # Low percentage, high reward
    RECOVERY_GAMBLE = "recovery_gamble"  # Aggressive recovery from trouble

class RiskProfile(Enum):
    """Risk profiles matching poker player types"""
    NIT = "nit"  # Ultra conservative (10% VPIP)
    TAG = "tag"  # Tight aggressive (20% VPIP)
    LAG = "lag"  # Loose aggressive (35% VPIP)
    MANIAC = "maniac"  # Ultra aggressive (50%+ VPIP)

@dataclass
class ShotRange:
    """Represents a range of possible shots with probabilities"""
    shot_type: ShotType
    success_probability: float  # 0.0 to 1.0
    risk_factor: float  # 0.0 (safe) to 1.0 (risky)
    expected_value: float  # Expected strokes saved/lost
    variance: float  # Outcome variance

    # Poker-style metrics
    fold_equity: float = 0.0  # Chance opponents concede
    bluff_frequency: float = 0.0  # How often this is a "bluff"
    pot_odds_required: float = 0.0  # Risk/reward threshold

    def get_equity_vs_field(self) -> float:
        """Calculate equity against the field (like poker hand equity)"""
        # Base equity on success probability
        base_equity = self.success_probability

        # Adjust for fold equity (psychological pressure)
        total_equity = base_equity + (1 - base_equity) * self.fold_equity

        return min(1.0, total_equity)

@dataclass
class ShotRangeMatrix:
    """Matrix of shot ranges for different situations"""
    lie_type: str
    distance_to_pin: float
    player_handicap: float
    game_situation: Dict[str, Any]

    # Available shot ranges
    ranges: List[ShotRange] = field(default_factory=list)

    # Optimal range based on game theory
    gto_range: Optional[ShotRange] = None

    # Exploitative adjustments
    exploitative_range: Optional[ShotRange] = None

    def __post_init__(self):
        """Calculate shot ranges on initialization"""
        self._calculate_base_ranges()
        self._calculate_gto_range()
        self._calculate_exploitative_adjustments()

    def _calculate_base_ranges(self):
        """Calculate all possible shot ranges for this situation"""
        self.ranges = []

        # Distance categories affect available shots
        if self.distance_to_pin <= 100:
            self._add_short_game_ranges()
        elif self.distance_to_pin <= 150:
            self._add_approach_ranges()
        elif self.distance_to_pin <= 200:
            self._add_long_approach_ranges()
        else:
            self._add_tee_shot_ranges()

    def _add_short_game_ranges(self):
        """Add short game shot ranges (wedges/chips)"""
        # Conservative: Aim for center of green
        self.ranges.append(ShotRange(
            shot_type=ShotType.SAFE_APPROACH,
            success_probability=0.85 - (self.player_handicap * 0.01),
            risk_factor=0.2,
            expected_value=-0.1,  # Slightly worse than average
            variance=0.3,
            fold_equity=0.0,
            bluff_frequency=0.0,
            pot_odds_required=0.2
        ))

        # Standard: Aim at pin with some margin
        self.ranges.append(ShotRange(
            shot_type=ShotType.STANDARD_APPROACH,
            success_probability=0.65 - (self.player_handicap * 0.015),
            risk_factor=0.5,
            expected_value=0.2,  # Positive EV
            variance=0.6,
            fold_equity=0.1,
            bluff_frequency=0.15,
            pot_odds_required=0.4
        ))

        # Aggressive: Attack tucked pin
        if self._is_pin_accessible():
            self.ranges.append(ShotRange(
                shot_type=ShotType.PIN_SEEKER,
                success_probability=0.35 - (self.player_handicap * 0.02),
                risk_factor=0.8,
                expected_value=0.4,  # High reward if successful
                variance=1.2,
                fold_equity=0.25,  # Puts pressure on opponents
                bluff_frequency=0.3,
                pot_odds_required=0.65
            ))

    def _add_approach_ranges(self):
        """Add mid-range approach shot ranges"""
        # Lay up option (if hazards present)
        if self._has_hazards():
            self.ranges.append(ShotRange(
                shot_type=ShotType.LAY_UP,
                success_probability=0.9,
                risk_factor=0.1,
                expected_value=-0.3,  # Costs strokes but safe
                variance=0.2,
                fold_equity=0.0,
                bluff_frequency=0.0,
                pot_odds_required=0.1
            ))

        # Standard approach
        self.ranges.append(ShotRange(
            shot_type=ShotType.STANDARD_APPROACH,
            success_probability=0.6 - (self.player_handicap * 0.015),
            risk_factor=0.4,
            expected_value=0.1,
            variance=0.7,
            fold_equity=0.05,
            bluff_frequency=0.1,
            pot_odds_required=0.35
        ))

        # Risk/reward play
        self.ranges.append(ShotRange(
            shot_type=ShotType.RISK_REWARD,
            success_probability=0.4 - (self.player_handicap * 0.02),
            risk_factor=0.7,
            expected_value=0.3,
            variance=1.0,
            fold_equity=0.2,
            bluff_frequency=0.25,
            pot_odds_required=0.6
        ))

    def _add_long_approach_ranges(self):
        """Add long approach shot ranges"""
        self.ranges.append(ShotRange(
            shot_type=ShotType.SAFE_APPROACH,
            success_probability=0.7 - (self.player_handicap * 0.01),
            risk_factor=0.3,
            expected_value=0.0,
            variance=0.5,
            fold_equity=0.0,
            bluff_frequency=0.05,
            pot_odds_required=0.25
        ))

        self.ranges.append(ShotRange(
            shot_type=ShotType.STANDARD_APPROACH,
            success_probability=0.5 - (self.player_handicap * 0.015),
            risk_factor=0.5,
            expected_value=0.15,
            variance=0.8,
            fold_equity=0.1,
            bluff_frequency=0.15,
            pot_odds_required=0.45
        ))

    def _add_tee_shot_ranges(self):
        """Add tee shot ranges"""
        # Fairway finder
        self.ranges.append(ShotRange(
            shot_type=ShotType.FAIRWAY_FINDER,
            success_probability=0.75 - (self.player_handicap * 0.01),
            risk_factor=0.2,
            expected_value=0.0,
            variance=0.4,
            fold_equity=0.0,
            bluff_frequency=0.0,
            pot_odds_required=0.2
        ))

        # Risk/reward (cut corner, carry hazard)
        if self._has_risk_reward_opportunity():
            self.ranges.append(ShotRange(
                shot_type=ShotType.RISK_REWARD,
                success_probability=0.45 - (self.player_handicap * 0.02),
                risk_factor=0.75,
                expected_value=0.5,  # Big advantage if successful
                variance=1.5,
                fold_equity=0.3,  # Intimidation factor
                bluff_frequency=0.35,
                pot_odds_required=0.7
            ))

        # Hero shot (very aggressive line)
        if self._allows_hero_shot():
            self.ranges.append(ShotRange(
                shot_type=ShotType.HERO_SHOT,
                success_probability=0.2 - (self.player_handicap * 0.02),
                risk_factor=0.95,
                expected_value=1.0,  # Huge reward
                variance=2.0,
                fold_equity=0.4,  # Maximum pressure
                bluff_frequency=0.5,
                pot_odds_required=0.85
            ))

    def _calculate_gto_range(self):
        """Calculate game theory optimal shot selection"""
        if not self.ranges:
            return

        # Calculate mixed strategy based on EV and variance
        best_ev = max(r.expected_value for r in self.ranges)

        # Find ranges within 20% of best EV
        viable_ranges = [r for r in self.ranges
                        if r.expected_value >= best_ev * 0.8]

        # Mix between viable ranges based on game situation
        if self._is_pressure_situation():
            # Under pressure, weight towards lower variance
            viable_ranges.sort(key=lambda r: r.variance)
            self.gto_range = viable_ranges[0]
        else:
            # Normal situation, choose highest EV
            viable_ranges.sort(key=lambda r: r.expected_value, reverse=True)
            self.gto_range = viable_ranges[0]

    def _calculate_exploitative_adjustments(self):
        """Calculate exploitative adjustments based on opponents"""
        if not self.gto_range:
            return

        # Start with GTO range
        self.exploitative_range = self.gto_range

        # Adjust based on opponent tendencies
        if self._opponents_play_scared():
            # Increase aggression against scared opponents
            aggressive_ranges = [r for r in self.ranges
                               if r.risk_factor > 0.6]
            if aggressive_ranges:
                self.exploitative_range = max(aggressive_ranges,
                                            key=lambda r: r.fold_equity)

        elif self._opponents_are_aggressive():
            # Play tighter against aggressive opponents
            conservative_ranges = [r for r in self.ranges
                                 if r.risk_factor < 0.4]
            if conservative_ranges:
                self.exploitative_range = max(conservative_ranges,
                                            key=lambda r: r.success_probability)

    def get_recommended_range(self, player_style: RiskProfile) -> Optional[ShotRange]:
        """Get recommended shot range based on player style"""
        if not self.ranges:
            return None

        # Filter ranges based on player style
        if player_style == RiskProfile.NIT:
            # Only play premium spots
            valid_ranges = [r for r in self.ranges if r.risk_factor <= 0.3]
        elif player_style == RiskProfile.TAG:
            # Balanced but selective
            valid_ranges = [r for r in self.ranges if r.risk_factor <= 0.6]
        elif player_style == RiskProfile.LAG:
            # Wide range with aggression
            valid_ranges = [r for r in self.ranges if r.expected_value > 0]
        else:  # MANIAC
            # Play any two cards
            valid_ranges = self.ranges

        if not valid_ranges:
            valid_ranges = [min(self.ranges, key=lambda r: r.risk_factor)]

        # Choose best from valid ranges
        return max(valid_ranges, key=lambda r: r.get_equity_vs_field())

    def get_range_distribution(self) -> Dict[str, float]:
        """Get percentage distribution of shot types (like VPIP)"""
        if not self.ranges:
            return {}

        total_ranges = len(self.ranges)
        distribution = {}

        for shot_type in ShotType:
            count = sum(1 for r in self.ranges if r.shot_type == shot_type)
            distribution[shot_type.value] = (count / total_ranges) * 100

        return distribution

    def calculate_3bet_range(self) -> List[ShotRange]:
        """Calculate '3-bet' range (ultra-aggressive counter shots)"""
        # Only include high risk/high reward shots
        three_bet_ranges = [r for r in self.ranges
                           if r.risk_factor >= 0.7 and r.fold_equity >= 0.2]

        return sorted(three_bet_ranges,
                     key=lambda r: r.expected_value,
                     reverse=True)

    # Helper methods
    def _is_pin_accessible(self) -> bool:
        """Check if pin position allows aggressive play"""
        return self.lie_type in ["fairway", "first cut"] and self.distance_to_pin <= 120

    def _has_hazards(self) -> bool:
        """Check if hazards are in play"""
        return bool(self.game_situation.get("hazards_present", False))

    def _has_risk_reward_opportunity(self) -> bool:
        """Check if risk/reward play is available"""
        return bool(self.game_situation.get("risk_reward_available", True))

    def _allows_hero_shot(self) -> bool:
        """Check if hero shot is possible"""
        return (self.player_handicap <= 10 and
                bool(self.game_situation.get("hero_shot_possible", False)))

    def _is_pressure_situation(self) -> bool:
        """Check if this is a high-pressure situation"""
        return (bool(self.game_situation.get("hole_number", 1) >= 16) or
                bool(self.game_situation.get("match_critical", False)))

    def _opponents_play_scared(self) -> bool:
        """Check if opponents tend to play conservatively"""
        return bool(self.game_situation.get("opponent_style", "") == "conservative")

    def _opponents_are_aggressive(self) -> bool:
        """Check if opponents tend to play aggressively"""
        return bool(self.game_situation.get("opponent_style", "") == "aggressive")


class ShotRangeAnalyzer:
    """Analyzer for shot selection using poker-style range analysis"""

    @staticmethod
    def analyze_shot_selection(
        lie_type: str,
        distance_to_pin: float,
        player_handicap: float,
        game_situation: Dict[str, Any],
        player_style: Optional[RiskProfile] = None
    ) -> Dict[str, Any]:
        """Perform complete shot range analysis"""

        # Create range matrix
        matrix = ShotRangeMatrix(
            lie_type=lie_type,
            distance_to_pin=distance_to_pin,
            player_handicap=player_handicap,
            game_situation=game_situation
        )

        # Determine player style if not provided
        if not player_style:
            player_style = ShotRangeAnalyzer._determine_player_style(
                player_handicap, game_situation
            )

        # Get recommended range
        recommended = matrix.get_recommended_range(player_style)

        # Build analysis
        analysis = {
            "recommended_shot": {
                "type": recommended.shot_type.value if recommended else None,
                "success_rate": f"{recommended.success_probability * 100:.1f}%" if recommended else "0%",
                "risk_level": f"{recommended.risk_factor * 100:.0f}%" if recommended else "0%",
                "expected_value": recommended.expected_value if recommended else 0,
                "equity_vs_field": f"{recommended.get_equity_vs_field() * 100:.1f}%" if recommended else "0%"
            },
            "gto_recommendation": {
                "type": matrix.gto_range.shot_type.value if matrix.gto_range else None,
                "reasoning": "Game theory optimal play based on EV maximization"
            },
            "exploitative_play": {
                "type": matrix.exploitative_range.shot_type.value if matrix.exploitative_range else None,
                "reasoning": "Adjusted for opponent tendencies"
            },
            "range_distribution": matrix.get_range_distribution(),
            "all_ranges": [
                {
                    "type": r.shot_type.value,
                    "success_rate": f"{r.success_probability * 100:.1f}%",
                    "risk": f"{r.risk_factor * 100:.0f}%",
                    "ev": f"{r.expected_value:+.2f}",
                    "equity": f"{r.get_equity_vs_field() * 100:.1f}%",
                    "pot_odds_needed": f"{r.pot_odds_required * 100:.0f}%"
                }
                for r in sorted(matrix.ranges,
                              key=lambda x: x.expected_value,
                              reverse=True)
            ],
            "3bet_ranges": [
                {
                    "type": r.shot_type.value,
                    "fold_equity": f"{r.fold_equity * 100:.0f}%",
                    "bluff_frequency": f"{r.bluff_frequency * 100:.0f}%"
                }
                for r in matrix.calculate_3bet_range()
            ],
            "player_style": {
                "profile": player_style.value,
                "description": ShotRangeAnalyzer._get_style_description(player_style)
            },
            "strategic_advice": ShotRangeAnalyzer._generate_strategic_advice(
                matrix, recommended, player_style, game_situation
            )
        }

        return analysis

    @staticmethod
    def _determine_player_style(handicap: float, game_situation: Dict) -> RiskProfile:
        """Determine player style based on handicap and situation"""
        # Base style on handicap
        if handicap >= 20:
            base_style = RiskProfile.NIT  # High handicaps play tight
        elif handicap >= 10:
            base_style = RiskProfile.TAG  # Mid handicaps balanced
        elif handicap >= 5:
            base_style = RiskProfile.LAG  # Low handicaps can be aggressive
        else:
            base_style = RiskProfile.MANIAC  # Scratch players have full range

        # Adjust for situation
        if game_situation.get("trailing_significantly", False):
            # Need to gamble when behind
            if base_style == RiskProfile.NIT:
                return RiskProfile.TAG
            elif base_style == RiskProfile.TAG:
                return RiskProfile.LAG
            else:
                return RiskProfile.MANIAC

        return base_style

    @staticmethod
    def _get_style_description(style: RiskProfile) -> str:
        """Get description of playing style"""
        descriptions = {
            RiskProfile.NIT: "Ultra-conservative, only plays premium positions",
            RiskProfile.TAG: "Selective aggression, balanced risk/reward",
            RiskProfile.LAG: "Wide range with aggressive tendencies",
            RiskProfile.MANIAC: "Maximum aggression, any position is playable"
        }
        return descriptions.get(style, "Unknown style")

    @staticmethod
    def _generate_strategic_advice(
        matrix: ShotRangeMatrix,
        recommended: ShotRange,
        player_style: RiskProfile,
        game_situation: Dict
    ) -> List[str]:
        """Generate strategic advice for shot selection"""
        advice = []

        # Range-based advice
        if recommended and recommended.risk_factor > 0.7:
            advice.append("🎯 High-risk play: Ensure pot odds justify the gamble")
        elif recommended and recommended.risk_factor < 0.3:
            advice.append("🛡️ Conservative play: Building your stack safely")

        # Fold equity advice
        if recommended and recommended.fold_equity > 0.2:
            advice.append("💪 This shot puts maximum pressure on opponents")

        # Bluff frequency advice
        if recommended and recommended.bluff_frequency > 0.3:
            advice.append("🎭 Include this in your bluff range for balance")

        # Situational advice
        if game_situation.get("hole_number", 0) >= 17:
            advice.append("⏰ Late game: Variance becomes more critical")

        if game_situation.get("partnership_formed", False):
            advice.append("🤝 Team play: Consider partner's position in range selection")

        # Style-specific advice
        if player_style == RiskProfile.NIT and matrix.gto_range and matrix.gto_range.risk_factor > 0.5:
            advice.append("📈 Consider expanding range - GTO suggests more aggression")
        elif player_style == RiskProfile.MANIAC and len(matrix.ranges) > 3:
            advice.append("📊 Too many options - focus on highest EV plays")

        return advice


# Integration function for existing codebase
def analyze_shot_decision(
    current_lie: str,
    distance: float,
    player_handicap: float,
    hole_number: int,
    team_situation: str = "solo",
    score_differential: int = 0,
    opponent_styles: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Main entry point for shot range analysis"""

    # Build game situation context
    game_situation = {
        "hole_number": hole_number,
        "partnership_formed": team_situation != "solo",
        "match_critical": abs(score_differential) >= 3 or hole_number >= 16,
        "trailing_significantly": score_differential <= -3,
        "hazards_present": distance > 150,  # Simplified assumption
        "risk_reward_available": True,
        "hero_shot_possible": distance > 200,
        "opponent_style": opponent_styles[0] if opponent_styles else "balanced"
    }

    # Perform analysis
    return ShotRangeAnalyzer.analyze_shot_selection(
        lie_type=current_lie,
        distance_to_pin=distance,
        player_handicap=player_handicap,
        game_situation=game_situation
    )
