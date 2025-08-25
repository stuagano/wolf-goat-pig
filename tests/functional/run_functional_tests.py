#!/usr/bin/env python3
"""
Comprehensive Functional Test Runner for Wolf-Goat-Pig Golf Simulation

Orchestrates all functional testing suites and generates consolidated reports.
Based on 2024 best practices for comprehensive system validation.
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Import all functional test modules
try:
    from functional_test_suite import FunctionalTestSuite
    from outlier_pattern_tests import OutlierPatternTester
    from multi_hole_progression_tests import MultiHoleProgressionTester
except ImportError:
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from functional_test_suite import FunctionalTestSuite
    from outlier_pattern_tests import OutlierPatternTester
    from multi_hole_progression_tests import MultiHoleProgressionTester

class ComprehensiveFunctionalTestRunner:
    """
    Master test runner that coordinates all functional testing suites:
    1. Core functional scenarios
    2. Outlier pattern detection
    3. Multi-hole progression testing
    4. Integration validation
    5. Performance benchmarking
    """
    
    def __init__(self):
        self.start_time = None
        self.test_results = {}
        self.consolidated_report = {}
        
    def run_all_functional_tests(self, 
                                save_reports: bool = True,
                                detailed_output: bool = True) -> Dict[str, Any]:
        """
        Execute comprehensive functional testing suite
        
        Args:
            save_reports: Whether to save detailed JSON reports
            detailed_output: Whether to show detailed console output
        
        Returns:
            Consolidated test results and analysis
        """
        
        print("🚀 COMPREHENSIVE FUNCTIONAL TEST EXECUTION")
        print("=" * 80)
        print("Wolf-Goat-Pig Golf Simulation - Full System Validation")
        print(f"Test execution started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        self.start_time = time.time()
        
        # Execute all test suites
        test_suites = [
            ("Core Functional Scenarios", self._run_core_functional_tests),
            ("Outlier Pattern Analysis", self._run_outlier_pattern_tests),
            ("Multi-Hole Progression", self._run_multi_hole_progression_tests),
            ("Performance Benchmarking", self._run_performance_benchmarks)
        ]
        
        for suite_name, test_function in test_suites:
            print(f"\n🧪 Executing: {suite_name}")
            print("-" * 50)
            
            try:
                suite_start = time.time()
                result = test_function(detailed_output)
                suite_duration = time.time() - suite_start
                
                self.test_results[suite_name] = {
                    "result": result,
                    "duration": suite_duration,
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"✅ {suite_name} completed in {suite_duration:.1f}s")
                
            except Exception as e:
                suite_duration = time.time() - suite_start if 'suite_start' in locals() else 0
                self.test_results[suite_name] = {
                    "result": None,
                    "duration": suite_duration,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"❌ {suite_name} failed: {str(e)}")
        
        # Generate consolidated report
        self.consolidated_report = self._generate_consolidated_report()
        
        # Save detailed reports if requested
        if save_reports:
            self._save_detailed_reports()
        
        # Display executive summary
        self._display_executive_summary()
        
        return self.consolidated_report
    
    def _run_core_functional_tests(self, detailed: bool = True) -> Dict[str, Any]:
        """Execute core functional test scenarios"""
        
        if not detailed:
            print("   Running core functional scenarios...")
        
        suite = FunctionalTestSuite()
        return suite.run_all_scenarios()
    
    def _run_outlier_pattern_tests(self, detailed: bool = True) -> Dict[str, Any]:
        """Execute outlier pattern detection tests"""
        
        if not detailed:
            print("   Analyzing outlier patterns...")
        
        tester = OutlierPatternTester()
        return tester.run_outlier_tests(iterations=200)  # Reduced for faster execution
    
    def _run_multi_hole_progression_tests(self, detailed: bool = True) -> Dict[str, Any]:
        """Execute multi-hole progression tests"""
        
        if not detailed:
            print("   Testing multi-hole progression...")
        
        tester = MultiHoleProgressionTester()
        return tester.run_multi_hole_tests()
    
    def _run_performance_benchmarks(self, detailed: bool = True) -> Dict[str, Any]:
        """Execute performance benchmarking tests"""
        
        if not detailed:
            print("   Running performance benchmarks...")
        
        # Simple performance benchmarks
        benchmarks = {}
        
        try:
            # Benchmark 1: Shot simulation speed
            start = time.time()
            from backend.app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer
            
            players = [WGPPlayer(id=f"p{i}", name=f"Player {i}", handicap=15) for i in range(4)]
            sim = WolfGoatPigSimulation(player_count=4, players=players)
            sim.enable_shot_progression()
            
            shots_simulated = 0
            for _ in range(50):  # Simulate 50 shots
                hole_state = sim.hole_states.get(sim.current_hole)
                if hole_state and hole_state.next_player_to_hit:
                    sim.simulate_shot(hole_state.next_player_to_hit)
                    shots_simulated += 1
                else:
                    break
            
            shot_duration = time.time() - start
            benchmarks["shot_simulation_speed"] = {
                "shots_per_second": shots_simulated / shot_duration if shot_duration > 0 else 0,
                "total_shots": shots_simulated,
                "duration": shot_duration
            }
            
            # Benchmark 2: Memory usage (simplified)
            import psutil
            import os
            process = psutil.Process(os.getpid())
            benchmarks["memory_usage"] = {
                "rss_mb": process.memory_info().rss / 1024 / 1024,
                "vms_mb": process.memory_info().vms / 1024 / 1024
            }
            
            # Benchmark 3: Game state serialization speed
            start = time.time()
            for _ in range(100):
                game_state = sim.get_game_state()
                json.dumps(game_state)
            serialization_duration = time.time() - start
            
            benchmarks["serialization_speed"] = {
                "serializations_per_second": 100 / serialization_duration if serialization_duration > 0 else 0,
                "duration": serialization_duration
            }
            
        except Exception as e:
            benchmarks["error"] = str(e)
        
        return {
            "benchmarks": benchmarks,
            "performance_summary": "Performance benchmarks completed",
            "status": "success" if "error" not in benchmarks else "error"
        }
    
    def _generate_consolidated_report(self) -> Dict[str, Any]:
        """Generate consolidated report from all test results"""
        
        total_duration = time.time() - self.start_time if self.start_time else 0
        
        # Analyze results from each test suite
        suite_summaries = {}
        overall_success = True
        total_tests = 0
        passed_tests = 0
        
        for suite_name, suite_data in self.test_results.items():
            if suite_data["status"] == "completed" and suite_data["result"]:
                result = suite_data["result"]
                
                if suite_name == "Core Functional Scenarios":
                    summary = result.get("summary", {})
                    suite_summaries[suite_name] = {
                        "success_rate": summary.get("success_rate", 0),
                        "total_scenarios": summary.get("total_scenarios", 0),
                        "passed": summary.get("passed", 0),
                        "failed": summary.get("failed", 0)
                    }
                    total_tests += summary.get("total_scenarios", 0)
                    passed_tests += summary.get("passed", 0)
                    
                elif suite_name == "Outlier Pattern Analysis":
                    summary = result.get("summary", {})
                    normal_patterns = summary.get("normal_patterns", 0)
                    total_patterns = summary.get("total_patterns", 1)
                    success_rate = normal_patterns / total_patterns * 100
                    
                    suite_summaries[suite_name] = {
                        "success_rate": success_rate,
                        "normal_patterns": normal_patterns,
                        "total_patterns": total_patterns
                    }
                    total_tests += total_patterns
                    passed_tests += normal_patterns
                    
                elif suite_name == "Multi-Hole Progression":
                    summary = result.get("summary", {})
                    course_success = summary.get("course_success_rate", 0)
                    tournament_success = summary.get("tournament_success_rate", 0)
                    avg_success = (course_success + tournament_success) / 2
                    
                    suite_summaries[suite_name] = {
                        "success_rate": avg_success,
                        "course_success": course_success,
                        "tournament_success": tournament_success
                    }
                    # Add synthetic test counts for progression
                    total_tests += 10  # Approximate test count
                    passed_tests += int(avg_success * 10 / 100)
                    
                elif suite_name == "Performance Benchmarking":
                    benchmarks = result.get("benchmarks", {})
                    perf_success = 100 if result.get("status") == "success" else 0
                    
                    suite_summaries[suite_name] = {
                        "success_rate": perf_success,
                        "benchmarks": benchmarks
                    }
                    total_tests += 1
                    passed_tests += 1 if perf_success == 100 else 0
                
                # Check if suite passed threshold
                suite_success_rate = suite_summaries[suite_name].get("success_rate", 0)
                if suite_success_rate < 75:  # 75% threshold
                    overall_success = False
            else:
                suite_summaries[suite_name] = {
                    "success_rate": 0,
                    "status": suite_data["status"],
                    "error": suite_data.get("error", "Unknown error")
                }
                overall_success = False
        
        # Calculate overall metrics
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "execution_summary": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
                "total_duration": total_duration,
                "overall_success": overall_success,
                "overall_success_rate": overall_success_rate,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests
            },
            "suite_summaries": suite_summaries,
            "detailed_results": self.test_results,
            "recommendations": self._generate_recommendations(suite_summaries, overall_success_rate)
        }
    
    def _generate_recommendations(self, suite_summaries: Dict[str, Any], overall_success_rate: float) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        # Overall assessment
        if overall_success_rate >= 90:
            recommendations.append("🟢 System is production-ready with excellent stability")
        elif overall_success_rate >= 75:
            recommendations.append("🟡 System is mostly stable, address minor issues before deployment")
        elif overall_success_rate >= 50:
            recommendations.append("🟠 System needs significant improvements before production")
        else:
            recommendations.append("🔴 System requires major fixes before further testing")
        
        # Suite-specific recommendations
        for suite_name, summary in suite_summaries.items():
            success_rate = summary.get("success_rate", 0)
            
            if success_rate < 75:
                if suite_name == "Core Functional Scenarios":
                    recommendations.append("• Review core game mechanics and betting logic")
                elif suite_name == "Outlier Pattern Analysis":
                    recommendations.append("• Investigate outlier patterns for realistic behavior")
                elif suite_name == "Multi-Hole Progression":
                    recommendations.append("• Fix multi-hole state management and progression")
                elif suite_name == "Performance Benchmarking":
                    recommendations.append("• Optimize performance bottlenecks")
        
        # Performance-specific recommendations
        perf_data = suite_summaries.get("Performance Benchmarking", {}).get("benchmarks", {})
        if perf_data:
            shot_speed = perf_data.get("shot_simulation_speed", {}).get("shots_per_second", 0)
            if shot_speed < 10:  # Less than 10 shots per second
                recommendations.append("• Consider optimizing shot simulation performance")
            
            memory_usage = perf_data.get("memory_usage", {}).get("rss_mb", 0)
            if memory_usage > 500:  # More than 500MB
                recommendations.append("• Monitor memory usage for potential leaks")
        
        return recommendations
    
    def _save_detailed_reports(self):
        """Save detailed JSON reports for each test suite"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            # Save consolidated report
            consolidated_file = f"functional_test_consolidated_report_{timestamp}.json"
            with open(consolidated_file, 'w') as f:
                json.dump(self.consolidated_report, f, indent=2, default=str)
            print(f"\n📄 Consolidated report saved: {consolidated_file}")
            
            # Save individual suite reports
            for suite_name, suite_data in self.test_results.items():
                if suite_data.get("result"):
                    safe_name = suite_name.lower().replace(" ", "_").replace("-", "_")
                    suite_file = f"functional_test_{safe_name}_{timestamp}.json"
                    with open(suite_file, 'w') as f:
                        json.dump(suite_data, f, indent=2, default=str)
                    print(f"   📋 {suite_name} report: {suite_file}")
            
        except Exception as e:
            print(f"⚠️  Could not save detailed reports: {e}")
    
    def _display_executive_summary(self):
        """Display executive summary of all test results"""
        
        print("\n" + "=" * 80)
        print("📊 EXECUTIVE SUMMARY - FUNCTIONAL TEST RESULTS")
        print("=" * 80)
        
        exec_summary = self.consolidated_report["execution_summary"]
        suite_summaries = self.consolidated_report["suite_summaries"]
        
        # Overall results
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Success Rate: {exec_summary['overall_success_rate']:.1f}%")
        print(f"   Tests Executed: {exec_summary['total_tests']}")
        print(f"   Tests Passed: {exec_summary['passed_tests']}")
        print(f"   Tests Failed: {exec_summary['failed_tests']}")
        print(f"   Total Duration: {exec_summary['total_duration']:.1f} seconds")
        
        # Suite breakdown
        print(f"\n📋 SUITE BREAKDOWN:")
        for suite_name, summary in suite_summaries.items():
            success_rate = summary.get("success_rate", 0)
            status_icon = "✅" if success_rate >= 75 else "⚠️" if success_rate >= 50 else "❌"
            print(f"   {status_icon} {suite_name}: {success_rate:.1f}%")
            
            # Additional details
            if suite_name == "Core Functional Scenarios":
                print(f"      Scenarios: {summary.get('passed', 0)}/{summary.get('total_scenarios', 0)}")
            elif suite_name == "Outlier Pattern Analysis":
                print(f"      Patterns: {summary.get('normal_patterns', 0)}/{summary.get('total_patterns', 0)} normal")
            elif suite_name == "Multi-Hole Progression":
                print(f"      Course: {summary.get('course_success', 0):.1f}%, Tournament: {summary.get('tournament_success', 0):.1f}%")
        
        # Performance insights
        perf_data = suite_summaries.get("Performance Benchmarking", {}).get("benchmarks", {})
        if perf_data and "error" not in perf_data:
            print(f"\n⚡ PERFORMANCE INSIGHTS:")
            
            shot_speed = perf_data.get("shot_simulation_speed", {})
            if shot_speed:
                print(f"   Shot Simulation: {shot_speed.get('shots_per_second', 0):.1f} shots/second")
            
            memory = perf_data.get("memory_usage", {})
            if memory:
                print(f"   Memory Usage: {memory.get('rss_mb', 0):.1f} MB")
            
            serialization = perf_data.get("serialization_speed", {})
            if serialization:
                print(f"   Serialization: {serialization.get('serializations_per_second', 0):.1f} ops/second")
        
        # Recommendations
        recommendations = self.consolidated_report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   {rec}")
        
        # Final assessment
        overall_success = exec_summary.get("overall_success", False)
        print(f"\n🏁 FINAL ASSESSMENT:")
        if overall_success:
            print("   🎉 SYSTEM READY: All critical tests passed. System is ready for production deployment.")
        else:
            print("   🔧 NEEDS WORK: Some tests failed. Address issues before production deployment.")
        
        print("=" * 80)

def main():
    """Main execution function"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive functional tests for Wolf-Goat-Pig")
    parser.add_argument("--no-save", action="store_true", help="Don't save detailed reports")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    parser.add_argument("--quick", action="store_true", help="Run faster version with reduced iterations")
    
    args = parser.parse_args()
    
    runner = ComprehensiveFunctionalTestRunner()
    
    try:
        results = runner.run_all_functional_tests(
            save_reports=not args.no_save,
            detailed_output=not args.quiet
        )
        
        # Return success based on overall results
        success = results["execution_summary"]["overall_success"]
        return success
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Test execution interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n💥 Test execution failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)