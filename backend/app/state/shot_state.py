from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ShotResult:
    """Data class for individual shot results"""
    player_id: str
    shot_result: Dict[str, Any]
    probabilities: Optional[Dict[str, Any]] = None


@dataclass
class ShotState:
    """
    Manages the chronological shot sequence during hole play.
    Extracted from GameState to follow single responsibility principle.
    """
    phase: str = "tee_shots"
    current_player_index: int = 0
    completed_shots: List[ShotResult] = field(default_factory=list)
    pending_decisions: List[Dict[str, Any]] = field(default_factory=list)

    def reset_for_hole(self):
        """Reset shot state for a new hole"""
        self.phase = "tee_shots"
        self.current_player_index = 0
        self.completed_shots = []
        self.pending_decisions = []

    def next_shot(self) -> bool:
        """
        Advance to the next shot in the sequence.
        Returns True if advanced, False if no more shots in current phase.
        """
        self.current_player_index += 1
        return self.current_player_index < self._get_phase_player_count()

    def add_completed_shot(self, player_id: str, shot_result: Dict[str, Any], 
                          probabilities: Optional[Dict[str, Any]] = None):
        """Add a completed shot to the sequence"""
        shot = ShotResult(
            player_id=player_id,
            shot_result=shot_result,
            probabilities=probabilities
        )
        self.completed_shots.append(shot)

    def has_next_shot(self, hitting_order: List[str]) -> bool:
        """Check if there are more shots available in current phase"""
        if self.phase == "tee_shots":
            return self.current_player_index < len(hitting_order)
        elif self.phase == "approach_shots":
            # Logic for approach shots based on teams
            return self._has_next_approach_shot(hitting_order)
        return False

    def get_current_player_id(self, hitting_order: List[str]) -> Optional[str]:
        """Get the ID of the player who should hit next"""
        if self.phase == "tee_shots" and self.current_player_index < len(hitting_order):
            return hitting_order[self.current_player_index]
        elif self.phase == "approach_shots":
            return self._get_next_approach_player(hitting_order)
        return None

    def advance_phase(self, new_phase: str):
        """Advance to a new phase of shot play"""
        self.phase = new_phase
        self.current_player_index = 0
        # Don't clear completed_shots as they may be needed for decisions

    def get_phase_summary(self, hitting_order: List[str]) -> Dict[str, Any]:
        """Get comprehensive information about current shot phase"""
        return {
            "phase": self.phase,
            "current_player_index": self.current_player_index,
            "shots_completed": len(self.completed_shots),
            "shots_remaining": max(0, len(hitting_order) - self.current_player_index),
            "completed_shots": [
                {
                    "player_id": shot.player_id,
                    "shot_result": shot.shot_result,
                    "probabilities": shot.probabilities
                }
                for shot in self.completed_shots
            ],
            "next_player": self.get_current_player_id(hitting_order),
            "pending_decisions": self.pending_decisions
        }

    def add_pending_decision(self, decision: Dict[str, Any]):
        """Add a decision that needs to be made"""
        self.pending_decisions.append(decision)

    def clear_pending_decisions(self):
        """Clear all pending decisions (after they're resolved)"""
        self.pending_decisions = []

    def get_tee_shot_results(self) -> List[Dict[str, Any]]:
        """Get all tee shot results for partnership decisions"""
        tee_shots = []
        for shot in self.completed_shots:
            if self.phase == "tee_shots" or shot.shot_result.get("shot_type") == "tee_shot":
                tee_shots.append({
                    "player_id": shot.player_id,
                    "result": shot.shot_result,
                    "probabilities": shot.probabilities
                })
        return tee_shots

    def is_phase_complete(self, hitting_order: List[str]) -> bool:
        """Check if the current phase is complete"""
        if self.phase == "tee_shots":
            return self.current_player_index >= len(hitting_order)
        elif self.phase == "approach_shots":
            return not self._has_next_approach_shot(hitting_order)
        return True

    def _get_phase_player_count(self) -> int:
        """Get the number of players that should participate in current phase"""
        if self.phase == "tee_shots":
            return 4  # All players hit tee shots
        elif self.phase == "approach_shots":
            return 2  # Typically partnership plays approach shots
        return 0

    def _has_next_approach_shot(self, hitting_order: List[str]) -> bool:
        """Check if there are more approach shots needed"""
        # This would depend on team formation and strategy
        # For now, simplified logic - extend as needed
        return self.current_player_index < 2  # Max 2 approach shots in partnership

    def _get_next_approach_player(self, hitting_order: List[str]) -> Optional[str]:
        """Get the next player for approach shots based on team strategy"""
        # This would be more complex in real implementation
        # Would consider team formation, shot positions, etc.
        if self.current_player_index < len(hitting_order):
            return hitting_order[self.current_player_index]
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize shot state to dictionary"""
        return {
            "phase": self.phase,
            "current_player_index": self.current_player_index,
            "completed_shots": [
                {
                    "player_id": shot.player_id,
                    "shot_result": shot.shot_result,
                    "probabilities": shot.probabilities
                }
                for shot in self.completed_shots
            ],
            "pending_decisions": self.pending_decisions
        }

    def from_dict(self, data: Dict[str, Any]):
        """Deserialize shot state from dictionary"""
        self.phase = data.get("phase", "tee_shots")
        self.current_player_index = data.get("current_player_index", 0)
        self.pending_decisions = data.get("pending_decisions", [])
        
        # Convert completed shots back to ShotResult objects
        self.completed_shots = []
        for shot_data in data.get("completed_shots", []):
            shot = ShotResult(
                player_id=shot_data.get("player_id", ""),
                shot_result=shot_data.get("shot_result", {}),
                probabilities=shot_data.get("probabilities")
            )
            self.completed_shots.append(shot)
    
    def __repr__(self) -> str:
        return (f"ShotState(phase='{self.phase}', "
                f"current_player_index={self.current_player_index}, "
                f"completed_shots={len(self.completed_shots)}, "
                f"pending_decisions={len(self.pending_decisions)})") 