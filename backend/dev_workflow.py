#!/usr/bin/env python3
"""
Development workflow for simulation engine
Interactive testing and debugging tools
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
from app.domain.player import Player
from app.state.betting_state import BettingState


class SimulationDebugger:
    """Interactive debugger for simulation engine"""
    
    def __init__(self):
        self.engine = WolfGoatPigSimulation()
        self.game_state = None
        self.human_player = Player("human", "You", 12.0)
        self.computer_configs = [
            {"id": "comp1", "name": "Alice", "handicap": 8.0, "personality": "balanced"},
            {"id": "comp2", "name": "Bob", "handicap": 15.0, "personality": "aggressive"},
            {"id": "comp3", "name": "Charlie", "handicap": 20.0, "personality": "conservative"}
        ]
    
    def setup_game(self, course_name='Wing Point Golf & Country Club'):
        """Setup a new game for testing"""
        print(f"🎮 Setting up game with course: {course_name}")
        self.game_state = self.engine.setup_simulation(
            self.human_player, 
            self.computer_configs, 
            course_name
        )
        print(f"✅ Game setup complete. Current hole: {self.game_state.current_hole}")
        print(f"✅ Captain: {self.game_state.player_manager.captain_id}")
        print(f"✅ Hitting order: {self.game_state.player_manager.hitting_order}")
    
    def show_game_state(self):
        """Display current game state"""
        if not self.game_state:
            print("❌ No game state. Run setup_game() first.")
            return
        
        print("\n📊 Current Game State:")
        print(f"   Hole: {self.game_state.current_hole}")
        print(f"   Captain: {self.game_state.player_manager.captain_id}")
        print(f"   Teams: {self.game_state.betting_state.teams}")
        print(f"   Base wager: {self.game_state.betting_state.base_wager}")
        print(f"   Doubled: {self.game_state.betting_state.doubled_status}")
        
        print("\n👥 Players:")
        for player in self.game_state.player_manager.players:
            print(f"   {player.name} (ID: {player.id}, Hdcp: {player.handicap}, Points: {player.points})")
    
    def test_partnership_scenario(self, scenario_type="decline"):
        """Test a specific partnership scenario"""
        if not self.game_state:
            self.setup_game()
        
        print(f"\n🤝 Testing Partnership {scenario_type.upper()} Scenario")
        print("=" * 50)
        
        # Setup partnership request
        self.game_state.betting_state.request_partner('comp1', 'human')
        print(f"✅ Partnership request: Alice asks You to be partner")
        print(f"   Teams state: {self.game_state.betting_state.teams}")
        
        # Human response
        if scenario_type == "decline":
            human_decisions = {'accept': False, 'partner_id': 'human'}
            print("✅ You decline the partnership")
        else:
            human_decisions = {'accept': True, 'partner_id': 'human'}
            print("✅ You accept the partnership")
        
        # Run simulation
        result_state, feedback, interaction = self.engine.simulate_hole(self.game_state, human_decisions)
        
        print(f"\n📋 Results:")
        print(f"   Final teams: {result_state.betting_state.teams}")
        print(f"   Base wager: {result_state.betting_state.base_wager}")
        print(f"   Doubled: {result_state.betting_state.doubled_status}")
        print(f"   Next hole: {result_state.current_hole}")
        
        # Update game state
        self.game_state = result_state
        
        return result_state, feedback, interaction
    
    def test_shot_simulation(self):
        """Test shot simulation in isolation"""
        print("\n🏌️ Testing Shot Simulation")
        print("=" * 30)
        
        from app.services.shot_simulator import ShotSimulator
        
        player = Player("test", "Test", 12.0)
        game_state = type('MockGameState', (), {'current_hole': 1})()
        
        # Test different shot types
        distances = [200, 150, 100, 50, 20, 5]
        
        for distance in distances:
            if distance > 100:
                result = ShotSimulator.simulate_approach_shot(player, distance, game_state)
                shot_type = "Approach"
            elif distance > 30:
                result = ShotSimulator._simulate_chip(player, distance, "fairway", game_state)
                shot_type = "Chip"
            else:
                result = ShotSimulator._simulate_putt(player, distance, game_state)
                shot_type = "Putt"
            
            print(f"   {shot_type} from {distance} yards: {result.remaining:.1f} remaining, {result.lie}, {result.shot_quality}")
    
    def interactive_test(self):
        """Interactive testing mode"""
        print("\n🎯 Interactive Testing Mode")
        print("=" * 30)
        print("Commands:")
        print("  setup - Setup new game")
        print("  state - Show current game state")
        print("  accept - Test partnership acceptance")
        print("  decline - Test partnership decline")
        print("  shots - Test shot simulation")
        print("  quit - Exit")
        
        while True:
            try:
                command = input("\n> ").strip().lower()
                
                if command == "quit":
                    break
                elif command == "setup":
                    self.setup_game()
                elif command == "state":
                    self.show_game_state()
                elif command == "accept":
                    self.test_partnership_scenario("accept")
                elif command == "decline":
                    self.test_partnership_scenario("decline")
                elif command == "shots":
                    self.test_shot_simulation()
                else:
                    print("❌ Unknown command")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()


def run_quick_validation():
    """Run quick validation of recent changes"""
    print("🔍 Quick Validation of Recent Changes")
    print("=" * 50)
    
    debugger = SimulationDebugger()
    
    # Test 1: Partnership decline
    print("\n1️⃣ Testing Partnership Decline")
    debugger.setup_game()
    result_state, feedback, interaction = debugger.test_partnership_scenario("decline")
    
    # Verify decline worked by checking feedback messages
    feedback_text = " ".join(feedback).lower()
    assert "decline" in feedback_text or "solo" in feedback_text or "pass" in feedback_text, "Should mention decline or solo in feedback"
    assert result_state.current_hole == 2, "Should advance to next hole"
    print("✅ Partnership decline validation PASSED")
    
    # Test 2: Partnership acceptance
    print("\n2️⃣ Testing Partnership Acceptance")
    debugger.setup_game()
    result_state, feedback, interaction = debugger.test_partnership_scenario("accept")
    
    # Verify acceptance worked by checking feedback messages
    feedback_text = " ".join(feedback).lower()
    assert "accept" in feedback_text or "team" in feedback_text or "absolutely" in feedback_text, "Should mention acceptance or team in feedback"
    assert result_state.current_hole == 2, "Should advance to next hole"
    print("✅ Partnership acceptance validation PASSED")
    
    # Test 3: Shot simulation
    print("\n3️⃣ Testing Shot Simulation")
    debugger.test_shot_simulation()
    print("✅ Shot simulation validation PASSED")
    
    print("\n🎉 All validations PASSED!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validate":
            run_quick_validation()
        elif command == "interactive":
            debugger = SimulationDebugger()
            debugger.interactive_test()
        elif command == "setup":
            debugger = SimulationDebugger()
            debugger.setup_game()
            debugger.show_game_state()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: validate, interactive, setup")
    else:
        print("Development Workflow for Simulation Engine")
        print("=" * 50)
        print("Usage:")
        print("  python dev_workflow.py validate    - Run quick validation")
        print("  python dev_workflow.py interactive - Interactive testing mode")
        print("  python dev_workflow.py setup       - Setup and show game state") 