"""
ShotResult domain object for the Wolf Goat Pig golf simulation.

This class represents the result of a golf shot with distance,
accuracy, position, and strategic implications.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
from .player import Player


class ShotQuality(Enum):
    """Enumeration of shot quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    TERRIBLE = "terrible"


class LieType(Enum):
    """Enumeration of lie types on the golf course."""
    FAIRWAY = "fairway"
    FIRST_CUT = "first cut"
    ROUGH = "rough"
    BUNKER = "bunker"
    TREES = "trees"
    HAZARD = "hazard"
    DEEP_ROUGH = "deep rough"


@dataclass
class ShotResult:
    """
    Represents the result of a golf shot in the Wolf Goat Pig simulation.
    
    This class encapsulates all shot-related data and provides
    methods for position analysis, scoring probability, and strategic implications.
    """
    
    player: Player
    drive: int
    lie: str
    remaining: int
    shot_quality: str
    penalty: int = 0
    
    # Optional fields for enhanced shot analysis
    hole_number: Optional[int] = None
    shot_number: Optional[int] = None
    wind_factor: Optional[float] = None
    pressure_factor: Optional[float] = None
    
    # Strategic analysis fields
    _position_quality: Optional[Dict[str, Any]] = None
    _scoring_probability: Optional[Dict[str, Any]] = None
    _partnership_value: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate and set default values after initialization."""
        if not isinstance(self.player, Player):
            raise ValueError("Player must be a Player object")
        
        if self.drive < 0:
            raise ValueError("Drive distance cannot be negative")
        
        if self.drive > 400:
            raise ValueError("Drive distance cannot exceed 400 yards")
        
        if self.remaining < 0:
            raise ValueError("Remaining distance cannot be negative")
        
        if self.remaining > 500:
            raise ValueError("Remaining distance cannot exceed 500 yards")
        
        if self.penalty < 0:
            raise ValueError("Penalty strokes cannot be negative")
        
        if self.penalty > 3:
            raise ValueError("Penalty strokes cannot exceed 3")
        
        # Validate shot quality
        valid_qualities = [q.value for q in ShotQuality]
        if self.shot_quality not in valid_qualities:
            raise ValueError(f"Shot quality must be one of: {valid_qualities}")
        
        # Validate lie type
        valid_lies = [l.value for l in LieType]
        if self.lie not in valid_lies:
            raise ValueError(f"Lie type must be one of: {valid_lies}")
    
    def get_shot_quality_enum(self) -> ShotQuality:
        """Get the shot quality as an enum."""
        return ShotQuality(self.shot_quality)
    
    def get_lie_enum(self) -> LieType:
        """Get the lie type as an enum."""
        return LieType(self.lie)
    
    def get_position_quality(self) -> Dict[str, Any]:
        """Assess the quality of the current position."""
        if self._position_quality is None:
            self._calculate_position_quality()
        return self._position_quality
    
    def get_scoring_probability(self) -> Dict[str, Any]:
        """Calculate scoring probability from this position."""
        if self._scoring_probability is None:
            self._calculate_scoring_probability()
        return self._scoring_probability
    
    def get_partnership_value(self) -> Dict[str, Any]:
        """Calculate the strategic value of partnering with this player."""
        if self._partnership_value is None:
            self._calculate_partnership_value()
        return self._partnership_value
    
    def _calculate_position_quality(self) -> None:
        """Calculate position quality based on lie and remaining distance."""
        lie = self.lie
        remaining = self.remaining
        
        # Scoring positions
        if lie == "fairway":
            if remaining <= 100:
                quality = "Excellent - Short iron to green"
                score = 90
            elif remaining <= 150:
                quality = "Good - Mid iron opportunity"
                score = 75
            else:
                quality = "Fair - Long approach needed"
                score = 60
        elif lie in ["first cut", "rough"]:
            if remaining <= 120:
                quality = "Good - Manageable from rough"
                score = 65
            else:
                quality = "Challenging - Long shot from rough"
                score = 45
        else:  # bunker, trees, hazard
            quality = "Difficult - Recovery shot needed"
            score = 25
        
        self._position_quality = {
            "quality_score": score,
            "description": quality,
            "lie_type": lie,
            "distance_category": "Short" if remaining <= 100 else "Medium" if remaining <= 150 else "Long"
        }
    
    def _calculate_scoring_probability(self) -> None:
        """Calculate scoring probability based on position and player skill."""
        position_quality = self.get_position_quality()
        base_score = position_quality["quality_score"]
        
        # Adjust for player handicap
        handicap_factor = max(0.5, 1.0 - (self.player.handicap / 36.0))
        adjusted_score = base_score * handicap_factor
        
        # Calculate probabilities
        birdie_prob = max(5, min(25, adjusted_score * 0.2))
        par_prob = max(20, min(60, adjusted_score * 0.6))
        bogey_prob = max(15, min(50, 100 - adjusted_score * 0.8))
        double_prob = max(5, min(30, 100 - adjusted_score))
        
        # Normalize probabilities
        total = birdie_prob + par_prob + bogey_prob + double_prob
        birdie_prob = round(birdie_prob / total * 100, 1)
        par_prob = round(par_prob / total * 100, 1)
        bogey_prob = round(bogey_prob / total * 100, 1)
        double_prob = round(double_prob / total * 100, 1)
        
        self._scoring_probability = {
            "birdie": birdie_prob,
            "par": par_prob,
            "bogey": bogey_prob,
            "double_bogey": double_prob,
            "expected_score": round(2 + (bogey_prob * 0.01) + (double_prob * 0.02), 1),
            "position_factor": position_quality["quality_score"],
            "handicap_factor": handicap_factor
        }
    
    def _calculate_partnership_value(self) -> None:
        """Calculate the strategic value of partnering with this player."""
        shot_quality = self.shot_quality
        remaining = self.remaining
        
        # Base value from shot quality
        if shot_quality == "excellent":
            base_value = 85
        elif shot_quality == "good":
            base_value = 70
        elif shot_quality == "average":
            base_value = 50
        elif shot_quality == "poor":
            base_value = 30
        else:  # terrible
            base_value = 15
        
        # Adjust for position
        if remaining <= 100:
            position_bonus = 15
        elif remaining <= 150:
            position_bonus = 10
        else:
            position_bonus = 0
        
        # Adjust for player handicap
        handicap_bonus = max(-10, min(10, (18 - self.player.handicap) * 2))
        
        final_value = min(100, base_value + position_bonus + handicap_bonus)
        
        self._partnership_value = {
            "partnership_appeal": final_value,
            "reason": f"{shot_quality} shot, {remaining} yards remaining",
            "strategic_value": "High" if final_value >= 70 else "Medium" if final_value >= 50 else "Low",
            "base_value": base_value,
            "position_bonus": position_bonus,
            "handicap_bonus": handicap_bonus
        }
    
    def get_strategic_implications(self) -> list:
        """Get strategic implications and advice for this shot."""
        implications = []
        
        # Shot quality implications
        if self.shot_quality == "excellent":
            implications.append("🎯 This player is in excellent position - strong partnership candidate")
        elif self.shot_quality == "terrible":
            implications.append("⚠️ Poor position - consider other partnership options")
        
        # Distance implications
        if self.remaining <= 100:
            implications.append("🎯 Short approach shot - high birdie/par probability")
        elif self.remaining > 200:
            implications.append("📏 Long approach required - more challenging scoring")
        
        # Lie implications
        if self.lie == "fairway":
            implications.append("✅ Perfect lie - clean contact expected")
        elif self.lie in ["trees", "hazard"]:
            implications.append("🌲 Trouble lie - recovery shot needed")
        
        # Penalty implications
        if self.penalty > 0:
            implications.append(f"⚠️ {self.penalty} penalty stroke(s) - challenging recovery")
        
        return implications
    
    def get_shot_description(self) -> str:
        """Create a detailed, realistic shot description."""
        # Quality descriptors
        quality_desc = {
            "excellent": "striped it",
            "good": "hit a solid drive",
            "average": "found the fairway",
            "poor": "struggled off the tee",
            "terrible": "got into trouble"
        }
        
        # Lie descriptors
        lie_desc = {
            "fairway": "sitting pretty in the fairway",
            "first cut": "in the first cut of rough",
            "rough": "nestled in the rough",
            "bunker": "caught the fairway bunker",
            "trees": "behind some trees",
            "hazard": "near the hazard",
            "deep rough": "buried in thick rough"
        }
        
        # Player identifier
        player_icon = "🧑" if self.player.id == "human" else "💻"
        
        base_desc = f"{player_icon} **{self.player.name}** {quality_desc.get(self.shot_quality, 'hit their drive')} {self.drive} yards, {lie_desc.get(self.lie, f'in the {self.lie}')}, leaving {self.remaining} yards to the pin."
        
        # Add quality-specific reactions
        if self.shot_quality == "excellent":
            base_desc += " 🎯 What a shot!"
        elif self.shot_quality == "terrible":
            base_desc += " 😬 That's not what they were looking for."
        
        # Add penalty information
        if self.penalty > 0:
            base_desc += f" ⚠️ {self.penalty} penalty stroke(s)."
        
        return base_desc
    
    def to_dict(self) -> dict:
        """Convert shot result to dictionary format for serialization."""
        return {
            "player": self.player.to_dict(),
            "drive": self.drive,
            "lie": self.lie,
            "remaining": self.remaining,
            "shot_quality": self.shot_quality,
            "penalty": self.penalty,
            "hole_number": self.hole_number,
            "shot_number": self.shot_number,
            "wind_factor": self.wind_factor,
            "pressure_factor": self.pressure_factor,
            "position_quality": self.get_position_quality(),
            "scoring_probability": self.get_scoring_probability(),
            "partnership_value": self.get_partnership_value(),
            "strategic_implications": self.get_strategic_implications(),
            "shot_description": self.get_shot_description()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ShotResult':
        """Create a ShotResult instance from a dictionary."""
        # Handle player data
        if isinstance(data["player"], dict):
            from .player import Player
            player = Player.from_dict(data["player"])
        else:
            player = data["player"]
        
        return cls(
            player=player,
            drive=data["drive"],
            lie=data["lie"],
            remaining=data["remaining"],
            shot_quality=data["shot_quality"],
            penalty=data.get("penalty", 0),
            hole_number=data.get("hole_number"),
            shot_number=data.get("shot_number"),
            wind_factor=data.get("wind_factor"),
            pressure_factor=data.get("pressure_factor")
        )
    
    def __str__(self) -> str:
        """String representation of the shot result."""
        return f"{self.player.name}: {self.drive} yards, {self.lie}, {self.remaining} yards remaining ({self.shot_quality})"
    
    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (f"ShotResult(player={self.player.name}, drive={self.drive}, "
                f"lie='{self.lie}', remaining={self.remaining}, "
                f"quality='{self.shot_quality}', penalty={self.penalty})")
    
    def __eq__(self, other) -> bool:
        """Equality comparison based on shot characteristics."""
        if not isinstance(other, ShotResult):
            return False
        return (self.player.id == other.player.id and
                self.drive == other.drive and
                self.lie == other.lie and
                self.remaining == other.remaining and
                self.shot_quality == other.shot_quality and
                self.penalty == other.penalty)
    
    def __hash__(self) -> int:
        """Hash based on shot characteristics."""
        return hash((self.player.id, self.drive, self.lie, self.remaining, self.shot_quality, self.penalty)) 