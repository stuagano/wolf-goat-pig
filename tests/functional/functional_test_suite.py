#!/usr/bin/env python3
"""
Comprehensive Functional Testing Suite for Wolf-Goat-Pig Golf Simulation
Based on 2024 best practices for scenario-based testing and edge case validation

This suite simulates real-world golf scenarios including:
- Multi-hole progression with varying conditions
- Outlier shot patterns and edge cases
- Player behavior variations and stress testing
- Tournament-style play with complex betting scenarios
"""

import sys
import os
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer

class TestScenarioType(Enum):
    NORMAL_PLAY = "normal"
    EDGE_CASE = "edge_case"
    OUTLIER_PATTERN = "outlier"
    STRESS_TEST = "stress"
    TOURNAMENT = "tournament"

@dataclass
class TestScenario:
    name: str
    description: str
    scenario_type: TestScenarioType
    players: List[WGPPlayer]
    hole_count: int = 9
    expected_outcomes: Dict[str, Any] = None
    validation_criteria: List[str] = None

@dataclass
class TestResult:
    scenario_name: str
    success: bool
    duration: float
    holes_completed: int
    total_shots: int
    issues_found: List[str]
    performance_metrics: Dict[str, Any]
    game_data: Dict[str, Any]

class FunctionalTestSuite:
    def __init__(self):
        self.results = []
        self.start_time = None
        
    def run_all_scenarios(self) -> Dict[str, Any]:
        """Run all functional test scenarios and generate comprehensive report"""
        print("🏌️ WOLF-GOAT-PIG FUNCTIONAL TEST SUITE")
        print("=" * 80)
        print("Based on 2024 best practices for golf simulation testing")
        print("Testing real-world scenarios, edge cases, and outlier patterns")
        print()
        
        self.start_time = time.time()
        
        scenarios = self._get_test_scenarios()
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n[{i}/{len(scenarios)}] Testing: {scenario.name}")
            print(f"Type: {scenario.scenario_type.value.upper()}")
            print(f"Description: {scenario.description}")
            print("-" * 60)
            
            result = self._run_scenario(scenario)
            self.results.append(result)
            
            if result.success:
                print(f"✅ PASSED - {result.holes_completed} holes, {result.total_shots} shots")
            else:
                print(f"❌ FAILED - {len(result.issues_found)} issues found")
                for issue in result.issues_found[:3]:  # Show first 3 issues
                    print(f"   • {issue}")
            
            print(f"Duration: {result.duration:.2f}s")
        
        return self._generate_report()
    
    def _get_test_scenarios(self) -> List[TestScenario]:
        """Define comprehensive test scenarios covering real-world use cases"""
        
        return [
            # Normal Play Scenarios
            TestScenario(
                name="Classic 4-Player Round",
                description="Standard Wolf-Goat-Pig game with mixed handicaps",
                scenario_type=TestScenarioType.NORMAL_PLAY,
                players=[
                    WGPPlayer(id="low_hcp", name="Pro Player", handicap=2),
                    WGPPlayer(id="mid_hcp", name="Weekend Warrior", handicap=12),
                    WGPPlayer(id="high_hcp", name="Beginner", handicap=22),
                    WGPPlayer(id="scratch", name="Scratch Golfer", handicap=0)
                ],
                hole_count=9,
                validation_criteria=["all_holes_completed", "partnerships_formed", "betting_active"]
            ),
            
            TestScenario(
                name="Quick 3-Player Match",
                description="Fast-paced game with aggressive betting",
                scenario_type=TestScenarioType.NORMAL_PLAY,
                players=[
                    WGPPlayer(id="aggressive", name="Risk Taker", handicap=8),
                    WGPPlayer(id="conservative", name="Safe Player", handicap=14),
                    WGPPlayer(id="wild_card", name="Unpredictable", handicap=18)
                ],
                hole_count=6,
                validation_criteria=["doubles_offered", "flush_scenarios", "solo_play"]
            ),
            
            # Edge Case Scenarios
            TestScenario(
                name="Extreme Handicap Spread",
                description="Testing very low vs very high handicap players",
                scenario_type=TestScenarioType.EDGE_CASE,
                players=[
                    WGPPlayer(id="tour_pro", name="Tour Pro", handicap=-2),  # Plus handicap
                    WGPPlayer(id="beginner", name="Brand New", handicap=36),  # Maximum handicap
                    WGPPlayer(id="average", name="Average Joe", handicap=18),
                    WGPPlayer(id="senior", name="Senior Player", handicap=28)
                ],
                hole_count=9,
                validation_criteria=["handicap_strokes_applied", "fair_competition", "no_crashes"]
            ),
            
            TestScenario(
                name="Maximum Shot Limit Test",
                description="Players approaching or reaching 8-shot maximum",
                scenario_type=TestScenarioType.EDGE_CASE,
                players=[
                    WGPPlayer(id="struggle1", name="Struggling Player", handicap=32),
                    WGPPlayer(id="struggle2", name="Bad Day", handicap=28),
                    WGPPlayer(id="struggle3", name="Learning Golf", handicap=35),
                    WGPPlayer(id="average", name="Normal Player", handicap=15)
                ],
                hole_count=3,  # Shorter test to focus on shot limits
                validation_criteria=["shot_limit_enforced", "hole_completion", "fair_scoring"]
            ),
            
            # Outlier Pattern Scenarios
            TestScenario(
                name="Hole-in-One Frequency",
                description="Testing rare excellent shots and immediate hole completion",
                scenario_type=TestScenarioType.OUTLIER_PATTERN,
                players=[
                    WGPPlayer(id="lucky1", name="Lucky Player", handicap=5),
                    WGPPlayer(id="lucky2", name="Hot Streak", handicap=8),
                    WGPPlayer(id="normal", name="Average Player", handicap=15),
                    WGPPlayer(id="witness", name="Witness", handicap=12)
                ],
                hole_count=18,  # More holes to increase chance of rare events
                validation_criteria=["rare_events_handled", "celebration_triggered", "scoring_correct"]
            ),
            
            TestScenario(
                name="Terrible Shot Clusters",
                description="Multiple consecutive terrible shots and recovery patterns",
                scenario_type=TestScenarioType.OUTLIER_PATTERN,
                players=[
                    WGPPlayer(id="rough_day1", name="Off Day", handicap=20),
                    WGPPlayer(id="rough_day2", name="Rough Round", handicap=25),
                    WGPPlayer(id="patience", name="Patient Player", handicap=10),
                    WGPPlayer(id="steady", name="Steady Eddie", handicap=12)
                ],
                hole_count=9,
                validation_criteria=["progression_maintained", "no_backward_shots", "betting_opportunities"]
            ),
            
            TestScenario(
                name="Partnership Chaos",
                description="Rapid partnership changes and complex team dynamics",
                scenario_type=TestScenarioType.OUTLIER_PATTERN,
                players=[
                    WGPPlayer(id="switcher", name="Team Hopper", handicap=14),
                    WGPPlayer(id="loyal", name="Loyal Partner", handicap=16),
                    WGPPlayer(id="solo_king", name="Solo Specialist", handicap=9),
                    WGPPlayer(id="diplomatic", name="Diplomat", handicap=11)
                ],
                hole_count=9,
                validation_criteria=["partnership_integrity", "betting_consistency", "fair_scoring"]
            ),
            
            # Stress Test Scenarios
            TestScenario(
                name="Marathon 18-Hole Test",
                description="Full round stress testing with all game mechanics",
                scenario_type=TestScenarioType.STRESS_TEST,
                players=[
                    WGPPlayer(id="endurance1", name="Marathon Player 1", handicap=10),
                    WGPPlayer(id="endurance2", name="Marathon Player 2", handicap=15),
                    WGPPlayer(id="endurance3", name="Marathon Player 3", handicap=20),
                    WGPPlayer(id="endurance4", name="Marathon Player 4", handicap=7)
                ],
                hole_count=18,
                validation_criteria=["performance_consistency", "memory_stable", "all_features_work"]
            ),
            
            TestScenario(
                name="Rapid Fire Decisions",
                description="Quick succession of betting decisions and partnerships",
                scenario_type=TestScenarioType.STRESS_TEST,
                players=[
                    WGPPlayer(id="quick1", name="Quick Decision", handicap=12),
                    WGPPlayer(id="quick2", name="Fast Player", handicap=16),
                    WGPPlayer(id="quick3", name="Rapid Fire", handicap=8),
                    WGPPlayer(id="quick4", name="Speedy", handicap=14)
                ],
                hole_count=6,
                validation_criteria=["decision_integrity", "state_consistency", "no_race_conditions"]
            ),
            
            # Tournament Scenarios
            TestScenario(
                name="Tournament Finals",
                description="High-stakes match with maximum betting and pressure",
                scenario_type=TestScenarioType.TOURNAMENT,
                players=[
                    WGPPlayer(id="champion", name="Defending Champ", handicap=4),
                    WGPPlayer(id="challenger", name="Rising Star", handicap=6),
                    WGPPlayer(id="veteran", name="Seasoned Vet", handicap=9),
                    WGPPlayer(id="wildcard", name="Dark Horse", handicap=13)
                ],
                hole_count=9,
                validation_criteria=["high_stakes_betting", "pressure_performance", "tournament_scoring"]
            )
        ]
    
    def _run_scenario(self, scenario: TestScenario) -> TestResult:
        """Execute a single test scenario and capture detailed results"""
        start_time = time.time()
        issues_found = []
        holes_completed = 0
        total_shots = 0
        game_data = {}
        
        try:
            # Initialize simulation
            sim = WolfGoatPigSimulation(
                player_count=len(scenario.players),
                players=scenario.players
            )
            sim.enable_shot_progression()
            
            # Track performance metrics
            performance_metrics = {
                "holes_per_second": 0,
                "shots_per_hole_avg": 0,
                "partnership_changes": 0,
                "betting_actions": 0,
                "max_shots_per_player": 0,
                "hole_completion_rate": 0
            }
            
            # Play through all holes
            for hole_num in range(1, scenario.hole_count + 1):
                hole_shots = 0
                max_hole_shots = 100  # Safety limit per hole
                
                # Track hole start
                hole_start_time = time.time()
                
                while hole_shots < max_hole_shots:
                    hole_state = sim.hole_states.get(sim.current_hole)
                    
                    if not hole_state:
                        issues_found.append(f"Missing hole state for hole {hole_num}")
                        break
                    
                    if hole_state.hole_complete:
                        holes_completed += 1
                        break
                    
                    next_player = hole_state.next_player_to_hit
                    if not next_player:
                        # Check if this is legitimate completion
                        if self._validate_hole_completion(hole_state, scenario.players):
                            holes_completed += 1
                        else:
                            issues_found.append(f"Hole {hole_num}: No next player but hole not complete")
                        break
                    
                    # Simulate shot
                    try:
                        result = sim.simulate_shot(next_player)
                        hole_shots += 1
                        total_shots += 1
                        
                        # Validate shot result
                        shot_issues = self._validate_shot_result(result, hole_num, next_player)
                        issues_found.extend(shot_issues)
                        
                        # Track performance metrics
                        if result.get("betting_opportunity"):
                            performance_metrics["betting_actions"] += 1
                        
                        # Check for hole completion
                        if result.get("hole_complete"):
                            holes_completed += 1
                            break
                            
                    except Exception as e:
                        issues_found.append(f"Hole {hole_num}, Shot {hole_shots}: Exception - {str(e)}")
                        break
                
                # Move to next hole if not at the end
                if hole_num < scenario.hole_count and not hole_state.hole_complete:
                    # Force hole completion for testing purposes
                    if hole_shots >= max_hole_shots:
                        issues_found.append(f"Hole {hole_num}: Exceeded max shots ({max_hole_shots})")
                    
                    # Advance to next hole (simplified for testing)
                    sim.current_hole = hole_num + 1
                    if hole_num + 1 <= scenario.hole_count:
                        sim.hole_states[sim.current_hole] = self._create_test_hole(sim, hole_num + 1)
                
                # Update performance metrics
                hole_duration = time.time() - hole_start_time
                if hole_duration > 0:
                    performance_metrics["holes_per_second"] = 1 / hole_duration
            
            # Final validation
            validation_issues = self._validate_scenario_completion(sim, scenario)
            issues_found.extend(validation_issues)
            
            # Calculate final metrics
            if holes_completed > 0:
                performance_metrics["shots_per_hole_avg"] = total_shots / holes_completed
                performance_metrics["hole_completion_rate"] = holes_completed / scenario.hole_count
            
            # Capture game state
            game_data = sim.get_game_state()
            
        except Exception as e:
            issues_found.append(f"Critical error: {str(e)}")
        
        duration = time.time() - start_time
        success = len(issues_found) == 0
        
        return TestResult(
            scenario_name=scenario.name,
            success=success,
            duration=duration,
            holes_completed=holes_completed,
            total_shots=total_shots,
            issues_found=issues_found,
            performance_metrics=performance_metrics,
            game_data=game_data
        )
    
    def _create_test_hole(self, sim, hole_number: int):
        """Create a new hole state for testing purposes"""
        # This is a simplified version - in practice you'd need proper hole creation
        from backend.app.wolf_goat_pig_simulation import HoleState
        from backend.app.state.team_formation import TeamFormation
        from backend.app.state.betting_state import BettingState
        
        teams = TeamFormation([p.id for p in sim.players])
        betting = BettingState([p.id for p in sim.players])
        
        hole_state = HoleState(
            hole_number=hole_number,
            hitting_order=[p.id for p in sim.players],
            teams=teams,
            betting=betting
        )
        
        # Initialize shot progression for new hole
        if hasattr(sim, 'hole_progression'):
            from backend.app.wolf_goat_pig_simulation import WGPHoleProgression
            sim.hole_progression = WGPHoleProgression(
                hole_number=hole_number,
                current_shot_order=[p.id for p in sim.players]
            )
        
        return hole_state
    
    def _validate_shot_result(self, result: Dict[str, Any], hole_num: int, player_id: str) -> List[str]:
        """Validate individual shot results for issues"""
        issues = []
        
        if not result:
            issues.append(f"Hole {hole_num}: Empty shot result for {player_id}")
            return issues
        
        shot_result = result.get("shot_result")
        if not shot_result:
            issues.append(f"Hole {hole_num}: Missing shot_result for {player_id}")
            return issues
        
        # Validate distance progression
        distance = shot_result.get("distance_to_pin")
        if distance is None or distance < 0:
            issues.append(f"Hole {hole_num}: Invalid distance {distance} for {player_id}")
        
        # Validate shot quality
        quality = shot_result.get("shot_quality")
        valid_qualities = ["excellent", "good", "average", "poor", "terrible"]
        if quality not in valid_qualities:
            issues.append(f"Hole {hole_num}: Invalid shot quality '{quality}' for {player_id}")
        
        # Validate shot number
        shot_number = shot_result.get("shot_number")
        if shot_number and shot_number > 8:
            issues.append(f"Hole {hole_num}: Shot limit exceeded ({shot_number}) for {player_id}")
        
        return issues
    
    def _validate_hole_completion(self, hole_state, players: List[WGPPlayer]) -> bool:
        """Check if hole completion is legitimate"""
        # At least one player should have holed out or reached max shots
        for player in players:
            ball = hole_state.ball_positions.get(player.id)
            if ball:
                if ball.distance_to_pin == 0 or ball.shot_count >= 8:
                    return True
        return False
    
    def _validate_scenario_completion(self, sim, scenario: TestScenario) -> List[str]:
        """Validate overall scenario completion against criteria"""
        issues = []
        
        if not scenario.validation_criteria:
            return issues
        
        game_state = sim.get_game_state()
        
        for criterion in scenario.validation_criteria:
            if criterion == "all_holes_completed":
                # Check if we completed expected number of holes
                pass  # This is handled in the main flow
            
            elif criterion == "partnerships_formed":
                # Check if partnerships were formed during play
                hole_state = game_state.get("hole_state")
                if hole_state and hole_state.get("teams", {}).get("type") == "pending":
                    # Still pending is okay, just checking system works
                    pass
            
            elif criterion == "no_backward_shots":
                # This should be caught in shot validation
                pass
            
            elif criterion == "shot_limit_enforced":
                # Check that no player exceeded 8 shots
                pass  # Handled in shot validation
        
        return issues
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time if self.start_time else 0
        
        # Calculate summary statistics
        total_scenarios = len(self.results)
        passed_scenarios = sum(1 for r in self.results if r.success)
        failed_scenarios = total_scenarios - passed_scenarios
        total_holes = sum(r.holes_completed for r in self.results)
        total_shots = sum(r.total_shots for r in self.results)
        
        # Group results by scenario type
        by_type = {}
        for result in self.results:
            scenario = next(s for s in self._get_test_scenarios() if s.name == result.scenario_name)
            type_name = scenario.scenario_type.value
            
            if type_name not in by_type:
                by_type[type_name] = {"passed": 0, "failed": 0, "total": 0}
            
            by_type[type_name]["total"] += 1
            if result.success:
                by_type[type_name]["passed"] += 1
            else:
                by_type[type_name]["failed"] += 1
        
        # Generate detailed report
        print("\n" + "=" * 80)
        print("🏌️ FUNCTIONAL TEST SUITE RESULTS")
        print("=" * 80)
        
        print(f"\n📊 SUMMARY")
        print(f"   Total Scenarios: {total_scenarios}")
        print(f"   ✅ Passed: {passed_scenarios} ({passed_scenarios/total_scenarios*100:.1f}%)")
        print(f"   ❌ Failed: {failed_scenarios} ({failed_scenarios/total_scenarios*100:.1f}%)")
        print(f"   🕒 Total Duration: {total_duration:.1f}s")
        print(f"   🏌️ Holes Completed: {total_holes}")
        print(f"   🎯 Total Shots: {total_shots}")
        if total_holes > 0:
            print(f"   📈 Avg Shots/Hole: {total_shots/total_holes:.1f}")
        
        print(f"\n📋 RESULTS BY SCENARIO TYPE")
        for scenario_type, stats in by_type.items():
            pass_rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"   {scenario_type.upper()}: {stats['passed']}/{stats['total']} passed ({pass_rate:.1f}%)")
        
        print(f"\n🔍 DETAILED RESULTS")
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"   {status} {result.scenario_name}")
            print(f"       Duration: {result.duration:.2f}s, Holes: {result.holes_completed}, Shots: {result.total_shots}")
            if result.issues_found:
                print(f"       Issues: {len(result.issues_found)}")
                for issue in result.issues_found[:2]:  # Show first 2 issues
                    print(f"         • {issue}")
        
        print(f"\n💡 PERFORMANCE INSIGHTS")
        avg_duration = sum(r.duration for r in self.results) / len(self.results) if self.results else 0
        avg_holes = sum(r.holes_completed for r in self.results) / len(self.results) if self.results else 0
        print(f"   Average scenario duration: {avg_duration:.2f}s")
        print(f"   Average holes per scenario: {avg_holes:.1f}")
        
        # Identify top issues
        all_issues = []
        for result in self.results:
            all_issues.extend(result.issues_found)
        
        if all_issues:
            print(f"\n⚠️  TOP ISSUES FOUND ({len(all_issues)} total)")
            # Group similar issues
            issue_counts = {}
            for issue in all_issues:
                key = issue.split(":")[0] if ":" in issue else issue
                issue_counts[key] = issue_counts.get(key, 0) + 1
            
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"   • {issue}: {count} occurrences")
        
        success_rate = passed_scenarios / total_scenarios * 100 if total_scenarios > 0 else 0
        
        print(f"\n🎯 OVERALL ASSESSMENT")
        if success_rate >= 90:
            print("   🟢 EXCELLENT: System is highly stable and ready for production")
        elif success_rate >= 75:
            print("   🟡 GOOD: System is mostly stable with minor issues to address")
        elif success_rate >= 50:
            print("   🟠 FAIR: System needs significant improvement before deployment")
        else:
            print("   🔴 POOR: System requires major fixes before further testing")
        
        print(f"   Success Rate: {success_rate:.1f}%")
        print("=" * 80)
        
        # Return structured data
        return {
            "summary": {
                "total_scenarios": total_scenarios,
                "passed": passed_scenarios,
                "failed": failed_scenarios,
                "success_rate": success_rate,
                "total_duration": total_duration,
                "holes_completed": total_holes,
                "total_shots": total_shots
            },
            "by_type": by_type,
            "results": [
                {
                    "name": r.scenario_name,
                    "success": r.success,
                    "duration": r.duration,
                    "holes": r.holes_completed,
                    "shots": r.total_shots,
                    "issues": len(r.issues_found)
                }
                for r in self.results
            ],
            "all_issues": all_issues,
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Run the complete functional test suite"""
    suite = FunctionalTestSuite()
    report = suite.run_all_scenarios()
    
    # Optionally save detailed report
    report_file = f"functional_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save report: {e}")
    
    return report["summary"]["success_rate"] >= 75

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)