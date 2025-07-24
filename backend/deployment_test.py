#!/usr/bin/env python3
"""
Deployment test script to verify the app can start properly
"""

import os
import sys
import traceback

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import fastapi
        print(f"✅ FastAPI version: {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn version: {uvicorn.__version__}")
    except ImportError as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import httpx
        print(f"✅ HTTPX version: {httpx.__version__}")
    except ImportError as e:
        print(f"❌ HTTPX import failed: {e}")
        return False
    
    return True

def test_app_creation():
    """Test that the FastAPI app can be created"""
    print("\n🔍 Testing app creation...")
    
    try:
        from app.main import app
        print("✅ FastAPI app imported successfully")
        print(f"✅ App has {len(app.routes)} routes")
        return True
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        traceback.print_exc()
        return False

def test_environment():
    """Test environment variables and configuration"""
    print("\n🔍 Testing environment...")
    
    # Check Python version
    print(f"✅ Python version: {sys.version}")
    
    # Check working directory
    print(f"✅ Working directory: {os.getcwd()}")
    
    # Check if we're in the right place
    if not os.path.exists("app/main.py"):
        print("❌ app/main.py not found - wrong directory?")
        return False
    
    print("✅ app/main.py found")
    
    # Check environment variables
    ghin_user = os.environ.get("GHIN_API_USER")
    ghin_pass = os.environ.get("GHIN_API_PASS")
    
    print(f"✅ GHIN_API_USER: {'SET' if ghin_user else 'MISSING'}")
    print(f"✅ GHIN_API_PASS: {'SET' if ghin_pass else 'MISSING'}")
    
    return True

def test_server_startup():
    """Test that the server can start (without actually starting it)"""
    print("\n🔍 Testing server startup simulation...")
    
    try:
        # This simulates what Render does
        import uvicorn
        from app.main import app
        
        # Test the uvicorn configuration
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
        
        print("✅ Uvicorn config created successfully")
        print(f"✅ Host: {config.host}")
        print(f"✅ Port: {config.port}")
        
        return True
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Wolf Goat Pig Deployment Test")
    print("=" * 40)
    
    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("App Creation", test_app_creation),
        ("Server Startup", test_server_startup),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Results:")
    print("=" * 40)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! App should deploy successfully.")
    else:
        print("⚠️ Some tests failed. Check the output above.")
    
    sys.exit(0 if all_passed else 1) 