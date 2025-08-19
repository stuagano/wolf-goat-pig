#!/usr/bin/env python3
"""
Wolf Goat Pig Local Development Runner

This script:
1. Kills any existing processes running on ports 3000 and 8000
2. Starts the backend (FastAPI) and frontend (React) simultaneously
3. Provides colored output and process management
4. Handles graceful shutdown with Ctrl+C
"""

import subprocess
import sys
import os
import signal
import time
import threading
from pathlib import Path

class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class LocalRunner:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
    def log(self, message, color=Colors.WHITE, prefix="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"{color}{Colors.BOLD}[{timestamp}] {prefix}:{Colors.END} {message}")
    
    def kill_existing_processes(self):
        """Kill any processes running on ports 3000 and 8000"""
        self.log("🔍 Checking for existing processes...", Colors.YELLOW, "CLEANUP")
        
        ports_to_check = [3000, 8000]
        for port in ports_to_check:
            try:
                # Find processes using the port
                result = subprocess.run(
                    ["lsof", "-ti", f":{port}"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid:
                            self.log(f"🔪 Killing process {pid} on port {port}", Colors.RED, "KILL")
                            subprocess.run(["kill", "-9", pid], check=False)
                else:
                    self.log(f"✅ Port {port} is free", Colors.GREEN, "PORT")
                    
            except Exception as e:
                self.log(f"Error checking port {port}: {e}", Colors.RED, "ERROR")
    
    def setup_backend(self):
        """Install backend dependencies and initialize database"""
        self.log("🐍 Setting up backend...", Colors.BLUE, "BACKEND")
        
        # Check if requirements are already installed
        try:
            subprocess.run(
                ["python", "-c", "import fastapi, uvicorn"],
                cwd=self.backend_dir,
                check=True,
                capture_output=True
            )
            self.log("✅ Backend dependencies already installed", Colors.GREEN, "BACKEND")
        except subprocess.CalledProcessError:
            self.log("📦 Installing backend dependencies...", Colors.YELLOW, "BACKEND")
            # Try local requirements first (better for Python 3.13+)
            try:
                subprocess.run(
                    ["pip", "install", "-r", "requirements-local.txt"],
                    cwd=self.backend_dir,
                    check=True
                )
            except subprocess.CalledProcessError:
                self.log("⚠️ Local requirements failed, trying main requirements...", Colors.YELLOW, "BACKEND")
                subprocess.run(
                    ["pip", "install", "-r", "requirements.txt"],
                    cwd=self.backend_dir,
                    check=True
                )
        
        # Initialize database
        self.log("🗄️ Initializing database...", Colors.BLUE, "BACKEND")
        subprocess.run(
            ["python", "-c", "from app.database import init_db; init_db()"],
            cwd=self.backend_dir,
            check=True
        )
    
    def setup_frontend(self):
        """Install frontend dependencies"""
        self.log("⚛️ Setting up frontend...", Colors.CYAN, "FRONTEND")
        
        # Check if node_modules exists
        if (self.frontend_dir / "node_modules").exists():
            self.log("✅ Frontend dependencies already installed", Colors.GREEN, "FRONTEND")
        else:
            self.log("📦 Installing frontend dependencies...", Colors.YELLOW, "FRONTEND")
            subprocess.run(
                ["npm", "install"],
                cwd=self.frontend_dir,
                check=True
            )
    
    def start_backend(self):
        """Start the FastAPI backend server"""
        self.log("🚀 Starting backend server...", Colors.BLUE, "BACKEND")
        
        cmd = [
            "uvicorn", "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        
        self.backend_process = subprocess.Popen(
            cmd,
            cwd=self.backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Start thread to handle backend output
        backend_thread = threading.Thread(
            target=self.handle_process_output,
            args=(self.backend_process, "BACKEND", Colors.BLUE),
            daemon=True
        )
        backend_thread.start()
    
    def start_frontend(self):
        """Start the React frontend server"""
        self.log("🚀 Starting frontend server...", Colors.CYAN, "FRONTEND")
        
        # Set environment variable to avoid browser auto-opening
        env = os.environ.copy()
        env["BROWSER"] = "none"
        
        self.frontend_process = subprocess.Popen(
            ["npm", "start"],
            cwd=self.frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env
        )
        
        # Start thread to handle frontend output
        frontend_thread = threading.Thread(
            target=self.handle_process_output,
            args=(self.frontend_process, "FRONTEND", Colors.CYAN),
            daemon=True
        )
        frontend_thread.start()
    
    def handle_process_output(self, process, name, color):
        """Handle output from a subprocess"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line and self.running:
                    # Clean up the line
                    clean_line = line.strip()
                    if clean_line and not clean_line.startswith('webpack compiled'):
                        self.log(clean_line, color, name)
        except Exception as e:
            if self.running:
                self.log(f"Output handler error: {e}", Colors.RED, name)
    
    def wait_for_servers(self):
        """Wait for both servers to be ready"""
        self.log("⏳ Waiting for servers to start...", Colors.YELLOW, "STARTUP")
        
        # Wait a bit for processes to start
        time.sleep(3)
        
        # Check backend health
        max_retries = 10
        for i in range(max_retries):
            try:
                result = subprocess.run(
                    ["curl", "-s", "http://localhost:8000/health"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    self.log("✅ Backend is ready!", Colors.GREEN, "BACKEND")
                    break
            except:
                pass
            
            if i < max_retries - 1:
                time.sleep(1)
        else:
            self.log("⚠️ Backend health check timeout", Colors.YELLOW, "BACKEND")
        
        # Frontend check (simpler - just see if port is listening)
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:3000"],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                self.log("✅ Frontend is ready!", Colors.GREEN, "FRONTEND")
        except:
            self.log("⚠️ Frontend connection timeout", Colors.YELLOW, "FRONTEND")
    
    def cleanup(self):
        """Clean up processes"""
        self.running = False
        self.log("🛑 Shutting down servers...", Colors.YELLOW, "CLEANUP")
        
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            self.log("✅ Backend stopped", Colors.GREEN, "CLEANUP")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
            self.log("✅ Frontend stopped", Colors.GREEN, "CLEANUP")
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print()  # New line after ^C
        self.cleanup()
        sys.exit(0)
    
    def run(self):
        """Main run method"""
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            self.log("🐺🐐🐷 Wolf Goat Pig Local Development Server", Colors.PURPLE, "START")
            self.log("=" * 60, Colors.WHITE, "")
            
            # Step 1: Kill existing processes
            self.kill_existing_processes()
            
            # Step 2: Setup dependencies
            self.setup_backend()
            self.setup_frontend()
            
            # Step 3: Start servers
            self.start_backend()
            time.sleep(2)  # Give backend a head start
            self.start_frontend()
            
            # Step 4: Wait for ready state
            self.wait_for_servers()
            
            # Step 5: Show access information
            self.log("=" * 60, Colors.WHITE, "")
            self.log("🌐 Frontend: http://localhost:3000", Colors.GREEN, "ACCESS")
            self.log("🔌 Backend API: http://localhost:8000", Colors.BLUE, "ACCESS")
            self.log("📚 API Docs: http://localhost:8000/docs", Colors.CYAN, "ACCESS")
            self.log("❤️ Health Check: http://localhost:8000/health", Colors.PURPLE, "ACCESS")
            self.log("=" * 60, Colors.WHITE, "")
            self.log("Press Ctrl+C to stop all servers", Colors.YELLOW, "INFO")
            
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
                
                # Check if processes are still running
                if self.backend_process and self.backend_process.poll() is not None:
                    self.log("💥 Backend process died!", Colors.RED, "ERROR")
                    break
                    
                if self.frontend_process and self.frontend_process.poll() is not None:
                    self.log("💥 Frontend process died!", Colors.RED, "ERROR")
                    break
                    
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            self.log(f"💥 Unexpected error: {e}", Colors.RED, "ERROR")
            self.cleanup()
            sys.exit(1)

def main():
    """Main entry point"""
    runner = LocalRunner()
    runner.run()

if __name__ == "__main__":
    main()