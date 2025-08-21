#!/usr/bin/env python3
"""
Wolf Goat Pig Simulation Startup Script
Simple script to get the simulation running with minimal setup
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_and_install_requirements():
    """Check if required packages are installed, install if missing"""
    logger = logging.getLogger(__name__)
    
    # Core requirements for basic functionality
    required_packages = [
        'fastapi>=0.110.0',
        'uvicorn[standard]>=0.29.0',
        'sqlalchemy>=2.0.30',
        'pydantic>=2.6.0',
        'python-multipart>=0.0.9'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        package_name = package.split('>=')[0].split('[')[0]
        try:
            __import__(package_name)
            logger.info(f"✅ {package_name} is available")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"❌ {package_name} is missing")
    
    if missing_packages:
        logger.info("📦 Installing missing packages...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--user"
            ] + missing_packages)
            logger.info("✅ Packages installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install packages: {e}")
            return False
    
    return True

def setup_environment():
    """Setup environment variables"""
    logger = logging.getLogger(__name__)
    
    # Set development environment
    os.environ["ENVIRONMENT"] = "development"
    
    # Set database URL to SQLite for simplicity
    db_path = Path(__file__).parent / "reports" / "wolf_goat_pig.db"
    db_path.parent.mkdir(exist_ok=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    
    logger.info(f"📁 Database path: {db_path}")
    logger.info("🔧 Environment configured for development")
    
    return True

def test_basic_imports():
    """Test if we can import the simulation without errors"""
    logger = logging.getLogger(__name__)
    
    try:
        # Add backend to path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        logger.info("🔍 Testing basic imports...")
        
        # Test core imports
        import app.database
        logger.info("✅ Database module imported")
        
        import app.wolf_goat_pig_simulation
        logger.info("✅ Simulation module imported")
        
        # Test creating simulation object
        from app.wolf_goat_pig_simulation import WolfGoatPigSimulation
        sim = WolfGoatPigSimulation(player_count=4)
        logger.info("✅ Simulation object created")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        return False

def start_backend_server():
    """Start the FastAPI backend server"""
    logger = logging.getLogger(__name__)
    
    try:
        import uvicorn
        
        # Add backend to path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        logger.info("🚀 Starting backend server...")
        logger.info("📍 Backend API: http://localhost:8000")
        logger.info("📖 API Docs: http://localhost:8000/docs")
        
        # Run the server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError:
        logger.error("❌ uvicorn not available")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        return False

def main():
    """Main startup process"""
    logger = setup_logging()
    
    logger.info("🐺 Wolf Goat Pig Simulation Startup")
    logger.info("=" * 50)
    
    # Step 1: Check and install requirements
    if not check_and_install_requirements():
        logger.error("❌ Failed to install requirements")
        return 1
    
    # Step 2: Setup environment
    if not setup_environment():
        logger.error("❌ Failed to setup environment")
        return 1
    
    # Step 3: Test imports
    if not test_basic_imports():
        logger.error("❌ Import tests failed")
        return 1
    
    # Step 4: Start server
    logger.info("✅ All checks passed - starting server...")
    try:
        start_backend_server()
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())