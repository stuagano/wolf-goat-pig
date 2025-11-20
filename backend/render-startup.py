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


def run_initialization_steps():
    """
    Run initialization steps with fault tolerance.
    Non-critical failures are logged but don't prevent server startup.
    """
    logger.info("🐺 Wolf-Goat-Pig Render Startup")
    logger.info("=" * 50)

    # Wait for database to be ready
    logger.info("⏳ Waiting for database...")
    time.sleep(3)  # Reduced from 5 to 3 seconds

    # Step 1: Initialize database and run seeding
    logger.info("🗄️ Running database initialization and seeding...")
    try:
        result = subprocess.run(
            [sys.executable, "startup.py", "--seed-only"],
            capture_output=True,
            text=True,
            timeout=90  # Reduced from 120 to 90 seconds
        )

        if result.returncode == 0:
            logger.info("✅ Database seeding completed successfully")
            logger.info(f"Output: {result.stdout[-500:]}")  # Log last 500 chars
        else:
            logger.warning(f"⚠️ Database seeding completed with warnings (code: {result.returncode})")
            logger.warning(f"Output: {result.stdout[-500:]}")
            if result.stderr:
                logger.warning(f"Errors: {result.stderr[-500:]}")
            # Don't exit - continue with startup

    except subprocess.TimeoutExpired as e:
        logger.error("❌ Database seeding timed out after 90 seconds")
        if e.stdout:
            logger.error(f"Partial output: {e.stdout.decode('utf-8')[-500:]}")
        if e.stderr:
            logger.error(f"Partial errors: {e.stderr.decode('utf-8')[-500:]}")
        logger.warning("🔄 Continuing with server startup anyway...")
    except Exception as e:
        logger.error(f"❌ Database seeding failed: {e}")
        logger.warning("🔄 Continuing with server startup anyway...")

    # Step 2: Run hole migration (skip if causing issues)
    skip_hole_migration = os.getenv("SKIP_HOLE_MIGRATION", "false").lower() == "true"

    if skip_hole_migration:
        logger.info("⏭️ Skipping hole migration (SKIP_HOLE_MIGRATION=true)")
    else:
        logger.info("🔄 Running hole data migration...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "app.migrations.add_holes_from_json"],
                capture_output=True,
                text=True,
                timeout=30  # Reduced from 60 to 30 seconds
            )

            if result.returncode == 0:
                logger.info("✅ Hole migration completed successfully")
            else:
                logger.warning(f"⚠️ Hole migration completed with warnings")
                logger.warning(f"Output: {result.stdout[-200:]}")
                if result.stderr:
                    logger.warning(f"Errors: {result.stderr[-200:]}")
                # Don't exit - continue with startup

        except subprocess.TimeoutExpired:
            logger.error("❌ Hole migration timed out after 30 seconds")
            logger.warning("🔄 Continuing with server startup anyway...")
        except Exception as e:
            logger.error(f"❌ Hole migration failed: {e}")
            logger.warning("🔄 Continuing with server startup anyway...")

    logger.info("✅ Initialization steps completed")

    # Set SKIP_SEEDING to prevent duplicate seeding in FastAPI startup event
    os.environ["SKIP_SEEDING"] = "true"
    logger.info("🔒 Set SKIP_SEEDING=true to prevent duplicate seeding in FastAPI startup")


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
