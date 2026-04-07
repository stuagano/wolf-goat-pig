"""
Debug API response to understand what's happening
"""
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import app

def test_debug_health():
    """Debug health endpoint response"""
    with TestClient(app) as client:
        response = client.get("/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        print(f"Response Headers: {response.headers}")
        
        # Also try some other endpoints
        print("\n--- Testing /docs ---")
        docs_response = client.get("/docs")
        print(f"Docs Status: {docs_response.status_code}")
        
        print("\n--- Testing / ---")
        root_response = client.get("/")
        print(f"Root Status: {root_response.status_code}")
        print(f"Root Body: {root_response.text[:200] if root_response.text else 'No body'}")

if __name__ == "__main__":
    test_debug_health()