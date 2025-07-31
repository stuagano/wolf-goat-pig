#!/usr/bin/env python
"""Test deployment endpoints"""
import httpx
import asyncio
from datetime import datetime

async def test_deployment():
    """Test both local and deployed endpoints"""
    
    endpoints = {
        "Local": "http://localhost:8000",
        "Render": "https://wolf-goat-pig-api.onrender.com"
    }
    
    for name, base_url in endpoints.items():
        print(f"\n=== Testing {name} ({base_url}) ===")
        
        # Test health endpoint
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/health", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✓ Health check passed: {data}")
                else:
                    print(f"✗ Health check failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
        
        # Test courses endpoint
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{base_url}/courses", timeout=10.0)
                if response.status_code == 200:
                    courses = response.json()
                    print(f"✓ Courses endpoint: Found {len(courses)} courses")
                else:
                    print(f"✗ Courses endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Failed to get courses: {e}")
    
    # Test Vercel frontend
    print(f"\n=== Testing Frontend (Vercel) ===")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://wolf-goat-pig.vercel.app", timeout=10.0)
            if response.status_code == 200:
                print(f"✓ Frontend is accessible")
            else:
                print(f"✗ Frontend returned: {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to connect to frontend: {e}")

if __name__ == "__main__":
    print(f"Deployment test started at {datetime.now()}")
    asyncio.run(test_deployment())