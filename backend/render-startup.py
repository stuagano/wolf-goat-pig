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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def run_initialization_steps():
    """
    Run initialization steps with fault tolerance.
    Non-critical failures are logged but don't prevent server startup.
    """
    logger.info("🐺 Wolf-Goat-Pig Render Startup")
    logger.info("=" * 50)

    # Wait for database to be ready
    logger.info("⏳ Waiting for database...")
    time.sleep(5)

    # Step 1: Initialize database and run seeding
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

    # Step 2: Run hole migration
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
    """Start the uvicorn server."""
    port = os.getenv("PORT", "8000")

    logger.info(f"🚀 Starting uvicorn server on 0.0.0.0:{port}")

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
            "--log-level", "info"
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
