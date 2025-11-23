"""
Monte Carlo simulation engine for Wolf Goat Pig betting odds.
Provides high-accuracy probability calculations through simulation.
"""

import random
import time
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
from .odds_calculator import PlayerState, HoleState, TeamConfiguration


@dataclass
class SimulationParams:
    """Parameters for Monte Carlo simulation"""
    num_simulations: int = 10000
    confidence_level: float = 0.95
    max_simulation_time_ms: float = 30.0  # Max time for simulations
    use_parallel: bool = True
    num_threads: int = 4
    early_stopping_threshold: float = 0.01  # Stop if confidence interval narrow enough


@dataclass
class SimulationResult:
    """Result of Monte Carlo simulation"""
    win_probabilities: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    num_simulations_run: int
    simulation_time_ms: float
    convergence_achieved: bool
    detailed_outcomes: Dict[str, Any]


class MonteCarloEngine:
    """
    Monte Carlo simulation engine for precise probability calculations.
    Uses simulation to handle complex interactions and edge cases.
    """

    def __init__(self, params: Optional[SimulationParams] = None):
        self.params = params or SimulationParams()
        self.random_seed: Optional[int] = None

    def set_seed(self, seed: int) -> None:
        """Set random seed for reproducible results"""
        self.random_seed = seed
        random.seed(seed)
        np.random.seed(seed)

    def simulate_hole_outcomes(
        self,
        players: List[PlayerState],
        hole: HoleState,
        params: Optional[SimulationParams] = None
    ) -> SimulationResult:
        """
        Run Monte Carlo simulation for hole outcomes.
        Returns precise win probabilities with confidence intervals.
        """
        start_time = time.time()
        sim_params = params or self.params
        
        if sim_params.use_parallel and sim_params.num_threads > 1:
            return self._run_parallel_simulation(players, hole, sim_params, start_time)
        else:
            return self._run_sequential_simulation(players, hole, sim_params, start_time)

    def _run_parallel_simulation(
        self,
        players: List[PlayerState],
        hole: HoleState,
        params: SimulationParams,
        start_time: float
    ) -> SimulationResult:
        """Run simulation using parallel threads for better performance"""
        
        sims_per_thread = params.num_simulations // params.num_threads
        remaining_sims = params.num_simulations % params.num_threads
        
        # Track results across all threads
        all_results = []
        
        with ThreadPoolExecutor(max_workers=params.num_threads) as executor:
            futures = []
            
            # Submit simulation tasks
            for thread_id in range(params.num_threads):
                thread_sims = sims_per_thread + (1 if thread_id < remaining_sims else 0)
                future = executor.submit(
                    self._run_simulation_batch,
                    players, hole, thread_sims, thread_id
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                    
                    # Check for early stopping
                    if len(all_results) >= 1000:  # Minimum for statistical validity
                        convergence = self._check_convergence(all_results, params.early_stopping_threshold)
                        if convergence:
                            break
                            
                except Exception as e:
                    print(f"Simulation batch failed: {e}")
                    continue
        
        # Process combined results
        simulation_time = (time.time() - start_time) * 1000
        return self._process_simulation_results(all_results, simulation_time, len(all_results))

    def _run_sequential_simulation(
        self,
        players: List[PlayerState],
        hole: HoleState,
        params: SimulationParams,
        start_time: float
    ) -> SimulationResult:
        """Run simulation sequentially"""
        
        results = self._run_simulation_batch(players, hole, params.num_simulations, 0)
        simulation_time = (time.time() - start_time) * 1000
        
        return self._process_simulation_results(results, simulation_time, len(results))

    def _run_simulation_batch(
        self,
        players: List[PlayerState],
        hole: HoleState,
        num_sims: int,
        thread_id: int
    ) -> List[Dict[str, Any]]:
        """Run a batch of simulations and return results"""
        
        results = []
        
        # Set thread-specific seed
        if self.random_seed is not None:
            np.random.seed(self.random_seed + thread_id)
            random.seed(self.random_seed + thread_id)
        
        for sim_id in range(num_sims):
            # Simulate one complete hole for all players
            hole_result = self._simulate_single_hole(players, hole)
            results.append(hole_result)
            
            # Early exit if taking too long
            if sim_id % 100 == 0 and sim_id > 0:
                # Check if we're taking too long (basic time check)
                pass  # Could add time check here if needed
        
        return results

    def _simulate_single_hole(
        self,
        players: List[PlayerState],
        hole: HoleState
    ) -> Dict[str, Any]:
        """Simulate a single hole completion for all players"""
        
        hole_scores = {}
        shot_details = {}
        
        for player in players:
            score, shots = self._simulate_player_hole(player, hole)
            hole_scores[player.id] = score
            shot_details[player.id] = shots
        
        # Determine winners based on team configuration
        winner_info = self._determine_hole_winner(hole_scores, players, hole)
        
        return {
            "scores": hole_scores,
            "shot_details": shot_details,
            "winner": winner_info["winner"],
            "winning_score": winner_info["winning_score"],
            "team_results": winner_info["team_results"]
        }

    def _simulate_player_hole(
        self,
        player: PlayerState,
        hole: HoleState
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Simulate a single player completing a hole"""
        
        current_distance = player.distance_to_pin if player.distance_to_pin > 0 else self._get_tee_distance(hole)
        current_lie = player.lie_type
        shots_taken = player.shots_taken
        shots_detail = []
        
        # Simulate until hole is completed (max 10 shots to prevent infinite loops)
        max_shots = 10
        while current_distance > 0 and shots_taken < max_shots:
            shots_taken += 1
            
            # Simulate the shot
            shot_result = self._simulate_shot(
                player.handicap,
                current_distance,
                current_lie,
                hole.difficulty_rating,
                hole.weather_factor
            )
            
            shots_detail.append({
                "shot_number": shots_taken,
                "starting_distance": current_distance,
                "starting_lie": current_lie,
                "result": shot_result
            })
            
            # Update position
            current_distance = shot_result["final_distance"]
            current_lie = shot_result["final_lie"]
            
            # Check if hole completed
            if shot_result["holed_out"]:
                break
            
            # Add penalty strokes if applicable
            if shot_result.get("penalty_strokes", 0) > 0:
                shots_taken += shot_result["penalty_strokes"]
        
        return shots_taken, shots_detail

    def _simulate_shot(
        self,
        handicap: float,
        distance: float,
        lie_type: str,
        hole_difficulty: float,
        weather_factor: float
    ) -> Dict[str, Any]:
        """Simulate a single golf shot with realistic outcomes"""
        
        # Base success probability
        success_prob = self._calculate_shot_success_probability(
            handicap, distance, lie_type, hole_difficulty
        )
        
        # Adjust for weather
        success_prob *= weather_factor
        
        # Roll for shot outcome
        roll = random.random()
        
        if roll < success_prob * 0.8:
            # Great shot
            return self._generate_great_shot_outcome(distance, lie_type)
        elif roll < success_prob:
            # Good shot
            return self._generate_good_shot_outcome(distance, lie_type)
        elif roll < success_prob + 0.2:
            # Average shot
            return self._generate_average_shot_outcome(distance, lie_type)
        elif roll < success_prob + 0.4:
            # Poor shot
            return self._generate_poor_shot_outcome(distance, lie_type)
        else:
            # Very poor shot (possible penalty)
            return self._generate_penalty_shot_outcome(distance, lie_type)

    def _calculate_shot_success_probability(
        self,
        handicap: float,
        distance: float,
        lie_type: str,
        hole_difficulty: float
    ) -> float:
        """Calculate base success probability for a shot"""
        
        # Distance-based probability
        if distance <= 3:  # Very short putt
            base_prob = 0.9
        elif distance <= 10:  # Short putt
            base_prob = 0.8
        elif distance <= 30:  # Medium putt/chip
            base_prob = 0.7
        elif distance <= 50:  # Long chip
            base_prob = 0.6
        elif distance <= 100:  # Short approach
            base_prob = 0.5
        elif distance <= 150:  # Medium approach
            base_prob = 0.4
        elif distance <= 200:  # Long approach
            base_prob = 0.3
        else:  # Long shot
            base_prob = 0.25
        
        # Handicap adjustment (lower handicap = better probability)
        hcp_factor = max(0.5, 1.0 - (handicap - 10) * 0.02)
        
        # Lie adjustment
        lie_factors = {
            "green": 1.1,
            "fringe": 1.05,
            "fairway": 1.0,
            "first_cut": 0.95,
            "rough": 0.8,
            "deep_rough": 0.6,
            "bunker": 0.5,
            "trees": 0.3,
            "water": 0.1  # Recovery shot
        }
        lie_factor = lie_factors.get(lie_type, 1.0)
        
        # Hole difficulty adjustment
        difficulty_factor = 1.1 - (hole_difficulty - 3.0) * 0.05
        
        final_prob = base_prob * hcp_factor * lie_factor * difficulty_factor
        return max(0.05, min(0.95, final_prob))

    def _generate_great_shot_outcome(self, distance: float, lie_type: str) -> Dict[str, Any]:
        """Generate outcome for a great shot"""
        if distance <= 5 and lie_type in ["green", "fringe"]:
            # Hole out
            return {
                "holed_out": True,
                "final_distance": 0,
                "final_lie": "hole",
                "quality": "excellent",
                "penalty_strokes": 0
            }
        else:
            # Get very close
            new_distance = max(0, distance * random.uniform(0.1, 0.3))
            new_lie = "green" if distance > 30 else lie_type
            return {
                "holed_out": False,
                "final_distance": new_distance,
                "final_lie": new_lie,
                "quality": "excellent",
                "penalty_strokes": 0
            }

    def _generate_good_shot_outcome(self, distance: float, lie_type: str) -> Dict[str, Any]:
        """Generate outcome for a good shot"""
        new_distance = max(0, distance * random.uniform(0.2, 0.5))
        new_lie = "green" if distance > 50 and new_distance < 30 else lie_type
        
        return {
            "holed_out": new_distance == 0,
            "final_distance": new_distance,
            "final_lie": new_lie,
            "quality": "good",
            "penalty_strokes": 0
        }

    def _generate_average_shot_outcome(self, distance: float, lie_type: str) -> Dict[str, Any]:
        """Generate outcome for an average shot"""
        new_distance = max(0, distance * random.uniform(0.4, 0.7))
        
        # Possible lie change
        if random.random() < 0.2:  # 20% chance of lie change
            new_lie = random.choice(["fairway", "first_cut", "rough"])
        else:
            new_lie = lie_type
        
        return {
            "holed_out": False,
            "final_distance": new_distance,
            "final_lie": new_lie,
            "quality": "average",
            "penalty_strokes": 0
        }

    def _generate_poor_shot_outcome(self, distance: float, lie_type: str) -> Dict[str, Any]:
        """Generate outcome for a poor shot"""
        # Poor shots often don't make much progress
        new_distance = max(distance * 0.6, distance * random.uniform(0.7, 1.1))
        
        # More likely to end up in trouble
        trouble_lies = ["rough", "deep_rough", "bunker"]
        new_lie = random.choice(trouble_lies) if random.random() < 0.4 else lie_type
        
        return {
            "holed_out": False,
            "final_distance": new_distance,
            "final_lie": new_lie,
            "quality": "poor",
            "penalty_strokes": 0
        }

    def _generate_penalty_shot_outcome(self, distance: float, lie_type: str) -> Dict[str, Any]:
        """Generate outcome for a shot that incurs penalty"""
        penalty_prob = 0.1  # 10% chance of penalty
        
        if random.random() < penalty_prob:
            # Penalty stroke (water, OB, etc.)
            new_distance = distance + random.uniform(10, 50)  # Back up
            new_lie = "rough"  # Drop area
            penalty_strokes = 1
        else:
            # Just a very poor shot
            new_distance = distance * random.uniform(0.8, 1.2)
            new_lie = "deep_rough"
            penalty_strokes = 0
        
        return {
            "holed_out": False,
            "final_distance": new_distance,
            "final_lie": new_lie,
            "quality": "very_poor",
            "penalty_strokes": penalty_strokes
        }

    def _get_tee_distance(self, hole: HoleState) -> float:
        """Get typical tee distance for a hole"""
        par_distances = {
            3: random.uniform(120, 180),  # Par 3
            4: random.uniform(350, 420),  # Par 4
            5: random.uniform(480, 550)   # Par 5
        }
        return par_distances.get(hole.par, 400)

    def _determine_hole_winner(
        self,
        hole_scores: Dict[str, int],
        players: List[PlayerState],
        hole: HoleState
    ) -> Dict[str, Any]:
        """Determine winner based on team configuration and scores"""
        
        if hole.teams == TeamConfiguration.SOLO:
            # Captain vs opponents best ball
            captain = next((p for p in players if p.is_captain), None)
            if captain:
                captain_score = hole_scores[captain.id]
                opponent_scores = [hole_scores[p.id] for p in players if not p.is_captain]
                best_opponent_score: Union[int, float] = min(opponent_scores) if opponent_scores else float('inf')

                winning_score: Union[int, float]
                if captain_score < best_opponent_score:
                    winner = "captain"
                    winning_score = captain_score
                elif best_opponent_score < captain_score:
                    winner = "opponents"
                    winning_score = best_opponent_score
                else:
                    winner = "tie"
                    winning_score = captain_score
                
                return {
                    "winner": winner,
                    "winning_score": winning_score,
                    "team_results": {
                        "captain": captain_score,
                        "opponents": best_opponent_score
                    }
                }
        
        elif hole.teams == TeamConfiguration.PARTNERS:
            # Team best ball
            team1_players = [p for p in players if p.team_id == "team1"]
            team2_players = [p for p in players if p.team_id == "team2"]
            
            if team1_players and team2_players:
                team1_score = min(hole_scores[p.id] for p in team1_players)
                team2_score = min(hole_scores[p.id] for p in team2_players)
                
                if team1_score < team2_score:
                    winner = "team1"
                    winning_score = team1_score
                elif team2_score < team1_score:
                    winner = "team2"
                    winning_score = team2_score
                else:
                    winner = "tie"
                    winning_score = team1_score
                
                return {
                    "winner": winner,
                    "winning_score": winning_score,
                    "team_results": {
                        "team1": team1_score,
                        "team2": team2_score
                    }
                }
        
        # Individual play or pending teams
        best_score = min(hole_scores.values())
        winners = [pid for pid, score in hole_scores.items() if score == best_score]
        
        return {
            "winner": winners[0] if len(winners) == 1 else "tie",
            "winning_score": best_score,
            "team_results": hole_scores
        }

    def _process_simulation_results(
        self,
        results: List[Dict[str, Any]],
        simulation_time: float,
        num_simulations: int
    ) -> SimulationResult:
        """Process simulation results and calculate statistics"""
        
        if not results:
            return SimulationResult(
                win_probabilities={},
                confidence_intervals={},
                num_simulations_run=0,
                simulation_time_ms=simulation_time,
                convergence_achieved=False,
                detailed_outcomes={}
            )
        
        # Count wins by player/team
        win_counts: Dict[str, int] = {}
        all_winners = []
        
        for result in results:
            winner = result["winner"]
            all_winners.append(winner)
            if winner != "tie":
                win_counts[winner] = win_counts.get(winner, 0) + 1
        
        # Calculate win probabilities
        total_simulations = len(results)
        win_probabilities = {}
        confidence_intervals = {}
        
        for winner_id in win_counts:
            wins = win_counts[winner_id]
            prob = wins / total_simulations
            win_probabilities[winner_id] = prob
            
            # Calculate 95% confidence interval using normal approximation
            if total_simulations > 30:  # Normal approximation valid
                margin_error = 1.96 * np.sqrt(prob * (1 - prob) / total_simulations)
                ci_lower = max(0, prob - margin_error)
                ci_upper = min(1, prob + margin_error)
                confidence_intervals[winner_id] = (ci_lower, ci_upper)
            else:
                confidence_intervals[winner_id] = (0, 1)  # Wide interval for small samples
        
        # Check convergence
        convergence = self._check_convergence_by_ci(confidence_intervals)
        
        # Detailed outcomes
        detailed_outcomes = {
            "score_distributions": self._calculate_score_distributions(results),
            "average_scores": self._calculate_average_scores(results),
            "tie_rate": all_winners.count("tie") / total_simulations,
            "simulation_metadata": {
                "total_simulations": total_simulations,
                "unique_winners": list(set(all_winners))
            }
        }
        
        return SimulationResult(
            win_probabilities=win_probabilities,
            confidence_intervals=confidence_intervals,
            num_simulations_run=num_simulations,
            simulation_time_ms=simulation_time,
            convergence_achieved=convergence,
            detailed_outcomes=detailed_outcomes
        )

    def _check_convergence(self, results: List[Dict[str, Any]], threshold: float) -> bool:
        """Check if simulation has converged"""
        if len(results) < 100:
            return False
        
        # Check last 100 vs previous 100 for stability
        recent_winners = [r["winner"] for r in results[-100:]]
        previous_winners = [r["winner"] for r in results[-200:-100]] if len(results) >= 200 else []
        
        if not previous_winners:
            return False
        
        # Calculate win rates for both periods
        recent_counts: Dict[str, int] = {}
        previous_counts: Dict[str, int] = {}
        
        for winner in recent_winners:
            recent_counts[winner] = recent_counts.get(winner, 0) + 1
        
        for winner in previous_winners:
            previous_counts[winner] = previous_counts.get(winner, 0) + 1
        
        # Check if win rates are stable
        max_difference: float = 0.0
        all_winners = set(recent_counts.keys()) | set(previous_counts.keys())
        
        for winner in all_winners:
            recent_rate = recent_counts.get(winner, 0) / len(recent_winners)
            previous_rate = previous_counts.get(winner, 0) / len(previous_winners)
            difference = abs(recent_rate - previous_rate)
            max_difference = max(max_difference, difference)
        
        return max_difference < threshold

    def _check_convergence_by_ci(self, confidence_intervals: Dict[str, Tuple[float, float]]) -> bool:
        """Check convergence based on confidence interval width"""
        if not confidence_intervals:
            return False
        
        # Consider converged if all confidence intervals are narrow enough
        max_ci_width: float = 0.0
        for ci_lower, ci_upper in confidence_intervals.values():
            width = ci_upper - ci_lower
            max_ci_width = max(max_ci_width, width)
        
        return max_ci_width < 0.1  # 10% maximum CI width

    def _calculate_score_distributions(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Calculate score distribution for each player"""
        player_scores: Dict[str, List[int]] = {}

        for result in results:
            for player_id, score in result["scores"].items():
                if player_id not in player_scores:
                    player_scores[player_id] = []
                player_scores[player_id].append(score)

        distributions = {}
        for player_id, scores in player_scores.items():
            score_counts: Dict[str, int] = {}
            for score in scores:
                score_counts[str(score)] = score_counts.get(str(score), 0) + 1
            
            total = len(scores)
            distributions[player_id] = {
                score: count / total for score, count in score_counts.items()
            }
        
        return distributions

    def _calculate_average_scores(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate average scores for each player"""
        player_scores: Dict[str, List[int]] = {}
        
        for result in results:
            for player_id, score in result["scores"].items():
                if player_id not in player_scores:
                    player_scores[player_id] = []
                player_scores[player_id].append(score)
        
        return {
            player_id: statistics.mean(scores)
            for player_id, scores in player_scores.items()
        }


# Factory function for easy integration
def run_monte_carlo_simulation(
    players: List[PlayerState],
    hole: HoleState,
    num_simulations: int = 5000,
    max_time_ms: float = 30.0
) -> SimulationResult:
    """
    Factory function to run Monte Carlo simulation with default parameters.
    Optimized for real-time use with time constraints.
    """
    params = SimulationParams(
        num_simulations=num_simulations,
        max_simulation_time_ms=max_time_ms,
        use_parallel=True,
        num_threads=min(4, num_simulations // 1000 + 1)
    )
    
    engine = MonteCarloEngine(params)
    return engine.simulate_hole_outcomes(players, hole, params)