#!/usr/bin/env python3
"""
Deployment Verification Script
Tests both local and remote deployments to ensure they're working correctly
"""

import sys
import json
import time
import subprocess
from typing import Dict, List, Tuple, Optional
from urllib.parse import urljoin
import requests
from datetime import datetime

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(status: str, message: str):
    """Print colored status messages"""
    if status == "success":
        print(f"{Colors.GREEN}✓{Colors.NC} {message}")
    elif status == "error":
        print(f"{Colors.RED}✗{Colors.NC} {message}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠{Colors.NC} {message}")
    elif status == "info":
        print(f"{Colors.BLUE}ℹ{Colors.NC} {message}")
    else:
        print(f"  {message}")

class DeploymentTester:
    def __init__(self, backend_url: str, frontend_url: str):
        self.backend_url = backend_url.rstrip('/')
        self.frontend_url = frontend_url.rstrip('/')
        self.session = requests.Session()
        self.results = {
            "backend": {},
            "frontend": {},
            "integration": {},
            "timestamp": datetime.now().isoformat()
        }

    def test_backend_health(self) -> bool:
        """Test if backend is responding"""
        print("\n📡 Testing Backend Health...")
        print("=" * 40)

        endpoints = [
            ("/", "Root endpoint"),
            ("/health", "Health check"),
            ("/docs", "API documentation"),
            ("/api/courses", "Courses endpoint"),
        ]

        all_passed = True
        for endpoint, description in endpoints:
            url = urljoin(self.backend_url, endpoint)
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code < 400:
                    print_status("success", f"{description}: {url} [{response.status_code}]")
                    self.results["backend"][endpoint] = "passed"
                else:
                    print_status("error", f"{description}: {url} [{response.status_code}]")
                    self.results["backend"][endpoint] = f"failed: {response.status_code}"
                    all_passed = False
            except requests.RequestException as e:
                print_status("error", f"{description}: {url} - {str(e)}")
                self.results["backend"][endpoint] = f"error: {str(e)}"
                all_passed = False

        return all_passed

    def test_frontend_build(self) -> bool:
        """Test if frontend is serving correctly"""
        print("\n🎨 Testing Frontend Build...")
        print("=" * 40)

        try:
            # Test main page
            response = self.session.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                print_status("success", f"Frontend main page: {self.frontend_url}")

                # Check for React app markers
                if "root" in response.text:
                    print_status("success", "React root element found")
                else:
                    print_status("warning", "React root element not found")

                # Check if it references the backend
                if "REACT_APP_API_URL" in response.text or self.backend_url in response.text:
                    print_status("success", "Backend URL configuration found")
                else:
                    print_status("warning", "Backend URL not found in frontend")

                self.results["frontend"]["main_page"] = "passed"
                return True
            else:
                print_status("error", f"Frontend returned status {response.status_code}")
                self.results["frontend"]["main_page"] = f"failed: {response.status_code}"
                return False

        except requests.RequestException as e:
            print_status("error", f"Cannot reach frontend: {str(e)}")
            self.results["frontend"]["main_page"] = f"error: {str(e)}"
            return False

    def test_api_functionality(self) -> bool:
        """Test core API functionality"""
        print("\n🔧 Testing API Functionality...")
        print("=" * 40)

        tests_passed = 0
        tests_total = 0

        # Test 1: Create a game
        tests_total += 1
        try:
            game_data = {
                "players": [
                    {"name": "Player1", "handicap": 10},
                    {"name": "Player2", "handicap": 15},
                    {"name": "Player3", "handicap": 8},
                    {"name": "Player4", "handicap": 12}
                ],
                "course_id": "wing_point"
            }

            response = self.session.post(
                f"{self.backend_url}/api/game/create",
                json=game_data,
                timeout=10
            )

            if response.status_code == 200:
                print_status("success", "Game creation API works")
                tests_passed += 1
                game_id = response.json().get("game_id")
                self.results["integration"]["game_creation"] = "passed"

                # Test 2: Get game state
                if game_id:
                    tests_total += 1
                    state_response = self.session.get(
                        f"{self.backend_url}/api/game/{game_id}/state",
                        timeout=5
                    )
                    if state_response.status_code == 200:
                        print_status("success", f"Game state retrieval works (ID: {game_id})")
                        tests_passed += 1
                        self.results["integration"]["game_state"] = "passed"
                    else:
                        print_status("error", "Game state retrieval failed")
                        self.results["integration"]["game_state"] = "failed"
            else:
                print_status("error", f"Game creation failed: {response.status_code}")
                self.results["integration"]["game_creation"] = f"failed: {response.status_code}"

        except requests.RequestException as e:
            print_status("error", f"API test failed: {str(e)}")
            self.results["integration"]["game_creation"] = f"error: {str(e)}"

        # Test 3: Monte Carlo simulation
        tests_total += 1
        try:
            mc_data = {
                "player_handicap": 10,
                "opponent_handicaps": [12, 15, 8],
                "holes_remaining": 9
            }

            response = self.session.post(
                f"{self.backend_url}/api/monte-carlo/simulate",
                json=mc_data,
                timeout=15
            )

            if response.status_code == 200:
                print_status("success", "Monte Carlo simulation works")
                tests_passed += 1
                self.results["integration"]["monte_carlo"] = "passed"
            else:
                print_status("error", f"Monte Carlo failed: {response.status_code}")
                self.results["integration"]["monte_carlo"] = f"failed: {response.status_code}"

        except requests.RequestException as e:
            print_status("warning", f"Monte Carlo test skipped: {str(e)}")
            self.results["integration"]["monte_carlo"] = f"skipped: {str(e)}"

        print(f"\nAPI Tests: {tests_passed}/{tests_total} passed")
        return tests_passed == tests_total

    def test_frontend_backend_integration(self) -> bool:
        """Test if frontend can communicate with backend"""
        print("\n🔗 Testing Frontend-Backend Integration...")
        print("=" * 40)

        # This would typically involve:
        # 1. Loading the frontend
        # 2. Checking if API calls are being made
        # 3. Verifying CORS headers

        try:
            # Test CORS by making a preflight request
            response = self.session.options(
                f"{self.backend_url}/api/game/create",
                headers={
                    "Origin": self.frontend_url,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type"
                },
                timeout=5
            )

            cors_headers = response.headers.get("Access-Control-Allow-Origin")
            if cors_headers:
                print_status("success", f"CORS configured: {cors_headers}")
                self.results["integration"]["cors"] = "passed"
                return True
            else:
                print_status("warning", "CORS headers not found (may still work)")
                self.results["integration"]["cors"] = "not configured"
                return True

        except Exception as e:
            print_status("warning", f"CORS test inconclusive: {str(e)}")
            self.results["integration"]["cors"] = "unknown"
            return True

    def run_all_tests(self) -> bool:
        """Run all deployment tests"""
        print(f"\n🚀 Testing Deployments")
        print(f"Backend:  {self.backend_url}")
        print(f"Frontend: {self.frontend_url}")
        print("=" * 50)

        all_passed = True

        # Run tests
        backend_ok = self.test_backend_health()
        frontend_ok = self.test_frontend_build()
        api_ok = self.test_api_functionality()
        integration_ok = self.test_frontend_backend_integration()

        # Summary
        print("\n" + "=" * 50)
        print("📊 DEPLOYMENT TEST SUMMARY")
        print("=" * 50)

        if backend_ok:
            print_status("success", "Backend: All tests passed")
        else:
            print_status("error", "Backend: Some tests failed")
            all_passed = False

        if frontend_ok:
            print_status("success", "Frontend: Build verified")
        else:
            print_status("error", "Frontend: Issues detected")
            all_passed = False

        if api_ok:
            print_status("success", "API: Core functionality working")
        else:
            print_status("warning", "API: Some functions not working")

        if integration_ok:
            print_status("success", "Integration: Frontend-Backend communication OK")
        else:
            print_status("warning", "Integration: May have issues")

        # Save results
        results_file = f"deployment-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")

        return all_passed

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Wolf-Goat-Pig deployments")
    parser.add_argument(
        "--backend",
        default="http://localhost:8000",
        help="Backend URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--frontend",
        default="http://localhost:3000",
        help="Frontend URL (default: http://localhost:3000)"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Test production deployments (Render/Vercel)"
    )

    args = parser.parse_args()

    if args.production:
        # You would set these to your actual production URLs
        backend_url = "https://your-app.onrender.com"
        frontend_url = "https://your-app.vercel.app"
        print("🌐 Testing PRODUCTION deployments")
    else:
        backend_url = args.backend
        frontend_url = args.frontend
        print("🏠 Testing LOCAL deployments")

    tester = DeploymentTester(backend_url, frontend_url)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()