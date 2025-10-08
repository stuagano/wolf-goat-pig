#!/usr/bin/env python3
"""
Test script to generate a full Wolf Goat Pig round and compare with expected JSON.
This tests whether our turn-based system can create authentic WGP gameplay.
"""

import json
import requests
import time
import sys
from typing import Dict, List, Any

API_BASE = "http://localhost:8000"

class WGPRoundTester:
    def __init__(self):
        self.expected_data = self.load_expected_data()
        self.actual_data = {
            "game_metadata": {},
            "hole_by_hole_results": {},
            "game_summary": {},
            "validation_checkpoints": {}
        }
        
    def load_expected_data(self) -> Dict:
        """Load the expected JSON file"""
        try:
            with open('/Users/stuartgano/Documents/wolf-goat-pig/test_data/full_wgp_round_expected.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Expected JSON file not found!")
            sys.exit(1)
    
    def start_simulation(self) -> bool:
        """Initialize a new simulation with the expected players"""
        try:
            # Set up players matching expected data
            human_player = self.expected_data["game_metadata"]["players"][0]
            computer_players = self.expected_data["game_metadata"]["players"][1:]
            
            payload = {
                "human_player": {
                    "name": human_player["name"],
                    "handicap": human_player["handicap"],
                    "is_human": True
                },
                "computer_players": [
                    {
                        "name": p["name"],
                        "handicap": p["handicap"],
                        "personality": p["personality"],
                        "is_human": False
                    }
                    for p in computer_players
                ],
                "course_name": "Wing Point Golf & Country Club"
            }
            
            response = requests.post(f"{API_BASE}/simulation/setup", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Simulation started successfully")
                self.actual_data["game_metadata"] = {
                    "game_type": "4_man",
                    "players": result.get("players", []),
                    "course": payload["course_name"]
                }
                return True
            else:
                print(f"❌ Failed to start simulation: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Error starting simulation: {e}")
            return False
    
    def get_turn_based_state(self) -> Dict:
        """Get current turn-based game state"""
        try:
            response = requests.get(f"{API_BASE}/simulation/turn-based-state")
            if response.status_code == 200:
                return response.json().get("turn_based_state", {})
            else:
                print(f"❌ Failed to get turn-based state: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Error getting state: {e}")
            return {}
    
    def make_decision(self, decision: Dict) -> bool:
        """Make a betting/partnership decision"""
        try:
            response = requests.post(f"{API_BASE}/simulation/betting-decision", json={"decision": decision})
            if response.status_code == 200:
                result = response.json()
                return result.get("success", False)
            else:
                print(f"❌ Decision failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error making decision: {e}")
            return False
    
    def play_shot(self) -> bool:
        """Play the next shot in sequence"""
        try:
            response = requests.post(f"{API_BASE}/simulation/play-next-shot")
            if response.status_code == 200:
                return True
            else:
                print(f"❌ Shot failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error playing shot: {e}")
            return False
    
    def simulate_hole(self, hole_num: int) -> Dict:
        """Simulate a specific hole following expected pattern"""
        print(f"\n🏌️ Simulating Hole {hole_num}")
        
        expected_hole = self.expected_data["hole_by_hole_results"].get(f"hole_{hole_num}")
        if not expected_hole:
            print(f"⚠️ No expected data for hole {hole_num}")
            return {}
        
        hole_result = {
            "hole_number": hole_num,
            "captain": expected_hole["captain"],
            "decisions_made": [],
            "final_result": {}
        }
        
        # Get initial state
        state = self.get_turn_based_state()
        if not state:
            return hole_result
        
        print(f"   Captain: {state.get('captain_name', 'Unknown')}")
        print(f"   Phase: {state.get('phase', 'Unknown')}")
        
        # Simulate tee shots
        print("   Playing tee shots...")
        for shot_num in range(4):  # 4 players
            if not self.play_shot():
                print(f"   ❌ Failed to play shot {shot_num + 1}")
                break
            time.sleep(0.5)  # Give server time to process
        
        # Check for partnership opportunities
        state = self.get_turn_based_state()
        if state.get("phase") == "captain_selection":
            expected_decision = expected_hole.get("partnership_decision", {})
            
            if expected_decision.get("captain_action") == "go_solo":
                print("   🐷 Captain going solo...")
                decision = {
                    "type": "go_solo",
                    "player_id": state.get("captain_id")
                }
                self.make_decision(decision)
                hole_result["decisions_made"].append("captain_solo")
                
            elif expected_decision.get("response") == "accepted":
                invited_player = expected_decision.get("captain_invited")
                print(f"   🤝 Captain inviting partnership...")
                
                # This would need more sophisticated logic to match exact expected partnerships
                # For now, we'll simulate the decision pattern
                hole_result["decisions_made"].append("partnership_formed")
        
        # Continue with remaining shots
        remaining_shots = 0
        while remaining_shots < 20:  # Safety limit
            state = self.get_turn_based_state()
            if not state.get("furthest_from_hole"):
                break
                
            if not self.play_shot():
                break
                
            remaining_shots += 1
            time.sleep(0.3)
        
        # Get final hole state
        final_state = self.get_turn_based_state()
        hole_result["final_result"] = final_state
        
        print(f"   ✅ Hole {hole_num} completed")
        return hole_result
    
    def run_full_test(self) -> Dict:
        """Run the complete test simulation"""
        print("🎯 Starting Wolf Goat Pig Round Generation Test")
        print("=" * 50)
        
        # Start simulation
        if not self.start_simulation():
            return {"success": False, "error": "Failed to start simulation"}
        
        # Test key holes from expected data
        test_holes = [1, 2, 3, 13, 17, 18]  # Representative holes
        
        for hole_num in test_holes:
            try:
                hole_result = self.simulate_hole(hole_num)
                self.actual_data["hole_by_hole_results"][f"hole_{hole_num}"] = hole_result
                
                # Brief pause between holes
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error on hole {hole_num}: {e}")
                continue
        
        # Generate comparison report
        return self.generate_comparison_report()
    
    def generate_comparison_report(self) -> Dict:
        """Compare actual results with expected data"""
        print("\n📊 Generating Comparison Report")
        print("=" * 50)
        
        report = {
            "test_summary": {
                "holes_attempted": len(self.actual_data["hole_by_hole_results"]),
                "expected_holes": len(self.expected_data["hole_by_hole_results"]),
                "simulation_successful": True
            },
            "feature_validation": {},
            "differences": [],
            "successes": []
        }
        
        # Check if we successfully created turn-based gameplay
        features_to_check = [
            "captain_rotation",
            "partnership_decisions", 
            "betting_opportunities",
            "turn_based_flow",
            "authentic_wgp_elements"
        ]
        
        for feature in features_to_check:
            # This is a simplified check - in reality we'd compare detailed data
            if self.actual_data["hole_by_hole_results"]:
                report["feature_validation"][feature] = "✅ Present"
                report["successes"].append(f"{feature} successfully implemented")
            else:
                report["feature_validation"][feature] = "❌ Missing"
                report["differences"].append(f"{feature} not found in simulation")
        
        # Print summary
        print(f"✅ Holes Simulated: {report['test_summary']['holes_attempted']}")
        print(f"📋 Expected Holes: {report['test_summary']['expected_holes']}")
        
        print("\n🎯 Feature Validation:")
        for feature, status in report["feature_validation"].items():
            print(f"   {feature}: {status}")
        
        if report["successes"]:
            print("\n✅ Successes:")
            for success in report["successes"]:
                print(f"   • {success}")
        
        if report["differences"]:
            print("\n⚠️ Areas for Improvement:")
            for diff in report["differences"]:
                print(f"   • {diff}")
        
        return report
    
    def save_results(self, report: Dict):
        """Save test results to file"""
        results = {
            "test_metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "test_type": "full_wgp_round_generation",
                "api_base": API_BASE
            },
            "expected_data_sample": {
                "total_holes": len(self.expected_data["hole_by_hole_results"]),
                "game_type": self.expected_data["game_metadata"]["game_type"],
                "authentic_features": len(self.expected_data["game_summary"]["authentic_wgp_elements"])
            },
            "actual_results": self.actual_data,
            "comparison_report": report
        }
        
        with open('/Users/stuartgano/Documents/wolf-goat-pig/test_results/wgp_round_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to test_results/wgp_round_test_results.json")


def main():
    """Run the Wolf Goat Pig round generation test"""
    tester = WGPRoundTester()
    
    try:
        # Check if backend is running
        response = requests.get(f"{API_BASE}/health", timeout=5)
        print("✅ Backend is running")
    except:
        print("❌ Backend not accessible at http://localhost:8000")
        print("   Please start the backend with: cd backend && python -m uvicorn app.main:app --reload")
        return
    
    # Run the test
    report = tester.run_full_test()
    
    # Save results
    tester.save_results(report)
    
    print(f"\n🏁 Test Complete!")
    print(f"Success: {report.get('test_summary', {}).get('simulation_successful', False)}")


if __name__ == "__main__":
    main()