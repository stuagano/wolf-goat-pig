#!/usr/bin/env python3
"""
Deployment validation script for Wolf Goat Pig project.
Validates both Render (backend) and Vercel (frontend) deployments.
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional
from urllib.parse import urljoin


class DeploymentValidator:
    """Validates deployment health and functionality."""
    
    def __init__(self, backend_url: str, frontend_url: str):
        self.backend_url = backend_url.rstrip('/')
        self.frontend_url = frontend_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        
    def validate_backend(self) -> Dict[str, Any]:
        """Validate backend deployment on Render."""
        print(f"🔍 Validating backend deployment at {self.backend_url}")
        results = {
            "status": "healthy",
            "tests": {},
            "errors": []
        }
        
        try:
            # Test 1: Health endpoint
            print("  Testing health endpoint...")
            health_response = self.session.get(f"{self.backend_url}/health")
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                results["tests"]["health_endpoint"] = {
                    "status": "✅ PASS",
                    "data": health_data
                }
                print(f"    ✅ Health endpoint: {health_data.get('status', 'unknown')}")
                
                # Check if all components are healthy
                components = health_data.get('components', {})
                unhealthy = [k for k, v in components.items() if 'unhealthy' in str(v)]
                if unhealthy:
                    results["errors"].append(f"Unhealthy components: {', '.join(unhealthy)}")
                    results["status"] = "degraded"
                    
            else:
                results["tests"]["health_endpoint"] = {
                    "status": f"❌ FAIL - HTTP {health_response.status_code}",
                    "error": health_response.text
                }
                results["status"] = "unhealthy"
                results["errors"].append(f"Health endpoint returned {health_response.status_code}")
                print(f"    ❌ Health endpoint failed: HTTP {health_response.status_code}")
                
            # Test 2: API Documentation
            print("  Testing API documentation...")
            docs_response = self.session.get(f"{self.backend_url}/docs")
            if docs_response.status_code == 200:
                results["tests"]["api_docs"] = {"status": "✅ PASS"}
                print("    ✅ API documentation accessible")
            else:
                results["tests"]["api_docs"] = {
                    "status": f"❌ FAIL - HTTP {docs_response.status_code}",
                    "error": docs_response.text
                }
                print(f"    ❌ API docs failed: HTTP {docs_response.status_code}")
                
            # Test 3: CORS headers
            print("  Testing CORS configuration...")
            options_response = self.session.options(f"{self.backend_url}/health")
            cors_headers = {
                k: v for k, v in options_response.headers.items() 
                if k.lower().startswith('access-control')
            }
            
            if cors_headers:
                results["tests"]["cors"] = {
                    "status": "✅ PASS",
                    "headers": cors_headers
                }
                print("    ✅ CORS headers configured")
            else:
                results["tests"]["cors"] = {"status": "⚠️ WARNING - No CORS headers found"}
                print("    ⚠️ No CORS headers found")
                
        except requests.exceptions.RequestException as e:
            results["status"] = "unreachable"
            results["errors"].append(f"Connection error: {str(e)}")
            results["tests"]["connection"] = {"status": f"❌ FAIL - {str(e)}"}
            print(f"    ❌ Connection failed: {e}")
            
        return results
        
    def validate_frontend(self) -> Dict[str, Any]:
        """Validate frontend deployment on Vercel."""
        print(f"🔍 Validating frontend deployment at {self.frontend_url}")
        results = {
            "status": "healthy",
            "tests": {},
            "errors": []
        }
        
        try:
            # Test 1: Main page loads
            print("  Testing main page...")
            main_response = self.session.get(self.frontend_url)
            
            if main_response.status_code == 200:
                content = main_response.text
                # Check for React app indicators
                if 'id="root"' in content or 'react' in content.lower():
                    results["tests"]["main_page"] = {"status": "✅ PASS"}
                    print("    ✅ Main page loads with React app")
                else:
                    results["tests"]["main_page"] = {
                        "status": "⚠️ WARNING - Page loads but React app not detected"
                    }
                    print("    ⚠️ Page loads but React app not clearly detected")
            else:
                results["tests"]["main_page"] = {
                    "status": f"❌ FAIL - HTTP {main_response.status_code}",
                    "error": main_response.text[:200]
                }
                results["status"] = "unhealthy"
                results["errors"].append(f"Main page returned {main_response.status_code}")
                print(f"    ❌ Main page failed: HTTP {main_response.status_code}")
                
            # Test 2: Static assets
            print("  Testing static assets...")
            manifest_response = self.session.get(f"{self.frontend_url}/manifest.json")
            if manifest_response.status_code == 200:
                results["tests"]["static_assets"] = {"status": "✅ PASS"}
                print("    ✅ Static assets accessible")
            else:
                results["tests"]["static_assets"] = {
                    "status": f"⚠️ WARNING - manifest.json not found (HTTP {manifest_response.status_code})"
                }
                print(f"    ⚠️ manifest.json not found")
                
            # Test 3: Security headers
            print("  Testing security headers...")
            security_headers = {
                k: v for k, v in main_response.headers.items() 
                if k.lower() in ['x-content-type-options', 'x-frame-options', 'x-xss-protection']
            }
            
            if len(security_headers) >= 2:
                results["tests"]["security_headers"] = {
                    "status": "✅ PASS",
                    "headers": security_headers
                }
                print("    ✅ Security headers configured")
            else:
                results["tests"]["security_headers"] = {
                    "status": "⚠️ WARNING - Limited security headers",
                    "headers": security_headers
                }
                print("    ⚠️ Limited security headers found")
                
        except requests.exceptions.RequestException as e:
            results["status"] = "unreachable"
            results["errors"].append(f"Connection error: {str(e)}")
            results["tests"]["connection"] = {"status": f"❌ FAIL - {str(e)}"}
            print(f"    ❌ Connection failed: {e}")
            
        return results
        
    def validate_integration(self) -> Dict[str, Any]:
        """Test frontend-backend integration."""
        print(f"🔗 Testing frontend-backend integration")
        results = {
            "status": "healthy",
            "tests": {},
            "errors": []
        }
        
        try:
            # This would require checking if frontend can reach backend
            # For now, we'll just verify the URLs are configured correctly
            print("  Checking API URL configuration...")
            
            # In a real test, we might load the frontend and check if it makes
            # successful API calls to the backend
            results["tests"]["api_configuration"] = {
                "status": "ℹ️  INFO - Manual verification needed",
                "backend_url": self.backend_url,
                "frontend_url": self.frontend_url,
                "note": "Verify frontend can reach backend API endpoints"
            }
            print("    ℹ️  Integration test requires manual verification")
            
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(f"Integration test error: {str(e)}")
            print(f"    ❌ Integration test failed: {e}")
            
        return results
        
    def run_validation(self) -> Dict[str, Any]:
        """Run complete deployment validation."""
        print("🚀 Starting deployment validation...")
        print(f"Backend URL: {self.backend_url}")
        print(f"Frontend URL: {self.frontend_url}")
        print("-" * 60)
        
        overall_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "backend_url": self.backend_url,
            "frontend_url": self.frontend_url,
            "backend": self.validate_backend(),
            "frontend": self.validate_frontend(),
            "integration": self.validate_integration(),
            "overall_status": "healthy"
        }
        
        # Determine overall status
        if (overall_results["backend"]["status"] == "unreachable" or 
            overall_results["frontend"]["status"] == "unreachable"):
            overall_results["overall_status"] = "unreachable"
        elif (overall_results["backend"]["status"] == "unhealthy" or 
              overall_results["frontend"]["status"] == "unhealthy"):
            overall_results["overall_status"] = "unhealthy"
        elif (overall_results["backend"]["status"] == "degraded" or 
              overall_results["frontend"]["status"] == "degraded"):
            overall_results["overall_status"] = "degraded"
            
        print("-" * 60)
        print(f"🏁 Validation complete - Overall status: {overall_results['overall_status'].upper()}")
        
        return overall_results


def main():
    """Main function to run deployment validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Wolf Goat Pig deployments")
    parser.add_argument(
        "--backend", 
        default="https://wolf-goat-pig-api.onrender.com",
        help="Backend URL (Render deployment)"
    )
    parser.add_argument(
        "--frontend", 
        default="https://wolf-goat-pig.vercel.app",
        help="Frontend URL (Vercel deployment)"
    )
    parser.add_argument(
        "--output", 
        choices=["json", "text"], 
        default="text",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    validator = DeploymentValidator(args.backend, args.frontend)
    results = validator.run_validation()
    
    if args.output == "json":
        print(json.dumps(results, indent=2))
    else:
        # Text output already printed during validation
        print(f"\nSummary:")
        print(f"  Backend: {results['backend']['status']}")
        print(f"  Frontend: {results['frontend']['status']}")
        print(f"  Overall: {results['overall_status']}")
        
        if results["backend"]["errors"] or results["frontend"]["errors"]:
            print(f"\nErrors found:")
            for error in results["backend"]["errors"]:
                print(f"  Backend: {error}")
            for error in results["frontend"]["errors"]:
                print(f"  Frontend: {error}")
    
    # Exit with error code if validation failed
    if results["overall_status"] in ["unhealthy", "unreachable"]:
        sys.exit(1)
    elif results["overall_status"] == "degraded":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()