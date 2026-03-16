"""
Manager Layer Contracts

Protocol definitions for all manager classes that handle game logic.
"""

from typing import Protocol, Dict, Any, List, Optional


class RuleManagerProtocol(Protocol):
    """Contract for RuleManager.

    Defines the interface for centralized Wolf Goat Pig rule enforcement.
    """

    @classmethod
    def get_instance(cls) -> 'RuleManagerProtocol':
        """Get singleton instance of RuleManager."""
        ...

    def can_form_partnership(
        self,
        captain_id: str,
        partner_id: str,
        game_state: Dict[str, Any]
    ) -> bool:
        """Check if captain can form partnership with partner.

        Args:
            captain_id: ID of captain player
            partner_id: ID of partner player
            game_state: Current game state

        Returns:
            True if partnership is allowed
        """
        ...

    def can_double(self, player_id: str, game_state: Dict[str, Any]) -> bool:
        """Check if player can double the wager."""
        ...

    def can_redouble(self, player_id: str, game_state: Dict[str, Any]) -> bool:
        """Check if player can redouble the wager."""
        ...

    def can_duncan(self, player_id: str, game_state: Dict[str, Any]) -> bool:
        """Check if Duncan special rule applies."""
        ...

    def validate_turn_order(
        self,
        player_id: str,
        current_player: str,
        game_phase: str
    ) -> bool:
        """Validate it's player's turn."""
        ...

    def validate_betting_phase(self, game_state: Dict[str, Any]) -> bool:
        """Check if betting phase is valid."""
        ...

    def validate_partnership_selection(
        self,
        captain_id: str,
        partner_id: str,
        game_state: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate partnership selection.

        Returns:
            Tuple of (is_valid, error_message)
        """
        ...

    def get_wager_multiplier(self, game_state: Dict[str, Any]) -> float:
        """Calculate current wager multiplier based on doubles/redoubles."""
        ...


class ScoringManagerProtocol(Protocol):
    """Contract for ScoringManager.

    Defines the interface for all scoring calculations.
    """

    @classmethod
    def get_instance(cls) -> 'ScoringManagerProtocol':
        """Get singleton instance of ScoringManager."""
        ...

    def calculate_hole_score(
        self,
        gross_strokes: int,
        par: int,
        handicap_strokes: int
    ) -> Dict[str, int]:
        """Calculate score for a single hole.

        Args:
            gross_strokes: Actual strokes taken
            par: Par for the hole
            handicap_strokes: Strokes to apply

        Returns:
            Dict with 'gross', 'net', 'vs_par'
        """
        ...

    def calculate_match_points(
        self,
        winning_team: List[str],
        losing_team: List[str],
        wager_multiplier: float
    ) -> Dict[str, int]:
        """Calculate match points for hole winner.

        Args:
            winning_team: List of winning player IDs
            losing_team: List of losing player IDs
            wager_multiplier: Current wager multiplier

        Returns:
            Dict mapping player_id to points won/lost
        """
        ...

    def calculate_game_totals(
        self,
        hole_scores: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate total game statistics.

        Args:
            hole_scores: List of all hole scores

        Returns:
            Dict with totals for each player
        """
        ...

    def calculate_team_score(
        self,
        player1_score: int,
        player2_score: int,
        format: str = "best_ball"
    ) -> int:
        """Calculate team score based on format.

        Args:
            player1_score: First player's score
            player2_score: Second player's score
            format: Scoring format (best_ball, scramble, etc.)

        Returns:
            Team score
        """
        ...

    def calculate_handicap_strokes(
        self,
        player_handicap: float,
        hole_handicap: int,
        course_rating: float,
        slope_rating: float
    ) -> int:
        """Calculate strokes to apply on a hole.

        Args:
            player_handicap: Player's handicap index
            hole_handicap: Hole handicap (1-18)
            course_rating: Course rating
            slope_rating: Slope rating

        Returns:
            Number of strokes to apply
        """
        ...

    def calculate_final_standings(
        self,
        player_points: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """Calculate final game standings.

        Args:
            player_points: Dict mapping player_id to total points

        Returns:
            List of players ordered by finish position
        """
        ...
