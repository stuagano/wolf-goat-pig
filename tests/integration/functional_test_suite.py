#!/usr/bin/env python3
"""
Functional Testing Suite for Wolf Goat Pig
Tests public URLs with headless Chrome and polls deployment status
"""

import time
import requests
import subprocess
import sys
import json
from datetime import datetime
from urllib.parse import urljoin
import threading
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

class DeploymentMonitor:
    """Monitor deployment status of Render and Vercel services"""
    
    def __init__(self):
        self.services = {
            "render_api": "https://wolf-goat-pig-api.onrender.com",
            "render_frontend": "https://wolf-goat-pig-frontend.onrender.com", 
            "vercel_frontend": "https://wolf-goat-pig.vercel.app"
        }
        self.deployment_status = {}
        
    def check_service_health(self, service_name, url):
        """Check if a service is responding"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return True, f"✅ {service_name}: Online (Status: {response.status_code})"
            else:
                return False, f"⚠️ {service_name}: Responding but status {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"❌ {service_name}: Offline - {str(e)}"
    
    def check_api_health(self):
        """Check API health endpoint"""
        try:
            response = requests.get(f"{self.services['render_api']}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return True, f"✅ API Health: {data.get('message', 'Healthy')}"
            else:
                return False, f"⚠️ API Health: Status {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"❌ API Health: Error - {str(e)}"
    
    def check_courses_endpoint(self):
        """Check if courses endpoint is working"""
        try:
            response = requests.get(f"{self.services['render_api']}/courses", timeout=10)
            if response.status_code == 200:
                courses = response.json()
                course_count = len(courses)
                return True, f"✅ Courses API: {course_count} courses loaded"
            else:
                return False, f"⚠️ Courses API: Status {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"❌ Courses API: Error - {str(e)}"
    
    def poll_services(self, max_attempts=30, delay=10):
        """Poll all services until they're ready or max attempts reached"""
        print("🔄 Polling services for deployment readiness...")
        
        for attempt in range(max_attempts):
            print(f"\n📊 Attempt {attempt + 1}/{max_attempts}")
            print("=" * 50)
            
            all_ready = True
            
            # Check API health
            api_ready, api_msg = self.check_api_health()
            print(api_msg)
            if not api_ready:
                all_ready = False
            
            # Check courses endpoint
            courses_ready, courses_msg = self.check_courses_endpoint()
            print(courses_msg)
            if not courses_ready:
                all_ready = False
            
            # Check frontend services
            for service_name, url in self.services.items():
                if "api" not in service_name:  # Skip API, already checked
                    ready, msg = self.check_service_health(service_name, url)
                    print(msg)
                    if not ready:
                        all_ready = False
            
            if all_ready:
                print(f"\n🎉 All services are ready after {attempt + 1} attempts!")
                return True
            
            if attempt < max_attempts - 1:
                print(f"⏳ Waiting {delay} seconds before next check...")
                time.sleep(delay)
        
        print(f"\n❌ Services not ready after {max_attempts} attempts")
        return False

class FunctionalTester:
    """Functional testing with headless Chrome"""
    
    def __init__(self):
        self.driver = None
        self.test_results = []
        
    def setup_driver(self):
        """Setup headless Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except WebDriverException as e:
            print(f"❌ Chrome driver setup failed: {e}")
            print("💡 Make sure Chrome and chromedriver are installed")
            return False
    
    def teardown_driver(self):
        """Clean up driver"""
        if self.driver:
            self.driver.quit()
    
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": timestamp
        }
        self.test_results.append(result)
        print(f"{timestamp} {status}: {test_name} - {message}")
    
    def wait_for_element(self, by, value, timeout=10):
        """Wait for element to be present"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None
    
    def test_frontend_loading(self, url, name):
        """Test if frontend loads properly"""
        print(f"\n🌐 Testing {name}: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(3)  # Allow page to load
            
            # Check if page loaded
            if "Wolf Goat Pig" in self.driver.title:
                self.log_test(f"{name} - Page Load", True, "Title contains 'Wolf Goat Pig'")
            else:
                self.log_test(f"{name} - Page Load", False, f"Unexpected title: {self.driver.title}")
                return False
            
            # Check for main content
            main_content = self.wait_for_element(By.TAG_NAME, "body")
            if main_content:
                self.log_test(f"{name} - Content Load", True, "Main content loaded")
            else:
                self.log_test(f"{name} - Content Load", False, "No main content found")
                return False
            
            return True
            
        except Exception as e:
            self.log_test(f"{name} - Page Load", False, f"Error: {str(e)}")
            return False
    
    def test_simulation_mode(self, url):
        """Test simulation mode functionality"""
        print(f"\n🎮 Testing Simulation Mode: {url}")
        
        try:
            # Navigate to simulation mode
            self.driver.get(url)
            time.sleep(3)
            
            # Look for simulation mode elements
            simulation_elements = [
                "Simulation Mode",
                "Your Details", 
                "Computer Opponents",
                "Course Selection"
            ]
            
            page_text = self.driver.page_source
            found_elements = []
            
            for element in simulation_elements:
                if element in page_text:
                    found_elements.append(element)
            
            if len(found_elements) >= 3:
                self.log_test("Simulation Mode - UI Elements", True, f"Found {len(found_elements)}/4 elements")
            else:
                self.log_test("Simulation Mode - UI Elements", False, f"Only found {found_elements}")
                return False
            
            # Test course selection dropdown
            try:
                # Look for course selection
                if "Course Selection" in page_text and "Wing Point" in page_text:
                    self.log_test("Simulation Mode - Course Selection", True, "Course dropdown available")
                else:
                    self.log_test("Simulation Mode - Course Selection", False, "Course selection not found")
            except Exception as e:
                self.log_test("Simulation Mode - Course Selection", False, f"Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_test("Simulation Mode - General", False, f"Error: {str(e)}")
            return False
    
    def test_api_connectivity(self, frontend_url):
        """Test if frontend can connect to API"""
        print(f"\n🔗 Testing API Connectivity from: {frontend_url}")
        
        try:
            self.driver.get(frontend_url)
            time.sleep(3)
            
            # Check browser console for API errors
            logs = self.driver.get_log('browser')
            api_errors = [log for log in logs if 'api' in log['message'].lower() and 'error' in log['message'].lower()]
            
            if not api_errors:
                self.log_test("API Connectivity - Console", True, "No API errors in console")
            else:
                self.log_test("API Connectivity - Console", False, f"Found {len(api_errors)} API errors")
            
            # Try to trigger an API call by looking for simulation mode
            if "Simulation Mode" in self.driver.page_source:
                self.log_test("API Connectivity - Functionality", True, "Simulation mode loaded (API working)")
            else:
                self.log_test("API Connectivity - Functionality", False, "Simulation mode not accessible")
            
            return True
            
        except Exception as e:
            self.log_test("API Connectivity - General", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all functional tests"""
        print("🧪 Starting Functional Test Suite")
        print("=" * 60)
        
        if not self.setup_driver():
            return False
        
        try:
            # Test URLs
            test_urls = [
                ("https://wolf-goat-pig.vercel.app", "Vercel Frontend"),
                ("https://wolf-goat-pig-frontend.onrender.com", "Render Frontend")
            ]
            
            for url, name in test_urls:
                if self.test_frontend_loading(url, name):
                    self.test_simulation_mode(url)
                    self.test_api_connectivity(url)
            
            return True
            
        finally:
            self.teardown_driver()
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 FUNCTIONAL TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            print(f"  {result['timestamp']} {result['status']}: {result['test']}")
            if result['message']:
                print(f"    → {result['message']}")
        
        # Save report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": (passed_tests/total_tests)*100
            },
            "results": self.test_results
        }
        
        with open("functional_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Report saved to: functional_test_report.json")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    print("🚀 Wolf Goat Pig Functional Test Suite")
    print("=" * 60)
    
    # Step 1: Monitor deployment status
    monitor = DeploymentMonitor()
    print("📡 Checking deployment status...")
    
    if not monitor.poll_services():
        print("❌ Services not ready. Exiting.")
        return False
    
    print("\n✅ All services are ready! Starting functional tests...")
    
    # Step 2: Run functional tests
    tester = FunctionalTester()
    success = tester.run_all_tests()
    
    # Step 3: Generate report
    all_passed = tester.generate_report()
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Your deployment is working correctly.")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the report for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 