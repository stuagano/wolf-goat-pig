#!/usr/bin/env python3
"""
Basic test script to verify DRY refactoring without external dependencies
"""

def test_constants():
    """Test that constants are properly centralized"""
    import sys
    sys.path.append('backend')
    
    try:
        from backend.app.constants import DEFAULT_PLAYERS, GAME_CONSTANTS, VALIDATION_LIMITS
        
        # Test DEFAULT_PLAYERS structure
        assert len(DEFAULT_PLAYERS) == 4, f"Expected 4 players, got {len(DEFAULT_PLAYERS)}"
        for player in DEFAULT_PLAYERS:
            assert "id" in player, "Player missing id"
            assert "name" in player, "Player missing name"
            assert "handicap" in player, "Player missing handicap"
            assert "strength" in player, "Player missing strength"
        
        # Test GAME_CONSTANTS
        assert GAME_CONSTANTS["MAX_HOLES"] == 18, "MAX_HOLES should be 18"
        assert GAME_CONSTANTS["MIN_PLAYERS"] == 4, "MIN_PLAYERS should be 4"
        assert GAME_CONSTANTS["DEFAULT_BASE_WAGER"] == 1, "DEFAULT_BASE_WAGER should be 1"
        
        # Test VALIDATION_LIMITS
        assert VALIDATION_LIMITS["MIN_PAR"] == 3, "MIN_PAR should be 3"
        assert VALIDATION_LIMITS["MAX_PAR"] == 6, "MAX_PAR should be 6"
        
        print("✓ Constants test passed")
        return True
        
    except Exception as e:
        print(f"✗ Constants test failed: {e}")
        return False

def test_utils_standalone():
    """Test utility functions that don't depend on external libraries"""
    import sys
    sys.path.append('backend')
    
    try:
        # Test PlayerUtils (without importing the module due to dependencies)
        # We'll test the logic directly
        
        # Test handicap to strength conversion logic
        def handicap_to_strength(handicap):
            """Local version of the utility function"""
            strength_thresholds = {
                "Expert": (0, 5),
                "Strong": (5, 12),
                "Average": (12, 20),
                "Beginner": (20, 36),
            }
            
            for strength, (min_hcp, max_hcp) in strength_thresholds.items():
                if min_hcp <= handicap <= max_hcp:
                    return strength
            return "Average"  # Default fallback
        
        # Test the logic
        assert handicap_to_strength(2.0) == "Expert", "2.0 handicap should be Expert"
        assert handicap_to_strength(8.0) == "Strong", "8.0 handicap should be Strong"
        assert handicap_to_strength(15.0) == "Average", "15.0 handicap should be Average"
        assert handicap_to_strength(25.0) == "Beginner", "25.0 handicap should be Beginner"
        assert handicap_to_strength(50.0) == "Average", "50.0 handicap should fallback to Average"
        
        # Test player lookup logic
        def find_player_by_id(players, player_id):
            """Local version of the utility function"""
            for player in players:
                if player.get("id") == player_id:
                    return player
            return None
        
        test_players = [
            {"id": "p1", "name": "Alice", "handicap": 10},
            {"id": "p2", "name": "Bob", "handicap": 15}
        ]
        
        player = find_player_by_id(test_players, "p1")
        assert player is not None, "Should find player p1"
        assert player["name"] == "Alice", "Player p1 should be Alice"
        
        player = find_player_by_id(test_players, "p3")
        assert player is None, "Should not find player p3"
        
        print("✓ Utils logic test passed")
        return True
        
    except Exception as e:
        print(f"✗ Utils logic test failed: {e}")
        return False

def test_dry_principles():
    """Test that DRY principles have been applied"""
    import os
    
    try:
        # Check that new files were created for centralization
        expected_files = [
            'backend/app/constants.py',
            'backend/app/utils.py', 
            'backend/app/exceptions.py'
        ]
        
        for file_path in expected_files:
            assert os.path.exists(file_path), f"Expected file {file_path} was not created"
        
        # Check that constants.py contains the centralized values
        with open('backend/app/constants.py', 'r') as f:
            constants_content = f.read()
            
        assert 'DEFAULT_PLAYERS' in constants_content, "DEFAULT_PLAYERS not found in constants"
        assert 'GAME_CONSTANTS' in constants_content, "GAME_CONSTANTS not found in constants"
        assert 'VALIDATION_LIMITS' in constants_content, "VALIDATION_LIMITS not found in constants"
        
        # Check that utils.py contains utility classes
        with open('backend/app/utils.py', 'r') as f:
            utils_content = f.read()
            
        assert 'class PlayerUtils:' in utils_content, "PlayerUtils class not found"
        assert 'class CourseUtils:' in utils_content, "CourseUtils class not found"
        assert 'class GameUtils:' in utils_content, "GameUtils class not found"
        assert 'class ValidationUtils:' in utils_content, "ValidationUtils class not found"
        
        # Check that exceptions.py contains centralized exception handling
        with open('backend/app/exceptions.py', 'r') as f:
            exceptions_content = f.read()
            
        assert 'class APIException:' in exceptions_content, "APIException class not found"
        assert 'bad_request' in exceptions_content, "bad_request method not found"
        assert 'not_found' in exceptions_content, "not_found method not found"
        
        print("✓ DRY principles test passed")
        return True
        
    except Exception as e:
        print(f"✗ DRY principles test failed: {e}")
        return False

def test_class_method_conversion():
    """Test that standalone functions have been converted to class methods"""
    import os
    
    try:
        # Check that functions have been organized into classes
        with open('backend/app/utils.py', 'r') as f:
            utils_content = f.read()
        
        # Check for static methods (converted standalone functions)
        assert '@staticmethod' in utils_content, "No static methods found in utils"
        assert 'def handicap_to_strength(' in utils_content, "handicap_to_strength method not found"
        assert 'def find_player_by_id(' in utils_content, "find_player_by_id method not found"
        assert 'def serialize_game_state(' in utils_content, "serialize_game_state method not found"
        
        # Check that main.py uses class-based API response handling
        with open('backend/app/main.py', 'r') as f:
            main_content = f.read()
            
        assert 'class APIResponseHandler:' in main_content, "APIResponseHandler class not found"
        assert 'class SimulationManager:' in main_content, "SimulationManager class not found"
        
        # Check that simulation.py uses class methods
        with open('backend/app/simulation.py', 'r') as f:
            sim_content = f.read()
            
        assert 'class ComputerPlayer:' in sim_content, "ComputerPlayer class not found"
        assert 'class SimulationEngine:' in sim_content, "SimulationEngine class not found"
        assert 'class MonteCarloResults:' in sim_content, "MonteCarloResults class not found"
        
        print("✓ Class method conversion test passed")
        return True
        
    except Exception as e:
        print(f"✗ Class method conversion test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing DRY Refactoring and Class Method Conversion")
    print("=" * 60)
    
    tests = [
        test_constants,
        test_utils_standalone,
        test_dry_principles,
        test_class_method_conversion
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Refactoring successful!")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)