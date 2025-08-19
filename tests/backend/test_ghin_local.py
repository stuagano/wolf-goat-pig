#!/usr/bin/env python3
"""
Test script to show GHIN diagnostic results locally
"""

import os
from app.main import ghin_diagnostic

def test_ghin_diagnostic():
    """Test the GHIN diagnostic function directly"""
    print("🔍 GHIN Diagnostic Test")
    print("=" * 40)
    
    # Call the diagnostic function directly
    result = ghin_diagnostic()
    
    print("📊 Diagnostic Results:")
    print(f"Status: {result['status']}")
    print("\nEnvironment Variables:")
    for key, value in result['environment_variables'].items():
        print(f"  {key}: {value}")
    
    print("\nAPI URLs:")
    for key, value in result['api_urls'].items():
        print(f"  {key}: {value}")
    
    if 'auth_test' in result:
        print(f"\nAuth Test: {result['auth_test']}")
    
    if 'search_test' in result:
        print(f"\nSearch Test: {result['search_test']}")
    
    print("\n" + "=" * 40)
    
    if result['status'] == 'CREDENTIALS_MISSING':
        print("❌ GHIN credentials not set")
        print("💡 To fix: Set GHIN_API_USER and GHIN_API_PASS environment variables")
    elif result['status'] == 'WORKING':
        print("✅ GHIN integration working!")
    else:
        print(f"⚠️ Status: {result['status']}")

if __name__ == "__main__":
    test_ghin_diagnostic() 