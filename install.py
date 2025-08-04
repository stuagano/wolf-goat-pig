#!/usr/bin/env python3
"""
Consolidated installer for Wolf Goat Pig application
Handles all dependencies: Python, Node.js, browsers, and system packages
"""

import subprocess
import sys
import os
import platform
import shutil
from pathlib import Path

class WolfGoatPigInstaller:
    def __init__(self):
        self.system = platform.system().lower()
        self.root_dir = Path(__file__).parent
        self.reports_dir = self.root_dir / "reports"
        
    def log(self, message, emoji="ℹ️"):
        """Print formatted log message"""
        print(f"{emoji} {message}")
        
    def run_command(self, command, description, shell=False, cwd=None):
        """Run command with error handling"""
        self.log(f"Running: {description}")
        try:
            if shell:
                result = subprocess.run(command, shell=True, check=True, cwd=cwd, 
                                      capture_output=False, text=True)
            else:
                result = subprocess.run(command, check=True, cwd=cwd,
                                      capture_output=False, text=True)
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Failed: {description} - {e}", "❌")
            return False
        except Exception as e:
            self.log(f"Error: {description} - {e}", "❌")
            return False
    
    def check_command_exists(self, command):
        """Check if command exists in PATH"""
        return shutil.which(command) is not None
    
    def install_python_dependencies(self):
        """Install Python dependencies for both main app and testing"""
        self.log("Installing Python dependencies...", "📦")
        
        # Check if we're in a virtual environment
        venv_path = self.root_dir / "backend" / "venv"
        if venv_path.exists():
            self.log("Using existing virtual environment", "🐍")
            python_cmd = str(venv_path / "bin" / "python")
            pip_cmd = [python_cmd, "-m", "pip", "install"]
        else:
            self.log("Using system Python with --user flag", "🐍")
            pip_cmd = [sys.executable, "-m", "pip", "install", "--user"]
        
        # Install main backend requirements
        backend_dir = self.root_dir / "backend"
        if (backend_dir / "requirements.txt").exists():
            cmd = pip_cmd + ["-r", "requirements.txt"]
            if not self.run_command(cmd, "Backend requirements", cwd=backend_dir):
                return False
        
        # Install test requirements
        test_files = ["requirements-test.txt", "requirements-testing.txt"]
        for test_file in test_files:
            test_path = self.root_dir / test_file
            if test_path.exists():
                cmd = pip_cmd + ["-r", str(test_path)]
                if not self.run_command(cmd, f"Test requirements ({test_file})"):
                    return False
        
        return True
    
    def install_node_dependencies(self):
        """Install Node.js dependencies"""
        self.log("Installing Node.js dependencies...", "📦")
        
        # Install root package dependencies
        if (self.root_dir / "package.json").exists():
            if not self.run_command(["npm", "install"], "Root npm dependencies", cwd=self.root_dir):
                return False
        
        # Install frontend dependencies
        frontend_dir = self.root_dir / "frontend"
        if (frontend_dir / "package.json").exists():
            if not self.run_command(["npm", "install"], "Frontend npm dependencies", cwd=frontend_dir):
                return False
        
        return True
    
    def install_playwright_browsers(self):
        """Install Playwright browsers"""
        self.log("Installing Playwright browsers...", "🌐")
        return self.run_command(["playwright", "install", "chromium"], "Playwright browsers")
    
    def setup_chrome_driver(self):
        """Setup Chrome WebDriver"""
        self.log("Setting up Chrome WebDriver...", "🔧")
        try:
            # Import here to avoid dependency issues during initial run
            from webdriver_manager.chrome import ChromeDriverManager
            
            driver_path = ChromeDriverManager().install()
            self.log(f"Chrome driver installed at: {driver_path}", "✅")
            
            # Add to PATH
            driver_dir = os.path.dirname(driver_path)
            current_path = os.environ.get('PATH', '')
            if driver_dir not in current_path:
                os.environ['PATH'] = f"{driver_dir}:{current_path}"
                self.log("Chrome driver added to PATH", "✅")
            
            return True
        except ImportError:
            self.log("webdriver-manager not installed yet, will install with dependencies", "⚠️")
            return True
        except Exception as e:
            self.log(f"Failed to setup Chrome driver: {e}", "❌")
            return False
    
    def install_system_dependencies(self):
        """Install system dependencies for headless browsers"""
        self.log("Installing system dependencies...", "🖥️")
        
        if self.system == "darwin":
            self.log("macOS detected. No additional system dependencies needed.", "ℹ️")
            return True
        elif self.system == "linux":
            return self._install_linux_dependencies()
        else:
            self.log(f"Unsupported system: {self.system}", "⚠️")
            return True
    
    def _install_linux_dependencies(self):
        """Install Linux-specific dependencies"""
        packages_apt = [
            "libnss3", "libgconf-2-4", "libxss1", "libasound2", "libxtst6",
            "libgtk-3-0", "libdrm2", "libxcomposite1", "libxdamage1",
            "libxrandr2", "libgbm1", "libxkbcommon0", "libatspi2.0-0"
        ]
        
        packages_yum = [
            "nss", "atk", "at-spi2-atk", "gtk3", "cups-libs", "libdrm",
            "libXt", "libXrandr", "alsa-lib", "mesa-libgbm", "libXScrnSaver"
        ]
        
        if self.check_command_exists("apt-get"):
            cmd = ["sudo", "apt-get", "update"]
            if not self.run_command(cmd, "Update package list"):
                return False
            cmd = ["sudo", "apt-get", "install", "-y"] + packages_apt
            return self.run_command(cmd, "Install system dependencies (apt)")
        elif self.check_command_exists("yum"):
            cmd = ["sudo", "yum", "install", "-y"] + packages_yum
            return self.run_command(cmd, "Install system dependencies (yum)")
        else:
            self.log("No supported package manager found", "⚠️")
            return True
    
    def check_prerequisites(self):
        """Check if required tools are installed"""
        self.log("Checking prerequisites...", "🔍")
        
        required_tools = {
            "python3": "Python 3",
            "pip": "pip",
            "node": "Node.js",
            "npm": "npm"
        }
        
        missing_tools = []
        for tool, name in required_tools.items():
            if not self.check_command_exists(tool):
                missing_tools.append(name)
        
        if missing_tools:
            self.log(f"Missing required tools: {', '.join(missing_tools)}", "❌")
            self.log("Please install them before running this installer", "💡")
            return False
        
        self.log("All prerequisites found", "✅")
        return True
    
    def setup_directories(self):
        """Create necessary directories"""
        self.log("Setting up directories...", "📁")
        
        directories = [self.reports_dir]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            self.log(f"Created directory: {directory}", "✅")
        
        return True
    
    def make_scripts_executable(self):
        """Make shell scripts executable"""
        self.log("Making scripts executable...", "🔧")
        
        scripts_dir = self.root_dir / "scripts"
        if scripts_dir.exists():
            for script in scripts_dir.glob("*.sh"):
                script.chmod(0o755)
                self.log(f"Made executable: {script.name}", "✅")
        
        return True
    
    def print_usage_instructions(self):
        """Print usage instructions"""
        self.log("Installation complete! 🎉", "✅")
        print("\n" + "=" * 60)
        print("🧪 TESTING COMMANDS:")
        print("  • All tests:           pytest")
        print("  • BDD tests only:      pytest -m bdd")
        print("  • API tests only:      pytest tests/test_monte_carlo_api.py")
        print("  • Smoke tests:         pytest -m smoke")
        print("  • With HTML report:    pytest --html=reports/test_report.html")
        print("\n🚀 DEVELOPMENT SERVERS:")
        print("  • Backend:  cd backend && python -m uvicorn app.main:app --reload")
        print("  • Frontend: cd frontend && npm start")
        print("\n🎮 FUNCTIONAL TESTS:")
        print("  • Run full suite:      python functional_test_suite.py")
        print("=" * 60)
    
    def install(self):
        """Run complete installation"""
        self.log("Starting Wolf Goat Pig installation...", "🚀")
        print("=" * 60)
        
        steps = [
            ("Check prerequisites", self.check_prerequisites),
            ("Setup directories", self.setup_directories),
            ("Install Python dependencies", self.install_python_dependencies),
            ("Install Node.js dependencies", self.install_node_dependencies),
            ("Install system dependencies", self.install_system_dependencies),
            ("Install Playwright browsers", self.install_playwright_browsers),
            ("Setup Chrome WebDriver", self.setup_chrome_driver),
            ("Make scripts executable", self.make_scripts_executable),
        ]
        
        for step_name, step_func in steps:
            self.log(f"Step: {step_name}", "⚡")
            if not step_func():
                self.log(f"Installation failed at: {step_name}", "❌")
                return False
        
        self.print_usage_instructions()
        return True

def main():
    """Main entry point"""
    installer = WolfGoatPigInstaller()
    success = installer.install()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())