#!/usr/bin/env python3
"""
Quick startup test to identify simulation issues
"""

import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_path)

def test_basic_imports():
    """Test if we can import core modules"""
    print("🔍 Testing basic imports...")
    
    try:
        import app.database
        print("✅ app.database imported")
    except Exception as e:
        print(f"❌ app.database failed: {e}")
        return False
    
    try:
        import app.models
        print("✅ app.models imported")
    except Exception as e:
        print(f"❌ app.models failed: {e}")
        return False
    
    try:
        import app.wolf_goat_pig_simulation
        print("✅ app.wolf_goat_pig_simulation imported")
    except Exception as e:
        print(f"❌ app.wolf_goat_pig_simulation failed: {e}")
        return False
    
    return True

def test_database_init():
    """Test database initialization without actually calling init_db()"""
    print("🗄️ Testing database setup...")
    
    try:
        from app.database import engine, SessionLocal, Base
        print("✅ Database components available")
        
        # Check if we can create a session (but don't initialize tables)
        session = SessionLocal()
        session.close()
        print("✅ Database session creation works")
        
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def test_simulation_creation():
    """Test if we can create a simulation object"""
    print("🎮 Testing simulation creation...")
    
    try:
        from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
        
        # Try to create simulation without database dependencies
        sim = WolfGoatPigSimulation(player_count=4)
        print("✅ WolfGoatPigSimulation created")
        
        # Test if basic methods exist
        if hasattr(sim, 'get_game_state'):
            print("✅ get_game_state method exists")
        else:
            print("❌ get_game_state method missing")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Simulation creation failed: {e}")
        return False

def main():
    """Run startup tests"""
    print("🐺 Wolf-Goat-Pig Startup Test")
    print("=" * 40)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("Database Setup", test_database_init),
        ("Simulation Creation", test_simulation_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 20)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n🎯 Results")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)