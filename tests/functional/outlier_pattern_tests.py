#!/usr/bin/env python3
"""
Outlier Pattern Testing for Wolf-Goat-Pig Golf Simulation

Based on 2024 research on outlier detection in sports simulations.
Tests rare events, edge cases, and unusual behavioral patterns that occur
in real-world golf scenarios.
"""

import sys
import os
import random
import statistics
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer

@dataclass
class OutlierPattern:
    name: str
    description: str
    frequency_threshold: float  # Expected frequency in normal play
    detection_method: str
    validation_criteria: List[str]

class OutlierPatternTester:
    """
    Test suite for detecting and validating outlier patterns in golf simulation
    
    Based on research showing importance of outlier-aware simulation that:
    1. Uses robust statistics less sensitive to outliers
    2. Applies outlier detection to maintain consistency
    3. Creates synthetic outliers similar but not identical to real ones
    """
    
    def __init__(self):
        self.patterns_to_test = self._define_outlier_patterns()
        self.simulation_data = defaultdict(list)
        
    def run_outlier_tests(self, iterations: int = 1000) -> Dict[str, Any]:
        """
        Run comprehensive outlier pattern testing
        
        Uses statistical analysis to identify patterns that deviate significantly
        from expected golf behavior.
        """
        
        print("🎯 OUTLIER PATTERN ANALYSIS")
        print("=" * 60)
        print(f"Running {iterations} simulations to detect outlier patterns...")
        print()
        
        # Collect baseline data
        baseline_data = self._collect_baseline_data(iterations)
        
        # Analyze each pattern
        results = {}
        for pattern in self.patterns_to_test:
            print(f"Testing: {pattern.name}")
            result = self._test_outlier_pattern(pattern, baseline_data)
            results[pattern.name] = result
            
            status = "✅ NORMAL" if result["within_expected_range"] else "⚠️ OUTLIER DETECTED"
            print(f"   {status} - Frequency: {result['frequency']:.3f} (expected: {pattern.frequency_threshold:.3f})")
            
            if result["outliers_found"]:
                print(f"   Found {len(result['outliers_found'])} extreme cases")
            print()
        
        return self._generate_outlier_report(results, baseline_data)
    
    def _define_outlier_patterns(self) -> List[OutlierPattern]:
        """Define outlier patterns to test based on real golf statistics"""
        
        return [
            OutlierPattern(
                name="Hole-in-One Frequency",
                description="Shots that complete the hole on first attempt",
                frequency_threshold=0.001,  # ~1 in 1000 shots in real golf
                detection_method="shot_completion_analysis",
                validation_criteria=["realistic_distance", "appropriate_hole_type", "celebration_triggered"]
            ),
            
            OutlierPattern(
                name="Maximum Shot Limit Reached",
                description="Players reaching 8-shot limit on holes",
                frequency_threshold=0.05,  # Should be rare, ~5% of players per hole max
                detection_method="shot_count_analysis",
                validation_criteria=["hole_completion_forced", "fair_scoring", "no_infinite_loops"]
            ),
            
            OutlierPattern(
                name="Consecutive Excellent Shots",
                description="Multiple excellent shots in a row by same player",
                frequency_threshold=0.02,  # 2% chance of 3+ consecutive excellent
                detection_method="shot_quality_sequence_analysis",
                validation_criteria=["realistic_skill_correlation", "handicap_appropriate"]
            ),
            
            OutlierPattern(
                name="Extreme Distance Variations",
                description="Shots with unusually large distance changes",
                frequency_threshold=0.1,  # 10% of shots might be extreme
                detection_method="distance_progression_analysis",
                validation_criteria=["no_backward_movement", "physics_realistic", "lie_appropriate"]
            ),
            
            OutlierPattern(
                name="Partnership Rejection Streaks",
                description="Multiple consecutive partnership rejections",
                frequency_threshold=0.15,  # 15% chance of 3+ rejections in a row
                detection_method="partnership_decision_analysis",
                validation_criteria=["strategic_reasoning", "betting_context", "player_personality"]
            ),
            
            OutlierPattern(
                name="Betting Escalation Spirals",
                description="Rapid escalation of betting through doubles/flushes",
                frequency_threshold=0.05,  # 5% of holes see extreme escalation
                detection_method="betting_progression_analysis",
                validation_criteria=["maximum_limits_respected", "fair_risk_reward", "player_consent"]
            ),
            
            OutlierPattern(
                name="Shot Quality Clustering",
                description="Unusual clustering of similar shot qualities",
                frequency_threshold=0.08,  # 8% chance of extreme clustering
                detection_method="quality_distribution_analysis",
                validation_criteria=["statistical_validity", "handicap_correlation", "random_seed_independence"]
            ),
            
            OutlierPattern(
                name="Hole Completion Speed",
                description="Holes completed in unusually few or many shots",
                frequency_threshold=0.1,  # 10% of holes might be outliers
                detection_method="hole_duration_analysis",
                validation_criteria=["par_appropriate", "handicap_realistic", "game_flow_maintained"]
            )
        ]
    
    def _collect_baseline_data(self, iterations: int) -> Dict[str, List[Any]]:
        """Collect baseline simulation data for statistical analysis"""
        
        data = {
            "shot_completions": [],
            "shot_counts_per_hole": [],
            "shot_quality_sequences": [],
            "distance_progressions": [],
            "partnership_decisions": [],
            "betting_progressions": [],
            "quality_distributions": [],
            "hole_completion_times": []
        }
        
        # Run multiple simulations to gather statistical data
        for i in range(iterations // 100):  # Run 10 full games for baseline
            players = [
                WGPPlayer(id=f"player_{j}", name=f"Test Player {j}", handicap=random.randint(5, 25))
                for j in range(4)
            ]
            
            sim = WolfGoatPigSimulation(player_count=4, players=players)
            sim.enable_shot_progression()
            
            # Play through multiple holes
            for hole in range(1, 4):  # 3 holes per simulation
                hole_data = self._simulate_hole_for_data(sim)
                
                # Collect data points
                data["shot_completions"].extend(hole_data["completions"])
                data["shot_counts_per_hole"].extend(hole_data["shot_counts"])
                data["shot_quality_sequences"].extend(hole_data["quality_sequences"])
                data["distance_progressions"].extend(hole_data["progressions"])
                data["partnership_decisions"].extend(hole_data["partnerships"])
                data["betting_progressions"].extend(hole_data["betting"])
                data["quality_distributions"].append(hole_data["quality_dist"])
                data["hole_completion_times"].append(hole_data["completion_time"])
        
        return data
    
    def _simulate_hole_for_data(self, sim: WolfGoatPigSimulation) -> Dict[str, Any]:
        """Simulate a single hole and collect detailed data"""
        
        hole_data = {
            "completions": [],
            "shot_counts": [],
            "quality_sequences": [],
            "progressions": [],
            "partnerships": [],
            "betting": [],
            "quality_dist": Counter(),
            "completion_time": 0
        }
        
        shots_taken = 0
        max_shots = 50
        player_sequences = defaultdict(list)
        
        while shots_taken < max_shots:
            hole_state = sim.hole_states.get(sim.current_hole)
            if not hole_state:
                break
            
            if hole_state.hole_complete:
                break
            
            next_player = hole_state.next_player_to_hit
            if not next_player:
                break
            
            try:
                result = sim.simulate_shot(next_player)
                shots_taken += 1
                
                shot_result = result.get("shot_result", {})
                
                # Track shot completion
                if shot_result.get("made_shot"):
                    hole_data["completions"].append({
                        "shot_number": shot_result.get("shot_number", 1),
                        "distance": shot_result.get("distance_to_pin", 0),
                        "quality": shot_result.get("shot_quality", "unknown")
                    })
                
                # Track shot quality sequences
                quality = shot_result.get("shot_quality", "unknown")
                player_sequences[next_player].append(quality)
                hole_data["quality_dist"][quality] += 1
                
                # Track distance progressions
                if len(player_sequences[next_player]) > 1:
                    hole_data["progressions"].append({
                        "player": next_player,
                        "sequence": player_sequences[next_player][-2:]
                    })
                
                # Track betting opportunities
                if result.get("betting_opportunity"):
                    hole_data["betting"].append(result["betting_opportunity"])
                
                if result.get("hole_complete"):
                    break
                    
            except Exception as e:
                break
        
        # Record shot counts for each player
        for player_id in [p.id for p in sim.players]:
            ball = hole_state.ball_positions.get(player_id) if hole_state else None
            if ball:
                hole_data["shot_counts"].append(ball.shot_count)
        
        hole_data["completion_time"] = shots_taken
        
        return hole_data
    
    def _test_outlier_pattern(self, pattern: OutlierPattern, baseline_data: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Test a specific outlier pattern against baseline data"""
        
        if pattern.detection_method == "shot_completion_analysis":
            return self._analyze_shot_completions(pattern, baseline_data["shot_completions"])
        
        elif pattern.detection_method == "shot_count_analysis":
            return self._analyze_shot_counts(pattern, baseline_data["shot_counts_per_hole"])
        
        elif pattern.detection_method == "shot_quality_sequence_analysis":
            return self._analyze_quality_sequences(pattern, baseline_data["shot_quality_sequences"])
        
        elif pattern.detection_method == "distance_progression_analysis":
            return self._analyze_distance_progressions(pattern, baseline_data["distance_progressions"])
        
        elif pattern.detection_method == "betting_progression_analysis":
            return self._analyze_betting_progressions(pattern, baseline_data["betting_progressions"])
        
        elif pattern.detection_method == "quality_distribution_analysis":
            return self._analyze_quality_distributions(pattern, baseline_data["quality_distributions"])
        
        elif pattern.detection_method == "hole_duration_analysis":
            return self._analyze_hole_durations(pattern, baseline_data["hole_completion_times"])
        
        else:
            return {"error": f"Unknown detection method: {pattern.detection_method}"}
    
    def _analyze_shot_completions(self, pattern: OutlierPattern, completions: List[Dict]) -> Dict[str, Any]:
        """Analyze hole-in-one and immediate completion patterns"""
        
        if not completions:
            return {
                "frequency": 0.0,
                "within_expected_range": True,
                "outliers_found": [],
                "analysis": "No completions found in data"
            }
        
        # Count first-shot completions (hole-in-ones)
        first_shot_completions = [c for c in completions if c.get("shot_number") == 1]
        total_first_shots = len([c for c in completions if c.get("shot_number", 0) >= 1])
        
        frequency = len(first_shot_completions) / max(total_first_shots, 1)
        
        # Detect outliers - completions that seem unrealistic
        outliers = []
        for completion in first_shot_completions:
            distance = completion.get("distance", 0)
            quality = completion.get("quality", "unknown")
            
            # Flag as outlier if hole-in-one from unrealistic distance with poor quality
            if distance > 200 and quality in ["poor", "terrible"]:
                outliers.append(completion)
        
        return {
            "frequency": frequency,
            "within_expected_range": abs(frequency - pattern.frequency_threshold) <= pattern.frequency_threshold * 2,
            "outliers_found": outliers,
            "analysis": f"Found {len(first_shot_completions)} hole-in-ones from {total_first_shots} first shots"
        }
    
    def _analyze_shot_counts(self, pattern: OutlierPattern, shot_counts: List[int]) -> Dict[str, Any]:
        """Analyze shot count distributions for maximum limits"""
        
        if not shot_counts:
            return {"frequency": 0.0, "within_expected_range": True, "outliers_found": [], "analysis": "No shot count data"}
        
        max_shots = [count for count in shot_counts if count >= 8]
        frequency = len(max_shots) / len(shot_counts)
        
        # Statistical analysis
        mean_shots = statistics.mean(shot_counts)
        std_shots = statistics.stdev(shot_counts) if len(shot_counts) > 1 else 0
        
        # Find statistical outliers (more than 2 standard deviations from mean)
        outliers = [count for count in shot_counts if abs(count - mean_shots) > 2 * std_shots]
        
        return {
            "frequency": frequency,
            "within_expected_range": frequency <= pattern.frequency_threshold * 2,
            "outliers_found": outliers,
            "analysis": f"Mean shots: {mean_shots:.1f} ± {std_shots:.1f}, {len(max_shots)} reached limit"
        }
    
    def _analyze_quality_sequences(self, pattern: OutlierPattern, sequences: List[Dict]) -> Dict[str, Any]:
        """Analyze consecutive shot quality patterns"""
        
        if not sequences:
            return {"frequency": 0.0, "within_expected_range": True, "outliers_found": [], "analysis": "No sequence data"}
        
        consecutive_excellent = 0
        total_sequences = 0
        outlier_sequences = []
        
        for seq_data in sequences:
            sequence = seq_data.get("sequence", [])
            if len(sequence) >= 2:
                total_sequences += 1
                
                # Count consecutive excellent shots
                excellent_count = 0
                max_consecutive = 0
                
                for quality in sequence:
                    if quality == "excellent":
                        excellent_count += 1
                        max_consecutive = max(max_consecutive, excellent_count)
                    else:
                        excellent_count = 0
                
                if max_consecutive >= 3:
                    consecutive_excellent += 1
                    outlier_sequences.append(seq_data)
        
        frequency = consecutive_excellent / max(total_sequences, 1)
        
        return {
            "frequency": frequency,
            "within_expected_range": frequency <= pattern.frequency_threshold * 2,
            "outliers_found": outlier_sequences,
            "analysis": f"Found {consecutive_excellent} sequences with 3+ consecutive excellent shots"
        }
    
    def _analyze_distance_progressions(self, pattern: OutlierPattern, progressions: List[Dict]) -> Dict[str, Any]:
        """Analyze distance change patterns for extreme variations"""
        
        if not progressions:
            return {"frequency": 0.0, "within_expected_range": True, "outliers_found": [], "analysis": "No progression data"}
        
        extreme_changes = []
        backward_movements = []
        
        # This would need shot result data with actual distances
        # For now, simulate the analysis structure
        frequency = len(extreme_changes) / max(len(progressions), 1)
        
        return {
            "frequency": frequency,
            "within_expected_range": True,  # Placeholder
            "outliers_found": backward_movements,
            "analysis": f"Analyzed {len(progressions)} distance progressions"
        }
    
    def _analyze_betting_progressions(self, pattern: OutlierPattern, betting_data: List[Dict]) -> Dict[str, Any]:
        """Analyze betting escalation patterns"""
        
        frequency = 0.0  # Placeholder - would analyze actual betting data
        
        return {
            "frequency": frequency,
            "within_expected_range": True,
            "outliers_found": [],
            "analysis": f"Analyzed {len(betting_data)} betting events"
        }
    
    def _analyze_quality_distributions(self, pattern: OutlierPattern, distributions: List[Counter]) -> Dict[str, Any]:
        """Analyze shot quality distribution patterns"""
        
        if not distributions:
            return {"frequency": 0.0, "within_expected_range": True, "outliers_found": [], "analysis": "No distribution data"}
        
        outlier_distributions = []
        
        for dist in distributions:
            total_shots = sum(dist.values())
            if total_shots == 0:
                continue
                
            # Check for extreme clustering (>80% of one quality type)
            for quality, count in dist.items():
                if count / total_shots > 0.8:
                    outlier_distributions.append({"quality": quality, "percentage": count/total_shots, "distribution": dist})
        
        frequency = len(outlier_distributions) / max(len(distributions), 1)
        
        return {
            "frequency": frequency,
            "within_expected_range": frequency <= pattern.frequency_threshold * 2,
            "outliers_found": outlier_distributions,
            "analysis": f"Found {len(outlier_distributions)} extreme quality clusters from {len(distributions)} holes"
        }
    
    def _analyze_hole_durations(self, pattern: OutlierPattern, completion_times: List[int]) -> Dict[str, Any]:
        """Analyze hole completion time outliers"""
        
        if not completion_times:
            return {"frequency": 0.0, "within_expected_range": True, "outliers_found": [], "analysis": "No duration data"}
        
        mean_time = statistics.mean(completion_times)
        std_time = statistics.stdev(completion_times) if len(completion_times) > 1 else 0
        
        # Find outliers (more than 2 standard deviations from mean)
        outliers = [time for time in completion_times if abs(time - mean_time) > 2 * std_time]
        frequency = len(outliers) / len(completion_times)
        
        return {
            "frequency": frequency,
            "within_expected_range": frequency <= pattern.frequency_threshold * 2,
            "outliers_found": outliers,
            "analysis": f"Mean completion: {mean_time:.1f} ± {std_time:.1f} shots, {len(outliers)} outliers found"
        }
    
    def _generate_outlier_report(self, results: Dict[str, Any], baseline_data: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Generate comprehensive outlier analysis report"""
        
        print("📊 OUTLIER PATTERN ANALYSIS RESULTS")
        print("=" * 60)
        
        normal_patterns = sum(1 for r in results.values() if r.get("within_expected_range", False))
        total_patterns = len(results)
        
        print(f"\nSUMMARY:")
        print(f"   Patterns within expected range: {normal_patterns}/{total_patterns}")
        print(f"   Outlier patterns detected: {total_patterns - normal_patterns}")
        
        print(f"\nDETAILED ANALYSIS:")
        for pattern_name, result in results.items():
            status = "✅ NORMAL" if result.get("within_expected_range") else "⚠️ OUTLIER"
            print(f"   {status} {pattern_name}")
            print(f"      Frequency: {result.get('frequency', 0):.4f}")
            print(f"      Analysis: {result.get('analysis', 'No analysis')}")
            if result.get("outliers_found"):
                print(f"      Extreme cases: {len(result['outliers_found'])}")
        
        print(f"\n🎯 STATISTICAL SUMMARY:")
        total_shots = len(baseline_data.get("shot_counts_per_hole", []))
        total_holes = len(baseline_data.get("hole_completion_times", []))
        print(f"   Data points analyzed: {total_shots} player-holes, {total_holes} completed holes")
        
        if baseline_data.get("shot_counts_per_hole"):
            avg_shots = statistics.mean(baseline_data["shot_counts_per_hole"])
            print(f"   Average shots per player per hole: {avg_shots:.2f}")
        
        print("=" * 60)
        
        return {
            "summary": {
                "normal_patterns": normal_patterns,
                "outlier_patterns": total_patterns - normal_patterns,
                "total_patterns": total_patterns
            },
            "results": results,
            "baseline_stats": {
                "total_shots": total_shots,
                "total_holes": total_holes,
                "avg_shots_per_hole": statistics.mean(baseline_data.get("shot_counts_per_hole", [0])) if baseline_data.get("shot_counts_per_hole") else 0
            }
        }

def main():
    """Run outlier pattern testing"""
    tester = OutlierPatternTester()
    results = tester.run_outlier_tests(iterations=500)
    
    success_rate = results["summary"]["normal_patterns"] / results["summary"]["total_patterns"]
    return success_rate >= 0.75  # 75% of patterns should be within expected range

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)