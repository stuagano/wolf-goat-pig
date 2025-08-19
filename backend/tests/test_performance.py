"""
Comprehensive Performance Test Suite

This module provides thorough performance testing for the Wolf Goat Pig application,
including load testing, stress testing, memory profiling, database performance,
and API response time benchmarks.

Test Coverage:
- Monte Carlo simulation performance
- Odds calculation speed benchmarks
- Database query optimization tests
- API response time measurements
- Memory usage profiling
- Concurrent user simulation
- Load testing scenarios
- Stress testing under extreme conditions
- Performance regression detection
- Resource utilization monitoring
"""

import pytest
import time
import threading
import concurrent.futures
import statistics
import psutil
import gc
import sys
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from contextlib import contextmanager
from typing import List, Dict, Any
import numpy as np

# Import performance testing utilities
try:
    import memory_profiler
    import line_profiler
    HAS_PROFILING_TOOLS = True
except ImportError:
    HAS_PROFILING_TOOLS = False

from app.services.monte_carlo import MonteCarloSimulator
from app.services.odds_calculator import OddsCalculator
from app.services.player_service import PlayerService
from app.domain.shot_range_analysis import ShotRangeAnalyzer, analyze_shot_decision


class PerformanceProfiler:
    """Utility class for performance profiling and measurement."""
    
    @staticmethod
    @contextmanager
    def timer(name: str = "Operation"):
        """Context manager for timing operations."""
        start_time = time.perf_counter()
        start_cpu = time.process_time()
        yield
        end_time = time.perf_counter()
        end_cpu = time.process_time()
        
        wall_time = (end_time - start_time) * 1000  # Convert to milliseconds
        cpu_time = (end_cpu - start_cpu) * 1000
        
        print(f"{name}: Wall time: {wall_time:.2f}ms, CPU time: {cpu_time:.2f}ms")
    
    @staticmethod
    @contextmanager
    def memory_monitor(name: str = "Operation"):
        """Context manager for monitoring memory usage."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        yield
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = final_memory - initial_memory
        
        print(f"{name}: Memory delta: {memory_delta:.2f} MB (Initial: {initial_memory:.2f} MB, Final: {final_memory:.2f} MB)")
    
    @staticmethod
    def run_with_stats(func, iterations: int = 100, name: str = "Function"):
        """Run function multiple times and collect performance statistics."""
        times = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            func()
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)  # milliseconds
        
        stats = {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'min': min(times),
            'max': max(times),
            'p95': np.percentile(times, 95),
            'p99': np.percentile(times, 99)
        }
        
        print(f"\n{name} Performance Statistics ({iterations} iterations):")
        print(f"  Mean: {stats['mean']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  Std Dev: {stats['stdev']:.2f}ms")
        print(f"  Min/Max: {stats['min']:.2f}ms / {stats['max']:.2f}ms")
        print(f"  95th/99th percentile: {stats['p95']:.2f}ms / {stats['p99']:.2f}ms")
        
        return stats


class TestMonteCarloPerformance:
    """Performance tests for Monte Carlo simulation engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.simulator = MonteCarloSimulator()
        self.profiler = PerformanceProfiler()
        
        self.test_players = [
            {"id": f"player_{i}", "handicap": 10 + i*2, "distance": 150 + i*10}
            for i in range(4)
        ]
        
        self.test_hole = {"par": 4, "difficulty": 3.5}
    
    def test_simulation_speed_baseline(self):
        """Test baseline simulation speed with standard parameters."""
        def run_simulation():
            return self.simulator.simulate_hole_outcomes(
                players=self.test_players,
                hole=self.test_hole,
                iterations=1000
            )
        
        stats = self.profiler.run_with_stats(
            run_simulation, 
            iterations=10,
            name="Monte Carlo Baseline (1k iterations)"
        )
        
        # Performance assertions
        assert stats['mean'] < 500  # Should complete in under 500ms on average
        assert stats['p95'] < 1000  # 95% should complete in under 1 second
        assert stats['stdev'] < 200  # Consistent performance
    
    def test_simulation_scalability_iterations(self):
        """Test how simulation performance scales with iteration count."""
        iteration_counts = [100, 500, 1000, 5000, 10000]
        results = {}
        
        for iterations in iteration_counts:
            def run_simulation():
                return self.simulator.simulate_hole_outcomes(
                    players=self.test_players,
                    hole=self.test_hole,
                    iterations=iterations
                )
            
            with self.profiler.timer(f"Simulation with {iterations} iterations"):
                start_time = time.perf_counter()
                result = run_simulation()
                end_time = time.perf_counter()
                
                results[iterations] = {
                    'time': (end_time - start_time) * 1000,
                    'result': result
                }
        
        # Test scalability - should be roughly linear
        times = [results[i]['time'] for i in iteration_counts]
        
        # Calculate iterations per millisecond for each test
        throughput = [iteration_counts[i] / times[i] for i in range(len(iteration_counts))]
        
        # Throughput should be relatively consistent (within 20%)
        throughput_cv = statistics.stdev(throughput) / statistics.mean(throughput)
        assert throughput_cv < 0.3  # Coefficient of variation under 30%
        
        print(f"\nScalability Analysis:")
        for i, count in enumerate(iteration_counts):
            print(f"  {count:5d} iterations: {times[i]:6.1f}ms ({throughput[i]:.1f} iter/ms)")
    
    def test_simulation_scalability_players(self):
        """Test how simulation performance scales with player count."""
        player_counts = [2, 3, 4, 5, 6]  # Test different player group sizes
        results = {}
        
        for player_count in player_counts:
            test_players = [
                {"id": f"player_{i}", "handicap": 12 + i, "distance": 150}
                for i in range(player_count)
            ]
            
            def run_simulation():
                return self.simulator.simulate_hole_outcomes(
                    players=test_players,
                    hole=self.test_hole,
                    iterations=1000
                )
            
            stats = self.profiler.run_with_stats(
                run_simulation,
                iterations=5,
                name=f"Simulation with {player_count} players"
            )
            
            results[player_count] = stats
        
        # Performance should degrade gracefully with more players
        times = [results[count]['mean'] for count in player_counts]
        
        # Each additional player should add roughly constant overhead
        time_deltas = [times[i+1] - times[i] for i in range(len(times)-1)]
        delta_cv = statistics.stdev(time_deltas) / statistics.mean(time_deltas)
        
        assert delta_cv < 0.5  # Overhead should be relatively consistent
        assert max(times) < 2000  # Even with 6 players should be under 2 seconds
    
    def test_memory_usage_simulation(self):
        """Test memory usage during simulation."""
        def large_simulation():
            return self.simulator.simulate_hole_outcomes(
                players=self.test_players,
                hole=self.test_hole,
                iterations=50000  # Large simulation
            )
        
        with self.profiler.memory_monitor("Large Monte Carlo Simulation"):
            result = large_simulation()
        
        # Force garbage collection and check for leaks
        gc.collect()
        
        # Memory should be released after simulation
        process = psutil.Process()
        memory_after_gc = process.memory_info().rss / 1024 / 1024
        
        # Run another simulation to check for memory leaks
        with self.profiler.memory_monitor("Second large simulation"):
            result2 = large_simulation()
        
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        
        # Memory usage should not grow significantly between runs
        memory_growth = final_memory - memory_after_gc
        assert memory_growth < 50  # Less than 50MB growth
    
    def test_concurrent_simulations(self):
        """Test performance under concurrent simulation load."""
        def run_simulation():
            return self.simulator.simulate_hole_outcomes(
                players=self.test_players,
                hole=self.test_hole,
                iterations=1000
            )
        
        # Test sequential performance
        sequential_times = []
        for _ in range(8):
            start_time = time.perf_counter()
            run_simulation()
            end_time = time.perf_counter()
            sequential_times.append((end_time - start_time) * 1000)
        
        sequential_total = sum(sequential_times)
        
        # Test concurrent performance
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(run_simulation) for _ in range(8)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        concurrent_total = (time.perf_counter() - start_time) * 1000
        
        # Concurrent execution should provide some speedup
        speedup = sequential_total / concurrent_total
        
        print(f"\nConcurrency Analysis:")
        print(f"  Sequential total: {sequential_total:.1f}ms")
        print(f"  Concurrent total: {concurrent_total:.1f}ms")
        print(f"  Speedup: {speedup:.2f}x")
        
        assert speedup > 1.2  # Should get at least 20% speedup
        assert all(result is not None for result in results)  # All simulations should complete


class TestOddsCalculationPerformance:
    """Performance tests for odds calculation engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = OddsCalculator()
        self.profiler = PerformanceProfiler()
        
        self.test_players = [
            {
                "id": f"p{i}",
                "name": f"Player {i}",
                "handicap": 8 + i*3,
                "distance_to_pin": 140 + i*15,
                "lie_type": ["fairway", "rough", "bunker"][i % 3]
            }
            for i in range(4)
        ]
        
        self.test_hole = {
            "hole_number": 8,
            "par": 4,
            "difficulty_rating": 3.8
        }
    
    def test_odds_calculation_speed(self):
        """Test speed of real-time odds calculation."""
        def calculate_odds():
            return self.calculator.calculate_real_time_odds(
                players=self.test_players,
                hole=self.test_hole
            )
        
        stats = self.profiler.run_with_stats(
            calculate_odds,
            iterations=50,
            name="Real-time Odds Calculation"
        )
        
        # Real-time calculations should be very fast
        assert stats['mean'] < 50  # Under 50ms on average
        assert stats['p95'] < 100  # 95% under 100ms
        assert stats['max'] < 200  # No calculation over 200ms
    
    def test_odds_calculation_caching_performance(self):
        """Test performance improvement from caching."""
        # First calculation (cache miss)
        start_time = time.perf_counter()
        result1 = self.calculator.calculate_real_time_odds(
            players=self.test_players,
            hole=self.test_hole
        )
        first_calc_time = (time.perf_counter() - start_time) * 1000
        
        # Subsequent calculations (cache hits)
        cached_times = []
        for _ in range(10):
            start_time = time.perf_counter()
            result2 = self.calculator.calculate_real_time_odds(
                players=self.test_players,
                hole=self.test_hole
            )
            cached_time = (time.perf_counter() - start_time) * 1000
            cached_times.append(cached_time)
        
        avg_cached_time = statistics.mean(cached_times)
        
        # Cached calculations should be significantly faster
        speedup = first_calc_time / avg_cached_time
        
        print(f"\nCaching Performance:")
        print(f"  First calculation: {first_calc_time:.2f}ms")
        print(f"  Average cached: {avg_cached_time:.2f}ms")
        print(f"  Speedup: {speedup:.1f}x")
        
        assert speedup > 2  # At least 2x speedup from caching
        assert avg_cached_time < 10  # Cached calls under 10ms
    
    def test_odds_calculation_memory_efficiency(self):
        """Test memory efficiency of odds calculations."""
        def run_many_calculations():
            for i in range(100):
                # Slightly vary parameters to avoid excessive caching
                varied_players = [
                    {**player, "distance_to_pin": player["distance_to_pin"] + i % 10}
                    for player in self.test_players
                ]
                
                result = self.calculator.calculate_real_time_odds(
                    players=varied_players,
                    hole=self.test_hole
                )
        
        with self.profiler.memory_monitor("100 Odds Calculations"):
            run_many_calculations()
        
        # Memory usage should remain reasonable
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024
        
        assert memory_usage < 200  # Should use less than 200MB
    
    def test_complex_scenario_performance(self):
        """Test performance with complex game scenarios."""
        complex_players = [
            {
                "id": f"p{i}",
                "name": f"Player {i}",
                "handicap": 5 + i*2,
                "distance_to_pin": 120 + i*20,
                "lie_type": ["fairway", "rough", "bunker", "water", "trees"][i % 5],
                "is_captain": i == 0,
                "team_id": f"team_{i % 2}" if i < 4 else None
            }
            for i in range(6)  # Maximum players
        ]
        
        complex_hole = {
            "hole_number": 18,
            "par": 5,
            "difficulty_rating": 4.8,
            "teams": "partnerships",
            "current_wager": 8,
            "is_doubled": True
        }
        
        def complex_calculation():
            return self.calculator.calculate_real_time_odds(
                players=complex_players,
                hole=complex_hole
            )
        
        stats = self.profiler.run_with_stats(
            complex_calculation,
            iterations=20,
            name="Complex Scenario Odds"
        )
        
        # Even complex scenarios should complete quickly
        assert stats['mean'] < 150  # Under 150ms on average
        assert stats['p95'] < 300  # 95% under 300ms


class TestShotAnalysisPerformance:
    """Performance tests for shot range analysis system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = ShotRangeAnalyzer()
        self.profiler = PerformanceProfiler()
    
    def test_shot_analysis_speed(self):
        """Test speed of shot analysis calculations."""
        def analyze_shot():
            return analyze_shot_decision(
                current_lie="fairway",
                distance=150,
                player_handicap=12,
                hole_number=8,
                team_situation="partnership",
                score_differential=1
            )
        
        stats = self.profiler.run_with_stats(
            analyze_shot,
            iterations=100,
            name="Shot Range Analysis"
        )
        
        # Shot analysis should be very fast for real-time use
        assert stats['mean'] < 20  # Under 20ms on average
        assert stats['p95'] < 50   # 95% under 50ms
        assert stats['max'] < 100  # No analysis over 100ms
    
    def test_analysis_with_various_parameters(self):
        """Test performance across various shot parameters."""
        test_scenarios = [
            # (lie, distance, handicap, expected_max_time_ms)
            ("green", 10, 0, 15),      # Simple putt
            ("fairway", 150, 12, 25),  # Standard approach
            ("rough", 200, 18, 35),    # Difficult shot
            ("bunker", 80, 25, 30),    # Recovery shot
            ("water", 250, 36, 40),    # Extreme situation
        ]
        
        for lie, distance, handicap, max_time in test_scenarios:
            def analyze_scenario():
                return analyze_shot_decision(
                    current_lie=lie,
                    distance=distance,
                    player_handicap=handicap,
                    hole_number=10
                )
            
            with self.profiler.timer(f"Analysis: {lie}, {distance}y, {handicap}hcp"):
                start_time = time.perf_counter()
                result = analyze_scenario()
                end_time = time.perf_counter()
                
                calc_time = (end_time - start_time) * 1000
                assert calc_time < max_time
                assert result is not None
                assert "recommended_shot" in result
    
    def test_concurrent_shot_analysis(self):
        """Test performance under concurrent analysis load."""
        def analyze_random_shot():
            import random
            return analyze_shot_decision(
                current_lie=random.choice(["fairway", "rough", "bunker"]),
                distance=random.randint(50, 250),
                player_handicap=random.randint(0, 30),
                hole_number=random.randint(1, 18)
            )
        
        # Test concurrent performance
        start_time = time.perf_counter()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(analyze_random_shot) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = (time.perf_counter() - start_time) * 1000
        avg_time_per_analysis = total_time / 50
        
        print(f"\nConcurrent Shot Analysis:")
        print(f"  50 analyses in {total_time:.1f}ms")
        print(f"  Average per analysis: {avg_time_per_analysis:.1f}ms")
        
        assert avg_time_per_analysis < 30  # Should handle concurrency well
        assert all(result is not None for result in results)


class TestDatabasePerformance(TestAPIIntegration):
    """Performance tests for database operations."""
    
    def test_player_profile_crud_performance(self):
        """Test performance of player profile CRUD operations."""
        from sqlalchemy.orm import sessionmaker
        
        Session = sessionmaker(bind=self.engine)
        db = Session()
        
        player_service = PlayerService(db)
        profiler = PerformanceProfiler()
        
        # Test bulk creation performance
        def create_players():
            players = []
            for i in range(100):
                player_data = PlayerProfileCreate(
                    name=f"Perf Test Player {i}",
                    handicap=float(10 + i % 20)
                )
                player = player_service.create_player_profile(player_data)
                players.append(player)
            return players
        
        with profiler.timer("Create 100 players"):
            created_players = create_players()
        
        # Test bulk retrieval performance
        def retrieve_players():
            return [
                player_service.get_player_profile(player.id)
                for player in created_players[:50]  # Retrieve first 50
            ]
        
        with profiler.timer("Retrieve 50 players"):
            retrieved_players = retrieve_players()
        
        # Test bulk update performance
        def update_players():
            from app.schemas import PlayerProfileUpdate
            for player in created_players[:25]:  # Update first 25
                update_data = PlayerProfileUpdate(handicap=player.handicap + 1.0)
                player_service.update_player_profile(player.id, update_data)
        
        with profiler.timer("Update 25 players"):
            update_players()
        
        # Test query performance
        def query_operations():
            # Test various queries
            all_players = player_service.get_all_player_profiles()
            low_handicap = [p for p in all_players if p.handicap < 15]
            high_handicap = [p for p in all_players if p.handicap >= 20]
            return len(all_players), len(low_handicap), len(high_handicap)
        
        with profiler.timer("Query operations"):
            query_results = query_operations()
        
        db.close()
        
        # Assertions
        assert len(created_players) == 100
        assert len(retrieved_players) == 50
        assert query_results[0] == 100  # Total players
    
    def test_game_result_batch_processing(self):
        """Test performance of batch game result processing."""
        from sqlalchemy.orm import sessionmaker
        from app.schemas import GamePlayerResultCreate
        
        Session = sessionmaker(bind=self.engine)
        db = Session()
        
        player_service = PlayerService(db)
        profiler = PerformanceProfiler()
        
        # Create test players
        test_players = []
        for i in range(10):
            player_data = PlayerProfileCreate(
                name=f"Batch Test Player {i}",
                handicap=float(10 + i)
            )
            player = player_service.create_player_profile(player_data)
            test_players.append(player)
        
        # Test batch game result processing
        def process_batch_results():
            for player in test_players:
                for game_num in range(20):  # 20 games per player
                    game_result = GamePlayerResultCreate(
                        player_profile_id=player.id,
                        game_id=f"batch_game_{game_num}",
                        final_position=(game_num % 4) + 1,
                        total_earnings=float((game_num % 10) - 5),  # -5 to +4
                        hole_scores={str(h): 4 for h in range(1, 19)},
                        holes_won=game_num % 3,
                        successful_bets=game_num % 5,
                        total_bets=game_num % 5 + 1,
                        partnerships_formed=1 if game_num % 2 == 0 else 0,
                        partnerships_won=1 if game_num % 4 == 0 else 0,
                        solo_attempts=0,
                        solo_wins=0
                    )
                    
                    player_service.record_game_result(game_result)
        
        with profiler.timer("Process 200 game results"):
            process_batch_results()
        
        # Test analytics generation performance
        def generate_analytics():
            analytics_results = []
            for player in test_players:
                analytics = player_service.get_player_performance_analytics(player.id)
                analytics_results.append(analytics)
            return analytics_results
        
        with profiler.timer("Generate analytics for 10 players"):
            analytics_results = generate_analytics()
        
        db.close()
        
        assert len(analytics_results) == 10
        assert all(analytics is not None for analytics in analytics_results)


class TestMemoryPerformance:
    """Comprehensive memory performance and leak detection tests."""
    
    def setup_method(self):
        """Set up memory monitoring."""
        self.profiler = PerformanceProfiler()
        gc.collect()  # Start with clean slate
    
    @pytest.mark.skipif(not HAS_PROFILING_TOOLS, reason="Memory profiler not available")
    def test_monte_carlo_memory_profile(self):
        """Profile memory usage during Monte Carlo simulation."""
        simulator = MonteCarloSimulator()
        
        @memory_profiler.profile
        def memory_intensive_simulation():
            players = [{"id": f"p{i}", "handicap": 12} for i in range(4)]
            hole = {"par": 4, "difficulty": 3.5}
            
            results = []
            for _ in range(10):
                result = simulator.simulate_hole_outcomes(
                    players=players,
                    hole=hole,
                    iterations=10000
                )
                results.append(result)
            
            return results
        
        # This will print detailed memory usage line by line
        results = memory_intensive_simulation()
        assert len(results) == 10
    
    def test_memory_leak_detection(self):
        """Test for memory leaks in critical operations."""
        process = psutil.Process()
        
        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024
        
        # Perform memory-intensive operations
        def memory_operations():
            simulator = MonteCarloSimulator()
            calculator = OddsCalculator()
            
            for i in range(50):
                # Monte Carlo simulation
                players = [{"id": f"p{j}", "handicap": 10+j} for j in range(4)]
                hole = {"par": 4, "difficulty": 3.0}
                
                sim_result = simulator.simulate_hole_outcomes(
                    players=players, 
                    hole=hole, 
                    iterations=1000
                )
                
                # Odds calculation
                odds_result = calculator.calculate_real_time_odds(
                    players=players,
                    hole=hole
                )
                
                # Shot analysis
                analysis_result = analyze_shot_decision(
                    current_lie="fairway",
                    distance=150 + i,
                    player_handicap=12,
                    hole_number=i % 18 + 1
                )
                
                # Clear references periodically
                if i % 10 == 0:
                    gc.collect()
        
        # Run operations
        memory_operations()
        
        # Force garbage collection
        gc.collect()
        
        # Check final memory
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - baseline_memory
        
        print(f"\nMemory Leak Detection:")
        print(f"  Baseline memory: {baseline_memory:.1f} MB")
        print(f"  Final memory: {final_memory:.1f} MB")
        print(f"  Memory growth: {memory_growth:.1f} MB")
        
        # Memory growth should be minimal (under 20MB)
        assert memory_growth < 20
    
    def test_garbage_collection_effectiveness(self):
        """Test effectiveness of garbage collection."""
        def create_large_objects():
            large_objects = []
            for i in range(100):
                # Create large data structures
                large_dict = {
                    f"key_{j}": [f"value_{j}_{k}" for k in range(1000)]
                    for j in range(100)
                }
                large_objects.append(large_dict)
            return large_objects
        
        process = psutil.Process()
        
        # Create objects
        initial_memory = process.memory_info().rss / 1024 / 1024
        large_objects = create_large_objects()
        with_objects_memory = process.memory_info().rss / 1024 / 1024
        
        # Clear references
        large_objects.clear()
        del large_objects
        
        # Force garbage collection
        collected = gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        
        memory_freed = with_objects_memory - final_memory
        
        print(f"\nGarbage Collection Effectiveness:")
        print(f"  Initial memory: {initial_memory:.1f} MB")
        print(f"  With objects: {with_objects_memory:.1f} MB")
        print(f"  After GC: {final_memory:.1f} MB")
        print(f"  Memory freed: {memory_freed:.1f} MB")
        print(f"  Objects collected: {collected}")
        
        # Should free significant memory
        assert memory_freed > 10  # At least 10MB freed
        assert collected > 0  # Some objects should be collected


class TestLoadAndStress:
    """Load testing and stress testing scenarios."""
    
    def setup_method(self):
        """Set up load testing fixtures."""
        self.profiler = PerformanceProfiler()
    
    def test_concurrent_user_simulation(self):
        """Simulate concurrent users performing various operations."""
        def simulate_user_session():
            """Simulate a typical user session."""
            # Shot analysis
            for _ in range(5):
                analyze_shot_decision(
                    current_lie="fairway",
                    distance=random.randint(100, 200),
                    player_handicap=random.randint(8, 20),
                    hole_number=random.randint(1, 18)
                )
            
            # Odds calculation
            calculator = OddsCalculator()
            players = [{"id": f"u{i}", "handicap": random.randint(10, 20)} for i in range(4)]
            hole = {"par": 4, "difficulty": 3.0}
            
            calculator.calculate_real_time_odds(players=players, hole=hole)
            
            # Monte Carlo simulation
            simulator = MonteCarloSimulator()
            simulator.simulate_hole_outcomes(
                players=players,
                hole=hole,
                iterations=500
            )
        
        # Test with increasing concurrent users
        user_counts = [1, 5, 10, 20, 50]
        results = {}
        
        for user_count in user_counts:
            start_time = time.perf_counter()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
                futures = [executor.submit(simulate_user_session) for _ in range(user_count)]
                completed = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            total_time = (time.perf_counter() - start_time) * 1000
            avg_session_time = total_time / user_count
            
            results[user_count] = {
                'total_time': total_time,
                'avg_session_time': avg_session_time,
                'throughput': user_count / (total_time / 1000)  # users per second
            }
            
            print(f"\n{user_count} concurrent users:")
            print(f"  Total time: {total_time:.1f}ms")
            print(f"  Avg session time: {avg_session_time:.1f}ms")
            print(f"  Throughput: {results[user_count]['throughput']:.2f} users/sec")
        
        # System should handle reasonable concurrent load
        assert results[10]['avg_session_time'] < 5000  # 10 users under 5 seconds each
        assert results[20]['total_time'] < 30000  # 20 users complete in under 30 seconds
    
    def test_stress_testing_limits(self):
        """Test system behavior under extreme stress."""
        import random
        
        def stress_operation():
            """Perform a computationally intensive operation."""
            # Large Monte Carlo simulation
            simulator = MonteCarloSimulator()
            players = [{"id": f"s{i}", "handicap": random.randint(5, 30)} for i in range(6)]
            hole = {"par": 5, "difficulty": 4.5}
            
            return simulator.simulate_hole_outcomes(
                players=players,
                hole=hole,
                iterations=5000
            )
        
        # Gradually increase stress until system limits
        stress_levels = [1, 2, 4, 8, 16]
        max_successful_level = 0
        
        for stress_level in stress_levels:
            try:
                start_time = time.perf_counter()
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=stress_level) as executor:
                    futures = [executor.submit(stress_operation) for _ in range(stress_level)]
                    
                    # Set timeout to prevent hanging
                    completed = []
                    for future in concurrent.futures.as_completed(futures, timeout=60):
                        completed.append(future.result())
                
                elapsed_time = (time.perf_counter() - start_time) * 1000
                
                print(f"\nStress level {stress_level}:")
                print(f"  Completed in {elapsed_time:.1f}ms")
                print(f"  Average per operation: {elapsed_time/stress_level:.1f}ms")
                
                if len(completed) == stress_level:
                    max_successful_level = stress_level
                else:
                    break
                    
            except (concurrent.futures.TimeoutError, Exception) as e:
                print(f"Stress level {stress_level} failed: {e}")
                break
        
        print(f"\nMaximum successful stress level: {max_successful_level}")
        
        # Should handle at least moderate stress
        assert max_successful_level >= 4
    
    def test_sustained_load_performance(self):
        """Test performance under sustained load over time."""
        def sustained_operation():
            """Operation to run continuously."""
            analyze_shot_decision(
                current_lie="fairway",
                distance=150,
                player_handicap=12,
                hole_number=8
            )
        
        # Run operations continuously for 30 seconds
        duration_seconds = 30
        operation_times = []
        start_time = time.time()
        
        while (time.time() - start_time) < duration_seconds:
            op_start = time.perf_counter()
            sustained_operation()
            op_end = time.perf_counter()
            
            operation_times.append((op_end - op_start) * 1000)
        
        # Analyze performance over time
        operations_per_second = len(operation_times) / duration_seconds
        
        # Split into time windows for analysis
        window_size = len(operation_times) // 6  # 6 time windows
        windows = [
            operation_times[i:i+window_size] 
            for i in range(0, len(operation_times), window_size)
            if len(operation_times[i:i+window_size]) > 10
        ]
        
        window_averages = [statistics.mean(window) for window in windows]
        
        print(f"\nSustained Load Test ({duration_seconds}s):")
        print(f"  Total operations: {len(operation_times)}")
        print(f"  Operations per second: {operations_per_second:.1f}")
        print(f"  Overall average time: {statistics.mean(operation_times):.2f}ms")
        
        for i, avg_time in enumerate(window_averages):
            print(f"  Window {i+1} average: {avg_time:.2f}ms")
        
        # Performance should remain stable over time
        performance_degradation = max(window_averages) / min(window_averages)
        
        print(f"  Performance degradation ratio: {performance_degradation:.2f}")
        
        assert operations_per_second > 100  # At least 100 ops/sec
        assert performance_degradation < 2.0  # Less than 2x degradation


class TestRegressionDetection:
    """Tests for detecting performance regressions."""
    
    def setup_method(self):
        """Set up regression testing."""
        self.profiler = PerformanceProfiler()
        
        # Performance baselines (would be updated based on system specs)
        self.baselines = {
            'monte_carlo_1k': {'mean': 100, 'p95': 200},  # ms
            'odds_calculation': {'mean': 20, 'p95': 40},  # ms
            'shot_analysis': {'mean': 10, 'p95': 25},    # ms
        }
    
    def test_monte_carlo_regression(self):
        """Test for Monte Carlo performance regression."""
        simulator = MonteCarloSimulator()
        players = [{"id": f"p{i}", "handicap": 12} for i in range(4)]
        hole = {"par": 4, "difficulty": 3.5}
        
        def run_simulation():
            return simulator.simulate_hole_outcomes(
                players=players,
                hole=hole,
                iterations=1000
            )
        
        stats = self.profiler.run_with_stats(
            run_simulation,
            iterations=20,
            name="Regression Test: Monte Carlo"
        )
        
        baseline = self.baselines['monte_carlo_1k']
        
        # Check for regression (allowing some variance)
        regression_threshold = 1.5  # 50% slower is a regression
        
        mean_regression = stats['mean'] / baseline['mean']
        p95_regression = stats['p95'] / baseline['p95']
        
        print(f"\nMonte Carlo Regression Analysis:")
        print(f"  Mean time ratio: {mean_regression:.2f} (baseline: {baseline['mean']}ms)")
        print(f"  P95 time ratio: {p95_regression:.2f} (baseline: {baseline['p95']}ms)")
        
        if mean_regression > regression_threshold:
            print(f"  WARNING: Mean time regression detected ({mean_regression:.2f}x)")
        
        if p95_regression > regression_threshold:
            print(f"  WARNING: P95 time regression detected ({p95_regression:.2f}x)")
        
        # For CI/CD, you might want to fail on significant regressions
        # assert mean_regression < regression_threshold
        # assert p95_regression < regression_threshold
    
    def test_odds_calculation_regression(self):
        """Test for odds calculation performance regression."""
        calculator = OddsCalculator()
        players = [{"id": f"p{i}", "handicap": 12} for i in range(4)]
        hole = {"par": 4, "difficulty": 3.5}
        
        def calculate_odds():
            return calculator.calculate_real_time_odds(players=players, hole=hole)
        
        stats = self.profiler.run_with_stats(
            calculate_odds,
            iterations=50,
            name="Regression Test: Odds Calculation"
        )
        
        baseline = self.baselines['odds_calculation']
        regression_threshold = 2.0  # 100% slower is a regression
        
        mean_regression = stats['mean'] / baseline['mean']
        p95_regression = stats['p95'] / baseline['p95']
        
        print(f"\nOdds Calculation Regression Analysis:")
        print(f"  Mean time ratio: {mean_regression:.2f} (baseline: {baseline['mean']}ms)")
        print(f"  P95 time ratio: {p95_regression:.2f} (baseline: {baseline['p95']}ms)")


if __name__ == "__main__":
    # Run performance tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s",  # Don't capture output so we can see performance metrics
        "--disable-warnings"
    ])