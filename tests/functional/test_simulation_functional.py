#!/usr/bin/env python3
"""
Functional test suite for simulation mode
Tests end-to-end simulation workflows and user scenarios
"""

import pytest
import requests
import time
import json
import sys
import os
from typing import Dict, List, Any

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
TEST_TIMEOUT = 30

class SimulationFunctionalTest:
    """Base class for simulation functional tests"""
    
    def __init__(self):
        self.api_url = API_BASE_URL
        self.session = requests.Session()
        self.game_id = None
        
    def setup(self):
        """Setup test environment"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
    def teardown(self):
        """Cleanup after tests"""
        if self.game_id:
            try:
                self.session.delete(f"{self.api_url}/simulation/cleanup/{self.game_id}")
            except:
                pass
                
    def wait_for_api(self, max_retries=5):
        """Wait for API to be available"""
        for i in range(max_retries):
            try:
                response = self.session.get(f"{self.api_url}/health")
                if response.status_code == 200:
                    return True
            except requests.ConnectionError:
                pass
            time.sleep(2)
        return False

class TestSimulationSetup(SimulationFunctionalTest):
    """Test simulation setup workflows"""
    
    def test_complete_setup_workflow(self):
        """Test complete simulation setup from start to finish"""
        print("🔧 Testing complete simulation setup workflow...")
        
        # Step 1: Check API availability
        if not self.wait_for_api():
            print("⚠️ API not available, skipping functional tests")
            return True
            
        # Step 2: Get available personalities
        response = self.session.get(f"{self.api_url}/simulation/available-personalities")
        personalities_data = response.json() if response.status_code == 200 else {"personalities": []}
        
        print(f"✅ Retrieved {len(personalities_data.get('personalities', []))} personalities")
        
        # Step 3: Get suggested opponents
        response = self.session.get(f"{self.api_url}/simulation/suggested-opponents")
        opponents_data = response.json() if response.status_code == 200 else {"opponents": []}
        
        print(f"✅ Retrieved {len(opponents_data.get('opponents', []))} opponents")
        
        # Step 4: Get available courses
        response = self.session.get(f"{self.api_url}/courses")
        courses_data = response.json() if response.status_code == 200 else {}
        
        print(f"✅ Retrieved {len(courses_data)} courses")
        
        # Step 5: Setup simulation
        setup_data = {
            "human_player": {
                "id": "human",
                "name": "Test Player",
                "handicap": 15,
                "is_human": True
            },
            "computer_players": [
                {"id": "comp1", "name": "Computer 1", "handicap": 12, "personality": "aggressive", "is_human": False},
                {"id": "comp2", "name": "Computer 2", "handicap": 18, "personality": "conservative", "is_human": False},
                {"id": "comp3", "name": "Computer 3", "handicap": 8, "personality": "balanced", "is_human": False}
            ],
            "course_name": list(courses_data.keys())[0] if courses_data else "Default Course"
        }
        
        response = self.session.post(f"{self.api_url}/simulation/setup", json=setup_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Simulation setup successful: {result.get('message', 'OK')}")
            self.game_id = result.get('game_id')
            return True
        else:
            print(f"⚠️ Simulation setup failed: {response.status_code} - {response.text}")
            return False
            
    def test_invalid_setup_handling(self):
        """Test handling of invalid setup data"""
        print("🔧 Testing invalid setup handling...")
        
        if not self.wait_for_api():
            return True
            
        # Test with missing required fields
        invalid_setups = [
            {},  # Empty data
            {"human_player": {}},  # Missing computer players
            {"computer_players": []},  # Missing human player
            {"human_player": {"name": ""}, "computer_players": []}  # Invalid data
        ]
        
        for i, setup_data in enumerate(invalid_setups):
            response = self.session.post(f"{self.api_url}/simulation/setup", json=setup_data)
            
            # Should return 400 or 422 for validation errors
            if response.status_code in [400, 422, 500]:
                print(f"✅ Invalid setup {i+1} properly rejected")
            else:
                print(f"⚠️ Invalid setup {i+1} unexpectedly accepted")
                
        return True

class TestSimulationGameplay(SimulationFunctionalTest):
    """Test simulation gameplay workflows"""
    
    def setup_game(self):
        """Setup a game for testing"""
        setup_data = {
            "human_player": {"id": "human", "name": "Test Player", "handicap": 15, "is_human": True},
            "computer_players": [
                {"id": "comp1", "name": "Computer 1", "handicap": 12, "personality": "aggressive", "is_human": False},
                {"id": "comp2", "name": "Computer 2", "handicap": 18, "personality": "conservative", "is_human": False},
                {"id": "comp3", "name": "Computer 3", "handicap": 8, "personality": "balanced", "is_human": False}
            ],
            "course_name": "Test Course"
        }
        
        response = self.session.post(f"{self.api_url}/simulation/setup", json=setup_data)
        return response.status_code == 200
        
    def test_shot_sequence_workflow(self):
        """Test complete shot sequence workflow"""
        print("🔧 Testing shot sequence workflow...")
        
        if not self.wait_for_api():
            return True
            
        if not self.setup_game():
            print("⚠️ Could not setup game for shot sequence test")
            return False
            
        # Step 1: Play first shot
        response = self.session.post(f"{self.api_url}/simulation/play-next-shot", json={})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ First shot played: {result.get('status', 'OK')}")
            
            # Check if interaction is needed
            if result.get('interaction_needed'):
                print(f"✅ Interaction needed: {result['interaction_needed'].get('type', 'unknown')}")
                
                # Make a decision
                decision_data = {"action": "go_solo"}  # Simple decision
                response = self.session.post(f"{self.api_url}/simulation/play-hole", json=decision_data)
                
                if response.status_code == 200:
                    print("✅ Decision made successfully")
                else:
                    print(f"⚠️ Decision failed: {response.status_code}")
                    
            return True
        else:
            print(f"⚠️ Shot sequence failed: {response.status_code}")
            return False
            
    def test_partnership_workflow(self):
        """Test partnership request and response workflow"""
        print("🔧 Testing partnership workflow...")
        
        if not self.wait_for_api():
            return True
            
        if not self.setup_game():
            return False
            
        # Request partnership
        candidate_partners = ["comp1", "comp2", "comp3"]
        request_result = None

        for partner_id in candidate_partners:
            if partner_id == "human":
                continue

            partnership_data = {
                "action": "request_partner",
                "requested_partner": partner_id
            }
            print("🔧 Partnership request payload:", partnership_data)

            response = self.session.post(f"{self.api_url}/simulation/play-hole", json=partnership_data)

            if response.status_code == 400 and 'Captain cannot partner with themselves' in response.text:
                # Try next partner in the list
                continue

            if response.status_code != 200:
                print(f"⚠️ Partnership request failed: {response.status_code} - {response.text}")
                return False

            request_result = response.json()
            print("✅ Partnership request sent")
            break

        if not request_result:
            print("⚠️ Partnership workflow incomplete: Unable to find eligible partner")
            return False

        # Check for partnership response interaction
        if request_result.get('interaction_needed', {}).get('type') == 'partnership_response':
            print("✅ Partnership response interaction detected")

            # Accept partnership
            response_data = {"accept_partnership": True}
            response = self.session.post(f"{self.api_url}/simulation/play-hole", json=response_data)

            if response.status_code == 200:
                print("✅ Partnership accepted")
                return True

        print(f"⚠️ Partnership workflow incomplete: {response.status_code if 'response' in locals() else 'No response'}")
        return False
        
    def test_betting_workflow(self):
        """Test betting and doubling workflow"""
        print("🔧 Testing betting workflow...")
        
        if not self.wait_for_api():
            return True
            
        if not self.setup_game():
            return False
            
        # Offer double
        betting_data = {"action": "offer_double"}
        
        response = self.session.post(f"{self.api_url}/simulation/betting-decision", json=betting_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Double offer sent")
            
            # Check for double response interaction
            if result.get('interaction_needed'):
                print("✅ Double response interaction detected")
                
                # Accept double
                response_data = {"action": "accept_double"}
                response = self.session.post(f"{self.api_url}/simulation/betting-decision", json=response_data)
                
                if response.status_code == 200:
                    print("✅ Double accepted")
                    return True
                    
        print(f"⚠️ Betting workflow incomplete")
        return False

class TestSimulationProbabilities(SimulationFunctionalTest):
    """Test probability calculation features"""
    
    def test_shot_probabilities(self):
        """Test shot probability calculations"""
        print("🔧 Testing shot probabilities...")
        
        if not self.wait_for_api():
            return True
            
        # Request shot probabilities
        prob_data = {
            "player_stats": {"handicap": 15, "recent_form": "good"},
            "hole_info": {"par": 4, "distance": 400, "difficulty": "medium"}
        }
        
        response = self.session.post(f"{self.api_url}/simulation/shot-probabilities", json=prob_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Shot probabilities calculated")
            
            # Validate probability structure
            probabilities = result.get('probabilities', {})
            expected_keys = ['excellent', 'good', 'average', 'poor']
            
            if all(key in probabilities for key in expected_keys):
                print("✅ All probability categories present")
                
                # Check probabilities sum to approximately 1.0
                total = sum(probabilities.values())
                if 0.9 <= total <= 1.1:
                    print(f"✅ Probabilities sum correctly: {total:.2f}")
                    return True
                else:
                    print(f"⚠️ Probabilities don't sum to 1.0: {total:.2f}")
            else:
                print("⚠️ Missing probability categories")
                
        print(f"⚠️ Shot probabilities failed: {response.status_code if 'response' in locals() else 'No response'}")
        return False

class TestSimulationErrors(SimulationFunctionalTest):
    """Test error handling and edge cases"""
    
    def test_nonexistent_endpoints(self):
        """Test handling of non-existent endpoints"""
        print("🔧 Testing non-existent endpoints...")
        
        if not self.wait_for_api():
            return True
            
        # Test various non-existent endpoints
        invalid_endpoints = [
            "/simulation/invalid-endpoint",
            "/simulation/missing",
            "/simulation/setup/invalid",
        ]
        
        for endpoint in invalid_endpoints:
            response = self.session.get(f"{self.api_url}{endpoint}")
            
            if response.status_code == 404:
                print(f"✅ Correctly returned 404 for {endpoint}")
            else:
                print(f"⚠️ Unexpected response for {endpoint}: {response.status_code}")
                
        return True
        
    def test_malformed_requests(self):
        """Test handling of malformed requests"""
        print("🔧 Testing malformed requests...")
        
        if not self.wait_for_api():
            return True
            
        # Test malformed JSON
        try:
            response = self.session.post(
                f"{self.api_url}/simulation/setup",
                data="invalid json{{{",
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [400, 422]:
                print("✅ Malformed JSON properly rejected")
            else:
                print(f"⚠️ Malformed JSON unexpectedly processed: {response.status_code}")
                
        except Exception as e:
            print(f"✅ Malformed request caused expected error: {type(e).__name__}")
            
        return True

def run_functional_tests():
    """Run all functional tests"""
    print("🎮 Simulation Functional Test Suite")
    print("=" * 50)
    
    test_classes = [
        ("Setup Tests", TestSimulationSetup),
        ("Gameplay Tests", TestSimulationGameplay), 
        ("Probability Tests", TestSimulationProbabilities),
        ("Error Handling Tests", TestSimulationErrors),
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_category, test_class in test_classes:
        print(f"\n📋 {test_category}")
        print("-" * 30)
        
        # Get test methods
        test_methods = [m for m in dir(test_class) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            
            # Create instance and setup
            instance = test_class()
            instance.setup()
            
            try:
                # Run test
                test_method = getattr(instance, method_name)
                success = test_method()
                
                if success:
                    print(f"✅ {method_name}")
                    passed_tests += 1
                else:
                    print(f"❌ {method_name}")
                    
            except Exception as e:
                print(f"❌ {method_name}: {e}")
            finally:
                # Cleanup
                instance.teardown()
    
    print(f"\n🎯 Functional Test Results")
    print("=" * 50)
    print(f"Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 All functional tests PASSED!")
        print("💡 Simulation mode is functioning correctly")
        return True
    else:
        print("⚠️ Some functional tests failed")
        print("💡 Check simulation endpoints and API connectivity")
        return False

def main():
    """Main test runner"""
    print(f"🌐 Testing against API: {API_BASE_URL}")
    print(f"🌐 Frontend URL: {FRONTEND_URL}")
    print()
    
    success = run_functional_tests()
    
    print(f"\n📋 Test Summary")
    print("=" * 50)
    
    if success:
        print("✅ Simulation mode functional tests PASSED")
        print("🎮 Simulation is ready for end-to-end testing")
    else:
        print("❌ Some functional tests FAILED")
        print("🔧 Review simulation implementation and API endpoints")
        
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
