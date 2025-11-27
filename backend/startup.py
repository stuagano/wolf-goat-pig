#!/usr/bin/env python3
"""
Wolf-Goat-Pig Application Startup Script

This script handles the complete startup sequence for the Wolf-Goat-Pig application,
including environment validation, database initialization, data seeding, and health checks.

Usage:
    python startup.py [options]
    
Options:
    --check-health          Only check application health
    --seed-only            Only run data seeding
    --force-seed           Force re-seeding even if data exists
    --verify-setup         Verify all systems without starting the server
    --environment ENV      Set environment (development, production, testing)
    --port PORT            Set port number for the server
    --host HOST            Set host address for the server
    --help                 Show this help message
"""

import sys
import os
import argparse
import logging
import asyncio
import time
from typing import Optional, Dict, Any, List

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the startup script."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)


class BootstrapManager:
    """
    Main bootstrap management class for the Wolf-Goat-Pig application.
    
    Handles the complete startup sequence including dependency checking,
    database initialization, data seeding, and health verification.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the BootstrapManager with configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.startup_results: Dict[str, Optional[Dict[str, Any]]] = {
            "environment": None,
            "dependencies": None,
            "database": None,
            "seeding": None,
            "health": None
        }
    
    def check_dependencies(self) -> Dict[str, Any]:
        """
        Check that all required Python packages are available.
        
        Returns:
            Dictionary with dependency check results
        """
        self.logger.info("📦 Checking dependencies...")
        dep_status = check_dependencies()
        
        self.startup_results["dependencies"] = dep_status
        
        if not dep_status["valid"]:
            self.logger.error("❌ Missing required dependencies:")
            for package in dep_status["missing"]:
                self.logger.error(f"  - {package}")
            self.logger.error("Please install missing packages with: pip install -r requirements.txt")
        else:
            self.logger.info("✅ All required dependencies available")
            for package, version in dep_status["versions"].items():
                self.logger.debug(f"  {package}: {version}")
        
        # Log optional missing packages as warnings
        if dep_status.get("optional_missing"):
            self.logger.warning("⚠️ Optional packages missing (may affect full functionality):")
            for package in dep_status["optional_missing"]:
                self.logger.warning(f"  - {package}")
        
        return dep_status
    
    async def initialize_database(self) -> Dict[str, Any]:
        """
        Set up database connections and initialize tables.
        
        Returns:
            Dictionary with database initialization results
        """
        self.logger.info("🗄️ Initializing database...")
        db_status = await initialize_database()
        
        self.startup_results["database"] = db_status
        
        if not db_status["initialized"]:
            self.logger.error(f"❌ Database initialization failed: {db_status.get('error', 'Unknown error')}")
        elif not db_status["connected"]:
            self.logger.error(f"❌ Database connection failed: {db_status.get('error', 'Unknown error')}")
        else:
            self.logger.info("✅ Database initialized and connected successfully")
        
        return db_status
    
    async def seed_data(self, force_reseed: bool = False) -> Dict[str, Any]:
        """
        Call seeding functions from app.seed_data safely.
        
        Args:
            force_reseed: If True, force re-seeding even if data exists
            
        Returns:
            Dictionary with seeding results
        """
        self.logger.info("🌱 Running data seeding...")
        seeding_results = await run_data_seeding(force_reseed=force_reseed)
        
        self.startup_results["seeding"] = seeding_results
        
        if seeding_results["status"] == "success":
            self.logger.info("✅ Data seeding completed successfully")
        elif seeding_results["status"] == "warning":
            self.logger.warning(f"⚠️ Data seeding completed with warnings: {seeding_results.get('message')}")
        else:
            self.logger.error(f"❌ Data seeding failed: {seeding_results.get('message')}")
        
        return seeding_results
    
    async def verify_health(self) -> Dict[str, Any]:
        """
        Check system health including database connectivity and seeded data.
        
        Returns:
            Dictionary with health check results
        """
        self.logger.info("🏥 Verifying application health...")
        health_status = await verify_application_health()
        
        self.startup_results["health"] = health_status
        
        if not health_status["healthy"]:
            self.logger.error("❌ Application health check failed")
            for component, status in health_status["components"].items():
                if "unhealthy" in str(status) or "error" in str(status):
                    self.logger.error(f"  {component}: {status}")
        else:
            self.logger.info("✅ All systems healthy")
            for component, status in health_status["components"].items():
                self.logger.info(f"  {component}: {status}")
        
        return health_status
    
    async def startup(self, skip_seeding: bool = False, force_reseed: bool = False) -> Dict[str, Any]:
        """
        Complete startup sequence with all bootstrap components.
        
        Args:
            skip_seeding: If True, skip the data seeding step
            force_reseed: If True, force re-seeding even if data exists
            
        Returns:
            Dictionary with complete startup results
        """
        self.logger.info("🐺 Starting Wolf-Goat-Pig application bootstrap sequence...")
        
        startup_success = True
        
        try:
            # 1. Validate environment
            self.logger.info("🔍 Validating environment...")
            env_status = validate_environment()
            self.startup_results["environment"] = env_status
            
            if not env_status["valid"]:
                self.logger.error("❌ Environment validation failed:")
                for error in env_status["errors"]:
                    self.logger.error(f"  - {error}")
                startup_success = False
                return self._build_startup_result(startup_success, "Environment validation failed")
            
            if env_status["warnings"]:
                for warning in env_status["warnings"]:
                    self.logger.warning(f"⚠️ {warning}")
            
            self.logger.info("✅ Environment validation passed")
            
            # 2. Check dependencies
            dep_status = self.check_dependencies()
            if not dep_status["valid"]:
                startup_success = False
                return self._build_startup_result(startup_success, "Dependency check failed")
            
            # 3. Initialize database
            db_status = await self.initialize_database()
            if not db_status["initialized"] or not db_status["connected"]:
                startup_success = False
                return self._build_startup_result(startup_success, "Database initialization failed")
            
            # 4. Seed data (optional)
            if not skip_seeding and os.getenv("SKIP_SEEDING", "false").lower() != "true":
                seeding_results = await self.seed_data(force_reseed=force_reseed)
                if seeding_results["status"] == "error":
                    self.logger.warning("🔄 Data seeding failed, but continuing with startup using fallback data")
            
            # 5. Verify health
            health_status = await self.verify_health()
            if not health_status["healthy"]:
                self.logger.warning("🔄 Health check failed, but continuing with startup")
            
            self.logger.info("✅ Bootstrap sequence completed successfully")
            return self._build_startup_result(startup_success, "Bootstrap completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Critical error during bootstrap: {e}")
            startup_success = False
            return self._build_startup_result(startup_success, f"Bootstrap failed: {str(e)}")
    
    def _build_startup_result(self, success: bool, message: str) -> Dict[str, Any]:
        """Build the final startup result dictionary."""
        return {
            "success": success,
            "message": message,
            "timestamp": time.time(),
            "results": self.startup_results.copy()
        }


def validate_environment() -> Dict[str, Any]:
    """Validate and set up environment variables."""
    env_status: Dict[str, Any] = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "config": {}
    }

    # Get environment
    environment = os.getenv("ENVIRONMENT", "development")
    env_status["config"]["environment"] = environment

    # Validate required environment variables
    required_vars: List[str] = []
    optional_vars: Dict[str, Optional[str]] = {
        "DATABASE_URL": None,
        "SKIP_SEEDING": "false",
        "LOG_LEVEL": "INFO",
        "PORT": "8000",
        "HOST": "0.0.0.0"
    }
    
    # Check required variables
    for var in required_vars:
        if not os.getenv(var):
            env_status["errors"].append(f"Required environment variable '{var}' is not set")
            env_status["valid"] = False
    
    # Set optional variables with defaults
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        if value != default and default is not None:
            env_status["config"][var.lower()] = value
        elif default is not None:
            env_status["config"][var.lower()] = default
            if var not in os.environ:
                os.environ[var] = default
    
    # Environment-specific validation
    if environment == "production":
        if not os.getenv("DATABASE_URL"):
            env_status["warnings"].append("Production environment without DATABASE_URL - using SQLite")

        # Security checks for production
        security_warnings: List[str] = []
        if os.getenv("DEBUG", "false").lower() == "true":
            security_warnings.append("DEBUG should not be enabled in production")

        for warning in security_warnings:
            env_status["warnings"].append(f"Security: {warning}")

    return env_status


def check_dependencies() -> Dict[str, Any]:
    """Check that all required dependencies are available."""
    dep_status: Dict[str, Any] = {
        "valid": True,
        "missing": [],
        "versions": {},
        "optional_missing": []
    }

    # Core required packages for basic functionality
    required_packages: List[str] = [
        "sqlalchemy",
        "pydantic"
    ]

    # Optional packages that are needed for full functionality
    optional_packages: List[str] = [
        "fastapi",
        "uvicorn",
        "httpx"
    ]

    # Check required packages
    for package in required_packages:
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "unknown")
            dep_status["versions"][package] = version
        except ImportError:
            dep_status["missing"].append(package)
            dep_status["valid"] = False

    # Check optional packages (won't fail bootstrap if missing)
    for package in optional_packages:
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "unknown")
            dep_status["versions"][package] = version
        except ImportError:
            dep_status["optional_missing"].append(package)
            # Don't mark as invalid for optional packages

    return dep_status


async def run_migrations() -> Dict[str, Any]:
    """Run database migrations to ensure schema is up-to-date."""
    migration_result: Dict[str, Any] = {
        "success": False,
        "message": "",
        "migrations_applied": []
    }

    try:
        import os
        from app.database import SessionLocal, engine
        from sqlalchemy import text, inspect
        from sqlalchemy.engine import Inspector

        database_url = os.getenv('DATABASE_URL', '')
        is_postgresql = 'postgresql://' in database_url or 'postgres://' in database_url

        db = SessionLocal()
        try:
            # Check if game_state table exists
            inspector: Inspector = inspect(engine)
            tables: List[str] = inspector.get_table_names()
            if 'game_state' not in tables:
                migration_result["success"] = True
                migration_result["message"] = "game_state table does not exist yet, will be created by init_db"
                return migration_result

            # Get existing columns
            from typing import cast
            columns_info = cast(List[Dict[str, Any]], inspector.get_columns('game_state'))
            columns: List[str] = [col['name'] for col in columns_info]
            logging.debug(f"Existing game_state columns: {columns}")

            migrations_applied: List[str] = []

            # Migration 1: Add game_id column if missing
            if 'game_id' not in columns:
                logging.info("  Adding game_id column to game_state...")
                if is_postgresql:
                    db.execute(text("ALTER TABLE game_state ADD COLUMN game_id VARCHAR"))
                    db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_game_id ON game_state(game_id)"))
                    db.execute(text("UPDATE game_state SET game_id = 'legacy-game-' || CAST(id AS VARCHAR) WHERE game_id IS NULL"))
                else:
                    db.execute(text("ALTER TABLE game_state ADD COLUMN game_id VARCHAR"))
                    db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_game_id ON game_state(game_id)"))
                    db.execute(text("UPDATE game_state SET game_id = 'legacy-game-' || CAST(id AS VARCHAR) WHERE game_id IS NULL"))
                migrations_applied.append("game_id column")
                logging.info("  ✅ Added game_id column")

            # Migration 2: Add created_at column if missing
            if 'created_at' not in columns:
                logging.info("  Adding created_at column to game_state...")
                if is_postgresql:
                    db.execute(text("ALTER TABLE game_state ADD COLUMN created_at VARCHAR"))
                    db.execute(text("UPDATE game_state SET created_at = NOW()::text WHERE created_at IS NULL"))
                else:
                    db.execute(text("ALTER TABLE game_state ADD COLUMN created_at VARCHAR"))
                    db.execute(text("UPDATE game_state SET created_at = datetime('now') WHERE created_at IS NULL"))
                migrations_applied.append("created_at column")
                logging.info("  ✅ Added created_at column")

            # Migration 3: Add updated_at column if missing
            if 'updated_at' not in columns:
                logging.info("  Adding updated_at column to game_state...")
                if is_postgresql:
                    db.execute(text("ALTER TABLE game_state ADD COLUMN updated_at VARCHAR"))
                    db.execute(text("UPDATE game_state SET updated_at = NOW()::text WHERE updated_at IS NULL"))
                else:
                    db.execute(text("ALTER TABLE game_state ADD COLUMN updated_at VARCHAR"))
                    db.execute(text("UPDATE game_state SET updated_at = datetime('now') WHERE updated_at IS NULL"))
                migrations_applied.append("updated_at column")
                logging.info("  ✅ Added updated_at column")

            # Migration 4: Add join_code column if missing
            if 'join_code' not in columns:
                logging.info("  Adding join_code column to game_state...")
                if is_postgresql:
                    db.execute(text("ALTER TABLE game_state ADD COLUMN join_code VARCHAR"))
                    db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_join_code ON game_state(join_code)"))
                else:
                    db.execute(text("ALTER TABLE game_state ADD COLUMN join_code VARCHAR"))
                    db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_game_state_join_code ON game_state(join_code)"))
                migrations_applied.append("join_code column")
                logging.info("  ✅ Added join_code column")

            # Migration 5: Add creator_user_id column if missing
            if 'creator_user_id' not in columns:
                logging.info("  Adding creator_user_id column to game_state...")
                db.execute(text("ALTER TABLE game_state ADD COLUMN creator_user_id VARCHAR"))
                migrations_applied.append("creator_user_id column")
                logging.info("  ✅ Added creator_user_id column")

            # Migration 6: Add game_status column if missing
            if 'game_status' not in columns:
                logging.info("  Adding game_status column to game_state...")
                if is_postgresql:
                    db.execute(text("ALTER TABLE game_state ADD COLUMN game_status VARCHAR DEFAULT 'setup'"))
                    db.execute(text("UPDATE game_state SET game_status = 'setup' WHERE game_status IS NULL"))
                else:
                    db.execute(text("ALTER TABLE game_state ADD COLUMN game_status VARCHAR DEFAULT 'setup'"))
                    db.execute(text("UPDATE game_state SET game_status = 'setup' WHERE game_status IS NULL"))
                migrations_applied.append("game_status column")
                logging.info("  ✅ Added game_status column")

            # Migration 7: Add tee_order column to game_players if missing
            if 'game_players' in tables:
                player_columns_info = cast(List[Dict[str, Any]], inspector.get_columns('game_players'))
                player_columns: List[str] = [col['name'] for col in player_columns_info]
                if 'tee_order' not in player_columns:
                    logging.info("  Adding tee_order column to game_players...")
                    if is_postgresql:
                        db.execute(text("ALTER TABLE game_players ADD COLUMN tee_order INTEGER"))
                        db.execute(text("CREATE INDEX IF NOT EXISTS idx_game_players_tee_order ON game_players(game_id, tee_order)"))
                    else:
                        db.execute(text("ALTER TABLE game_players ADD COLUMN tee_order INTEGER"))
                        db.execute(text("CREATE INDEX IF NOT EXISTS idx_game_players_tee_order ON game_players(game_id, tee_order)"))
                    migrations_applied.append("tee_order column to game_players")
                    logging.info("  ✅ Added tee_order column to game_players")

            # Migration 8: Add special event stats to player_statistics
            if 'player_statistics' in tables:
                stats_columns_info = cast(List[Dict[str, Any]], inspector.get_columns('player_statistics'))
                stats_columns: List[str] = [col['name'] for col in stats_columns_info]

                # Ping pong tracking
                if 'ping_pong_count' not in stats_columns:
                    logging.info("  Adding special event stats columns to player_statistics...")
                    db.execute(text("ALTER TABLE player_statistics ADD COLUMN ping_pong_count INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE player_statistics ADD COLUMN ping_pong_wins INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE player_statistics ADD COLUMN invisible_aardvark_appearances INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE player_statistics ADD COLUMN invisible_aardvark_wins INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE player_statistics ADD COLUMN duncan_attempts INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE player_statistics ADD COLUMN duncan_wins INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE player_statistics ADD COLUMN tunkarri_attempts INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE player_statistics ADD COLUMN tunkarri_wins INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE player_statistics ADD COLUMN big_dick_attempts INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE player_statistics ADD COLUMN big_dick_wins INTEGER DEFAULT 0"))
                    migrations_applied.append("special event stats columns to player_statistics")
                    logging.info("  ✅ Added special event stats columns to player_statistics")

            # Migration 9: Add special event stats to game_player_results
            if 'game_player_results' in tables:
                results_columns_info = cast(List[Dict[str, Any]], inspector.get_columns('game_player_results'))
                results_columns: List[str] = [col['name'] for col in results_columns_info]

                if 'ping_pongs' not in results_columns:
                    logging.info("  Adding special event stats columns to game_player_results...")
                    db.execute(text("ALTER TABLE game_player_results ADD COLUMN ping_pongs INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE game_player_results ADD COLUMN ping_pongs_won INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE game_player_results ADD COLUMN invisible_aardvark_holes INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE game_player_results ADD COLUMN invisible_aardvark_holes_won INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE game_player_results ADD COLUMN duncan_attempts INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE game_player_results ADD COLUMN duncan_wins INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE game_player_results ADD COLUMN tunkarri_attempts INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE game_player_results ADD COLUMN tunkarri_wins INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE game_player_results ADD COLUMN big_dick_attempts INTEGER DEFAULT 0"))
                    db.execute(text("ALTER TABLE game_player_results ADD COLUMN big_dick_wins INTEGER DEFAULT 0"))
                    migrations_applied.append("special event stats columns to game_player_results")
                    logging.info("  ✅ Added special event stats columns to game_player_results")

            db.commit()

            if migrations_applied:
                migration_result["success"] = True
                migration_result["message"] = f"Applied {len(migrations_applied)} migration(s): {', '.join(migrations_applied)}"
                migration_result["migrations_applied"] = migrations_applied
            else:
                migration_result["success"] = True
                migration_result["message"] = "No migrations needed - schema is up-to-date"

        except Exception as e:
            db.rollback()
            migration_result["message"] = f"Migration failed: {str(e)}"
            logging.error(f"  ❌ Migration error: {e}")
            raise
        finally:
            db.close()

    except Exception as e:
        migration_result["message"] = f"Migration setup failed: {str(e)}"
        logging.error(f"  ❌ Migration setup error: {e}")

    return migration_result


async def initialize_database() -> Dict[str, Any]:
    """Initialize the database and verify connection."""
    db_status: Dict[str, Any] = {
        "initialized": False,
        "connected": False,
        "migrated": False,
        "error": None
    }

    try:
        from app.database import init_db, SessionLocal
        from sqlalchemy import text

        # Initialize database tables
        init_db()
        db_status["initialized"] = True
        logging.info("✅ Database tables initialized")

        # Test connection
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db.commit()
            db_status["connected"] = True
            logging.info("✅ Database connection verified")
        except Exception as e:
            db_status["error"] = f"Connection test failed: {str(e)}"
            logging.error(f"❌ Database connection test failed: {e}")
        finally:
            db.close()

        # Run migrations to ensure schema is up-to-date
        if db_status["connected"]:
            try:
                logging.info("🔄 Applying database migrations...")
                migration_result = await run_migrations()
                db_status["migrated"] = migration_result["success"]
                if migration_result["success"]:
                    logging.info("✅ Database migrations completed")
                else:
                    logging.warning(f"⚠️ Database migrations completed with warnings: {migration_result.get('message', '')}")
            except Exception as e:
                logging.warning(f"⚠️ Database migrations failed (continuing anyway): {e}")
                db_status["migrated"] = False

    except Exception as e:
        db_status["error"] = str(e)
        logging.error(f"❌ Database initialization failed: {e}")

    return db_status


async def run_data_seeding(force_reseed: bool = False) -> Dict[str, Any]:
    """Run the data seeding process."""
    logging.info("🌱 Starting data seeding process...")
    
    try:
        from app.seed_data import seed_all_data
        
        results = seed_all_data(force_reseed=force_reseed)
        
        if results["status"] == "success":
            logging.info("✅ Data seeding completed successfully")
            
            # Log summary
            if "results" in results:
                for component, result in results["results"].items():
                    added = result.get("added", 0)
                    if added > 0:
                        logging.info(f"  📊 {component}: {added} items added")
                        
        elif results["status"] == "warning":
            logging.warning(f"⚠️ Data seeding completed with warnings: {results.get('message')}")
            
        else:
            logging.error(f"❌ Data seeding failed: {results.get('message')}")
        
        return results
        
    except Exception as e:
        logging.error(f"❌ Critical error during data seeding: {e}")
        return {
            "status": "error",
            "message": f"Seeding process failed: {str(e)}"
        }


async def verify_application_health() -> Dict[str, Any]:
    """Verify that all application systems are healthy."""
    health_status: Dict[str, Any] = {
        "healthy": True,
        "components": {},
        "warnings": []
    }
    
    try:
        # Import after environment is set up
        from app.database import SessionLocal
        from app.game_state import game_state
        from app.wolf_goat_pig_simulation import WolfGoatPigGame
        from app.seed_data import get_seeding_status
        from sqlalchemy import text
        
        # 1. Database health
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            health_status["components"]["database"] = "healthy"
            logging.info("✅ Database health check passed")
        except Exception as e:
            health_status["components"]["database"] = f"unhealthy: {str(e)}"
            health_status["healthy"] = False
            logging.error(f"❌ Database health check failed: {e}")
        
        # 2. Course availability
        try:
            courses = game_state.get_courses()
            if courses and len(courses) > 0:
                health_status["components"]["courses"] = f"healthy ({len(courses)} courses)"
                logging.info(f"✅ Course health check passed - {len(courses)} courses available")
            else:
                health_status["components"]["courses"] = "warning: no courses available"
                health_status["warnings"].append("No courses available")
                logging.warning("⚠️ No courses available")
        except Exception as e:
            health_status["components"]["courses"] = f"unhealthy: {str(e)}"
            health_status["healthy"] = False
            logging.error(f"❌ Course health check failed: {e}")
        
        # 3. Simulation engine
        try:
            test_sim = WolfGoatPigGame(player_count=4)
            health_status["components"]["simulation"] = "healthy"
            logging.info("✅ Simulation engine health check passed")
        except Exception as e:
            health_status["components"]["simulation"] = f"unhealthy: {str(e)}"
            health_status["healthy"] = False
            logging.error(f"❌ Simulation engine health check failed: {e}")
        
        # 4. Data seeding status
        try:
            seeding_status = get_seeding_status()
            if seeding_status["status"] == "success":
                health_status["components"]["data_seeding"] = "healthy"
                logging.info("✅ Data seeding health check passed")
            else:
                health_status["components"]["data_seeding"] = f"warning: {seeding_status.get('message', 'unknown')}"
                health_status["warnings"].append("Data seeding incomplete")
                logging.warning("⚠️ Data seeding health check showed warnings")
        except Exception as e:
            health_status["components"]["data_seeding"] = f"error: {str(e)}"
            health_status["warnings"].append("Data seeding status unavailable")
            logging.warning(f"⚠️ Data seeding health check failed: {e}")
        
        # Overall health assessment
        unhealthy_components = [k for k, v in health_status["components"].items() if "unhealthy" in str(v)]
        if unhealthy_components:
            health_status["healthy"] = False
            logging.error(f"❌ Application health check failed - unhealthy components: {', '.join(unhealthy_components)}")
        elif health_status["warnings"]:
            logging.warning(f"⚠️ Application health check passed with warnings: {len(health_status['warnings'])} warnings")
        else:
            logging.info("✅ Application health check passed - all systems healthy")
            
    except Exception as e:
        health_status["healthy"] = False
        health_status["components"]["system"] = f"critical error: {str(e)}"
        logging.error(f"❌ Critical error during health check: {e}")
    
    return health_status


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False) -> None:
    """Start the FastAPI server using uvicorn."""
    try:
        import uvicorn
        
        logging.info(f"🚀 Starting Wolf-Goat-Pig server on {host}:{port}")
        
        # Configure uvicorn
        config = uvicorn.Config(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info" if os.getenv("LOG_LEVEL", "INFO").upper() == "INFO" else "debug",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        server.run()
        
    except ImportError:
        logging.error("❌ uvicorn not available - cannot start server")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ Failed to start server: {e}")
        sys.exit(1)


def seed_data(force_reseed: bool = False) -> Dict[str, Any]:
    """
    Data seeding function that calls the seeding functions from app.seed_data.
    
    This function provides a synchronous interface to the seeding process
    and handles errors gracefully for bootstrap testing scenarios.
    
    Args:
        force_reseed: If True, force re-seeding even if data exists
        
    Returns:
        Dictionary with seeding results and status
    """
    logger = logging.getLogger(__name__)
    logger.info("🌱 Starting data seeding process...")
    
    try:
        # Import and call the main seeding function from app.seed_data
        from app.seed_data import seed_all_data
        
        results = seed_all_data(force_reseed=force_reseed)
        
        if results["status"] == "success":
            logger.info("✅ Data seeding completed successfully")
            
            # Log summary if available
            if "results" in results:
                total_added = 0
                for component, result in results["results"].items():
                    added = result.get("added", 0)
                    if isinstance(added, int):
                        total_added += added
                    if added > 0:
                        logger.info(f"  📊 {component}: {added} items added")
                
                logger.info(f"  📈 Total items added: {total_added}")
                        
        elif results["status"] == "warning":
            logger.warning(f"⚠️ Data seeding completed with warnings: {results.get('message')}")
            
        else:
            logger.error(f"❌ Data seeding failed: {results.get('message')}")
        
        return results
        
    except ImportError as e:
        error_msg = f"Failed to import seeding functions: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "timestamp": time.time()
        }
        
    except Exception as e:
        error_msg = f"Critical error during data seeding: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {
            "status": "error",
            "message": error_msg,
            "timestamp": time.time()
        }


def verify_health() -> Dict[str, Any]:
    """
    Health verification function that checks system health synchronously.

    This function provides a synchronous interface to health checking
    for bootstrap testing scenarios where async is not available.

    Returns:
        Dictionary with health status and component details
    """
    logger = logging.getLogger(__name__)
    logger.info("🏥 Checking application health...")

    health_status: Dict[str, Any] = {
        "healthy": True,
        "components": {},
        "warnings": [],
        "timestamp": time.time()
    }
    
    try:
        # Check if we can import required modules (dependency check)
        try:
            from app.database import SessionLocal
            from app.game_state import game_state
            from app.wolf_goat_pig import WolfGoatPigGame
            from app.seed_data import get_seeding_status
            from sqlalchemy import text
            
            health_status["components"]["imports"] = "healthy"
            logger.info("✅ Required modules import successfully")
        except ImportError as e:
            health_status["components"]["imports"] = f"unhealthy: {str(e)}"
            health_status["healthy"] = False
            logger.error(f"❌ Module import failed: {e}")
            return health_status
        
        # 1. Database health check
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            health_status["components"]["database"] = "healthy"
            logger.info("✅ Database connectivity verified")
        except Exception as e:
            health_status["components"]["database"] = f"unhealthy: {str(e)}"
            health_status["healthy"] = False
            logger.error(f"❌ Database health check failed: {e}")
        
        # 2. Course availability check
        try:
            courses = game_state.get_courses()
            if courses and len(courses) > 0:
                health_status["components"]["courses"] = f"healthy ({len(courses)} courses)"
                logger.info(f"✅ Course availability verified - {len(courses)} courses")
            else:
                health_status["components"]["courses"] = "warning: no courses available"
                health_status["warnings"].append("No courses available")
                logger.warning("⚠️ No courses found")
        except Exception as e:
            health_status["components"]["courses"] = f"error: {str(e)}"
            health_status["warnings"].append("Course availability check failed")
            logger.warning(f"⚠️ Course availability check failed: {e}")
        
        # 3. Simulation engine check
        try:
            test_sim = WolfGoatPigGame(player_count=4)
            health_status["components"]["simulation"] = "healthy"
            logger.info("✅ Simulation engine verified")
        except Exception as e:
            health_status["components"]["simulation"] = f"error: {str(e)}"
            health_status["warnings"].append("Simulation engine check failed")
            logger.warning(f"⚠️ Simulation engine check failed: {e}")
        
        # 4. Data seeding status check
        try:
            seeding_status = get_seeding_status()
            if seeding_status["status"] == "success":
                health_status["components"]["data_seeding"] = "healthy"
                logger.info("✅ Data seeding status verified")
            else:
                health_status["components"]["data_seeding"] = f"warning: {seeding_status.get('message', 'unknown')}"
                health_status["warnings"].append("Data seeding incomplete or failed")
                logger.warning("⚠️ Data seeding status check showed issues")
        except Exception as e:
            health_status["components"]["data_seeding"] = f"error: {str(e)}"
            health_status["warnings"].append("Data seeding status unavailable")
            logger.warning(f"⚠️ Data seeding status check failed: {e}")
        
        # Overall health assessment
        unhealthy_components = [
            k for k, v in health_status["components"].items() 
            if "unhealthy" in str(v)
        ]
        
        if unhealthy_components:
            health_status["healthy"] = False
            logger.error(f"❌ Health check failed - unhealthy components: {', '.join(unhealthy_components)}")
        elif health_status["warnings"]:
            logger.warning(f"⚠️ Health check passed with {len(health_status['warnings'])} warnings")
        else:
            logger.info("✅ All systems healthy")
            
    except Exception as e:
        health_status["healthy"] = False
        health_status["components"]["system"] = f"critical error: {str(e)}"
        logger.error(f"❌ Critical error during health check: {e}")
    
    return health_status


async def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(description="Wolf-Goat-Pig Application Startup")
    parser.add_argument("--check-health", action="store_true", help="Only check application health")
    parser.add_argument("--seed-only", action="store_true", help="Only run data seeding")
    parser.add_argument("--force-seed", action="store_true", help="Force re-seeding even if data exists")
    parser.add_argument("--verify-setup", action="store_true", help="Verify all systems without starting server")
    parser.add_argument("--environment", help="Set environment (development, production, testing)")
    parser.add_argument("--port", type=int, default=8000, help="Set port number for the server")
    parser.add_argument("--host", default="0.0.0.0", help="Set host address for the server")
    parser.add_argument("--log-level", default="INFO", help="Set logging level")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload in development")
    parser.add_argument("--bootstrap-test", action="store_true", help="Run bootstrap components test")
    parser.add_argument("--use-bootstrap-manager", action="store_true", help="Use BootstrapManager for startup")
    
    args = parser.parse_args()
    
    # Set environment if provided
    if args.environment:
        os.environ["ENVIRONMENT"] = args.environment
    
    # Setup logging
    setup_logging(args.log_level)
    
    logging.info("🐺 Wolf-Goat-Pig Application Startup")
    logging.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Handle bootstrap test mode
    if args.bootstrap_test:
        logging.info("🧪 Running bootstrap components test...")

        # Test each component independently
        test_results: Dict[str, str] = {}
        
        # Test 1: BootstrapManager class availability
        try:
            manager = BootstrapManager()
            test_results["bootstrap_manager"] = "✅ Available"
            logging.info("✅ BootstrapManager class: Available")
        except Exception as e:
            test_results["bootstrap_manager"] = f"❌ Failed: {e}"
            logging.error(f"❌ BootstrapManager class: Failed - {e}")
        
        # Test 2: seed_data function availability
        try:
            # Test that the function exists and can be called
            result = seed_data(force_reseed=False)
            if result["status"] in ["success", "warning"]:
                test_results["seed_data"] = "✅ Available and functional"
                logging.info("✅ seed_data function: Available and functional")
            else:
                test_results["seed_data"] = f"⚠️ Available but returned error: {result.get('message')}"
                logging.warning(f"⚠️ seed_data function: Available but returned error - {result.get('message')}")
        except Exception as e:
            test_results["seed_data"] = f"❌ Failed: {e}"
            logging.error(f"❌ seed_data function: Failed - {e}")
        
        # Test 3: verify_health function availability
        try:
            # Test that the function exists and can be called
            result = verify_health()
            if result["healthy"] or result["warnings"]:
                test_results["verify_health"] = "✅ Available and functional"
                logging.info("✅ verify_health function: Available and functional")
            else:
                test_results["verify_health"] = "⚠️ Available but reported unhealthy system"
                logging.warning("⚠️ verify_health function: Available but reported unhealthy system")
        except Exception as e:
            test_results["verify_health"] = f"❌ Failed: {e}"
            logging.error(f"❌ verify_health function: Failed - {e}")
        
        # Summary
        logging.info("🧪 Bootstrap components test results:")
        all_passed: bool = True
        for component, test_result in test_results.items():
            logging.info(f"  {component}: {test_result}")
            if "❌" in test_result:
                all_passed = False
        
        if all_passed:
            logging.info("✅ All bootstrap components test passed!")
            sys.exit(0)
        else:
            logging.error("❌ Some bootstrap components tests failed!")
            sys.exit(1)
    
    # Handle BootstrapManager mode
    if args.use_bootstrap_manager:
        logging.info("🏗️ Using BootstrapManager for startup sequence...")
        
        try:
            manager = BootstrapManager()
            result = await manager.startup(
                skip_seeding=args.verify_setup or os.getenv("SKIP_SEEDING", "false").lower() == "true",
                force_reseed=args.force_seed
            )
            
            if result["success"]:
                logging.info("✅ BootstrapManager startup completed successfully")
                
                # Exit early for verification modes
                if args.check_health or args.verify_setup or args.seed_only:
                    sys.exit(0)
                
                # Continue to server startup for normal operation
                logging.info("🎯 Continuing to server startup...")
            else:
                logging.error(f"❌ BootstrapManager startup failed: {result['message']}")
                sys.exit(1)
                
        except Exception as e:
            logging.error(f"❌ BootstrapManager startup failed with exception: {e}")
            sys.exit(1)
    
    # 1. Validate environment
    logging.info("🔍 Validating environment...")
    env_status = validate_environment()
    
    if not env_status["valid"]:
        logging.error("❌ Environment validation failed:")
        for error in env_status["errors"]:
            logging.error(f"  - {error}")
        sys.exit(1)
    
    if env_status["warnings"]:
        for warning in env_status["warnings"]:
            logging.warning(f"⚠️ {warning}")
    
    logging.info("✅ Environment validation passed")
    
    # 2. Check dependencies
    logging.info("📦 Checking dependencies...")
    dep_status = check_dependencies()
    
    if not dep_status["valid"]:
        logging.error("❌ Missing required dependencies:")
        for package in dep_status["missing"]:
            logging.error(f"  - {package}")
        logging.error("Please install missing packages with: pip install -r requirements.txt")
        sys.exit(1)
    
    logging.info("✅ All required dependencies available")
    for package, version in dep_status["versions"].items():
        logging.debug(f"  {package}: {version}")
    
    # Log optional missing packages as warnings
    if dep_status.get("optional_missing"):
        logging.warning("⚠️ Optional packages missing (may affect full functionality):")
        for package in dep_status["optional_missing"]:
            logging.warning(f"  - {package}")
        logging.warning("Note: Server startup may not be available without uvicorn and fastapi")
    
    # 3. Initialize database
    if not args.check_health:
        logging.info("🗄️ Initializing database...")
        db_status = await initialize_database()
        
        if not db_status["initialized"]:
            logging.error(f"❌ Database initialization failed: {db_status.get('error', 'Unknown error')}")
            sys.exit(1)
        
        if not db_status["connected"]:
            logging.error(f"❌ Database connection failed: {db_status.get('error', 'Unknown error')}")
            sys.exit(1)
    
    # 4. Data seeding
    if args.seed_only or (not args.check_health and not args.verify_setup):
        if os.getenv("SKIP_SEEDING", "false").lower() != "true":
            seeding_results = await run_data_seeding(force_reseed=args.force_seed)
            
            if seeding_results["status"] == "error":
                logging.error("❌ Critical data seeding failure")
                if not args.seed_only:
                    logging.warning("🔄 Continuing with server startup using fallback data")
                else:
                    sys.exit(1)
        else:
            logging.info("⏭️ Data seeding skipped (SKIP_SEEDING=true)")
    
    # 5. Health verification
    if args.check_health or args.verify_setup or not args.seed_only:
        logging.info("🏥 Verifying application health...")
        health_status = await verify_application_health()
        
        if not health_status["healthy"]:
            logging.error("❌ Application health check failed")
            for component, status in health_status["components"].items():
                if "unhealthy" in str(status) or "error" in str(status):
                    logging.error(f"  {component}: {status}")
            
            if args.check_health or args.verify_setup:
                sys.exit(1)
            else:
                logging.warning("🔄 Continuing with server startup despite health check failures")
        else:
            logging.info("✅ All systems healthy")
            for component, status in health_status["components"].items():
                logging.info(f"  {component}: {status}")
    
    # 6. Exit early if only checking or verifying
    if args.check_health:
        logging.info("🏁 Health check complete")
        sys.exit(0 if health_status["healthy"] else 1)
    
    if args.seed_only:
        logging.info("🏁 Data seeding complete")
        sys.exit(0)
    
    if args.verify_setup:
        logging.info("🏁 Setup verification complete")
        sys.exit(0 if health_status["healthy"] else 1)
    
    # 7. Start the server
    environment = os.getenv("ENVIRONMENT", "development")
    reload = environment == "development" and not args.no_reload
    
    logging.info("🎯 All systems ready - starting server...")
    start_server(host=args.host, port=args.port, reload=reload)


def run_bootstrap_test() -> bool:
    """
    Standalone function to test bootstrap components.
    This can be called directly for testing purposes.
    """
    setup_logging("INFO")

    logging.info("🧪 Running standalone bootstrap components test...")

    # Test results
    test_results: Dict[str, bool] = {
        "bootstrap_manager": False,
        "seed_data": False,
        "verify_health": False
    }
    
    # Test 1: BootstrapManager class
    try:
        manager = BootstrapManager()
        test_results["bootstrap_manager"] = True
        logging.info("✅ BootstrapManager class: Available")
    except Exception as e:
        logging.error(f"❌ BootstrapManager class: Failed - {e}")
    
    # Test 2: seed_data function
    try:
        result = seed_data(force_reseed=False)
        if result and "status" in result:
            test_results["seed_data"] = True
            logging.info("✅ seed_data function: Available and functional")
        else:
            logging.error("❌ seed_data function: Available but returned invalid result")
    except Exception as e:
        logging.error(f"❌ seed_data function: Failed - {e}")
    
    # Test 3: verify_health function  
    try:
        result = verify_health()
        if result and "healthy" in result:
            test_results["verify_health"] = True
            logging.info("✅ verify_health function: Available and functional")
        else:
            logging.error("❌ verify_health function: Available but returned invalid result")
    except Exception as e:
        logging.error(f"❌ verify_health function: Failed - {e}")
    
    # Summary
    all_passed = all(test_results.values())
    passed_count = sum(test_results.values())
    total_count = len(test_results)
    
    logging.info(f"🧪 Bootstrap test results: {passed_count}/{total_count} components passed")
    
    if all_passed:
        logging.info("✅ All bootstrap components are available and functional!")
        return True
    else:
        logging.error("❌ Some bootstrap components are missing or non-functional!")
        for component, passed in test_results.items():
            if not passed:
                logging.error(f"  ❌ {component}: FAILED")
        return False


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("👋 Startup interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"❌ Critical startup error: {e}")
        sys.exit(1)