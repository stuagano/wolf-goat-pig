#!/usr/bin/env python3
"""
Comprehensive test script to verify all Wolf-Goat-Pig API routes are working.
Run this to ensure the backend is fully functional.

Usage:
    python test_all_routes.py [--local | --production]
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configuration
LOCAL_API = "http://localhost:8000"
PRODUCTION_API = "https://wolf-goat-pig.onrender.com"

# Use production by default, or local if specified
API_BASE_URL = LOCAL_API if "--local" in sys.argv else PRODUCTION_API

# Test data
TEST_ADMIN_EMAIL = "stuagano@gmail.com"
TEST_CSV_URL = "https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/export?format=csv&gid=0"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class RouteTestSuite:
    def __init__(self):
        self.results = []
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def log_result(self, endpoint: str, method: str, status: str, message: str = "", response_code: int = 0):
        """Log test result"""
        self.total += 1
        
        if status == "PASS":
            self.passed += 1
            icon = "✅"
            color = GREEN
        elif status == "FAIL":
            self.failed += 1
            icon = "❌"
            color = RED
        elif status == "WARN":
            self.warnings += 1
            icon = "⚠️"
            color = YELLOW
        else:
            icon = "ℹ️"
            color = BLUE
            
        result = f"{color}{icon} [{method}] {endpoint}{RESET}"
        if response_code:
            result += f" ({response_code})"
        if message:
            result += f" - {message}"
            
        print(result)
        self.results.append({
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "message": message,
            "response_code": response_code
        })

    async def test_health_endpoints(self, client: httpx.AsyncClient):
        """Test basic health check endpoints"""
        print(f"\n{BLUE}=== Testing Health Endpoints ==={RESET}")
        
        # Health check
        try:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                self.log_result("/health", "GET", "PASS", "API is healthy", response.status_code)
            else:
                self.log_result("/health", "GET", "FAIL", f"Unexpected status", response.status_code)
        except Exception as e:
            self.log_result("/health", "GET", "FAIL", str(e))
            
        # Root endpoint
        try:
            response = await client.get(f"{API_BASE_URL}/")
            self.log_result("/", "GET", "PASS" if response.status_code in [200, 404] else "FAIL", 
                          "", response.status_code)
        except Exception as e:
            self.log_result("/", "GET", "FAIL", str(e))

    async def test_game_endpoints(self, client: httpx.AsyncClient):
        """Test game-related endpoints"""
        print(f"\n{BLUE}=== Testing Game Endpoints ==={RESET}")
        
        endpoints = [
            ("GET", "/game/state", None),
            ("GET", "/game/tips", None),
            ("GET", "/game/player_strokes", None),
            ("POST", "/game/start", {}),
            ("POST", "/game/action", {"action_type": "INITIALIZE_GAME", "payload": {}}),
            ("GET", "/simulation/run", None),
            ("GET", "/players", None),
            ("GET", "/courses", None),
            ("GET", "/rules", None),
        ]
        
        for method, endpoint, data in endpoints:
            try:
                if method == "GET":
                    response = await client.get(f"{API_BASE_URL}{endpoint}")
                else:
                    response = await client.post(f"{API_BASE_URL}{endpoint}", json=data or {})
                
                if response.status_code in [200, 201]:
                    self.log_result(endpoint, method, "PASS", "", response.status_code)
                elif response.status_code == 422:
                    self.log_result(endpoint, method, "WARN", "Validation error", response.status_code)
                elif response.status_code == 404:
                    self.log_result(endpoint, method, "WARN", "Not found", response.status_code)
                else:
                    self.log_result(endpoint, method, "FAIL", f"Status {response.status_code}", response.status_code)
            except Exception as e:
                self.log_result(endpoint, method, "FAIL", str(e)[:50])

    async def test_player_endpoints(self, client: httpx.AsyncClient):
        """Test player management endpoints"""
        print(f"\n{BLUE}=== Testing Player Endpoints ==={RESET}")
        
        # Create a test player with unique name
        import time
        test_player = {
            "name": f"Test Player {int(time.time())}",
            "email": f"test{int(time.time())}@example.com",
            "handicap": 10.5
        }
        
        try:
            # Create player
            response = await client.post(f"{API_BASE_URL}/players", json=test_player)
            if response.status_code in [200, 201]:
                player_id = response.json().get("id")
                self.log_result("/players", "POST", "PASS", "Created test player", response.status_code)
                
                # Get player
                response = await client.get(f"{API_BASE_URL}/players/{player_id}")
                self.log_result(f"/players/{player_id}", "GET", 
                              "PASS" if response.status_code == 200 else "FAIL", 
                              "", response.status_code)
                
                # Update player
                response = await client.put(f"{API_BASE_URL}/players/{player_id}", 
                                          json={"handicap": 12.0})
                self.log_result(f"/players/{player_id}", "PUT", 
                              "PASS" if response.status_code == 200 else "FAIL", 
                              "", response.status_code)
                
                # Get availability
                response = await client.get(f"{API_BASE_URL}/players/{player_id}/availability")
                self.log_result(f"/players/{player_id}/availability", "GET", 
                              "PASS" if response.status_code == 200 else "FAIL", 
                              "", response.status_code)
                
            else:
                self.log_result("/players", "POST", "FAIL", "Could not create player", response.status_code)
        except Exception as e:
            self.log_result("/players", "POST", "FAIL", str(e)[:50])

    async def test_ghin_endpoints(self, client: httpx.AsyncClient):
        """Test GHIN integration endpoints"""
        print(f"\n{BLUE}=== Testing GHIN Endpoints ==={RESET}")
        
        # GHIN diagnostic
        try:
            response = await client.get(f"{API_BASE_URL}/ghin/diagnostic")
            self.log_result("/ghin/diagnostic", "GET", 
                          "PASS" if response.status_code == 200 else "WARN", 
                          "GHIN not configured" if response.status_code != 200 else "",
                          response.status_code)
        except Exception as e:
            self.log_result("/ghin/diagnostic", "GET", "FAIL", str(e)[:50])
        
        # GHIN lookup (will fail without credentials)
        try:
            response = await client.get(f"{API_BASE_URL}/ghin/lookup?last_name=Smith")
            if response.status_code == 200:
                self.log_result("/ghin/lookup", "GET", "PASS", "GHIN configured", response.status_code)
            elif response.status_code == 500:
                self.log_result("/ghin/lookup", "GET", "WARN", "GHIN not configured", response.status_code)
            else:
                self.log_result("/ghin/lookup", "GET", "FAIL", "", response.status_code)
        except Exception as e:
            self.log_result("/ghin/lookup", "GET", "FAIL", str(e)[:50])

    async def test_sheet_integration_endpoints(self, client: httpx.AsyncClient):
        """Test Google Sheets integration endpoints"""
        print(f"\n{BLUE}=== Testing Sheet Integration Endpoints ==={RESET}")
        
        # Fetch Google Sheet
        try:
            response = await client.post(
                f"{API_BASE_URL}/sheet-integration/fetch-google-sheet",
                json={"csv_url": TEST_CSV_URL},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                self.log_result("/sheet-integration/fetch-google-sheet", "POST", "PASS", 
                              f"Fetched {data.get('total_rows', 0)} rows", response.status_code)
            else:
                self.log_result("/sheet-integration/fetch-google-sheet", "POST", "FAIL", 
                              "", response.status_code)
        except Exception as e:
            self.log_result("/sheet-integration/fetch-google-sheet", "POST", "FAIL", str(e)[:50])
        
        # Sync WGP Sheet
        try:
            response = await client.post(
                f"{API_BASE_URL}/sheet-integration/sync-wgp-sheet",
                json={"csv_url": TEST_CSV_URL},
                timeout=60
            )
            if response.status_code == 200:
                self.log_result("/sheet-integration/sync-wgp-sheet", "POST", "PASS", 
                              "Sheet synced", response.status_code)
            else:
                self.log_result("/sheet-integration/sync-wgp-sheet", "POST", "WARN", 
                              "Sync failed", response.status_code)
        except Exception as e:
            self.log_result("/sheet-integration/sync-wgp-sheet", "POST", "FAIL", str(e)[:50])

    async def test_email_oauth_endpoints(self, client: httpx.AsyncClient):
        """Test email and OAuth2 endpoints"""
        print(f"\n{BLUE}=== Testing Email/OAuth2 Endpoints ==={RESET}")
        
        headers = {"X-Admin-Email": TEST_ADMIN_EMAIL}
        
        # Email configuration status
        try:
            response = await client.get(f"{API_BASE_URL}/admin/email-config", headers=headers)
            self.log_result("/admin/email-config", "GET", 
                          "PASS" if response.status_code == 200 else "WARN", 
                          "", response.status_code)
        except Exception as e:
            self.log_result("/admin/email-config", "GET", "FAIL", str(e)[:50])
        
        # OAuth2 status
        try:
            response = await client.get(f"{API_BASE_URL}/admin/oauth2-status", headers=headers)
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", {})
                configured = status.get("configured", False)
                self.log_result("/admin/oauth2-status", "GET", "PASS", 
                              "OAuth2 configured" if configured else "OAuth2 not configured", 
                              response.status_code)
            else:
                self.log_result("/admin/oauth2-status", "GET", "WARN", "", response.status_code)
        except Exception as e:
            self.log_result("/admin/oauth2-status", "GET", "FAIL", str(e)[:50])

    async def test_analytics_endpoints(self, client: httpx.AsyncClient):
        """Test analytics and reporting endpoints"""
        print(f"\n{BLUE}=== Testing Analytics Endpoints ==={RESET}")
        
        endpoints = [
            ("GET", "/analytics/game-stats", None),
            ("GET", "/analytics/player-performance", None),
            ("GET", "/leaderboard", None),
            ("GET", "/signups", None),
        ]
        
        for method, endpoint, data in endpoints:
            try:
                response = await client.get(f"{API_BASE_URL}{endpoint}")
                if response.status_code == 200:
                    self.log_result(endpoint, method, "PASS", "", response.status_code)
                elif response.status_code == 404:
                    self.log_result(endpoint, method, "WARN", "Not found", response.status_code)
                else:
                    self.log_result(endpoint, method, "FAIL", "", response.status_code)
            except Exception as e:
                self.log_result(endpoint, method, "FAIL", str(e)[:50])

    async def test_course_endpoints(self, client: httpx.AsyncClient):
        """Test course management endpoints"""
        print(f"\n{BLUE}=== Testing Course Endpoints ==={RESET}")
        
        # Get courses
        try:
            response = await client.get(f"{API_BASE_URL}/courses")
            if response.status_code == 200:
                courses = response.json()
                self.log_result("/courses", "GET", "PASS", 
                              f"Found {len(courses)} courses", response.status_code)
                
                # If courses exist, test getting a specific one by index
                if courses and len(courses) > 0:
                    course_id = 0  # Use index 0 for first course
                    response = await client.get(f"{API_BASE_URL}/courses/{course_id}")
                    self.log_result(f"/courses/{course_id}", "GET", 
                                  "PASS" if response.status_code == 200 else "FAIL", 
                                  "", response.status_code)
            else:
                self.log_result("/courses", "GET", "FAIL", "", response.status_code)
        except Exception as e:
            self.log_result("/courses", "GET", "FAIL", str(e)[:50])
        
        # Test course import preview
        try:
            response = await client.post(
                f"{API_BASE_URL}/courses/import/preview",
                json={"course_name": "Pebble Beach"}
            )
            if response.status_code in [200, 404]:
                self.log_result("/courses/import/preview", "POST", 
                              "PASS" if response.status_code == 200 else "WARN", 
                              "Course not found" if response.status_code == 404 else "",
                              response.status_code)
            else:
                self.log_result("/courses/import/preview", "POST", "FAIL", "", response.status_code)
        except Exception as e:
            self.log_result("/courses/import/preview", "POST", "FAIL", str(e)[:50])

    def print_summary(self):
        """Print test summary"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Test Summary for {API_BASE_URL}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        print(f"Total Tests: {self.total}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        
        success_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        
        if success_rate >= 80:
            print(f"\n{GREEN}✅ API Health: GOOD ({success_rate:.1f}% passing){RESET}")
        elif success_rate >= 60:
            print(f"\n{YELLOW}⚠️  API Health: FAIR ({success_rate:.1f}% passing){RESET}")
        else:
            print(f"\n{RED}❌ API Health: POOR ({success_rate:.1f}% passing){RESET}")
        
        # List failed endpoints
        if self.failed > 0:
            print(f"\n{RED}Failed Endpoints:{RESET}")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - [{result['method']}] {result['endpoint']}: {result['message']}")
        
        # List warnings
        if self.warnings > 0:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for result in self.results:
                if result["status"] == "WARN":
                    print(f"  - [{result['method']}] {result['endpoint']}: {result['message']}")

async def main():
    """Main test runner"""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Wolf-Goat-Pig API Route Tester{RESET}")
    print(f"{BLUE}Testing: {API_BASE_URL}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    suite = RouteTestSuite()
    
    # Configure client with longer timeout
    timeout = httpx.Timeout(30.0, connect=10.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        # Run all test suites
        await suite.test_health_endpoints(client)
        await suite.test_game_endpoints(client)
        await suite.test_player_endpoints(client)
        await suite.test_course_endpoints(client)
        await suite.test_ghin_endpoints(client)
        await suite.test_sheet_integration_endpoints(client)
        await suite.test_email_oauth_endpoints(client)
        await suite.test_analytics_endpoints(client)
    
    # Print summary
    suite.print_summary()
    
    # Return exit code based on results
    if suite.failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    # Check for help flag
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)
    
    # Run the tests
    asyncio.run(main())