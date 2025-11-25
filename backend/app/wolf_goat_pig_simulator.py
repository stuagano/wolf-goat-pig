"""
Wolf Goat Pig Simulator

This module provides simulation capabilities for the Wolf Goat Pig game,
including Monte Carlo analysis and probabilistic shot generation.

The WolfGoatPigSimulator class extends WolfGoatPigGame with simulation-specific
methods while maintaining all core game tracking functionality.
"""

import logging
import random
from typing import Any, Dict, List, Optional

from .wolf_goat_pig import Player, WGPShotResult, WolfGoatPigGame

logger = logging.getLogger(__name__)


class WolfGoatPigSimulator(WolfGoatPigGame):
    """
    Simulation engine for Wolf Goat Pig game.
    
    Extends WolfGoatPigGame with Monte Carlo simulation and probabilistic
    shot generation capabilities. Use this class when you need to:
    - Run Monte Carlo simulations for betting analysis
    - Generate simulated shot results for testing
    - Analyze probabilistic outcomes
    
    For real game tracking without simulation, use WolfGoatPigGame directly.
    
    Example:
        ```python
        # Create simulator
        sim = WolfGoatPigSimulator(player_count=4)
        
        # Use inherited game functionality
        sim.start_hole(1)
        
        # Use simulation-specific functionality
        results = sim.run_monte_carlo_simulation(iterations=1000)
        shot = sim.simulate_shot(player_id="p1")
        ```
    """

    def __init__(self, *args, **kwargs):
        """Initialize the simulator with all game engine capabilities."""
        super().__init__(*args, **kwargs)
        logger.info(f"Initialized WolfGoatPigSimulator for game {self.game_id}")

    # =========================================================================
    # MONTE CARLO SIMULATION
    # =========================================================================

    def run_monte_carlo_simulation(
        self,
        iterations: int = 1000,
        scenario: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for betting scenario analysis.
        
        Args:
            iterations: Number of simulations to run
            scenario: Optional scenario parameters
            
        Returns:
            Dictionary with simulation results including:
            - win_probabilities: Dict[player_id, float]
            - expected_values: Dict[player_id, float]
            - confidence_intervals: Dict[player_id, Tuple[float, float]]
        """
        logger.info(f"Running Monte Carlo simulation with {iterations} iterations")

        # Save current game state
        saved_state = self._save_simulation_state()

        results = {
            "iterations": iterations,
            "win_probabilities": {},
            "expected_values": {},
            "outcomes": []
        }

        # Run simulations
        outcomes: List[Dict[str, Any]] = []
        for i in range(iterations):
            # Restore state for each iteration
            self._restore_simulation_state(saved_state)

            # Simulate hole completion
            outcome = self._simulate_hole_completion()
            outcomes.append(outcome)

        results["outcomes"] = outcomes

        # Calculate statistics
        results["win_probabilities"] = self._calculate_win_probabilities(
            outcomes
        )
        results["expected_values"] = self._calculate_expected_values(
            outcomes
        )

        # Restore original state
        self._restore_simulation_state(saved_state)

        logger.info("Monte Carlo simulation complete")
        return results

    def _save_simulation_state(self) -> Dict[str, Any]:
        """Save current game state for simulation."""
        return {
            "players": [
                {
                    "id": p.id,
                    "points": p.points,
                    "float_used": p.float_used,
                    "solo_count": p.solo_count
                }
                for p in self.players
            ],
            "current_hole": self.current_hole,
            "hole_states": self.hole_states.copy() if hasattr(self, 'hole_states') else {}
        }

    def _restore_simulation_state(self, state: Dict[str, Any]) -> None:
        """Restore game state from saved state."""
        for player_data in state["players"]:
            player = next(p for p in self.players if p.id == player_data["id"])
            player.points = player_data["points"]
            player.float_used = player_data["float_used"]
            player.solo_count = player_data["solo_count"]

        self.current_hole = state["current_hole"]
        if hasattr(self, 'hole_states'):
            self.hole_states = state["hole_states"].copy()

    def _simulate_hole_completion(self) -> Dict[str, Any]:
        """Simulate completion of current hole."""
        # Simulate shots for all players
        hole_results: Dict[str, Any] = {}
        for player in self.players:
            shots = self._simulate_player_hole(player)
            hole_results[player.id] = {
                "total_strokes": len(shots),
                "shots": shots
            }

        return hole_results

    def _simulate_player_hole(self, player: Player) -> List[WGPShotResult]:
        """Simulate all shots for a player on current hole."""
        shots = []
        distance_remaining: float = 400.0  # Starting distance (yards)
        shot_number = 1

        while distance_remaining > 0 and shot_number < 10:  # Max 10 shots
            shot = self._simulate_player_shot(
                player_id=player.id,
                handicap=player.handicap,
                shot_number=shot_number,
                distance_to_pin=distance_remaining
            )
            shots.append(shot)

            if shot.made_shot:
                break

            distance_remaining = shot.distance_to_pin
            shot_number += 1

        return shots

    def _calculate_win_probabilities(self, outcomes: List[Dict]) -> Dict[str, float]:
        """Calculate win probability for each player."""
        win_counts: Dict[str, float] = {p.id: 0.0 for p in self.players}

        for outcome in outcomes:
            # Determine winner(s) based on strokes
            min_strokes = min(
                outcome[pid]["total_strokes"]
                for pid in outcome.keys()
            )
            winners = [
                pid for pid, data in outcome.items()
                if data["total_strokes"] == min_strokes
            ]

            # Award fractional wins for ties
            for winner in winners:
                win_counts[winner] += 1.0 / float(len(winners))

        # Convert to probabilities
        total = float(len(outcomes))
        return {
            pid: float(count) / total
            for pid, count in win_counts.items()
        }

    def _calculate_expected_values(self, outcomes: List[Dict]) -> Dict[str, float]:
        """Calculate expected value for each player."""
        # Simplified EV calculation
        # In real implementation, this would factor in betting state
        return {p.id: 0.0 for p in self.players}

    # =========================================================================
    # SHOT SIMULATION
    # =========================================================================

    def simulate_shot(
        self,
        player_id: str,
        lie_type: Optional[str] = None,
        distance_to_pin: Optional[float] = None
    ) -> WGPShotResult:
        """
        Generate a simulated shot result.
        
        Args:
            player_id: ID of player taking the shot
            lie_type: Optional lie type (tee, fairway, rough, sand, green)
            distance_to_pin: Optional distance to pin in yards
            
        Returns:
            WGPShotResult with simulated outcome
        """
        player = next(p for p in self.players if p.id == player_id)

        # Use provided values or determine from game state
        if distance_to_pin is None:
            distance_to_pin = 400.0  # Default starting distance

        if lie_type is None:
            lie_type = "tee" if distance_to_pin > 300 else "fairway"

        return self._simulate_player_shot(
            player_id=player_id,
            handicap=player.handicap,
            shot_number=1,
            distance_to_pin=distance_to_pin,
            lie_type=lie_type
        )

    def _simulate_player_shot(
        self,
        player_id: str,
        handicap: float,
        shot_number: int,
        distance_to_pin: float,
        lie_type: str = "fairway"
    ) -> WGPShotResult:
        """
        Simulate a single shot for a player.
        
        Args:
            player_id: Player ID
            handicap: Player handicap
            shot_number: Shot number in sequence
            distance_to_pin: Distance to pin in yards
            lie_type: Type of lie
            
        Returns:
            WGPShotResult with simulated outcome
        """
        # Determine shot quality based on handicap and lie
        shot_quality = self._determine_shot_quality(handicap, lie_type)

        # Calculate new distance based on quality
        if distance_to_pin <= 100:
            # Short game
            new_distance = self._simulate_short_game_shot(
                handicap, distance_to_pin, lie_type
            )
        elif shot_number == 1 and distance_to_pin > 200:
            # Tee shot
            hole_par = 4  # Default
            new_distance = self._simulate_tee_shot_distance(handicap, hole_par)
        else:
            # Approach shot
            new_distance = self._simulate_approach_shot(
                handicap, distance_to_pin, lie_type
            )

        # Determine if shot was holed
        made_shot = new_distance <= 0.5 or (
            distance_to_pin <= 3 and random.random() < 0.7
        )

        # Determine next lie type
        next_lie = self._determine_lie_type(shot_quality, distance_to_pin)

        return WGPShotResult(
            player_id=player_id,
            shot_number=shot_number,
            lie_type=next_lie if not made_shot else "hole",
            distance_to_pin=max(0, new_distance),
            shot_quality=shot_quality,
            made_shot=made_shot,
            penalty_strokes=0
        )

    def _determine_shot_quality(self, handicap: float, lie_type: str) -> str:
        """
        Determine shot quality based on handicap and lie.
        
        Args:
            handicap: Player handicap
            lie_type: Type of lie
            
        Returns:
            Shot quality: excellent, good, average, poor, terrible
        """
        # Base probability on handicap (lower handicap = better shots)
        skill_factor = max(0, 1 - (handicap / 30))

        # Adjust for lie difficulty
        lie_difficulty = {
            "tee": 0.9,
            "fairway": 1.0,
            "green": 1.1,
            "rough": 0.7,
            "sand": 0.5
        }

        adjusted_skill = skill_factor * lie_difficulty.get(lie_type, 1.0)

        # Determine quality
        rand = random.random()
        if rand < adjusted_skill * 0.2:
            return "excellent"
        elif rand < adjusted_skill * 0.5:
            return "good"
        elif rand < adjusted_skill * 0.8:
            return "average"
        elif rand < 0.9:
            return "poor"
        else:
            return "terrible"

    def _simulate_tee_shot_distance(self, handicap: float, hole_par: int) -> float:
        """
        Simulate tee shot distance based on handicap and hole par.
        
        Returns distance remaining to pin.
        """
        if hole_par == 3:
            # Par 3 - aiming for green
            if handicap <= 5:
                return random.uniform(5, 25)  # Good players get close
            elif handicap <= 15:
                return random.uniform(15, 45)  # Mid handicaps
            else:
                return random.uniform(25, 65)  # High handicaps
        elif hole_par == 4:
            # Par 4 - drive down fairway
            if handicap <= 5:
                return random.uniform(120, 180)  # Good position
            elif handicap <= 15:
                return random.uniform(140, 220)  # Reasonable distance
            else:
                return random.uniform(160, 280)  # Longer remaining
        else:  # Par 5
            # Par 5 - long drive
            if handicap <= 5:
                return random.uniform(180, 280)  # Good position for approach
            elif handicap <= 15:
                return random.uniform(220, 320)  # Still manageable
            else:
                return random.uniform(280, 380)  # Longer approach needed

    def _simulate_approach_shot(
        self,
        handicap: float,
        prev_distance: float,
        lie_type: str
    ) -> float:
        """
        Simulate approach shot advancement.
        
        Returns new distance to pin.
        """
        # Short game (under 100 yards) - different logic
        if prev_distance <= 100:
            return self._simulate_short_game_shot(handicap, prev_distance, lie_type)

        # Full shots (over 100 yards)
        if handicap <= 5:
            if prev_distance > 200:
                advance_distance = random.uniform(80, 120)
            else:
                advance_distance = random.uniform(40, 60)
        elif handicap <= 15:
            if prev_distance > 200:
                advance_distance = random.uniform(60, 100)
            else:
                advance_distance = random.uniform(30, 80)
        else:
            if prev_distance > 200:
                advance_distance = random.uniform(40, 80)
            else:
                advance_distance = random.uniform(20, 50)

        # Adjust for lie difficulty
        lie_penalty = 1.0
        if lie_type == "rough":
            lie_penalty = 0.8
        elif lie_type == "sand":
            lie_penalty = 0.6

        # Calculate new distance
        new_distance = max(0, prev_distance - (advance_distance * lie_penalty))
        return new_distance

    def _simulate_short_game_shot(
        self,
        handicap: float,
        distance: float,
        lie_type: str
    ) -> float:
        """
        Handle shots within 100 yards - chipping and putting.
        
        Returns new distance to pin.
        """
        if distance <= 3:
            # Very short putts - should usually go in or get very close
            if handicap <= 5:
                return random.uniform(0, 1) if random.random() > 0.85 else 0
            elif handicap <= 15:
                return random.uniform(0, 2) if random.random() > 0.75 else 0
            else:
                return random.uniform(0, 3) if random.random() > 0.6 else 0

        elif distance <= 15:
            # Putting range - should get close to hole
            if handicap <= 5:
                return random.uniform(0, 3)  # Usually within 3 feet
            elif handicap <= 15:
                return random.uniform(0, 5)  # Usually within 5 feet
            else:
                return random.uniform(0, 8)  # Within 8 feet

        elif distance <= 40:
            # Chipping/short pitch range
            skill_factor = max(0.1, 1 - (handicap / 25))

            if lie_type == "green":
                # On green - putting
                if handicap <= 5:
                    return random.uniform(1, 6)
                elif handicap <= 15:
                    return random.uniform(2, 10)
                else:
                    return random.uniform(3, 15)
            else:
                # Chipping from off green
                base_result = random.uniform(2, 12) / skill_factor
                if lie_type == "sand":
                    base_result *= 1.5  # Sand shots are harder
                elif lie_type == "rough":
                    base_result *= 1.2
                return min(base_result, distance * 0.8)

        else:
            # 40-100 yard range - pitch shots
            skill_factor = max(0.2, 1 - (handicap / 30))

            if handicap <= 5:
                target_range = random.uniform(3, 15)  # Get it close
            elif handicap <= 15:
                target_range = random.uniform(5, 25)  # Pretty close
            else:
                target_range = random.uniform(8, 35)  # Somewhere on green

            # Adjust for lie
            if lie_type == "sand":
                target_range *= 1.4
            elif lie_type == "rough":
                target_range *= 1.2

            return min(target_range, distance * 0.9)

    def _determine_lie_type(self, shot_quality: str, distance: float) -> str:
        """
        Determine lie type based on shot quality and distance.
        
        Returns lie type: tee, fairway, rough, sand, green
        """
        if distance <= 20:
            return "green"

        if shot_quality == "excellent":
            return random.choice(["fairway", "fairway", "fairway", "green"])
        elif shot_quality == "good":
            return random.choice(["fairway", "fairway", "green"])
        elif shot_quality == "average":
            return random.choice(["fairway", "rough"])
        elif shot_quality == "poor":
            return random.choice(["rough", "sand"])
        else:  # terrible
            return random.choice(["rough", "sand", "rough"])
