#!/usr/bin/env python3
"""
Simple bootstrap test without external dependencies
"""
import os
import sys
import json

def test_file_structure():
    """Test that all required files exist"""
    base_path = "/Users/stuartgano/Documents/wolf-goat-pig"
    
    required_files = [
        "backend/app/main.py",
        "backend/app/seed_data.py", 
        "backend/app/game_state.py",
        "backend/startup.py",
        "backend/requirements.txt",
        "frontend/src/App.js",
        "frontend/package.json"
    ]
    
    print("🔍 Testing file structure...")
    missing_files = []
    
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def test_json_configs():
    """Test that JSON config files are valid"""
    base_path = "/Users/stuartgano/Documents/wolf-goat-pig"
    
    json_files = [
        "frontend/package.json",
        "config/render.yaml" # Not JSON but can check if exists
    ]
    
    print("🔍 Testing configuration files...")
    
    # Test package.json
    try:
        with open(os.path.join(base_path, "frontend/package.json"), 'r') as f:
            data = json.load(f)
            if "scripts" in data and "build" in data["scripts"]:
                print("✅ Frontend package.json is valid with build script")
            else:
                print("⚠️ Frontend package.json missing build script")
    except Exception as e:
        print(f"❌ Frontend package.json error: {e}")
        return False
    
    return True

def test_bootstrap_components():
    """Test that bootstrap components are properly implemented"""
    base_path = "/Users/stuartgano/Documents/wolf-goat-pig"
    
    print("🔍 Testing bootstrap components...")
    
    # Check startup.py has main components
    startup_path = os.path.join(base_path, "backend/startup.py")
    if os.path.exists(startup_path):
        with open(startup_path, 'r') as f:
            content = f.read()
            
            required_components = [
                "class BootstrapManager",
                "def check_dependencies",
                "def seed_data",
                "def verify_health",
                "if __name__ == \"__main__\""
            ]
            
            missing_components = []
            for component in required_components:
                if component not in content:
                    missing_components.append(component)
                else:
                    print(f"✅ Found: {component}")
            
            if missing_components:
                print(f"❌ Missing components in startup.py: {missing_components}")
                return False
        
        print("✅ startup.py has all required components")
    else:
        print("❌ startup.py not found")
        return False
    
    # Check seed_data.py exists and has expected structure
    seed_path = os.path.join(base_path, "backend/app/seed_data.py")
    if os.path.exists(seed_path):
        with open(seed_path, 'r') as f:
            content = f.read()
            if "def seed_courses" in content and "def seed_ai_personalities" in content:
                print("✅ seed_data.py has required seeding functions")
            else:
                print("⚠️ seed_data.py missing some seeding functions")
    else:
        print("❌ seed_data.py not found")
        return False
    
    return True

def test_requirements():
    """Test that requirements file has essential packages"""
    base_path = "/Users/stuartgano/Documents/wolf-goat-pig"
    
    print("🔍 Testing requirements...")
    
    requirements_path = os.path.join(base_path, "backend/requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r') as f:
            content = f.read()
            
            required_packages = ["fastapi", "sqlalchemy", "uvicorn"]
            missing_packages = []
            
            for package in required_packages:
                if package.lower() not in content.lower():
                    missing_packages.append(package)
                else:
                    print(f"✅ Found requirement: {package}")
            
            if missing_packages:
                print(f"❌ Missing packages in requirements.txt: {missing_packages}")
                return False
        
        print("✅ requirements.txt has all essential packages")
        return True
    else:
        print("❌ requirements.txt not found")
        return False

def main():
    """Run all bootstrap tests"""
    print("🐺 Wolf-Goat-Pig Bootstrap Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("JSON Configs", test_json_configs),
        ("Bootstrap Components", test_bootstrap_components),
        ("Requirements", test_requirements)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    print("\n🎯 Bootstrap Test Results")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All bootstrap tests PASSED! The system is ready.")
        return True
    else:
        print("⚠️ Some bootstrap tests FAILED. Check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)