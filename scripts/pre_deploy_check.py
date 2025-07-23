#!/usr/bin/env python3
"""
Pre-deployment validation script for Wolf Goat Pig API
Runs syntax checks, import tests, and basic validation before deployment
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def check_python_syntax():
    """Check Python syntax for all backend files"""
    print("🔍 Checking Python syntax...")
    
    backend_files = [
        "backend/app/main.py",
        "backend/app/simulation.py", 
        "backend/app/database.py",
        "backend/app/models.py",
        "backend/app/schemas.py",
        "backend/app/crud.py",
        "backend/app/game_state.py"
    ]
    
    for file_path in backend_files:
        if os.path.exists(file_path):
            try:
                subprocess.run([sys.executable, "-m", "py_compile", file_path], 
                             check=True, capture_output=True, text=True)
                print(f"✅ {file_path} - syntax OK")
            except subprocess.CalledProcessError as e:
                print(f"❌ {file_path} - syntax error:")
                print(e.stderr)
                return False
        else:
            print(f"⚠️  {file_path} - file not found")
    
    return True

def check_imports():
    """Check that all imports work correctly"""
    print("\n🔍 Checking imports...")
    
    try:
        # Test database module
        from app.database import init_db
        print("✅ Database module imports OK")
        
        # Test main module (without running server)
        import app.main
        print("✅ Main module imports OK")
        
        # Test simulation module
        from app.simulation import SimulationEngine
        print("✅ Simulation module imports OK")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def check_requirements():
    """Check that requirements.txt has all necessary packages"""
    print("\n🔍 Checking requirements...")
    
    req_file = "backend/requirements.txt"
    if not os.path.exists(req_file):
        print(f"❌ {req_file} not found")
        return False
    
    with open(req_file) as f:
        requirements = f.read()
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy", 
        "psycopg2-binary",
        "python-multipart",
        "httpx"
    ]
    
    missing = []
    for package in required_packages:
        if package.lower() not in requirements.lower():
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages in requirements.txt: {missing}")
        return False
    
    print("✅ Requirements check passed")
    return True

def check_frontend():
    """Check frontend configuration"""
    print("\n🔍 Checking frontend...")
    
    package_json = "frontend/package.json"
    if not os.path.exists(package_json):
        print(f"❌ {package_json} not found")
        return False
    
    print("✅ Frontend package.json found")
    return True

def main():
    """Run all pre-deployment checks"""
    print("🚀 Wolf Goat Pig Pre-Deployment Validation")
    print("=" * 50)
    
    checks = [
        ("Python Syntax", check_python_syntax),
        ("Python Imports", check_imports),
        ("Requirements", check_requirements),
        ("Frontend Config", check_frontend)
    ]
    
    all_passed = True
    for name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {name} check failed with exception: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All pre-deployment checks PASSED! 🎉")
        print("🚀 Ready for deployment!")
        sys.exit(0)
    else:
        print("❌ Some checks FAILED! 💥")
        print("🔧 Please fix the issues before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()