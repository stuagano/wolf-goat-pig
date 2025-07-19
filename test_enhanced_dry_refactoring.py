#!/usr/bin/env python3
"""
Enhanced DRY Refactoring Test Script

This script validates the enhanced DRY refactoring improvements including:
- Additional PlayerUtils methods
- GameStateUtils class
- Improved abstraction patterns
- Code consolidation
"""
import sys
import os
import importlib.util

def import_backend_module(module_name):
    """Import a backend module safely"""
    try:
        module_path = os.path.join("backend", "app", f"{module_name}.py")
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"❌ Failed to import {module_name}: {e}")
        return None

def test_enhanced_player_utils():
    """Test the enhanced PlayerUtils with new methods"""
    print("Testing Enhanced PlayerUtils...")
    
    utils = import_backend_module("utils")
    if not utils:
        return False
    
    PlayerUtils = utils.PlayerUtils
    
    # Test data
    test_players = [
        {"id": "p1", "name": "Alice", "handicap": 10},
        {"id": "p2", "name": "Bob", "handicap": 15},
        {"id": "p3", "name": "Charlie", "handicap": 20}
    ]
    
    # Test extract_player_ids
    player_ids = PlayerUtils.extract_player_ids(test_players)
    assert player_ids == ["p1", "p2", "p3"], f"Expected ['p1', 'p2', 'p3'], got {player_ids}"
    
    # Test get_players_excluding
    excluded = PlayerUtils.get_players_excluding(test_players, ["p1", "p3"])
    assert excluded == ["p2"], f"Expected ['p2'], got {excluded}"
    
    # Test create_player_id_mapping
    mapping = PlayerUtils.create_player_id_mapping(test_players, 0)
    expected_mapping = {"p1": 0, "p2": 0, "p3": 0}
    assert mapping == expected_mapping, f"Expected {expected_mapping}, got {mapping}"
    
    # Test get_players_by_ids
    filtered_players = PlayerUtils.get_players_by_ids(test_players, ["p1", "p3"])
    assert len(filtered_players) == 2, f"Expected 2 players, got {len(filtered_players)}"
    assert filtered_players[0]["id"] == "p1", "First player should be p1"
    assert filtered_players[1]["id"] == "p3", "Second player should be p3"
    
    print("✓ Enhanced PlayerUtils tests passed")
    return True

def test_game_state_utils():
    """Test the new GameStateUtils class"""
    print("Testing GameStateUtils...")
    
    utils = import_backend_module("utils")
    if not utils:
        return False
    
    GameStateUtils = utils.GameStateUtils
    
    # Test data
    test_players = [
        {"id": "p1", "name": "Alice"},
        {"id": "p2", "name": "Bob"},
        {"id": "p3", "name": "Charlie"}
    ]
    
    # Test create_hitting_order
    hitting_order = GameStateUtils.create_hitting_order(test_players)
    assert len(hitting_order) == 3, f"Expected 3 players in order, got {len(hitting_order)}"
    assert set(hitting_order) == {"p1", "p2", "p3"}, "All player IDs should be in hitting order"
    
    # Test initialize_player_tracking_dicts
    tracking_dicts = GameStateUtils.initialize_player_tracking_dicts(test_players)
    expected_keys = ["hole_scores", "player_float_used", "_last_points"]
    for key in expected_keys:
        assert key in tracking_dicts, f"Missing key: {key}"
        assert len(tracking_dicts[key]) == 3, f"Expected 3 entries for {key}"
    
    # Verify specific values
    assert all(v is None for v in tracking_dicts["hole_scores"].values()), "hole_scores should all be None"
    assert all(v is False for v in tracking_dicts["player_float_used"].values()), "player_float_used should all be False"
    assert all(v == 0 for v in tracking_dicts["_last_points"].values()), "_last_points should all be 0"
    
    # Test format_winner_names
    assert GameStateUtils.format_winner_names([]) == "Nobody"
    assert GameStateUtils.format_winner_names(["Alice"]) == "Alice"
    assert GameStateUtils.format_winner_names(["Alice", "Bob"]) == "Alice and Bob"
    assert GameStateUtils.format_winner_names(["Alice", "Bob", "Charlie"]) == "Alice, Bob, and Charlie"
    
    print("✓ GameStateUtils tests passed")
    return True

def test_dry_violations_eliminated():
    """Test that specific DRY violations have been eliminated"""
    print("Testing DRY violation elimination...")
    
    # Read game_state.py to verify patterns have been replaced
    try:
        with open("backend/app/game_state.py", "r") as f:
            game_state_content = f.read()
    except FileNotFoundError:
        print("❌ Could not find game_state.py")
        return False
    
    # Check that repeated patterns have been replaced with utility calls
    dry_violations = [
        '[p["id"] for p in self.players if p["id"] not in',  # Should use get_players_excluding
        '{p["id"]: None for p in self.players}',  # Should use create_player_id_mapping
        '{p["id"]: False for p in self.players}',  # Should use create_player_id_mapping
        '{p["id"]: 0 for p in self.players}',  # Should use create_player_id_mapping
    ]
    
    for violation in dry_violations:
        if violation in game_state_content:
            print(f"❌ DRY violation still exists: {violation}")
            return False
    
    # Check that utility calls are present
    utility_calls = [
        "PlayerUtils.get_players_excluding",
        "PlayerUtils.create_player_id_mapping",
        "GameStateUtils.initialize_player_tracking_dicts",
        "GameStateUtils.create_hitting_order"
    ]
    
    for call in utility_calls:
        if call not in game_state_content:
            print(f"❌ Expected utility call not found: {call}")
            return False
    
    print("✓ DRY violations successfully eliminated")
    return True

def test_constants_centralization():
    """Test that constants are properly centralized"""
    print("Testing constants centralization...")
    
    constants = import_backend_module("constants")
    if not constants:
        return False
    
    # Verify key constants exist
    required_constants = [
        "DEFAULT_PLAYERS",
        "DEFAULT_COURSES", 
        "GAME_CONSTANTS",
        "VALIDATION_LIMITS",
        "STRENGTH_THRESHOLDS",
        "PERSONALITY_DESCRIPTIONS",
        "SUGGESTED_OPPONENTS"
    ]
    
    for const in required_constants:
        if not hasattr(constants, const):
            print(f"❌ Missing constant: {const}")
            return False
    
    # Test that game constants have proper structure
    game_constants = constants.GAME_CONSTANTS
    required_game_constants = [
        "MAX_HOLES",
        "MIN_PLAYERS", 
        "MAX_PLAYERS",
        "DEFAULT_BASE_WAGER",
        "DEFAULT_GAME_PHASE"
    ]
    
    for const in required_game_constants:
        if const not in game_constants:
            print(f"❌ Missing game constant: {const}")
            return False
    
    print("✓ Constants centralization verified")
    return True

def test_exception_handling_centralization():
    """Test centralized exception handling"""
    print("Testing exception handling centralization...")
    
    exceptions = import_backend_module("exceptions")
    if not exceptions:
        return False
    
    APIException = exceptions.APIException
    
    # Test basic exception creation
    bad_request = APIException.bad_request("Test error")
    assert bad_request.status_code == 400, "Bad request should have status 400"
    assert bad_request.detail == "Test error", "Detail should match input"
    
    not_found = APIException.not_found("Resource missing")
    assert not_found.status_code == 404, "Not found should have status 404"
    
    validation_error = APIException.validation_error("field", "value", "constraint")
    assert validation_error.status_code == 400, "Validation error should have status 400"
    assert "field" in validation_error.detail, "Field should be in detail"
    
    print("✓ Exception handling centralization verified")
    return True

def test_api_response_standardization():
    """Test API response standardization"""
    print("Testing API response standardization...")
    
    # Read main.py to verify APIResponseHandler usage
    try:
        with open("backend/app/main.py", "r") as f:
            main_content = f.read()
    except FileNotFoundError:
        print("❌ Could not find main.py")
        return False
    
    # Check that APIResponseHandler is used
    if "APIResponseHandler" not in main_content:
        print("❌ APIResponseHandler not found in main.py")
        return False
    
    # Check for standardized response methods
    response_methods = [
        "APIResponseHandler.success_response",
        "APIResponseHandler.game_state_response", 
        "APIResponseHandler.game_state_with_result"
    ]
    
    for method in response_methods:
        if method not in main_content:
            print(f"❌ Response method not used: {method}")
            return False
    
    print("✓ API response standardization verified")
    return True

def main():
    """Run all enhanced DRY refactoring tests"""
    print("🔧 Testing Enhanced DRY Refactoring")
    print("=" * 60)
    
    tests = [
        test_enhanced_player_utils,
        test_game_state_utils,
        test_dry_violations_eliminated,
        test_constants_centralization,
        test_exception_handling_centralization,
        test_api_response_standardization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Enhanced tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All enhanced DRY refactoring tests passed!")
        return True
    else:
        print("❌ Some enhanced tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)