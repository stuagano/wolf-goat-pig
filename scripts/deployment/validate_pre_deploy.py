#!/usr/bin/env python3
"""
Deployment Validation Script for Wolf Goat Pig

This script checks for common deployment issues before deploying to Render/Vercel.
Run this script before deploying to catch issues early.
"""

import os
import sys
import ast
import json
import re
from pathlib import Path
from typing import List, Dict, Any

class DeploymentValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"

    def add_issue(self, issue: str):
        """Add a critical issue that will prevent deployment"""
        self.issues.append(f"❌ {issue}")

    def add_warning(self, warning: str):
        """Add a warning that might cause issues"""
        self.warnings.append(f"⚠️  {warning}")

    def validate_python_imports(self):
        """Check for problematic import patterns"""
        print("🔍 Checking Python imports...")
        
        python_files = list(self.backend_dir.glob("**/*.py"))
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for absolute backend imports
                if re.search(r'from backend\.', content):
                    self.add_issue(f"Absolute import found in {file_path.relative_to(self.root_dir)}")
                
                # Check for missing imports
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Name):
                            # Check for common missing imports
                            if node.id == 'Any' and 'from typing import' in content and 'Any' not in content:
                                self.add_issue(f"Missing 'Any' import in {file_path.relative_to(self.root_dir)}")
                except SyntaxError as e:
                    self.add_issue(f"Syntax error in {file_path.relative_to(self.root_dir)}: {e}")
                        
            except Exception as e:
                self.add_warning(f"Could not read {file_path.relative_to(self.root_dir)}: {e}")

    def validate_requirements(self):
        """Check requirements.txt for issues"""
        print("🔍 Checking requirements.txt...")
        
        req_file = self.backend_dir / "requirements.txt"
        if not req_file.exists():
            self.add_issue("requirements.txt not found in backend/")
            return
        
        try:
            with open(req_file, 'r') as f:
                requirements = f.read()
            
            # Check for version pinning
            lines = [line.strip() for line in requirements.split('\n') if line.strip() and not line.startswith('#')]
            unpinned = [line for line in lines if '==' not in line and line]
            
            if unpinned:
                self.add_warning(f"Unpinned dependencies: {', '.join(unpinned)}")
            
            # Check for essential packages
            essential = ['fastapi', 'uvicorn', 'sqlalchemy', 'httpx']
            for package in essential:
                if not any(package.lower() in line.lower() for line in lines):
                    self.add_issue(f"Missing essential package: {package}")
                    
        except Exception as e:
            self.add_issue(f"Could not read requirements.txt: {e}")

    def validate_configuration_files(self):
        """Check deployment configuration files"""
        print("🔍 Checking configuration files...")
        
        # Check render.yaml
        render_file = self.root_dir / "render.yaml"
        if render_file.exists():
            try:
                with open(render_file, 'r') as f:
                    content = f.read()
                if 'healthCheckPath: /health' not in content:
                    self.add_warning("Health check path not configured in render.yaml")
            except Exception as e:
                self.add_warning(f"Could not read render.yaml: {e}")
        else:
            self.add_warning("render.yaml not found - needed for Render deployment")
        
        # Check vercel.json
        vercel_file = self.root_dir / "vercel.json"
        if vercel_file.exists():
            try:
                with open(vercel_file, 'r') as f:
                    vercel_config = json.load(f)
                
                if 'builds' not in vercel_config:
                    self.add_issue("vercel.json missing 'builds' configuration")
                
                if 'routes' not in vercel_config:
                    self.add_issue("vercel.json missing 'routes' configuration")
                    
            except json.JSONDecodeError as e:
                self.add_issue(f"Invalid JSON in vercel.json: {e}")
            except Exception as e:
                self.add_warning(f"Could not read vercel.json: {e}")
        else:
            self.add_warning("vercel.json not found - needed for Vercel deployment")

    def validate_frontend_build(self):
        """Check frontend configuration"""
        print("🔍 Checking frontend configuration...")
        
        package_json = self.frontend_dir / "package.json"
        if not package_json.exists():
            self.add_issue("frontend/package.json not found")
            return
        
        try:
            with open(package_json, 'r') as f:
                package_config = json.load(f)
            
            # Check scripts
            scripts = package_config.get('scripts', {})
            if 'build' not in scripts:
                self.add_issue("Missing 'build' script in package.json")
            
            # Check dependencies
            deps = package_config.get('dependencies', {})
            essential_deps = ['react', 'react-dom', 'react-scripts']
            for dep in essential_deps:
                if dep not in deps:
                    self.add_issue(f"Missing essential dependency: {dep}")
                    
        except json.JSONDecodeError as e:
            self.add_issue(f"Invalid JSON in package.json: {e}")
        except Exception as e:
            self.add_issue(f"Could not read package.json: {e}")

    def validate_environment_variables(self):
        """Check environment variable configuration"""
        print("🔍 Checking environment variables...")
        
        # Check if .env.example exists
        env_example = self.root_dir / ".env.example"
        if not env_example.exists():
            self.add_warning(".env.example not found - helpful for deployment setup")
        
        # Check for hardcoded URLs in code
        python_files = list(self.backend_dir.glob("**/*.py"))
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for hardcoded localhost URLs
                if 'localhost:' in content and 'os.getenv' not in content:
                    self.add_warning(f"Hardcoded localhost found in {file_path.relative_to(self.root_dir)}")
                    
            except Exception:
                pass  # Skip files that can't be read

    def validate_database_configuration(self):
        """Check database configuration"""
        print("🔍 Checking database configuration...")
        
        database_file = self.backend_dir / "app" / "database.py"
        if not database_file.exists():
            self.add_issue("database.py not found")
            return
        
        try:
            with open(database_file, 'r') as f:
                content = f.read()
            
            # Check for proper DATABASE_URL handling
            if 'DATABASE_URL' not in content:
                self.add_issue("DATABASE_URL not handled in database.py")
            
            # Check for PostgreSQL support
            if 'postgresql' not in content:
                self.add_warning("PostgreSQL support not detected in database.py")
                
        except Exception as e:
            self.add_warning(f"Could not read database.py: {e}")

    def validate_api_endpoints(self):
        """Check API endpoint configuration"""
        print("🔍 Checking API endpoints...")
        
        main_file = self.backend_dir / "app" / "main.py"
        if not main_file.exists():
            self.add_issue("main.py not found")
            return
        
        try:
            with open(main_file, 'r') as f:
                content = f.read()
            
            # Check for health endpoint
            if '@app.get("/health")' not in content:
                self.add_issue("Health endpoint not found - required for Render")
            
            # Check for CORS configuration
            if 'CORSMiddleware' not in content:
                self.add_issue("CORS middleware not configured")
            
            # Check for proper error handling
            if 'exception_handler' not in content:
                self.add_warning("Global exception handler not found")
                
        except Exception as e:
            self.add_issue(f"Could not read main.py: {e}")

    def validate_file_structure(self):
        """Check required file structure"""
        print("🔍 Checking file structure...")
        
        required_files = [
            "backend/app/main.py",
            "backend/app/database.py",
            "backend/requirements.txt",
            "frontend/package.json",
            "frontend/src/App.js"
        ]
        
        for file_path in required_files:
            full_path = self.root_dir / file_path
            if not full_path.exists():
                self.add_issue(f"Required file missing: {file_path}")

    def run_validation(self):
        """Run all validation checks"""
        print("🚀 Starting deployment validation...\n")
        
        self.validate_file_structure()
        self.validate_python_imports()
        self.validate_requirements()
        self.validate_configuration_files()
        self.validate_frontend_build()
        self.validate_environment_variables()
        self.validate_database_configuration()
        self.validate_api_endpoints()
        
        print("\n" + "="*60)
        print("📋 DEPLOYMENT VALIDATION RESULTS")
        print("="*60)
        
        if self.issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  {issue}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if not self.issues and not self.warnings:
            print("\n✅ All checks passed! Ready for deployment.")
            return True
        elif not self.issues:
            print(f"\n✅ No critical issues found. {len(self.warnings)} warnings to review.")
            print("Deployment should succeed, but consider addressing warnings.")
            return True
        else:
            print(f"\n❌ {len(self.issues)} critical issues found. Fix these before deploying.")
            print("Deployment will likely fail with these issues.")
            return False

def main():
    """Main function"""
    validator = DeploymentValidator()
    success = validator.run_validation()
    
    if success:
        print("\n🎉 Ready to deploy!")
        print("\nNext steps:")
        print("1. Commit and push your changes")
        print("2. Deploy backend to Render")
        print("3. Deploy frontend to Vercel")
        print("4. Configure environment variables")
        print("5. Test the deployed application")
        sys.exit(0)
    else:
        print("\n🔧 Fix the issues above and run this script again.")
        sys.exit(1)

if __name__ == "__main__":
    main()