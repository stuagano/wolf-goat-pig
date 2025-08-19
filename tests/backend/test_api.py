#!/usr/bin/env python3
"""
Simple test script to verify FastAPI app structure and endpoints
"""

import asyncio
from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint():
    """Test the health endpoint"""
    client = TestClient(app)
    response = client.get("/health")
    print(f"Health endpoint status: {response.status_code}")
    print(f"Health endpoint response: {response.json()}")
    return response.status_code == 200

def test_ghin_diagnostic():
    """Test the GHIN diagnostic endpoint"""
    client = TestClient(app)
    response = client.get("/ghin/diagnostic")
    print(f"GHIN diagnostic status: {response.status_code}")
    print(f"GHIN diagnostic response: {response.json()}")
    return response.status_code == 200

def test_app_structure():
    """Test that the app has the expected structure"""
    print("Testing FastAPI app structure...")
    
    # Check if app is properly initialized
    assert hasattr(app, 'routes'), "App should have routes"
    print(f"✅ App has {len(app.routes)} routes")
    
    # List all routes
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append(f"{list(route.methods)[0]} {route.path}")
    
    print("Available routes:")
    for route in sorted(routes):
        print(f"  {route}")
    
    # Check for specific endpoints
    health_routes = [r for r in routes if "/health" in r]
    ghin_routes = [r for r in routes if "/ghin" in r]
    
    print(f"✅ Health routes: {len(health_routes)}")
    print(f"✅ GHIN routes: {len(ghin_routes)}")
    
    return len(health_routes) > 0 and len(ghin_routes) > 0

if __name__ == "__main__":
    print("🔍 Testing Wolf Goat Pig API...")
    
    try:
        # Test app structure
        structure_ok = test_app_structure()
        
        # Test health endpoint
        health_ok = test_health_endpoint()
        
        # Test GHIN diagnostic
        ghin_ok = test_ghin_diagnostic()
        
        print("\n📊 Test Results:")
        print(f"  App Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
        print(f"  Health Endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
        print(f"  GHIN Diagnostic: {'✅ PASS' if ghin_ok else '❌ FAIL'}")
        
        if all([structure_ok, health_ok, ghin_ok]):
            print("\n🎉 All tests passed! API is working correctly.")
        else:
            print("\n⚠️ Some tests failed. Check the output above.")
            
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc() 