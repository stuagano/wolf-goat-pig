#!/usr/bin/env python3
"""
Setup script for functional testing
Installs dependencies and Chrome driver
"""

import subprocess
import sys
import os
from webdriver_manager.chrome import ChromeDriverManager

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-testing.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_chrome_driver():
    """Setup Chrome driver"""
    print("🔧 Setting up Chrome driver...")
    try:
        # Install Chrome driver
        driver_path = ChromeDriverManager().install()
        print(f"✅ Chrome driver installed at: {driver_path}")
        
        # Set environment variable
        os.environ['PATH'] = f"{os.path.dirname(driver_path)}:{os.environ.get('PATH', '')}"
        print("✅ Chrome driver added to PATH")
        return True
    except Exception as e:
        print(f"❌ Failed to setup Chrome driver: {e}")
        return False

def check_chrome_installation():
    """Check if Chrome is installed"""
    print("🔍 Checking Chrome installation...")
    try:
        # Try to find Chrome
        result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Chrome found at: {result.stdout.strip()}")
            return True
        else:
            print("⚠️ Chrome not found in PATH")
            print("💡 Please install Chrome manually:")
            print("   - macOS: brew install --cask google-chrome")
            print("   - Ubuntu: sudo apt-get install google-chrome-stable")
            print("   - Windows: Download from https://www.google.com/chrome/")
            return False
    except Exception as e:
        print(f"❌ Error checking Chrome: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Functional Testing Environment")
    print("=" * 50)
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Check Chrome
    if not check_chrome_installation():
        print("⚠️ Chrome not found, but continuing...")
    
    # Setup Chrome driver
    if not setup_chrome_driver():
        return False
    
    print("\n✅ Setup complete! You can now run:")
    print("   python functional_test_suite.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 