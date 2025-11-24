"""
Scoring Manager for Wolf Goat Pig Application.

This manager centralizes all scoring logic including:
- Hole score calculations (gross and net)
- Match play point calculations
- Money distribution (Karl Marx rule)
- Carryover handling
- Best ball team scoring
- Handicap-adjusted scoring
- Concession point awards (partners and solo modes)
- Game totals and summaries

Integrates with HandicapValidator for handicap calculations.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..validators import HandicapValidationError, HandicapValidator
from ..wolf_goat_pig import WolfGoatPigGame

logger = logging.getLogger(__name__)


@dataclass
class HoleResult:
    """
    Represents the result of a single hole.

    Attributes:
        hole_number: The hole number (1-18)
        winning_team: List of player IDs on winning team (None if halved)
        losing_team: List of player IDs on losing team (None if halved)
        halved: Whether the hole was halved (tied)
        gross_scores: Dictionary of player_id -> gross score
        net_scores: Dictionary of player_id -> net score
        team1_score: Best ball score for team 1
        team2_score: Best ball score for team 2
        wager: Wager amount for this hole
        points_changes: Dictionary of player_id -> points won/lost
        money_changes: Dictionary of player_id -> money won/lost
        carried_over: Whether this hole was carried over from previous
        carryover_amount: Amount carried over to next hole
    """
    hole_number: int
    winning_team: Optional[List[str]] = None
    losing_team: Optional[List[str]] = None
    halved: bool = False
    gross_scores: Dict[str, int] = field(default_factory=dict)
    net_scores: Dict[str, int] = field(default_factory=dict)
    team1_score: Optional[int] = None
    team2_score: Optional[int] = None
    wager: float = 1.0
    points_changes: Dict[str, int] = field(default_factory=dict)
    money_changes: Dict[str, float] = field(default_factory=dict)
    carried_over: bool = False
    carryover_amount: float = 0.0


@dataclass
class GameTotals:
    """
    Represents final game totals.

    Attributes:
        total_holes_played: Number of holes completed
        player_totals: Dictionary of player_id -> total points/money
        standings: List of (player_id, total) tuples sorted by total
        winner: Player ID of winner (or None if tied)
        holes_won: Dictionary of player_id -> holes won count
        holes_halved: Total holes halved
        total_carryover: Total amount carried over in game
    """
    total_holes_played: int
    player_totals: Dict[str, float] = field(default_factory=dict)
    standings: List[Tuple[str, float]] = field(default_factory=list)
    winner: Optional[str] = None
    holes_won: Dict[str, int] = field(default_factory=dict)
    holes_halved: int = 0
    total_carryover: float = 0.0


class ScoringManager:
    """
    Centralized scoring manager for Wolf Goat Pig game.

    This class implements the singleton pattern and provides all scoring
    calculations including handicap adjustments, match play scoring,
    money distribution using the Karl Marx rule, and game summaries.

    Usage:
        manager = ScoringManager()
        net_score = manager.calculate_hole_score(gross_score=5, handicap_strokes=1)
        points = manager.calculate_match_points(winning_team, losing_team, wager)
    """

    _instance = None

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ScoringManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, game_engine: Optional[WolfGoatPigGame] = None):
        """Initialize the scoring manager."""
        if self._initialized:
            return

        self._initialized = True
        logger.info("ScoringManager initialized")

    def calculate_hole_score(
        self,
        gross_score: int,
        handicap_strokes: int
    ) -> int:
        """
        Calculate net score for a hole.

        Subtracts handicap strokes from gross score to determine net score.
        Uses HandicapValidator for validation.

        Args:
            gross_score: Player's actual strokes on hole (must be positive)
            handicap_strokes: Number of strokes to subtract (0-3 typically)

        Returns:
            Net score (gross - handicap strokes)

        Raises:
            HandicapValidationError: If scores are invalid

        Example:
            >>> manager = ScoringManager()
            >>> manager.calculate_hole_score(gross_score=5, handicap_strokes=1)
            4
            >>> manager.calculate_hole_score(gross_score=6, handicap_strokes=2)
            4
        """
        try:
            net_score = HandicapValidator.calculate_net_score(
                gross_score=gross_score,
                strokes_received=handicap_strokes,
                validate=True
            )

            logger.debug(
                f"Calculated net score: gross={gross_score}, "
                f"strokes={handicap_strokes}, net={net_score}"
            )

            return net_score

        except HandicapValidationError as e:
            logger.error(f"Error calculating hole score: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calculating hole score: {e}")
            raise ValueError(f"Failed to calculate hole score: {str(e)}")

    def calculate_team_score(
        self,
        player1_score: int,
        player2_score: int
    ) -> int:
        """
        Calculate best ball team score.

        In best ball format, the team's score is the lower of the two
        partner scores for the hole.

        Args:
            player1_score: First player's score (net)
            player2_score: Second player's score (net)

        Returns:
            Team's best ball score (minimum of the two)

        Example:
            >>> manager = ScoringManager()
            >>> manager.calculate_team_score(player1_score=4, player2_score=5)
            4
            >>> manager.calculate_team_score(player1_score=6, player2_score=6)
            6
        """
        try:
            if player1_score < 1 or player2_score < 1:
                raise ValueError("Scores must be positive integers")

            team_score = min(player1_score, player2_score)

            logger.debug(
                f"Calculated team score: p1={player1_score}, "
                f"p2={player2_score}, team={team_score}"
            )

            return team_score

        except Exception as e:
            logger.error(f"Error calculating team score: {e}")
            raise ValueError(f"Failed to calculate team score: {str(e)}")

    def calculate_match_points(
        self,
        winning_team: List[str],
        losing_team: List[str],
        wager_multiplier: float = 1.0
    ) -> Dict[str, int]:
        """
        Calculate match play points for a hole.

        In match play, the winning team receives points equal to the
        wager multiplied by the number of players on the losing team.
        Each losing player loses the wager amount.

        Args:
            winning_team: List of player IDs on winning team
            losing_team: List of player IDs on losing team
            wager_multiplier: Multiplier for base wager (default 1.0)

        Returns:
            Dictionary mapping player_id to points won/lost

        Example:
            >>> manager = ScoringManager()
            >>> manager.calculate_match_points(
            ...     winning_team=['p1', 'p2'],
            ...     losing_team=['p3', 'p4'],
            ...     wager_multiplier=2.0
            ... )
            {'p1': 2, 'p2': 2, 'p3': -2, 'p4': -2}
        """
        try:
            if not winning_team:
                raise ValueError("Winning team cannot be empty")
            if not losing_team:
                raise ValueError("Losing team cannot be empty")
            if wager_multiplier <= 0:
                raise ValueError("Wager multiplier must be positive")

            wager = int(wager_multiplier)
            points_changes = {}

            # Calculate total points at stake
            total_points = wager * len(winning_team)

            # Winners split the total points
            points_per_winner = total_points // len(winning_team)
            winner_remainder = total_points % len(winning_team)

            for i, player_id in enumerate(winning_team):
                points = points_per_winner
                # Distribute remainder to first few winners
                if i < winner_remainder:
                    points += 1
                points_changes[player_id] = points

            # Losers each lose the wager
            total_owed = wager * len(losing_team)
            points_per_loser = total_owed // len(losing_team)
            loser_remainder = total_owed % len(losing_team)

            for i, player_id in enumerate(losing_team):
                points = points_per_loser
                # Distribute remainder to first few losers
                if i < loser_remainder:
                    points += 1
                points_changes[player_id] = -points

            logger.debug(
                f"Calculated match points: wager={wager}, "
                f"winners={len(winning_team)}, losers={len(losing_team)}, "
                f"changes={points_changes}"
            )

            return points_changes

        except Exception as e:
            logger.error(f"Error calculating match points: {e}")
            raise ValueError(f"Failed to calculate match points: {str(e)}")

    def calculate_money_distribution(
        self,
        hole_results: List[HoleResult],
        base_wager: float = 0.25
    ) -> Dict[str, float]:
        """
        Calculate total money won/lost per player across multiple holes.

        Converts points to money using base wager (default 0.25 = 1 quarter).
        Applies Karl Marx rule for distribution.

        Args:
            hole_results: List of HoleResult objects
            base_wager: Base wager amount in dollars (default 0.25 for quarters)

        Returns:
            Dictionary mapping player_id to total money won/lost

        Example:
            >>> manager = ScoringManager()
            >>> results = [
            ...     HoleResult(hole_number=1, points_changes={'p1': 2, 'p2': -2}),
            ...     HoleResult(hole_number=2, points_changes={'p1': 1, 'p2': -1})
            ... ]
            >>> manager.calculate_money_distribution(results, base_wager=0.25)
            {'p1': 0.75, 'p2': -0.75}
        """
        try:
            if base_wager <= 0:
                raise ValueError("Base wager must be positive")

            money_distribution = {}

            # Aggregate points across all holes
            for result in hole_results:
                for player_id, points in result.points_changes.items():
                    if player_id not in money_distribution:
                        money_distribution[player_id] = 0.0
                    money_distribution[player_id] += points * base_wager

            # Round to 2 decimal places (cents)
            money_distribution = {
                player_id: round(amount, 2)
                for player_id, amount in money_distribution.items()
            }

            logger.debug(
                f"Calculated money distribution: base_wager={base_wager}, "
                f"holes={len(hole_results)}, distribution={money_distribution}"
            )

            return money_distribution

        except Exception as e:
            logger.error(f"Error calculating money distribution: {e}")
            raise ValueError(f"Failed to calculate money distribution: {str(e)}")

    def calculate_karl_marx_distribution(
        self,
        winners: List[str],
        losers: List[str],
        wager: int,
        current_points: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Apply Karl Marx rule for point distribution.

        "From each according to his ability, to each according to his need."
        Players furthest down (lowest points) pay/receive less.

        Args:
            winners: List of winning player IDs
            losers: List of losing player IDs
            wager: Wager amount for the hole
            current_points: Dictionary of player_id -> current total points

        Returns:
            Dictionary mapping player_id to points won/lost

        Example:
            >>> manager = ScoringManager()
            >>> manager.calculate_karl_marx_distribution(
            ...     winners=['p1', 'p2'],
            ...     losers=['p3', 'p4'],
            ...     wager=2,
            ...     current_points={'p1': 10, 'p2': 5, 'p3': 8, 'p4': 3}
            ... )
            {'p1': 2, 'p2': 2, 'p3': -2, 'p4': -2}
        """
        try:
            if not winners or not losers:
                raise ValueError("Winners and losers cannot be empty")
            if wager <= 0:
                raise ValueError("Wager must be positive")

            points_changes = {}

            # Calculate totals
            total_won = wager * len(losers)
            total_owed = wager * len(winners)

            # Winners get points (sorted by current points - ascending)
            # Players with fewer points get slightly more
            if len(winners) == 1:
                points_changes[winners[0]] = total_won
            else:
                points_per_winner = total_won // len(winners)
                remainder = total_won % len(winners)

                # Sort winners by current points (ascending - furthest down gets priority)
                sorted_winners = sorted(
                    winners,
                    key=lambda pid: current_points.get(pid, 0)
                )

                for i, winner in enumerate(sorted_winners):
                    points_changes[winner] = points_per_winner
                    # Last few get extra (those with more points)
                    if i >= len(sorted_winners) - remainder:
                        points_changes[winner] += 1

            # Losers lose points (sorted by current points - ascending)
            # Players with fewer points pay slightly less
            if len(losers) == 1:
                points_changes[losers[0]] = -total_owed
            else:
                points_per_loser = total_owed // len(losers)
                remainder = total_owed % len(losers)

                # Sort losers by current points (ascending - furthest down pays less)
                sorted_losers = sorted(
                    losers,
                    key=lambda pid: current_points.get(pid, 0)
                )

                for i, loser in enumerate(sorted_losers):
                    points_changes[loser] = -points_per_loser
                    # Last few pay extra (those with more points)
                    if i >= len(sorted_losers) - remainder:
                        points_changes[loser] -= 1

            logger.debug(
                f"Applied Karl Marx rule: winners={len(winners)}, "
                f"losers={len(losers)}, wager={wager}, changes={points_changes}"
            )

            return points_changes

        except Exception as e:
            logger.error(f"Error applying Karl Marx rule: {e}")
            raise ValueError(f"Failed to apply Karl Marx distribution: {str(e)}")

    def calculate_carryover(
        self,
        hole_results: List[HoleResult],
        current_carryover: float = 0.0
    ) -> float:
        """
        Calculate carryover amount to next hole.

        When a hole is halved (tied), the wager carries over to the next hole,
        accumulating if multiple holes are halved in a row.

        Args:
            hole_results: List of recent HoleResult objects
            current_carryover: Current carryover amount

        Returns:
            New carryover amount

        Example:
            >>> manager = ScoringManager()
            >>> results = [
            ...     HoleResult(hole_number=1, halved=True, wager=1.0),
            ...     HoleResult(hole_number=2, halved=True, wager=1.0)
            ... ]
            >>> manager.calculate_carryover(results, current_carryover=0.0)
            2.0
        """
        try:
            carryover = current_carryover

            for result in hole_results:
                if result.halved:
                    carryover += result.wager
                    logger.debug(
                        f"Hole {result.hole_number} halved, "
                        f"adding {result.wager} to carryover (total: {carryover})"
                    )
                else:
                    # Carryover is resolved, reset to 0
                    if carryover > 0:
                        logger.debug(
                            f"Hole {result.hole_number} won, "
                            f"carryover of {carryover} resolved"
                        )
                    carryover = 0.0

            return carryover

        except Exception as e:
            logger.error(f"Error calculating carryover: {e}")
            raise ValueError(f"Failed to calculate carryover: {str(e)}")

    def calculate_game_totals(
        self,
        all_hole_results: List[HoleResult]
    ) -> GameTotals:
        """
        Calculate final game totals from all hole results.

        Aggregates points, money, wins, and creates final standings.

        Args:
            all_hole_results: List of all HoleResult objects for the game

        Returns:
            GameTotals object with complete game statistics

        Example:
            >>> manager = ScoringManager()
            >>> results = [
            ...     HoleResult(
            ...         hole_number=1,
            ...         winning_team=['p1'],
            ...         losing_team=['p2'],
            ...         points_changes={'p1': 2, 'p2': -2}
            ...     ),
            ...     HoleResult(hole_number=2, halved=True)
            ... ]
            >>> totals = manager.calculate_game_totals(results)
            >>> totals.player_totals
            {'p1': 2, 'p2': -2}
        """
        try:
            player_totals = {}
            holes_won = {}
            holes_halved = 0
            total_carryover = 0.0

            # Aggregate results
            for result in all_hole_results:
                # Count halved holes
                if result.halved:
                    holes_halved += 1
                    if result.carryover_amount > 0:
                        total_carryover += result.carryover_amount
                    continue

                # Count wins
                if result.winning_team:
                    for player_id in result.winning_team:
                        holes_won[player_id] = holes_won.get(player_id, 0) + 1

                # Aggregate points
                for player_id, points in result.points_changes.items():
                    if player_id not in player_totals:
                        player_totals[player_id] = 0
                    player_totals[player_id] += points

            # Create standings (sorted by total, descending)
            standings = sorted(
                player_totals.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Determine winner (or tie)
            winner = None
            if standings and len(standings) > 0:
                if len(standings) == 1 or standings[0][1] > standings[1][1]:
                    winner = standings[0][0]

            game_totals = GameTotals(
                total_holes_played=len(all_hole_results),
                player_totals=player_totals,
                standings=standings,
                winner=winner,
                holes_won=holes_won,
                holes_halved=holes_halved,
                total_carryover=total_carryover
            )

            logger.info(
                f"Calculated game totals: holes={len(all_hole_results)}, "
                f"winner={winner}, halved={holes_halved}"
            )

            return game_totals

        except Exception as e:
            logger.error(f"Error calculating game totals: {e}")
            raise ValueError(f"Failed to calculate game totals: {str(e)}")

    def calculate_handicap_adjusted_score(
        self,
        gross_scores: Dict[str, int],
        handicaps: Dict[str, float],
        stroke_indexes: Dict[str, int],
        hole_stroke_index: int
    ) -> Dict[str, int]:
        """
        Calculate handicap-adjusted scores for all players on a hole.

        Uses USGA stroke allocation rules with match play format:
        strokes are calculated relative to the player with the lowest
        handicap in the group.

        Args:
            gross_scores: Dictionary of player_id -> gross score
            handicaps: Dictionary of player_id -> handicap
            stroke_indexes: Dictionary of player_id -> course handicap
            hole_stroke_index: Stroke index for this hole (1-18)

        Returns:
            Dictionary mapping player_id to net score

        Raises:
            HandicapValidationError: If handicaps or scores are invalid

        Example:
            >>> manager = ScoringManager()
            >>> manager.calculate_handicap_adjusted_score(
            ...     gross_scores={'p1': 5, 'p2': 6},
            ...     handicaps={'p1': 10.0, 'p2': 18.0},
            ...     stroke_indexes={'p1': 10, 'p2': 18},
            ...     hole_stroke_index=5
            ... )
            {'p1': 4, 'p2': 5}
        """
        try:
            # Validate hole stroke index
            HandicapValidator.validate_stroke_index(hole_stroke_index)

            # Calculate net handicaps relative to lowest handicap player
            net_handicaps = HandicapValidator.calculate_net_handicaps(handicaps)

            net_scores = {}

            for player_id in gross_scores:
                # Get player data
                gross_score = gross_scores[player_id]
                net_handicap = net_handicaps.get(player_id, 0.0)

                # Validate original handicap for logging
                original_handicap = handicaps.get(player_id, 0.0)
                HandicapValidator.validate_handicap(original_handicap)

                # Calculate strokes received on this hole (with Creecher Feature support)
                # Use net handicap (relative to lowest player)
                strokes_received = HandicapValidator.calculate_strokes_received_with_creecher(
                    course_handicap=net_handicap,
                    stroke_index=hole_stroke_index,
                    validate=True
                )

                # Calculate net score
                net_score = self.calculate_hole_score(
                    gross_score=gross_score,
                    handicap_strokes=strokes_received
                )

                net_scores[player_id] = net_score

                logger.debug(
                    f"Player {player_id}: gross={gross_score}, "
                    f"original_handicap={original_handicap}, net_handicap={net_handicap}, "
                    f"strokes={strokes_received}, net={net_score}"
                )

            return net_scores

        except HandicapValidationError as e:
            logger.error(f"Handicap validation error: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Error calculating handicap-adjusted scores: {e}")
            raise ValueError(f"Failed to calculate adjusted scores: {str(e)}")

    def award_concession_points(
        self,
        game_state: Any,
        conceding_player: Optional[str],
        conceding_team: Optional[int],
        hole_number: int
    ) -> Dict[str, int]:
        """
        Award points to winning team(s) based on hole concession.

        Handles both "partners" and "solo" team types. In solo mode,
        solo player wins get 2x multiplier. Marks hole as completed
        with concession tracking.

        Args:
            game_state: Current game state object
            conceding_player: Player ID who is conceding (if individual)
            conceding_team: Team number conceding (if team)
            hole_number: Current hole number

        Returns:
            Dict mapping player_id to points awarded

        Example:
            >>> manager = ScoringManager()
            >>> points = manager.award_concession_points(
            ...     game_state=game_state,
            ...     conceding_player=None,
            ...     conceding_team=1,
            ...     hole_number=5
            ... )
            >>> points
            {'player_2': 2, 'player_3': 2}
        """
        try:
            # Get hole state
            hole_states = game_state.hole_states if hasattr(game_state, 'hole_states') else game_state.get('hole_states', {})
            if hole_number not in hole_states:
                raise ValueError(f"Hole {hole_number} not found in game state")

            hole_state = hole_states[hole_number]

            # Mark hole as completed with concession
            hole_state.status = "completed"
            hole_state.conceded = True
            hole_state.conceding_player = conceding_player if conceding_player is not None else conceding_team

            # Get current wager
            wager = hole_state.betting.current_wager or 1

            # Dictionary to track points awarded
            points_awarded = {}

            # Get player manager
            player_manager = game_state.player_manager if hasattr(game_state, 'player_manager') else None
            if not player_manager:
                raise ValueError("Player manager not found in game state")

            # Determine winners based on team structure
            if hole_state.teams.type == "partners":
                # In partners mode, one team concedes, the other wins
                if conceding_team == 1:
                    # Team 1 conceded, Team 2 wins
                    for pid in hole_state.teams.team2 or []:
                        player = next((p for p in player_manager.players if p.id == pid), None)
                        if player:
                            player.points += wager
                            points_awarded[pid] = wager
                            logger.debug(f"Awarded {wager} points to player {pid} (Team 2 wins)")
                else:
                    # Team 2 conceded, Team 1 wins
                    for pid in hole_state.teams.team1 or []:
                        player = next((p for p in player_manager.players if p.id == pid), None)
                        if player:
                            player.points += wager
                            points_awarded[pid] = wager
                            logger.debug(f"Awarded {wager} points to player {pid} (Team 1 wins)")

            elif hole_state.teams.type == "solo":
                # In solo mode, if solo player concedes, the other team wins
                solo_player = hole_state.teams.solo_player
                if conceding_player == solo_player:
                    # Solo player conceded, partners win
                    for pid in hole_state.teams.team1 or []:
                        player = next((p for p in player_manager.players if p.id == pid), None)
                        if player:
                            player.points += wager
                            points_awarded[pid] = wager
                            logger.debug(f"Awarded {wager} points to player {pid} (partners win)")
                else:
                    # Partner(s) conceded, solo player wins (gets double points)
                    player = next((p for p in player_manager.players if p.id == solo_player), None)
                    if player:
                        solo_points = wager * 2
                        player.points += solo_points
                        points_awarded[solo_player] = solo_points
                        logger.debug(f"Awarded {solo_points} points to solo player {solo_player} (2x multiplier)")
            else:
                raise ValueError(f"Unknown team type: {hole_state.teams.type}")

            logger.info(
                f"Hole {hole_number} conceded. "
                f"Conceding player: {conceding_player}, Conceding team: {conceding_team}, "
                f"Points awarded: {points_awarded}"
            )

            return points_awarded

        except Exception as e:
            logger.error(f"Error awarding concession points: {e}")
            raise ValueError(f"Failed to award concession points: {str(e)}")

    def get_hole_summary(
        self,
        hole_number: int,
        game_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get comprehensive summary for a single hole.

        Includes scores, teams, betting, and results.

        Args:
            hole_number: Hole number (1-18)
            game_state: Current game state dictionary

        Returns:
            Dictionary with complete hole summary

        Example:
            >>> manager = ScoringManager()
            >>> summary = manager.get_hole_summary(hole_number=1, game_state={...})
            >>> summary.keys()
            dict_keys(['hole_number', 'teams', 'scores', 'betting', 'result'])
        """
        try:
            if hole_number < 1 or hole_number > 18:
                raise ValueError("Hole number must be between 1 and 18")

            # Extract hole state from game state
            hole_states = game_state.get('hole_states', {})
            if hole_number not in hole_states:
                raise ValueError(f"Hole {hole_number} not found in game state")

            hole_state = hole_states[hole_number]

            summary = {
                'hole_number': hole_number,
                'teams': {
                    'type': hole_state.get('teams', {}).get('type'),
                    'team1': hole_state.get('teams', {}).get('team1', []),
                    'team2': hole_state.get('teams', {}).get('team2', []),
                    'solo_player': hole_state.get('teams', {}).get('solo_player')
                },
                'scores': {
                    'gross': hole_state.get('scores', {}),
                    'net': hole_state.get('net_scores', {}),
                    'team1_score': hole_state.get('team1_score'),
                    'team2_score': hole_state.get('team2_score')
                },
                'betting': {
                    'base_wager': hole_state.get('betting', {}).get('base_wager', 1),
                    'current_wager': hole_state.get('betting', {}).get('current_wager', 1),
                    'doubled': hole_state.get('betting', {}).get('doubled', False),
                    'carry_over': hole_state.get('betting', {}).get('carry_over', False),
                    'special_rules': {
                        'duncan': hole_state.get('betting', {}).get('duncan_invoked', False),
                        'tunkarri': hole_state.get('betting', {}).get('tunkarri_invoked', False),
                        'float': hole_state.get('betting', {}).get('float_invoked', False)
                    }
                },
                'result': {
                    'complete': hole_state.get('hole_complete', False),
                    'halved': hole_state.get('halved', False),
                    'winning_team': hole_state.get('winning_team'),
                    'points_changes': hole_state.get('points_changes', {})
                }
            }

            logger.debug(f"Generated summary for hole {hole_number}")

            return summary

        except Exception as e:
            logger.error(f"Error getting hole summary: {e}")
            raise ValueError(f"Failed to get hole summary: {str(e)}")

    def get_game_summary(
        self,
        game_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get comprehensive summary for entire game.

        Includes all holes, totals, standings, and statistics.

        Args:
            game_state: Complete game state dictionary

        Returns:
            Dictionary with complete game summary

        Example:
            >>> manager = ScoringManager()
            >>> summary = manager.get_game_summary(game_state={...})
            >>> summary.keys()
            dict_keys(['game_id', 'total_holes', 'current_hole', 'players',
                       'standings', 'hole_results'])
        """
        try:
            players = game_state.get('players', [])
            hole_states = game_state.get('hole_states', {})
            current_hole = game_state.get('current_hole', 1)

            # Aggregate player totals
            player_totals = {}
            for player in players:
                player_id = player.get('id')
                player_totals[player_id] = {
                    'name': player.get('name'),
                    'handicap': player.get('handicap'),
                    'points': player.get('points', 0),
                    'holes_won': 0,
                    'holes_lost': 0,
                    'holes_halved': 0
                }

            # Process each completed hole
            hole_results = []
            for hole_num in range(1, current_hole):
                if hole_num not in hole_states:
                    continue

                hole_state = hole_states[hole_num]
                if not hole_state.get('hole_complete', False):
                    continue

                hole_summary = self.get_hole_summary(hole_num, game_state)
                hole_results.append(hole_summary)

                # Update player stats
                result = hole_summary.get('result', {})
                if result.get('halved'):
                    for player_id in player_totals:
                        player_totals[player_id]['holes_halved'] += 1
                elif result.get('winning_team'):
                    for player_id in result['winning_team']:
                        if player_id in player_totals:
                            player_totals[player_id]['holes_won'] += 1

                    # Infer losing team
                    all_player_ids = set(player_totals.keys())
                    winning_ids = set(result['winning_team'])
                    losing_ids = all_player_ids - winning_ids
                    for player_id in losing_ids:
                        player_totals[player_id]['holes_lost'] += 1

            # Create standings
            standings = sorted(
                player_totals.items(),
                key=lambda x: x[1]['points'],
                reverse=True
            )

            summary = {
                'game_id': game_state.get('game_id'),
                'total_holes': len(hole_results),
                'current_hole': current_hole,
                'players': player_totals,
                'standings': [
                    {
                        'player_id': player_id,
                        'player_name': data['name'],
                        'total_points': data['points'],
                        'holes_won': data['holes_won'],
                        'holes_lost': data['holes_lost'],
                        'holes_halved': data['holes_halved']
                    }
                    for player_id, data in standings
                ],
                'hole_results': hole_results,
                'game_status': game_state.get('game_status', 'unknown')
            }

            logger.info(
                f"Generated game summary: {len(hole_results)} holes completed, "
                f"{len(players)} players"
            )

            return summary

        except Exception as e:
            logger.error(f"Error getting game summary: {e}")
            raise ValueError(f"Failed to get game summary: {str(e)}")


# Singleton accessor function
_manager_instance = None


def get_scoring_manager() -> ScoringManager:
    """
    Get the singleton ScoringManager instance.

    This function provides access to the shared scoring manager instance,
    creating it if it doesn't exist yet.

    Returns:
        ScoringManager singleton instance

    Example:
        >>> manager = get_scoring_manager()
        >>> net_score = manager.calculate_hole_score(5, 1)
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ScoringManager()
    return _manager_instance
