"""
Score Calculation Service

Centralized scoring logic for Wolf Goat Pig game.
Consolidates duplicate scoring methods from:
- wolf_goat_pig.py (_calculate_partners_points, _calculate_solo_points)
- simplified_scoring.py (_calculate_solo_points, _calculate_partners_points)
- scoring_manager.py (calculate_hole_score, calculate_team_score)

This service provides a single source of truth for all scoring calculations.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("app.services.score_calculation")


class TeamType(Enum):
    """Types of team formations in Wolf Goat Pig."""
    PARTNERS = "partners"  # 2v2 best ball
    SOLO = "solo"          # 1 vs all
    ALL_VS_ALL = "all_vs_all"  # Everyone for themselves


@dataclass
class HoleResult:
    """Result of a hole calculation."""
    points_changes: Dict[str, int]
    winners: List[str]
    losers: List[str]
    message: str
    halved: bool
    team_type: TeamType
    wager: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "points_changes": self.points_changes,
            "winners": self.winners,
            "losers": self.losers,
            "message": self.message,
            "halved": self.halved,
            "team_type": self.team_type.value,
            "wager": self.wager
        }


@dataclass
class TeamConfig:
    """Configuration for team-based scoring."""
    team_type: TeamType
    team1: List[str] = None
    team2: List[str] = None
    solo_player: Optional[str] = None
    opponents: List[str] = None

    def __post_init__(self):
        self.team1 = self.team1 or []
        self.team2 = self.team2 or []
        self.opponents = self.opponents or []


class ScoreCalculationService:
    """
    Centralized service for all scoring calculations.

    Provides methods for:
    - Net score calculation (gross - handicap strokes)
    - Best ball team scoring
    - Solo vs all scoring
    - Partners scoring
    - Special rule applications (Karl Marx, Duncan, Tunkarri)

    Usage:
        service = ScoreCalculationService()

        # Calculate net score
        net = service.calculate_net_score(gross=5, handicap_strokes=1)

        # Calculate hole points for partners
        result = service.calculate_hole_points(
            scores={"p1": 4, "p2": 5, "p3": 4, "p4": 6},
            team_config=TeamConfig(
                team_type=TeamType.PARTNERS,
                team1=["p1", "p2"],
                team2=["p3", "p4"]
            ),
            wager=2
        )
    """

    def __init__(self):
        self._initialized = True
        logger.debug("ScoreCalculationService initialized")

    # =========================================================================
    # Core Score Calculations
    # =========================================================================

    def calculate_net_score(
        self,
        gross_score: int,
        handicap_strokes: int = 0,
        validate: bool = True
    ) -> int:
        """
        Calculate net score from gross score and handicap strokes.

        Args:
            gross_score: Player's actual strokes on the hole
            handicap_strokes: Strokes received based on handicap (0-3 typical)
            validate: Whether to validate inputs

        Returns:
            Net score (gross - handicap strokes, minimum 1)

        Raises:
            ValueError: If validation fails

        Example:
            >>> service.calculate_net_score(gross=5, handicap_strokes=1)
            4
        """
        if validate:
            if gross_score < 1:
                raise ValueError(f"Gross score must be positive, got {gross_score}")
            if handicap_strokes < 0:
                raise ValueError(f"Handicap strokes cannot be negative, got {handicap_strokes}")

        net_score = max(1, gross_score - handicap_strokes)

        logger.debug(f"Net score: gross={gross_score}, strokes={handicap_strokes}, net={net_score}")
        return net_score

    def calculate_team_best_ball(self, scores: List[int]) -> int:
        """
        Calculate best ball score for a team.

        In best ball format, the team's score is the minimum score
        among all team members.

        Args:
            scores: List of individual player scores

        Returns:
            Best (lowest) score among team members

        Raises:
            ValueError: If scores list is empty

        Example:
            >>> service.calculate_team_best_ball([4, 5, 6])
            4
        """
        if not scores:
            raise ValueError("Cannot calculate best ball with empty scores")

        best = min(scores)
        logger.debug(f"Best ball from {scores}: {best}")
        return best

    # =========================================================================
    # Hole Points Calculations
    # =========================================================================

    def calculate_hole_points(
        self,
        scores: Dict[str, int],
        team_config: TeamConfig,
        wager: int = 1,
        apply_special_rules: bool = False,
        special_rules: Optional[Dict[str, bool]] = None
    ) -> HoleResult:
        """
        Calculate points for a hole based on scores and team configuration.

        This is the main entry point for hole scoring. Routes to appropriate
        calculation method based on team type.

        Args:
            scores: Player ID to score mapping
            team_config: Team configuration (partners, solo, etc.)
            wager: Base wager for the hole
            apply_special_rules: Whether to apply special rule multipliers
            special_rules: Dict of special rules invoked (duncan, tunkarri, etc.)

        Returns:
            HoleResult with points changes, winners, message, etc.

        Raises:
            ValueError: If configuration is invalid
        """
        special_rules = special_rules or {}

        if team_config.team_type == TeamType.PARTNERS:
            result = self._calculate_partners_points(
                scores=scores,
                team1=team_config.team1,
                team2=team_config.team2,
                wager=wager
            )
        elif team_config.team_type == TeamType.SOLO:
            result = self._calculate_solo_points(
                scores=scores,
                solo_player=team_config.solo_player,
                opponents=team_config.opponents,
                wager=wager
            )
        elif team_config.team_type == TeamType.ALL_VS_ALL:
            result = self._calculate_all_vs_all_points(
                scores=scores,
                wager=wager
            )
        else:
            raise ValueError(f"Unknown team type: {team_config.team_type}")

        # Apply special rules if enabled
        if apply_special_rules and not result.halved:
            result = self._apply_special_rules(result, special_rules)

        return result

    def _calculate_partners_points(
        self,
        scores: Dict[str, int],
        team1: List[str],
        team2: List[str],
        wager: int
    ) -> HoleResult:
        """
        Calculate points for partners (2v2) format.

        Uses best ball scoring - each team's score is their lowest.

        Args:
            scores: Player ID to score mapping
            team1: List of player IDs on team 1
            team2: List of player IDs on team 2
            wager: Wager amount

        Returns:
            HoleResult with points changes
        """
        if not team1 or not team2:
            raise ValueError("Both teams must have players")

        # Get best ball for each team
        team1_scores = [scores[pid] for pid in team1 if pid in scores]
        team2_scores = [scores[pid] for pid in team2 if pid in scores]

        if not team1_scores or not team2_scores:
            raise ValueError("Both teams must have valid scores")

        team1_score = min(team1_scores)
        team2_score = min(team2_scores)

        # Initialize all players to 0
        all_players = set(team1) | set(team2)
        points_changes = {pid: 0 for pid in all_players}

        if team1_score < team2_score:
            # Team 1 wins
            winners = list(team1)
            losers = list(team2)
            for pid in team1:
                points_changes[pid] = wager
            for pid in team2:
                points_changes[pid] = -wager
            message = f"Team 1 wins ({team1_score} vs {team2_score})"
            halved = False

        elif team2_score < team1_score:
            # Team 2 wins
            winners = list(team2)
            losers = list(team1)
            for pid in team2:
                points_changes[pid] = wager
            for pid in team1:
                points_changes[pid] = -wager
            message = f"Team 2 wins ({team2_score} vs {team1_score})"
            halved = False

        else:
            # Halved
            winners = []
            losers = []
            message = f"Hole halved ({team1_score} all)"
            halved = True

        return HoleResult(
            points_changes=points_changes,
            winners=winners,
            losers=losers,
            message=message,
            halved=halved,
            team_type=TeamType.PARTNERS,
            wager=wager
        )

    def _calculate_solo_points(
        self,
        scores: Dict[str, int],
        solo_player: str,
        opponents: List[str],
        wager: int
    ) -> HoleResult:
        """
        Calculate points for solo (1 vs all) format.

        Solo player wins/loses against each opponent individually.

        Args:
            scores: Player ID to score mapping
            solo_player: ID of the solo player
            opponents: List of opponent player IDs
            wager: Wager amount per opponent

        Returns:
            HoleResult with points changes
        """
        if not solo_player or solo_player not in scores:
            raise ValueError(f"Invalid solo player: {solo_player}")
        if not opponents:
            raise ValueError("Solo player must have opponents")

        solo_score = scores[solo_player]
        opponent_scores = [scores[pid] for pid in opponents if pid in scores]

        if not opponent_scores:
            raise ValueError("Opponents must have valid scores")

        best_opponent_score = min(opponent_scores)

        # Initialize points
        all_players = {solo_player} | set(opponents)
        points_changes = {pid: 0 for pid in all_players}

        if solo_score < best_opponent_score:
            # Solo player wins - collects from all opponents
            winners = [solo_player]
            losers = list(opponents)
            points_changes[solo_player] = wager * len(opponents)
            for opp in opponents:
                points_changes[opp] = -wager
            message = f"Solo player wins ({solo_score} vs {best_opponent_score})"
            halved = False

        elif best_opponent_score < solo_score:
            # Opponents win - solo player pays all
            winners = list(opponents)
            losers = [solo_player]
            points_changes[solo_player] = -wager * len(opponents)
            for opp in opponents:
                points_changes[opp] = wager
            message = f"Opponents win ({best_opponent_score} vs {solo_score})"
            halved = False

        else:
            # Halved
            winners = []
            losers = []
            message = f"Hole halved ({solo_score} all)"
            halved = True

        return HoleResult(
            points_changes=points_changes,
            winners=winners,
            losers=losers,
            message=message,
            halved=halved,
            team_type=TeamType.SOLO,
            wager=wager
        )

    def _calculate_all_vs_all_points(
        self,
        scores: Dict[str, int],
        wager: int
    ) -> HoleResult:
        """
        Calculate points for all vs all (skins-like) format.

        Winner takes all from every other player.

        Args:
            scores: Player ID to score mapping
            wager: Wager amount

        Returns:
            HoleResult with points changes
        """
        if not scores:
            raise ValueError("No scores provided")

        # Find the winning score and winners
        best_score = min(scores.values())
        winners = [pid for pid, score in scores.items() if score == best_score]
        losers = [pid for pid in scores if pid not in winners]

        points_changes = {pid: 0 for pid in scores}

        if len(winners) == 1:
            # Single winner takes from all
            winner = winners[0]
            points_changes[winner] = wager * len(losers)
            for loser in losers:
                points_changes[loser] = -wager
            message = f"Winner takes all ({best_score})"
            halved = False
        else:
            # Multiple winners - hole is pushed/halved
            message = f"Hole pushed - {len(winners)} players tied at {best_score}"
            halved = True

        return HoleResult(
            points_changes=points_changes,
            winners=winners,
            losers=losers,
            message=message,
            halved=halved,
            team_type=TeamType.ALL_VS_ALL,
            wager=wager
        )

    # =========================================================================
    # Special Rules
    # =========================================================================

    def _apply_special_rules(
        self,
        result: HoleResult,
        special_rules: Dict[str, bool]
    ) -> HoleResult:
        """
        Apply special rule multipliers to hole result.

        Supports:
        - Duncan/Tunkarri: 3-for-2 rule (1.5x winner points)
        - Karl Marx: Distribution based on standings

        Args:
            result: Base hole result
            special_rules: Dict of rules that are active

        Returns:
            Modified HoleResult with multipliers applied
        """
        modified_points = dict(result.points_changes)

        # 3-for-2 rule (Duncan/Tunkarri)
        if special_rules.get("duncan") or special_rules.get("tunkarri"):
            for winner in result.winners:
                if modified_points.get(winner, 0) > 0:
                    modified_points[winner] = int(modified_points[winner] * 1.5)
            logger.debug("Applied 3-for-2 rule multiplier")

        # Double Down
        if special_rules.get("double_down"):
            for pid in modified_points:
                modified_points[pid] *= 2
            logger.debug("Applied double down multiplier")

        return HoleResult(
            points_changes=modified_points,
            winners=result.winners,
            losers=result.losers,
            message=result.message,
            halved=result.halved,
            team_type=result.team_type,
            wager=result.wager
        )

    def apply_karl_marx_rule(
        self,
        winners: List[str],
        losers: List[str],
        wager: int,
        current_standings: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Apply Karl Marx rule for point distribution.

        "From each according to his ability, to each according to his need"
        - Players furthest down receive more
        - Players furthest up pay more

        Args:
            winners: List of winning player IDs
            losers: List of losing player IDs
            wager: Base wager amount
            current_standings: Current point standings

        Returns:
            Adjusted points changes
        """
        if not winners or not losers:
            return {pid: 0 for pid in set(winners) | set(losers)}

        points_changes = {}

        # Sort by standings
        sorted_losers = sorted(losers, key=lambda p: current_standings.get(p, 0), reverse=True)
        sorted_winners = sorted(winners, key=lambda p: current_standings.get(p, 0))

        # Calculate base distribution
        total_owed = wager * len(winners)

        # Losers pay (highest standing pays most)
        for i, loser in enumerate(sorted_losers):
            weight = len(sorted_losers) - i  # Higher index = lower weight
            points_changes[loser] = -(wager * weight // len(sorted_losers))

        # Winners receive (lowest standing gets most)
        total_paid = abs(sum(v for v in points_changes.values() if v < 0))
        for i, winner in enumerate(sorted_winners):
            weight = len(sorted_winners) - i
            points_changes[winner] = (total_paid * weight) // (len(sorted_winners) * len(sorted_winners))

        logger.debug(f"Karl Marx distribution: {points_changes}")
        return points_changes

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def compare_scores(
        self,
        scores: Dict[str, int],
        use_net: bool = True,
        handicaps: Optional[Dict[str, float]] = None,
        hole_handicap_index: int = 9
    ) -> Tuple[List[str], int]:
        """
        Compare scores and determine winner(s).

        Args:
            scores: Player ID to gross score mapping
            use_net: Whether to use net scoring
            handicaps: Player handicaps (required if use_net=True)
            hole_handicap_index: Hole's handicap index (1-18)

        Returns:
            Tuple of (list of winner IDs, winning score)
        """
        if use_net and handicaps:
            # Convert to net scores
            net_scores = {}
            for pid, gross in scores.items():
                strokes = self._calculate_strokes_received(
                    handicaps.get(pid, 0),
                    hole_handicap_index
                )
                net_scores[pid] = self.calculate_net_score(gross, strokes)
            scores = net_scores

        best_score = min(scores.values())
        winners = [pid for pid, score in scores.items() if score == best_score]

        return winners, best_score

    def _calculate_strokes_received(
        self,
        handicap: float,
        hole_handicap_index: int
    ) -> int:
        """
        Calculate strokes received on a hole based on handicap.

        Args:
            handicap: Player's course handicap
            hole_handicap_index: Hole's handicap index (1-18)

        Returns:
            Number of strokes received (0-3)
        """
        if handicap <= 0:
            return 0

        full_strokes = int(handicap // 18)
        remaining = handicap % 18

        if remaining >= hole_handicap_index:
            return full_strokes + 1

        return full_strokes

    def calculate_final_standings(
        self,
        hole_results: List[HoleResult]
    ) -> Dict[str, int]:
        """
        Calculate final standings from a list of hole results.

        Args:
            hole_results: List of HoleResult objects

        Returns:
            Dict of player ID to total points
        """
        standings: Dict[str, int] = {}

        for result in hole_results:
            for pid, points in result.points_changes.items():
                standings[pid] = standings.get(pid, 0) + points

        return standings


# Singleton instance for convenience
_service_instance: Optional[ScoreCalculationService] = None


def get_score_calculation_service() -> ScoreCalculationService:
    """Get or create the score calculation service singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ScoreCalculationService()
    return _service_instance
