#!/usr/bin/env python3
"""
Wolf Goat Pig - Quick Deployment Check
Simple validation script for deployment readiness
"""

import subprocess
import sys
import os
from pathlib import Path

def run_cmd(cmd, cwd=None):
    """Run command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_backend():
    """Check backend deployment readiness"""
    print("🔍 Checking backend...")
    
    # Check if venv exists
    if not Path("backend/venv").exists():
        print("❌ Backend virtual environment missing")
        return False
    
    # Test backend imports
    success, _, stderr = run_cmd(
        "source venv/bin/activate && python -c 'from app.main import app'", 
        cwd="backend"
    )
    if not success:
        print(f"❌ Backend import failed: {stderr}")
        return False
    
    print("✅ Backend OK")
    return True

def check_frontend():
    """Check frontend deployment readiness"""
    print("🔍 Checking frontend...")
    
    # Test frontend build
    success, stdout, stderr = run_cmd("npm run build", cwd="frontend")
    if not success:
        print(f"❌ Frontend build failed: {stderr}")
        return False
    
    if "Failed to compile" in stdout:
        print("❌ Frontend compilation errors")
        return False
    
    print("✅ Frontend OK")
    return True

def check_configs():
    """Check deployment configurations"""
    print("🔍 Checking deployment configs...")
    
    required_files = ["render.yaml", "vercel.json"]
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Missing {file}")
            return False
    
    print("✅ Configs OK")
    return True

def main():
    """Main validation"""
    print("🚀 Wolf Goat Pig - Deployment Check")
    print("=" * 40)
    
    os.chdir(Path(__file__).parent)
    
    checks = [
        ("Backend", check_backend),
        ("Frontend", check_frontend), 
        ("Configs", check_configs)
    ]
    
    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 Ready for deployment!")
        return 0
    else:
        print("🔧 Fix issues before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())