#!/usr/bin/env python3
"""
Render-specific startup script for Wolf-Goat-Pig backend.

This script handles initialization in a production environment where we want
the server to start even if non-critical initialization steps fail.
"""

import os
import sys
import logging
import subprocess
import time
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.info(f"📡 Received signal {sig_name}, initiating graceful shutdown...")
    shutdown_requested = True
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def wait_for_database(max_attempts=30, delay=2):
    """
    Wait for database to be ready with retry logic.

    Args:
        max_attempts: Maximum number of connection attempts
        delay: Delay in seconds between attempts

    Returns:
        bool: True if database is ready, False otherwise
    """
    logger.info("⏳ Waiting for database to be ready...")

    for attempt in range(1, max_attempts + 1):
        try:
            # Try to import and test database connection
            sys.path.insert(0, os.path.dirname(__file__))
            from app.database import SessionLocal
            from sqlalchemy import text

            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                db.commit()
                logger.info(f"✅ Database ready after {attempt} attempt(s)")
                return True
            finally:
                db.close()

        except Exception as e:
            if attempt < max_attempts:
                logger.warning(f"⏳ Database not ready (attempt {attempt}/{max_attempts}): {e}")
                time.sleep(delay)
            else:
                logger.error(f"❌ Database not ready after {max_attempts} attempts: {e}")
                return False

    return False


def run_initialization_steps():
    """
    Run initialization steps with fault tolerance.
    Non-critical failures are logged but don't prevent server startup.
    """
    logger.info("🐺 Wolf-Goat-Pig Render Startup")
    logger.info("=" * 50)

    # Wait for database to be ready with retry logic
    if not wait_for_database():
        logger.error("❌ Database connection failed, but continuing with startup...")
        # Continue anyway - app might still work with retry logic in endpoints

    # Step 1: Run database migrations
    logger.info("🔄 Running database migrations...")
    try:
        result = subprocess.run(
            [sys.executable, "run_migrations.py"],
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )

        if result.returncode == 0:
            logger.info("✅ Database migrations completed successfully")
            if result.stdout:
                logger.info(f"Migration output: {result.stdout}")
        else:
            logger.warning(f"⚠️ Database migrations completed with warnings")
            logger.warning(f"Output: {result.stdout}")
            if result.stderr:
                logger.warning(f"Errors: {result.stderr}")
            # Don't exit - continue with startup

    except subprocess.TimeoutExpired:
        logger.error("❌ Database migrations timed out after 60 seconds")
        logger.warning("🔄 Continuing with server startup anyway...")
    except Exception as e:
        logger.error(f"❌ Database migrations failed: {e}")
        logger.warning("🔄 Continuing with server startup anyway...")

    # Step 2: Initialize database and run seeding
    logger.info("🗄️ Running database initialization and seeding...")
    try:
        result = subprocess.run(
            [sys.executable, "startup.py", "--seed-only"],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode == 0:
            logger.info("✅ Database seeding completed successfully")
        else:
            logger.warning(f"⚠️ Database seeding completed with warnings")
            logger.warning(f"Output: {result.stdout}")
            if result.stderr:
                logger.warning(f"Errors: {result.stderr}")
            # Don't exit - continue with startup

    except subprocess.TimeoutExpired:
        logger.error("❌ Database seeding timed out after 120 seconds")
        logger.warning("🔄 Continuing with server startup anyway...")
    except Exception as e:
        logger.error(f"❌ Database seeding failed: {e}")
        logger.warning("🔄 Continuing with server startup anyway...")

    # Step 3: Run hole migration
    logger.info("🔄 Running hole data migration...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "app.migrations.add_holes_from_json"],
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )

        if result.returncode == 0:
            logger.info("✅ Hole migration completed successfully")
        else:
            logger.warning(f"⚠️ Hole migration completed with warnings")
            logger.warning(f"Output: {result.stdout}")
            if result.stderr:
                logger.warning(f"Errors: {result.stderr}")
            # Don't exit - continue with startup

    except subprocess.TimeoutExpired:
        logger.error("❌ Hole migration timed out after 60 seconds")
        logger.warning("🔄 Continuing with server startup anyway...")
    except Exception as e:
        logger.error(f"❌ Hole migration failed: {e}")
        logger.warning("🔄 Continuing with server startup anyway...")

    logger.info("✅ Initialization steps completed")


def start_server():
    """Start the uvicorn server with production-optimized settings."""
    port = os.getenv("PORT", "8000")

    logger.info(f"🚀 Starting uvicorn server on 0.0.0.0:{port}")

    # Set flag to skip FastAPI startup initialization since we've already done it
    os.environ["SKIP_FASTAPI_STARTUP_INIT"] = "true"

    try:
        # Use exec to replace this process with uvicorn
        # This ensures that uvicorn receives signals properly
        os.execvp(sys.executable, [
            sys.executable,
            "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", port,
            "--workers", "1",
            "--log-level", "info",
            "--timeout-keep-alive", "75",  # Keep connections alive longer
            "--timeout-graceful-shutdown", "30",  # Allow 30s for graceful shutdown
            "--limit-concurrency", "100",  # Limit concurrent connections
            "--backlog", "2048",  # Connection backlog
            "--no-access-log"  # Reduce logging overhead (Render already captures logs)
        ])
    except Exception as e:
        logger.error(f"❌ Failed to start uvicorn: {e}")
        sys.exit(1)


def main():
    """Main startup function."""
    try:
        # Run initialization steps
        run_initialization_steps()

        # Start the server (this replaces the current process)
        start_server()

    except KeyboardInterrupt:
        logger.info("👋 Startup interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Critical startup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
