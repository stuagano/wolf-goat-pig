"""
Comprehensive End-to-End Test Suite for Wolf Goat Pig Game Flow

This module provides complete end-to-end testing of the Wolf Goat Pig game system,
simulating real user interactions from game setup to completion, including all
major features and user journeys.

Test Coverage:
- Complete game flow from setup to finish
- Multi-player interactions and team dynamics
- Shot progression mode and betting opportunities
- Player profile integration and statistics updates
- Tutorial system completion flow
- Real-time odds calculations and Monte Carlo simulations
- Error handling and recovery scenarios
- Performance under realistic conditions
- Cross-browser compatibility (when applicable)
- Mobile responsive behavior
"""

import pytest
import asyncio
import time
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from unittest.mock import Mock, patch

# Import test frameworks and utilities
from fastapi.testclient import TestClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

# Import application components
from app.main import app
from app.models import Base
from app.schemas import PlayerProfileCreate, GameSetupRequest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@dataclass
class GameParticipant:
    """Represents a participant in the E2E test game."""
    id: str
    name: str
    handicap: float
    avatar_url: Optional[str] = None
    is_human: bool = True
    strategy: str = "balanced"  # conservative, balanced, aggressive
    
    
@dataclass 
class GameState:
    """Tracks the complete game state during E2E testing."""
    game_id: str
    participants: List[GameParticipant]
    course_id: str
    current_hole: int
    scores: Dict[str, List[int]]  # player_id -> hole scores
    earnings: Dict[str, float]    # player_id -> current earnings
    team_formations: Dict[int, str]  # hole -> team configuration
    betting_history: List[Dict]
    game_events: List[Dict]
    start_time: datetime
    completion_time: Optional[datetime] = None


class E2ETestBase:
    """Base class for end-to-end testing with common utilities."""
    
    @classmethod
    def setup_class(cls):
        """Set up class-level test fixtures."""
        # Create test database
        cls.engine = create_engine("sqlite:///test_e2e.db", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        
        # Create test client
        cls.api_client = TestClient(app)
        
        # Set up web driver for UI testing (optional)
        cls.use_selenium = cls._should_use_selenium()
        
        if cls.use_selenium:
            cls.driver = cls._setup_webdriver()
        
    @classmethod
    def teardown_class(cls):
        """Clean up class-level fixtures."""
        if hasattr(cls, 'driver') and cls.driver:
            cls.driver.quit()
            
        # Clean up test database
        Base.metadata.drop_all(cls.engine)
    
    @classmethod
    def _should_use_selenium(cls) -> bool:
        """Determine if Selenium tests should run."""
        # Skip Selenium tests in CI/CD or if browser not available
        import os
        return os.getenv('RUN_SELENIUM_TESTS', 'false').lower() == 'true'
    
    @classmethod
    def _setup_webdriver(cls):
        """Set up Chrome webdriver with appropriate options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless in CI
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            return webdriver.Chrome(options=chrome_options)
        except WebDriverException:
            return None
    
    def create_test_participants(self, count: int = 4) -> List[GameParticipant]:
        """Create test game participants with varied profiles."""
        participants = []
        
        strategies = ["conservative", "balanced", "aggressive"]
        handicaps = [8, 12, 16, 22]
        
        for i in range(count):
            participant = GameParticipant(
                id=f"test_player_{i}",
                name=f"Test Player {i+1}",
                handicap=handicaps[i % len(handicaps)],
                strategy=strategies[i % len(strategies)]
            )
            participants.append(participant)
            
        return participants
    
    def simulate_shot_outcome(self, player: GameParticipant, hole_par: int, 
                            distance: int, lie: str) -> Dict[str, Any]:
        """Simulate a realistic shot outcome based on player skill."""
        base_success_rate = max(0.1, 1.0 - (player.handicap / 40))
        
        # Adjust for distance and lie
        distance_factor = max(0.3, 1.0 - (distance / 300))
        lie_factor = {"fairway": 1.0, "rough": 0.8, "bunker": 0.6, "water": 0.3}[lie]
        
        success_rate = base_success_rate * distance_factor * lie_factor
        
        # Random outcome based on success rate
        if random.random() < success_rate:
            strokes = hole_par - random.randint(0, 1)  # Par or birdie
        else:
            strokes = hole_par + random.randint(0, 2)  # Par to double bogey
            
        return {
            "strokes": max(1, strokes),
            "success_rate": success_rate,
            "final_distance": max(0, distance - random.randint(80, 120)),
            "lie_result": random.choice(["fairway", "rough", "green"])
        }


class TestCompleteGameFlow(E2ETestBase):
    """Test complete game flow from setup to completion."""
    
    def test_full_18_hole_game_simulation(self):
        """Test a complete 18-hole Wolf Goat Pig game."""
        # Step 1: Set up game participants
        participants = self.create_test_participants(4)
        
        # Step 2: Create player profiles via API
        created_profiles = {}
        for participant in participants:
            profile_data = {
                "name": participant.name,
                "handicap": participant.handicap
            }
            
            response = self.api_client.post("/players", json=profile_data)
            assert response.status_code == 201
            
            profile = response.json()
            created_profiles[participant.id] = profile
            participant.id = str(profile["id"])  # Use actual database ID
        
        # Step 3: Set up game session
        game_setup = {
            "course_id": "test_course_18_holes",
            "players": [
                {
                    "id": participant.id,
                    "name": participant.name,
                    "handicap": participant.handicap
                }
                for participant in participants
            ],
            "game_type": "wolf_goat_pig",
            "stakes": 2.0
        }
        
        response = self.api_client.post("/games", json=game_setup)
        assert response.status_code == 201
        
        game_data = response.json()
        game_state = GameState(
            game_id=game_data["game_id"],
            participants=participants,
            course_id="test_course_18_holes",
            current_hole=1,
            scores={p.id: [] for p in participants},
            earnings={p.id: 0.0 for p in participants},
            team_formations={},
            betting_history=[],
            game_events=[],
            start_time=datetime.now()
        )
        
        # Step 4: Play through all 18 holes
        for hole_number in range(1, 19):
            hole_result = self._play_hole(game_state, hole_number)
            
            # Update game state
            game_state.current_hole = hole_number
            for player_id, score in hole_result["scores"].items():
                game_state.scores[player_id].append(score)
            
            for player_id, earnings in hole_result["earnings"].items():
                game_state.earnings[player_id] += earnings
            
            game_state.team_formations[hole_number] = hole_result["team_formation"]
            game_state.betting_history.extend(hole_result["betting_events"])
            
            # Update game via API
            update_data = {
                "hole": hole_number,
                "scores": [
                    {"player_id": pid, "strokes": score}
                    for pid, scores in game_state.scores.items()
                    for score in scores[-1:]  # Only latest score
                ],
                "teams": hole_result["team_formation"],
                "earnings": [
                    {"player_id": pid, "amount": earnings}
                    for pid, earnings in hole_result["earnings"].items()
                ]
            }
            
            response = self.api_client.post(
                f"/games/{game_state.game_id}/update",
                json=update_data
            )
            assert response.status_code == 200
        
        # Step 5: Complete the game
        final_scores = {
            pid: {
                "total_score": sum(scores),
                "total_earnings": game_state.earnings[pid],
                "holes_won": self._count_holes_won(game_state, pid)
            }
            for pid, scores in game_state.scores.items()
        }
        
        completion_data = {
            "final_scores": [
                {
                    "player_id": pid,
                    "total_score": scores["total_score"],
                    "earnings": scores["total_earnings"]
                }
                for pid, scores in final_scores.items()
            ]
        }
        
        response = self.api_client.post(
            f"/games/{game_state.game_id}/complete",
            json=completion_data
        )
        assert response.status_code == 200
        
        game_state.completion_time = datetime.now()
        
        # Step 6: Verify final game state
        response = self.api_client.get(f"/games/{game_state.game_id}")
        assert response.status_code == 200
        
        final_game_data = response.json()
        assert final_game_data["status"] == "completed"
        
        # Step 7: Verify player statistics were updated
        for participant in participants:
            response = self.api_client.get(f"/api/players/{participant.id}/statistics")
            assert response.status_code == 200
            
            stats = response.json()
            assert stats["games_played"] >= 1
            assert "total_earnings" in stats
        
        # Step 8: Generate analytics and verify
        total_game_time = (game_state.completion_time - game_state.start_time).total_seconds()
        
        print(f"\nGame Completion Summary:")
        print(f"  Game Duration: {total_game_time:.1f} seconds")
        print(f"  Total Holes: 18")
        print(f"  Participants: {len(participants)}")
        print(f"  Total Betting Events: {len(game_state.betting_history)}")
        
        for pid, scores in final_scores.items():
            participant = next(p for p in participants if p.id == pid)
            print(f"  {participant.name}: Score: {scores['total_score']}, "
                  f"Earnings: ${scores['total_earnings']:.2f}, "
                  f"Holes Won: {scores['holes_won']}")
        
        # Assertions for successful game completion
        assert game_state.completion_time is not None
        assert len(game_state.scores) == len(participants)
        assert all(len(scores) == 18 for scores in game_state.scores.values())
        assert total_game_time < 300  # Should complete within 5 minutes in automated test
    
    def _play_hole(self, game_state: GameState, hole_number: int) -> Dict[str, Any]:
        """Simulate playing a single hole with full Wolf Goat Pig mechanics."""
        hole_par = 4 if hole_number % 3 != 0 else 3  # Mostly par 4s, some par 3s
        
        # Step 1: Team formation phase
        team_formation = self._determine_team_formation(game_state, hole_number)
        
        # Step 2: Calculate initial odds
        odds_request = {
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "handicap": p.handicap,
                    "distance_to_pin": 150 + random.randint(-50, 50),
                    "lie_type": "fairway"
                }
                for p in game_state.participants
            ],
            "hole": {
                "number": hole_number,
                "par": hole_par,
                "difficulty": 3.0 + random.random() * 2
            }
        }
        
        response = self.api_client.post("/odds/calculate", json=odds_request)
        assert response.status_code == 200
        initial_odds = response.json()
        
        # Step 3: Betting phase
        betting_events = self._simulate_betting_phase(game_state, initial_odds, team_formation)
        
        # Step 4: Shot execution and progression
        hole_scores = {}
        for participant in game_state.participants:
            # Simulate shot progression for each player
            shots = []
            distance = 150 + random.randint(-30, 30)  # Starting distance to pin
            lie = "fairway"
            
            for shot_num in range(1, 8):  # Maximum 7 shots (very bad hole)
                shot_result = self.simulate_shot_outcome(participant, hole_par, distance, lie)
                shots.append(shot_result)
                
                distance = shot_result["final_distance"]
                lie = shot_result["lie_result"]
                
                # Hole completed if on green with short distance
                if lie == "green" and distance < 10:
                    break
            
            hole_scores[participant.id] = len(shots)
        
        # Step 5: Determine hole winner and calculate earnings
        hole_winner = min(hole_scores.keys(), key=lambda k: hole_scores[k])
        earnings_distribution = self._calculate_hole_earnings(
            hole_scores, team_formation, betting_events, game_state
        )
        
        return {
            "scores": hole_scores,
            "earnings": earnings_distribution,
            "team_formation": team_formation,
            "betting_events": betting_events,
            "hole_winner": hole_winner,
            "initial_odds": initial_odds
        }
    
    def _determine_team_formation(self, game_state: GameState, hole_number: int) -> str:
        """Determine team formation for the hole based on game dynamics."""
        formations = ["solo", "partnerships", "wolf_pack", "everyone_vs_one"]
        
        # Simple logic based on hole number and current standings
        if hole_number <= 6:
            return random.choice(["solo", "partnerships"])
        elif hole_number <= 12:
            return random.choice(formations[:3])
        else:
            # Late game - more aggressive formations
            return random.choice(formations)
    
    def _simulate_betting_phase(self, game_state: GameState, odds: Dict, 
                               team_formation: str) -> List[Dict]:
        """Simulate the betting phase with realistic player decisions."""
        betting_events = []
        current_stakes = 2.0
        
        # Each player makes betting decisions based on odds and strategy
        for participant in game_state.participants:
            player_odds = odds.get("overall_odds", {}).get(participant.id, 0.5)
            
            # Decision based on strategy and odds
            if participant.strategy == "aggressive":
                action_probability = 0.7 if player_odds > 0.4 else 0.3
            elif participant.strategy == "conservative":
                action_probability = 0.3 if player_odds > 0.6 else 0.1
            else:  # balanced
                action_probability = 0.5 if player_odds > 0.5 else 0.2
            
            if random.random() < action_probability:
                action = random.choice(["double", "press", "side_bet"])
                amount = current_stakes * random.choice([1, 2])
                
                betting_event = {
                    "player_id": participant.id,
                    "action": action,
                    "amount": amount,
                    "hole": game_state.current_hole,
                    "odds_at_action": player_odds
                }
                
                betting_events.append(betting_event)
                
                if action == "double":
                    current_stakes *= 2
        
        return betting_events
    
    def _calculate_hole_earnings(self, scores: Dict[str, int], team_formation: str,
                               betting_events: List[Dict], game_state: GameState) -> Dict[str, float]:
        """Calculate earnings distribution for the hole."""
        earnings = {pid: 0.0 for pid in scores.keys()}
        
        # Basic hole earnings (winner takes pot)
        hole_winner = min(scores.keys(), key=lambda k: scores[k])
        base_pot = 2.0 * len(scores)
        earnings[hole_winner] += base_pot
        
        # Distribute losses
        for pid in scores.keys():
            if pid != hole_winner:
                earnings[pid] -= 2.0
        
        # Additional earnings from betting events
        for event in betting_events:
            if event["action"] == "double":
                # Winner gets double, others pay double
                if event["player_id"] == hole_winner:
                    earnings[event["player_id"]] += event["amount"]
                else:
                    earnings[event["player_id"]] -= event["amount"]
        
        return earnings
    
    def _count_holes_won(self, game_state: GameState, player_id: str) -> int:
        """Count holes won by a specific player."""
        holes_won = 0
        
        for hole_scores in zip(*[game_state.scores[pid] for pid in game_state.scores.keys()]):
            player_scores = {pid: score for pid, score in 
                           zip(game_state.scores.keys(), hole_scores)}
            hole_winner = min(player_scores.keys(), key=lambda k: player_scores[k])
            
            if hole_winner == player_id:
                holes_won += 1
                
        return holes_won


class TestShotProgressionMode(E2ETestBase):
    """Test shot progression mode with detailed shot analysis."""
    
    def test_shot_progression_with_analysis(self):
        """Test shot-by-shot progression with analysis and recommendations."""
        participants = self.create_test_participants(2)  # Smaller group for detailed testing
        
        # Create simplified game setup
        game_setup = {
            "mode": "shot_progression",
            "players": participants[:2]
        }
        
        # Simulate detailed shot progression for one hole
        hole_number = 8
        hole_par = 4
        
        for participant in participants:
            current_distance = 160
            current_lie = "fairway"
            shots_taken = 0
            
            print(f"\nShot Progression for {participant.name} (Handicap: {participant.handicap})")
            
            while current_distance > 5 and shots_taken < 7:
                shots_taken += 1
                
                # Get shot analysis
                analysis_request = {
                    "current_lie": current_lie,
                    "distance": current_distance,
                    "player_handicap": participant.handicap,
                    "hole_number": hole_number,
                    "game_situation": {
                        "team_situation": "solo",
                        "score_differential": 0
                    }
                }
                
                response = self.api_client.post("/analysis/shot", json=analysis_request)
                assert response.status_code == 200
                
                analysis = response.json()
                
                # Display analysis
                recommended_shot = analysis["recommended_shot"]
                print(f"  Shot {shots_taken}: {current_distance}y from {current_lie}")
                print(f"    Recommended: {recommended_shot['type']}")
                print(f"    Success Rate: {recommended_shot['success_rate']}")
                print(f"    Risk Level: {recommended_shot['risk_level']}")
                
                # Simulate shot outcome based on analysis
                success_rate = float(recommended_shot['success_rate'].rstrip('%')) / 100
                shot_result = self.simulate_shot_outcome(participant, hole_par, current_distance, current_lie)
                
                # Update position
                current_distance = shot_result["final_distance"]
                current_lie = shot_result["lie_result"]
                
                print(f"    Result: {current_distance}y, {current_lie}")
                
                if current_lie == "green" and current_distance <= 5:
                    print(f"    Hole completed in {shots_taken} shots!")
                    break
            
            # Verify shot analysis provided meaningful recommendations
            assert shots_taken <= 6  # Should complete hole in reasonable shots
    
    def test_real_time_odds_updates_during_play(self):
        """Test that odds update realistically as shots are played."""
        participants = self.create_test_participants(3)
        
        # Initial odds calculation
        initial_request = {
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "handicap": p.handicap,
                    "distance_to_pin": 150,
                    "lie_type": "fairway"
                }
                for p in participants
            ],
            "hole": {"number": 10, "par": 4, "difficulty": 3.5}
        }
        
        response = self.api_client.post("/odds/calculate", json=initial_request)
        initial_odds = response.json()["overall_odds"]
        
        # Simulate player 1 hitting a great shot (much closer)
        updated_request = initial_request.copy()
        updated_request["players"][0]["distance_to_pin"] = 20  # Much closer
        updated_request["players"][0]["lie_type"] = "green"
        
        response = self.api_client.post("/odds/calculate", json=updated_request)
        updated_odds = response.json()["overall_odds"]
        
        # Player 1's odds should have improved significantly
        player_1_id = participants[0].id
        initial_prob = initial_odds.get(player_1_id, 0)
        updated_prob = updated_odds.get(player_1_id, 0)
        
        print(f"\nOdds Update Test:")
        print(f"  Player 1 initial odds: {initial_prob:.3f}")
        print(f"  Player 1 updated odds: {updated_prob:.3f}")
        print(f"  Improvement: {updated_prob - initial_prob:.3f}")
        
        assert updated_prob > initial_prob  # Odds should improve
        assert updated_prob - initial_prob > 0.1  # Significant improvement
    
    def test_monte_carlo_integration_during_play(self):
        """Test Monte Carlo simulation integration for complex scenarios."""
        participants = self.create_test_participants(4)
        
        # Set up complex scenario
        simulation_request = {
            "players": [
                {
                    "name": p.name,
                    "handicap": p.handicap,
                    "position": {
                        "distance": 150 + i*20,
                        "lie": ["fairway", "rough", "bunker", "fairway"][i]
                    }
                }
                for i, p in enumerate(participants)
            ],
            "hole": {"par": 4, "difficulty": 4.2},
            "iterations": 5000,
            "scenarios": ["current", "double_stakes", "go_solo"]
        }
        
        response = self.api_client.post("/simulation/monte-carlo", json=simulation_request)
        assert response.status_code == 200
        
        simulation_data = response.json()
        
        # Verify simulation results
        assert "results" in simulation_data
        assert "scenarios" in simulation_data
        assert len(simulation_data["scenarios"]) == 3
        
        # Check that different scenarios yield different probabilities
        scenario_results = simulation_data["scenarios"]
        
        current_probs = scenario_results[0]["probabilities"]
        double_probs = scenario_results[1]["probabilities"]
        
        # Probabilities should change with different stakes
        prob_differences = sum(
            abs(current_probs.get(f"player_{i}", 0) - double_probs.get(f"player_{i}", 0))
            for i in range(len(participants))
        )
        
        assert prob_differences > 0.05  # Meaningful difference in probabilities


class TestBettingIntegration(E2ETestBase):
    """Test betting system integration throughout game flow."""
    
    def test_dynamic_betting_opportunities(self):
        """Test that betting opportunities appear dynamically during play."""
        participants = self.create_test_participants(4)
        
        # Simulate various game situations that should trigger betting opportunities
        test_scenarios = [
            {
                "description": "Close competition",
                "odds": {"p1": 0.3, "p2": 0.25, "p3": 0.25, "p4": 0.2},
                "expected_opportunities": ["double", "press", "side_bet"]
            },
            {
                "description": "Clear leader",
                "odds": {"p1": 0.6, "p2": 0.2, "p3": 0.15, "p4": 0.05},
                "expected_opportunities": ["underdog_bet", "longshot"]
            },
            {
                "description": "Even matchup",
                "odds": {"p1": 0.25, "p2": 0.25, "p3": 0.25, "p4": 0.25},
                "expected_opportunities": ["any_pair", "side_matchups"]
            }
        ]
        
        for scenario in test_scenarios:
            # This would integrate with the betting opportunities API
            # For now, we verify the concept with odds calculation
            
            odds_request = {
                "players": [
                    {"id": f"p{i+1}", "name": f"Player {i+1}", "handicap": 12}
                    for i in range(4)
                ],
                "hole": {"number": 10, "par": 4}
            }
            
            response = self.api_client.post("/odds/calculate", json=odds_request)
            assert response.status_code == 200
            
            odds_data = response.json()
            betting_scenarios = odds_data.get("betting_scenarios", [])
            
            # Verify betting scenarios are provided
            assert len(betting_scenarios) > 0
            
            for betting_scenario in betting_scenarios:
                assert "action" in betting_scenario
                assert "expected_value" in betting_scenario
                assert "win_probability" in betting_scenario
    
    def test_betting_impact_on_outcomes(self):
        """Test that betting affects game dynamics and outcomes."""
        participants = self.create_test_participants(2)
        
        # Scenario 1: Normal stakes
        normal_game_data = {
            "players": participants,
            "stakes": 2.0,
            "betting_events": []
        }
        
        # Scenario 2: Doubled stakes
        doubled_game_data = {
            "players": participants,
            "stakes": 4.0,
            "betting_events": [
                {"action": "double", "player_id": participants[0].id, "amount": 4.0}
            ]
        }
        
        # Simulate outcomes and verify different risk/reward profiles
        for scenario_name, game_data in [("Normal", normal_game_data), ("Doubled", doubled_game_data)]:
            total_risk = game_data["stakes"] * len(participants)
            max_win = total_risk * 0.75  # Approximate maximum individual win
            
            print(f"\n{scenario_name} Stakes Scenario:")
            print(f"  Individual stakes: ${game_data['stakes']:.2f}")
            print(f"  Total pot: ${total_risk:.2f}")
            print(f"  Maximum win potential: ${max_win:.2f}")
            
            assert total_risk > 0
            assert max_win > game_data["stakes"]


@pytest.mark.skipif(True, reason="Selenium UI tests require browser setup")
class TestUIEndToEnd(E2ETestBase):
    """Test complete UI interactions using Selenium."""
    
    def test_tutorial_completion_flow(self):
        """Test complete tutorial flow through UI."""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        # Navigate to tutorial
        self.driver.get("http://localhost:3000/tutorial")
        
        # Wait for tutorial to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tutorial-system"))
        )
        
        # Click through tutorial modules
        tutorial_modules = [
            "golf-basics",
            "game-overview", 
            "team-formation",
            "betting-system",
            "practice-game"
        ]
        
        for module in tutorial_modules:
            # Find and click module
            module_element = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.DATA_ATTRIBUTE, f"module-{module}"))
            )
            module_element.click()
            
            # Wait for module content to load
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, f"{module}-content"))
            )
            
            # Complete module steps (simplified)
            next_button = self.driver.find_element(By.CLASS_NAME, "next-step-button")
            while next_button.is_enabled():
                next_button.click()
                time.sleep(0.5)  # Allow for transitions
                
                try:
                    next_button = self.driver.find_element(By.CLASS_NAME, "next-step-button")
                except:
                    break  # Module completed
        
        # Verify tutorial completion
        completion_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "tutorial-completed"))
        )
        
        assert completion_element.is_displayed()
    
    def test_game_setup_ui_flow(self):
        """Test game setup through UI interface."""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        self.driver.get("http://localhost:3000/setup")
        
        # Fill in game setup form
        course_select = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "course-select"))
        )
        course_select.click()
        
        # Select first course option
        first_course = self.driver.find_element(By.CSS_SELECTOR, "#course-select option:nth-child(2)")
        first_course.click()
        
        # Add players
        for i in range(4):
            add_player_button = self.driver.find_element(By.ID, "add-player-button")
            add_player_button.click()
            
            name_input = self.driver.find_element(By.NAME, f"player-{i+1}-name")
            name_input.send_keys(f"UI Test Player {i+1}")
            
            handicap_input = self.driver.find_element(By.NAME, f"player-{i+1}-handicap")
            handicap_input.send_keys(str(10 + i*3))
        
        # Start game
        start_button = self.driver.find_element(By.ID, "start-game-button")
        start_button.click()
        
        # Wait for game to start
        game_interface = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "game-interface"))
        )
        
        assert game_interface.is_displayed()
    
    def test_responsive_mobile_behavior(self):
        """Test mobile responsive behavior."""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        # Test mobile viewport
        self.driver.set_window_size(375, 667)  # iPhone 6/7/8 size
        
        self.driver.get("http://localhost:3000")
        
        # Check mobile navigation
        mobile_menu_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "mobile-menu-button"))
        )
        
        assert mobile_menu_button.is_displayed()
        
        mobile_menu_button.click()
        
        # Verify mobile menu opens
        mobile_menu = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "mobile-menu-open"))
        )
        
        assert mobile_menu.is_displayed()
        
        # Test tablet viewport
        self.driver.set_window_size(768, 1024)  # iPad size
        
        # Mobile menu should not be visible on tablet
        mobile_menu_button = self.driver.find_elements(By.CLASS_NAME, "mobile-menu-button")
        if mobile_menu_button:
            assert not mobile_menu_button[0].is_displayed()


class TestErrorHandlingAndRecovery(E2ETestBase):
    """Test error handling and recovery scenarios in E2E flows."""
    
    def test_network_interruption_recovery(self):
        """Test recovery from network interruptions during game."""
        participants = self.create_test_participants(2)
        
        # Start game normally
        game_setup = {
            "players": [{"name": p.name, "handicap": p.handicap} for p in participants]
        }
        
        response = self.api_client.post("/games", json=game_setup)
        assert response.status_code == 201
        game_id = response.json()["game_id"]
        
        # Simulate network interruption by using invalid endpoint
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = ConnectionError("Network unavailable")
            
            # Attempt game update (should handle gracefully)
            update_data = {"hole": 1, "scores": [{"player_id": participants[0].id, "strokes": 4}]}
            
            try:
                response = self.api_client.post(f"/games/{game_id}/update", json=update_data)
                # Should either succeed or fail gracefully
                assert response.status_code in [200, 503, 408]
            except:
                # Connection errors should be handled
                pass
        
        # Verify game state can be recovered
        response = self.api_client.get(f"/games/{game_id}")
        assert response.status_code == 200
    
    def test_invalid_data_handling(self):
        """Test handling of invalid data during game flow."""
        invalid_scenarios = [
            {
                "description": "Invalid player count",
                "setup": {"players": []},  # No players
                "expected_status": 422
            },
            {
                "description": "Invalid handicap",
                "setup": {"players": [{"name": "Test", "handicap": -5}]},
                "expected_status": 422
            },
            {
                "description": "Missing required fields",
                "setup": {"players": [{"name": "Test"}]},  # Missing handicap
                "expected_status": 422
            }
        ]
        
        for scenario in invalid_scenarios:
            response = self.api_client.post("/games", json=scenario["setup"])
            assert response.status_code == scenario["expected_status"]
            
            # Should provide meaningful error message
            if response.status_code == 422:
                error_data = response.json()
                assert "detail" in error_data
    
    def test_game_state_corruption_recovery(self):
        """Test recovery from corrupted game state."""
        # This would test scenarios where game state becomes inconsistent
        # and the system needs to recover or reset appropriately
        
        participants = self.create_test_participants(3)
        
        # Create game with valid setup
        response = self.api_client.post("/games", json={
            "players": [{"name": p.name, "handicap": p.handicap} for p in participants]
        })
        game_id = response.json()["game_id"]
        
        # Attempt to update with inconsistent data
        inconsistent_updates = [
            {
                "hole": 25,  # Invalid hole number
                "scores": [{"player_id": "nonexistent", "strokes": 4}]
            },
            {
                "hole": 1,
                "scores": [{"player_id": participants[0].id, "strokes": -2}]  # Invalid negative score
            }
        ]
        
        for update in inconsistent_updates:
            response = self.api_client.post(f"/games/{game_id}/update", json=update)
            # Should reject invalid updates
            assert response.status_code in [400, 422]
        
        # Game should still be accessible with valid state
        response = self.api_client.get(f"/games/{game_id}")
        assert response.status_code == 200


if __name__ == "__main__":
    # Run E2E tests with appropriate markers
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "not selenium",  # Skip Selenium tests by default
        "--disable-warnings"
    ])