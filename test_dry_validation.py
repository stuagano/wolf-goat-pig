#!/usr/bin/env python3
"""
DRY Validation Test Script

Simple validation of DRY principles by examining code content directly.
"""

def test_file_dry_violations(filename, violations):
    """Test that specific DRY violations have been eliminated from a file"""
    try:
        with open(filename, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Could not find {filename}")
        return False
    
    violations_found = []
    for violation in violations:
        if violation in content:
            violations_found.append(violation)
    
    if violations_found:
        print(f"❌ DRY violations still exist in {filename}:")
        for violation in violations_found:
            print(f"   - {violation}")
        return False
    
    return True

def test_file_has_improvements(filename, improvements):
    """Test that specific improvements are present in a file"""
    try:
        with open(filename, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Could not find {filename}")
        return False
    
    missing_improvements = []
    for improvement in improvements:
        if improvement not in content:
            missing_improvements.append(improvement)
    
    if missing_improvements:
        print(f"❌ Missing improvements in {filename}:")
        for improvement in missing_improvements:
            print(f"   - {improvement}")
        return False
    
    return True

def test_game_state_dry():
    """Test DRY improvements in game_state.py"""
    print("Testing game_state.py DRY improvements...")
    
    violations = [
        '[p["id"] for p in self.players if p["id"] not in',
        '[p["id"] for p in self.players if p["id"] !=',
        '{p["id"]: None for p in self.players}',
        '{p["id"]: False for p in self.players}',
        '{p["id"]: 0 for p in self.players}',
        '[p["id"] for p in DEFAULT_PLAYERS]'
    ]
    
    improvements = [
        "PlayerUtils.get_players_excluding",
        "PlayerUtils.create_player_id_mapping", 
        "GameStateUtils.initialize_player_tracking_dicts",
        "GameStateUtils.create_hitting_order",
        "PlayerUtils.extract_player_ids"
    ]
    
    violations_ok = test_file_dry_violations("backend/app/game_state.py", violations)
    improvements_ok = test_file_has_improvements("backend/app/game_state.py", improvements)
    
    if violations_ok and improvements_ok:
        print("✓ game_state.py DRY improvements verified")
        return True
    
    return False

def test_main_py_dry():
    """Test DRY improvements in main.py"""
    print("Testing main.py DRY improvements...")
    
    violations = [
        'HTTPException(status_code=400,',
        'HTTPException(status_code=404,',
        '"status": "ok", "game_state": serialize_game_state'
    ]
    
    improvements = [
        "APIResponseHandler",
        "APIException",
        "SerializationUtils",
        "SimulationManager",
        "SimulationInsightGenerator"
    ]
    
    violations_ok = test_file_dry_violations("backend/app/main.py", violations)
    improvements_ok = test_file_has_improvements("backend/app/main.py", improvements)
    
    if violations_ok and improvements_ok:
        print("✓ main.py DRY improvements verified")
        return True
    
    return False

def test_utils_structure():
    """Test that utils.py has proper class structure"""
    print("Testing utils.py class structure...")
    
    required_classes = [
        "class PlayerUtils:",
        "class CourseUtils:",
        "class GameUtils:",
        "class ValidationUtils:",
        "class SerializationUtils:",
        "class SimulationUtils:",
        "class GameStateUtils:"
    ]
    
    try:
        with open("backend/app/utils.py", "r") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Could not find utils.py")
        return False
    
    missing_classes = []
    for cls in required_classes:
        if cls not in content:
            missing_classes.append(cls)
    
    if missing_classes:
        print("❌ Missing utility classes:")
        for cls in missing_classes:
            print(f"   - {cls}")
        return False
    
    print("✓ utils.py class structure verified")
    return True

def test_constants_structure():
    """Test that constants.py has proper structure"""
    print("Testing constants.py structure...")
    
    required_constants = [
        "DEFAULT_PLAYERS =",
        "DEFAULT_COURSES =",
        "GAME_CONSTANTS =",
        "VALIDATION_LIMITS =",
        "STRENGTH_THRESHOLDS =",
        "PERSONALITY_DESCRIPTIONS =",
        "SUGGESTED_OPPONENTS ="
    ]
    
    try:
        with open("backend/app/constants.py", "r") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Could not find constants.py")
        return False
    
    missing_constants = []
    for const in required_constants:
        if const not in content:
            missing_constants.append(const)
    
    if missing_constants:
        print("❌ Missing constants:")
        for const in missing_constants:
            print(f"   - {const}")
        return False
    
    print("✓ constants.py structure verified")
    return True

def test_exceptions_structure():
    """Test that exceptions.py has proper structure"""
    print("Testing exceptions.py structure...")
    
    required_elements = [
        "class APIException:",
        "def bad_request(",
        "def not_found(",
        "def validation_error(",
        "class GameStateException(",
        "class ValidationException("
    ]
    
    try:
        with open("backend/app/exceptions.py", "r") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Could not find exceptions.py")
        return False
    
    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print("❌ Missing exception elements:")
        for element in missing_elements:
            print(f"   - {element}")
        return False
    
    print("✓ exceptions.py structure verified")
    return True

def main():
    """Run all DRY validation tests"""
    print("🔍 Validating DRY Refactoring Implementation")
    print("=" * 60)
    
    tests = [
        test_game_state_dry,
        test_main_py_dry,
        test_utils_structure,
        test_constants_structure,
        test_exceptions_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"DRY validation tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All DRY validation tests passed!")
        print("✨ Comprehensive DRY refactoring successfully implemented!")
        return True
    else:
        print("❌ Some DRY validation tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)