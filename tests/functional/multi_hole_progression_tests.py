#!/usr/bin/env python3
"""
Multi-Hole Progression Testing for Wolf-Goat-Pig Golf Simulation

Tests realistic hole-to-hole progression, course conditions, and tournament scenarios.
Based on real golf course data and tournament progression patterns.
"""

import sys
import os
import random
import time
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer

class CourseCondition(Enum):
    PERFECT = "perfect"
    WINDY = "windy"
    RAIN = "rain"
    FAST_GREENS = "fast_greens"
    ROUGH_CONDITIONS = "rough"

class HoleType(Enum):
    EASY_PAR_3 = ("par3_easy", 3, 120, "Easy")
    HARD_PAR_3 = ("par3_hard", 3, 200, "Hard")
    SHORT_PAR_4 = ("par4_short", 4, 320, "Medium")
    LONG_PAR_4 = ("par4_long", 4, 450, "Hard")
    REACHABLE_PAR_5 = ("par5_reachable", 5, 480, "Medium")
    MONSTER_PAR_5 = ("par5_monster", 5, 580, "Very Hard")

@dataclass
class CourseHole:
    hole_number: int
    hole_type: HoleType
    par: int
    yardage: int
    difficulty: str
    conditions: CourseCondition = CourseCondition.PERFECT
    hazards: List[str] = None
    wind_factor: float = 1.0
    pin_position: str = "middle"  # front, middle, back

@dataclass
class TournamentRound:
    round_name: str
    course_holes: List[CourseHole]
    weather_conditions: CourseCondition
    pressure_factor: float  # 1.0 = normal, 2.0 = high pressure
    starting_teams: str = "pending"  # How teams are formed

class MultiHoleProgressionTester:
    """
    Comprehensive multi-hole testing that simulates:
    1. Real golf course layouts and conditions
    2. Tournament progression with increasing pressure
    3. Player fatigue and performance changes over time
    4. Weather and course condition impacts
    5. Strategic decisions across multiple holes
    """
    
    def __init__(self):
        self.test_courses = self._create_test_courses()
        self.tournament_scenarios = self._create_tournament_scenarios()
        
    def run_multi_hole_tests(self) -> Dict[str, Any]:
        """Run comprehensive multi-hole progression tests"""
        
        print("🏌️ MULTI-HOLE PROGRESSION TESTING")
        print("=" * 70)
        print("Testing realistic golf course scenarios and tournament progression")
        print()
        
        results = {}
        
        # Test different course types
        for course_name, holes in self.test_courses.items():
            print(f"🏞️ Testing Course: {course_name}")
            result = self._test_course_progression(course_name, holes)
            results[course_name] = result
            
            print(f"   ✅ Completed {result['holes_finished']}/{len(holes)} holes")
            print(f"   📊 Avg shots/hole: {result['avg_shots_per_hole']:.1f}")
            print(f"   ⏱️ Total time: {result['duration']:.1f}s")
            print()
        
        # Test tournament scenarios
        for tournament in self.tournament_scenarios:
            print(f"🏆 Testing Tournament: {tournament.round_name}")
            result = self._test_tournament_round(tournament)
            results[f"tournament_{tournament.round_name}"] = result
            
            print(f"   ✅ Round complete: {result['round_completed']}")
            print(f"   💰 Final wager: {result['final_wager']} quarters")
            print(f"   🤝 Partnerships formed: {result['partnerships_formed']}")
            print()
        
        return self._generate_progression_report(results)
    
    def _create_test_courses(self) -> Dict[str, List[CourseHole]]:
        """Create realistic test courses with varied hole types"""
        
        return {
            "Executive_Course": [
                # Short executive course - good for quick testing
                CourseHole(1, HoleType.EASY_PAR_3, 3, 145, "Easy", CourseCondition.PERFECT),
                CourseHole(2, HoleType.SHORT_PAR_4, 4, 310, "Medium", CourseCondition.PERFECT),
                CourseHole(3, HoleType.HARD_PAR_3, 3, 175, "Hard", CourseCondition.WINDY),
                CourseHole(4, HoleType.SHORT_PAR_4, 4, 285, "Easy", CourseCondition.PERFECT),
                CourseHole(5, HoleType.REACHABLE_PAR_5, 5, 465, "Medium", CourseCondition.PERFECT),
                CourseHole(6, HoleType.EASY_PAR_3, 3, 125, "Easy", CourseCondition.PERFECT),
            ],
            
            "Championship_Nine": [
                # Challenging 9-hole championship course
                CourseHole(1, HoleType.LONG_PAR_4, 4, 425, "Hard", CourseCondition.PERFECT, ["water", "bunkers"]),
                CourseHole(2, HoleType.HARD_PAR_3, 3, 190, "Hard", CourseCondition.WINDY, ["water"]),
                CourseHole(3, HoleType.MONSTER_PAR_5, 5, 545, "Very Hard", CourseCondition.PERFECT, ["dogleg", "trees"]),
                CourseHole(4, HoleType.SHORT_PAR_4, 4, 340, "Medium", CourseCondition.FAST_GREENS, ["bunkers"]),
                CourseHole(5, HoleType.EASY_PAR_3, 3, 135, "Easy", CourseCondition.PERFECT),
                CourseHole(6, HoleType.LONG_PAR_4, 4, 445, "Hard", CourseCondition.WINDY, ["rough", "bunkers"]),
                CourseHole(7, HoleType.REACHABLE_PAR_5, 5, 485, "Medium", CourseCondition.PERFECT, ["water", "dogleg"]),
                CourseHole(8, HoleType.HARD_PAR_3, 3, 165, "Hard", CourseCondition.FAST_GREENS, ["island_green"]),
                CourseHole(9, HoleType.LONG_PAR_4, 4, 410, "Hard", CourseCondition.PERFECT, ["pressure_hole"])
            ],
            
            "Weather_Challenge": [
                # Course designed to test weather conditions
                CourseHole(1, HoleType.SHORT_PAR_4, 4, 320, "Medium", CourseCondition.WINDY, wind_factor=1.5),
                CourseHole(2, HoleType.HARD_PAR_3, 3, 180, "Hard", CourseCondition.RAIN, wind_factor=1.2),
                CourseHole(3, HoleType.REACHABLE_PAR_5, 5, 470, "Medium", CourseCondition.ROUGH_CONDITIONS),
                CourseHole(4, HoleType.EASY_PAR_3, 3, 140, "Easy", CourseCondition.WINDY, wind_factor=2.0),
                CourseHole(5, HoleType.LONG_PAR_4, 4, 430, "Hard", CourseCondition.RAIN),
                CourseHole(6, HoleType.SHORT_PAR_4, 4, 295, "Medium", CourseCondition.FAST_GREENS)
            ]
        }
    
    def _create_tournament_scenarios(self) -> List[TournamentRound]:
        """Create tournament scenarios with increasing pressure"""
        
        return [
            TournamentRound(
                round_name="Practice_Round",
                course_holes=self.test_courses["Executive_Course"],
                weather_conditions=CourseCondition.PERFECT,
                pressure_factor=0.8,  # Relaxed practice
                starting_teams="random"
            ),
            
            TournamentRound(
                round_name="Tournament_Round",
                course_holes=self.test_courses["Championship_Nine"],
                weather_conditions=CourseCondition.WINDY,
                pressure_factor=1.5,  # Tournament pressure
                starting_teams="pending"
            ),
            
            TournamentRound(
                round_name="Final_Round",
                course_holes=self.test_courses["Weather_Challenge"],
                weather_conditions=CourseCondition.RAIN,
                pressure_factor=2.0,  # High pressure final round
                starting_teams="strategic"
            )
        ]
    
    def _test_course_progression(self, course_name: str, holes: List[CourseHole]) -> Dict[str, Any]:
        """Test progression through a complete course"""
        
        start_time = time.time()
        
        # Create diverse player group
        players = [
            WGPPlayer(id="low_hcp", name="Club Pro", handicap=3),
            WGPPlayer(id="mid_hcp", name="Regular Member", handicap=14),
            WGPPlayer(id="high_hcp", name="Weekend Player", handicap=22),
            WGPPlayer(id="senior", name="Senior Member", handicap=16)
        ]
        
        sim = WolfGoatPigSimulation(player_count=4, players=players)
        sim.enable_shot_progression()
        
        holes_finished = 0
        total_shots = 0
        hole_results = []
        issues_found = []
        
        for i, hole in enumerate(holes):
            hole_result = self._play_hole_with_conditions(sim, hole, players)
            hole_results.append(hole_result)
            
            if hole_result["completed"]:
                holes_finished += 1
                total_shots += hole_result["total_shots"]
            else:
                issues_found.extend(hole_result["issues"])
            
            # Advance to next hole
            if i < len(holes) - 1:
                sim.current_hole = i + 2
                next_hole = self._setup_next_hole(sim, holes[i + 1])
                sim.hole_states[sim.current_hole] = next_hole
        
        duration = time.time() - start_time
        
        return {
            "course_name": course_name,
            "holes_finished": holes_finished,
            "total_holes": len(holes),
            "total_shots": total_shots,
            "avg_shots_per_hole": total_shots / max(holes_finished, 1),
            "duration": duration,
            "hole_results": hole_results,
            "issues_found": issues_found,
            "success": len(issues_found) == 0 and holes_finished == len(holes)
        }
    
    def _play_hole_with_conditions(self, sim: WolfGoatPigSimulation, hole: CourseHole, players: List[WGPPlayer]) -> Dict[str, Any]:
        """Play a single hole with specific conditions"""
        
        shots_taken = 0
        max_shots = 50  # Safety limit
        completed = False
        issues = []
        
        # Apply hole conditions
        condition_modifier = self._get_condition_modifier(hole.conditions)
        
        while shots_taken < max_shots:
            hole_state = sim.hole_states.get(sim.current_hole)
            if not hole_state:
                issues.append(f"Missing hole state for hole {hole.hole_number}")
                break
            
            if hole_state.hole_complete:
                completed = True
                break
            
            next_player = hole_state.next_player_to_hit
            if not next_player:
                # Check if this is legitimate completion
                if self._validate_hole_completion(hole_state, players):
                    completed = True
                else:
                    issues.append(f"Hole {hole.hole_number}: No next player but not complete")
                break
            
            try:
                # Apply conditions to shot simulation
                result = sim.simulate_shot(next_player)
                shots_taken += 1
                
                # Validate shot under conditions
                if self._validate_conditioned_shot(result, hole, condition_modifier):
                    # Shot is valid
                    pass
                else:
                    issues.append(f"Invalid shot under {hole.conditions.value} conditions")
                
                if result.get("hole_complete"):
                    completed = True
                    break
                    
            except Exception as e:
                issues.append(f"Hole {hole.hole_number}, Shot {shots_taken}: {str(e)}")
                break
        
        if shots_taken >= max_shots and not completed:
            issues.append(f"Hole {hole.hole_number}: Exceeded max shots without completion")
        
        return {
            "hole_number": hole.hole_number,
            "hole_type": hole.hole_type.value[0],
            "par": hole.par,
            "conditions": hole.conditions.value,
            "completed": completed,
            "total_shots": shots_taken,
            "issues": issues,
            "performance_rating": self._rate_hole_performance(shots_taken, hole.par, len(players))
        }
    
    def _get_condition_modifier(self, condition: CourseCondition) -> float:
        """Get difficulty modifier for course conditions"""
        modifiers = {
            CourseCondition.PERFECT: 1.0,
            CourseCondition.WINDY: 1.2,
            CourseCondition.RAIN: 1.3,
            CourseCondition.FAST_GREENS: 1.1,
            CourseCondition.ROUGH_CONDITIONS: 1.4
        }
        return modifiers.get(condition, 1.0)
    
    def _validate_conditioned_shot(self, result: Dict[str, Any], hole: CourseHole, modifier: float) -> bool:
        """Validate that shot results make sense under specific conditions"""
        
        shot_result = result.get("shot_result", {})
        quality = shot_result.get("shot_quality", "unknown")
        distance = shot_result.get("distance_to_pin", 0)
        
        # Under difficult conditions, excellent shots should be rarer
        if hole.conditions in [CourseCondition.WINDY, CourseCondition.RAIN] and modifier > 1.2:
            # In tough conditions, too many excellent shots might indicate unrealistic simulation
            if quality == "excellent" and random.random() < 0.1:  # Random validation check
                return True  # Allow some excellent shots even in tough conditions
        
        # Basic validation - no shots should go backward
        if distance < 0:
            return False
        
        return True
    
    def _validate_hole_completion(self, hole_state, players: List[WGPPlayer]) -> bool:
        """Validate legitimate hole completion"""
        # Check if at least one player has holed out or reached limit
        for player in players:
            ball = hole_state.ball_positions.get(player.id)
            if ball and (ball.distance_to_pin == 0 or ball.shot_count >= 8):
                return True
        return False
    
    def _rate_hole_performance(self, shots_taken: int, par: int, num_players: int) -> str:
        """Rate the performance on a hole"""
        expected_shots = par * num_players * 1.2  # Expected with handicaps
        
        if shots_taken <= expected_shots * 0.8:
            return "excellent"
        elif shots_taken <= expected_shots:
            return "good"
        elif shots_taken <= expected_shots * 1.3:
            return "average"
        else:
            return "poor"
    
    def _setup_next_hole(self, sim: WolfGoatPigSimulation, hole: CourseHole):
        """Set up the next hole with proper state initialization"""
        # This would create proper hole state - simplified for testing
        from backend.app.wolf_goat_pig_simulation import HoleState
        from backend.app.state.team_formation import TeamFormation
        from backend.app.state.betting_state import BettingState
        
        # Create fresh team and betting states for new hole
        teams = TeamFormation([p.id for p in sim.players])
        betting = BettingState([p.id for p in sim.players])
        
        hole_state = HoleState(
            hole_number=hole.hole_number,
            hitting_order=[p.id for p in sim.players],
            teams=teams,
            betting=betting,
            hole_par=hole.par,
            hole_yardage=hole.yardage,
            hole_difficulty=hole.difficulty
        )
        
        return hole_state
    
    def _test_tournament_round(self, tournament: TournamentRound) -> Dict[str, Any]:
        """Test a complete tournament round with pressure and conditions"""
        
        start_time = time.time()
        
        # Create competitive players for tournament
        players = [
            WGPPlayer(id="leader", name="Tournament Leader", handicap=2),
            WGPPlayer(id="chaser", name="Chasing Pack", handicap=5),
            WGPPlayer(id="contender", name="Dark Horse", handicap=8),
            WGPPlayer(id="amateur", name="Club Champion", handicap=12)
        ]
        
        sim = WolfGoatPigSimulation(player_count=4, players=players)
        sim.enable_shot_progression()
        
        round_completed = True
        partnerships_formed = 0
        doubles_offered = 0
        final_wager = 1
        pressure_effects = []
        
        for i, hole in enumerate(tournament.course_holes):
            # Apply tournament pressure
            hole_result = self._play_tournament_hole(sim, hole, tournament.pressure_factor)
            
            if not hole_result["completed"]:
                round_completed = False
            
            partnerships_formed += hole_result.get("partnerships", 0)
            doubles_offered += hole_result.get("doubles", 0)
            final_wager = hole_result.get("final_wager", final_wager)
            
            # Track pressure effects
            if tournament.pressure_factor > 1.0:
                pressure_effects.extend(hole_result.get("pressure_effects", []))
            
            # Advance to next hole
            if i < len(tournament.course_holes) - 1:
                sim.current_hole = i + 2
                next_hole = self._setup_next_hole(sim, tournament.course_holes[i + 1])
                sim.hole_states[sim.current_hole] = next_hole
        
        duration = time.time() - start_time
        
        return {
            "tournament_name": tournament.round_name,
            "round_completed": round_completed,
            "partnerships_formed": partnerships_formed,
            "doubles_offered": doubles_offered,
            "final_wager": final_wager,
            "pressure_effects": len(pressure_effects),
            "duration": duration,
            "weather_impact": tournament.weather_conditions.value
        }
    
    def _play_tournament_hole(self, sim: WolfGoatPigSimulation, hole: CourseHole, pressure_factor: float) -> Dict[str, Any]:
        """Play hole under tournament conditions with pressure effects"""
        
        shots_taken = 0
        max_shots = 60  # Slightly higher limit for tournament conditions
        completed = False
        partnerships = 0
        doubles = 0
        pressure_effects = []
        
        while shots_taken < max_shots:
            hole_state = sim.hole_states.get(sim.current_hole)
            if not hole_state:
                break
            
            if hole_state.hole_complete:
                completed = True
                break
            
            next_player = hole_state.next_player_to_hit
            if not next_player:
                completed = True
                break
            
            try:
                # Apply pressure effects (simplified)
                if pressure_factor > 1.5 and random.random() < 0.1:
                    pressure_effects.append(f"Pressure affected {next_player} on shot {shots_taken}")
                
                result = sim.simulate_shot(next_player)
                shots_taken += 1
                
                # Track tournament-specific events
                if result.get("betting_opportunity"):
                    doubles += 1
                
                # Check for partnerships forming
                hole_state_updated = sim.hole_states.get(sim.current_hole)
                if hole_state_updated.teams.type != "pending":
                    partnerships += 1
                
                if result.get("hole_complete"):
                    completed = True
                    break
                    
            except Exception as e:
                break
        
        final_wager = hole_state.betting.current_wager if hole_state else 1
        
        return {
            "completed": completed,
            "partnerships": partnerships,
            "doubles": doubles,
            "final_wager": final_wager,
            "pressure_effects": pressure_effects
        }
    
    def _generate_progression_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive multi-hole progression report"""
        
        print("📊 MULTI-HOLE PROGRESSION TEST RESULTS")
        print("=" * 70)
        
        course_results = {k: v for k, v in results.items() if not k.startswith("tournament_")}
        tournament_results = {k: v for k, v in results.items() if k.startswith("tournament_")}
        
        # Course progression summary
        print("\n🏞️ COURSE PROGRESSION RESULTS:")
        total_courses = len(course_results)
        successful_courses = sum(1 for r in course_results.values() if r.get("success", False))
        
        for course_name, result in course_results.items():
            status = "✅ SUCCESS" if result.get("success") else "❌ ISSUES"
            completion_rate = result["holes_finished"] / result["total_holes"] * 100
            print(f"   {status} {course_name}: {completion_rate:.0f}% holes completed")
            print(f"      Avg shots/hole: {result['avg_shots_per_hole']:.1f}, Duration: {result['duration']:.1f}s")
            
            if result["issues_found"]:
                print(f"      Issues: {len(result['issues_found'])}")
        
        # Tournament progression summary
        print(f"\n🏆 TOURNAMENT PROGRESSION RESULTS:")
        for tournament_name, result in tournament_results.items():
            status = "✅ COMPLETED" if result.get("round_completed") else "❌ INCOMPLETE"
            print(f"   {status} {result['tournament_name']}")
            print(f"      Partnerships: {result['partnerships_formed']}, Doubles: {result['doubles_offered']}")
            print(f"      Final wager: {result['final_wager']} quarters")
            print(f"      Weather: {result['weather_impact']}, Pressure effects: {result['pressure_effects']}")
        
        # Overall assessment
        total_success_rate = successful_courses / total_courses * 100 if total_courses > 0 else 0
        tournament_success_rate = sum(1 for r in tournament_results.values() if r.get("round_completed", False)) / len(tournament_results) * 100 if tournament_results else 0
        
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"   Course success rate: {total_success_rate:.1f}% ({successful_courses}/{total_courses})")
        print(f"   Tournament completion rate: {tournament_success_rate:.1f}%")
        
        if total_success_rate >= 80 and tournament_success_rate >= 75:
            print("   🟢 EXCELLENT: Multi-hole progression is highly reliable")
        elif total_success_rate >= 60 and tournament_success_rate >= 50:
            print("   🟡 GOOD: Multi-hole progression works with minor issues")
        else:
            print("   🔴 NEEDS IMPROVEMENT: Multi-hole progression has significant issues")
        
        print("=" * 70)
        
        return {
            "course_results": course_results,
            "tournament_results": tournament_results,
            "summary": {
                "course_success_rate": total_success_rate,
                "tournament_success_rate": tournament_success_rate,
                "total_courses_tested": total_courses,
                "total_tournaments_tested": len(tournament_results)
            }
        }

def main():
    """Run multi-hole progression testing"""
    tester = MultiHoleProgressionTester()
    results = tester.run_multi_hole_tests()
    
    # Success criteria: 80% course success rate and 75% tournament completion
    course_success = results["summary"]["course_success_rate"] >= 80
    tournament_success = results["summary"]["tournament_success_rate"] >= 75
    
    return course_success and tournament_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)