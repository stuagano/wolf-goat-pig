"""
Player domain object for the Wolf Goat Pig golf simulation.

This class represents a golfer in the simulation with their
handicap, scoring, and game state information.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class HandicapCategory(Enum):
    """Enumeration of handicap categories for player classification."""
    SCRATCH = "scratch"  # 0-5
    LOW = "low"          # 6-12
    MID = "mid"          # 13-18
    HIGH = "high"        # 19-25
    BEGINNER = "beginner"  # 26+


class StrengthLevel(Enum):
    """Enumeration of player strength levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    POOR = "poor"


@dataclass
class Player:
    """
    Represents a golfer in the Wolf Goat Pig simulation.
    
    This class encapsulates all player-related data and provides
    methods for handicap analysis, scoring, and game state management.
    """

    id: str
    name: str
    handicap: float
    points: int = 0
    strength: Optional[str] = None
    is_human: bool = False  # Flag to identify human players

    # Game state fields
    hole_scores: dict = field(default_factory=dict)
    float_used: bool = False
    last_points: int = 0

    def __post_init__(self):
        """Validate and set default values after initialization."""
        if not self.id or not self.id.strip():
            raise ValueError("Player ID cannot be empty")

        if not self.name or not self.name.strip():
            raise ValueError("Player name cannot be empty")

        if self.handicap < 0:
            raise ValueError("Handicap cannot be negative")

        if self.handicap > 54:
            raise ValueError("Handicap cannot exceed 54")

        # Set strength based on handicap if not provided
        if self.strength is None:
            self.strength = self.get_strength_level().value

    def get_handicap_category(self) -> HandicapCategory:
        """Get the handicap category for this player."""
        if self.handicap <= 5:
            return HandicapCategory.SCRATCH
        elif self.handicap <= 12:
            return HandicapCategory.LOW
        elif self.handicap <= 18:
            return HandicapCategory.MID
        elif self.handicap <= 25:
            return HandicapCategory.HIGH
        else:
            return HandicapCategory.BEGINNER

    def get_strength_level(self) -> StrengthLevel:
        """Get the strength level based on handicap."""
        if self.handicap <= 5:
            return StrengthLevel.EXCELLENT
        elif self.handicap <= 10:
            return StrengthLevel.GOOD
        elif self.handicap <= 15:
            return StrengthLevel.AVERAGE
        elif self.handicap <= 20:
            return StrengthLevel.BELOW_AVERAGE
        else:
            return StrengthLevel.POOR

    def get_expected_drive_distance(self) -> int:
        """Get expected drive distance based on handicap."""
        if self.handicap <= 5:
            return 265
        elif self.handicap <= 12:
            return 245
        elif self.handicap <= 20:
            return 225
        else:
            return 200

    def get_shot_quality_weights(self) -> list[float]:
        """Get shot quality probability weights based on handicap."""
        if self.handicap <= 5:
            return [0.15, 0.40, 0.30, 0.12, 0.03]  # More excellent/good
        elif self.handicap <= 12:
            return [0.12, 0.38, 0.32, 0.15, 0.03]  # Standard distribution
        elif self.handicap <= 20:
            return [0.08, 0.30, 0.35, 0.20, 0.07]  # More average/poor
        else:
            return [0.05, 0.20, 0.35, 0.25, 0.15]  # More poor/terrible

    def add_points(self, points: int) -> None:
        """Add points to the player's total."""
        self.last_points = self.points
        self.points += points

    def get_points_change(self) -> int:
        """Get the change in points from the last update."""
        return self.points - self.last_points

    def record_hole_score(self, hole_number: int, score: int) -> None:
        """Record a score for a specific hole."""
        self.hole_scores[hole_number] = score

    def get_hole_score(self, hole_number: int) -> Optional[int]:
        """Get the score for a specific hole."""
        return self.hole_scores.get(hole_number)

    def use_float(self) -> bool:
        """Use the player's float option if available."""
        if not self.float_used:
            self.float_used = True
            return True
        return False

    def can_use_float(self) -> bool:
        """Check if the player can use their float option."""
        return not self.float_used

    def reset_float(self) -> None:
        """Reset the float option (typically at the start of a new hole)."""
        self.float_used = False

    def to_dict(self) -> dict:
        """Convert player to dictionary format for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "handicap": self.handicap,
            "points": self.points,
            "strength": self.strength,
            "is_human": self.is_human,
            "hole_scores": self.hole_scores.copy(),
            "float_used": self.float_used,
            "last_points": self.last_points
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Player':
        """Create a Player instance from a dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            handicap=data["handicap"],
            points=data.get("points", 0),
            strength=data.get("strength"),
            is_human=data.get("is_human", False),
            hole_scores=data.get("hole_scores", {}),
            float_used=data.get("float_used", False),
            last_points=data.get("last_points", 0)
        )

    def __str__(self) -> str:
        """String representation of the player."""
        return f"{self.name} (Handicap: {self.handicap}, Points: {self.points})"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (f"Player(id='{self.id}', name='{self.name}', "
                f"handicap={self.handicap}, points={self.points}, "
                f"strength='{self.strength}')")

    def __eq__(self, other: object) -> bool:
        """Equality comparison based on player ID."""
        if not isinstance(other, Player):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on player ID."""
        return hash(self.id)

    @staticmethod
    def get_human_player_id(players: List["Player"]) -> str:
        """
        Get the human player ID from a list of players.
        This is a centralized utility function for human player identification.
        
        Args:
            players: List of Player objects
            
        Returns:
            str: The ID of the human player, or first player as fallback
        """
        for player in players:
            if hasattr(player, 'is_human') and player.is_human:
                return player.id

        # Fallback: assume first player is human (for backward compatibility)
        if players:
            return players[0].id

        return "p1"  # Ultimate fallback
