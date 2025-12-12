#!/usr/bin/env python3
"""
Saturday Pairing Job Script

This script is designed to be run via cron on Saturday afternoons.
It generates random pairings for the next Sunday and sends email notifications.

Usage:
    python run_saturday_pairings.py

Cron example (run every Saturday at 2:00 PM):
    0 14 * * 6 cd /path/to/wolf-goat-pig/backend && python scripts/run_saturday_pairings.py >> /var/log/wolf-goat-pig/pairings.log 2>&1

Environment variables:
    API_URL - Base URL of the API (default: http://localhost:8000)

Alternatively, you can run directly against the database by importing the service.
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_via_api():
    """Run the Saturday job by calling the API endpoint."""
    import requests

    api_url = os.getenv("API_URL", "http://localhost:8000")
    endpoint = f"{api_url}/pairings/run-saturday-job"

    logger.info(f"Calling Saturday pairing job at {endpoint}")

    try:
        response = requests.post(endpoint, timeout=60)
        response.raise_for_status()

        result = response.json()
        logger.info(f"Job completed successfully: {result}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return False


def run_directly():
    """Run the Saturday job directly using the service (bypasses API)."""
    # Add the backend app to the path
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, backend_path)

    from app import database
    from app.services.pairing_scheduler_service import PairingSchedulerService

    logger.info("Running Saturday pairing job directly")

    try:
        db = database.SessionLocal()
        result = PairingSchedulerService.run_saturday_job(db)

        if result["success"]:
            logger.info(
                f"Job completed: {result['team_count']} teams, "
                f"{result['emails_sent']} emails sent for {result['game_date']}"
            )
        else:
            logger.warning(f"Job did not generate pairings: {result['message']}")

        return result["success"]

    except Exception as e:
        logger.error(f"Direct execution failed: {e}")
        return False
    finally:
        db.close()


def main():
    """Main entry point."""
    logger.info(f"Starting Saturday pairing job at {datetime.now().isoformat()}")

    # Try API first, fall back to direct execution
    use_api = os.getenv("USE_API", "true").lower() == "true"

    if use_api:
        success = run_via_api()
        if not success:
            logger.info("API call failed, trying direct execution...")
            success = run_directly()
    else:
        success = run_directly()

    if success:
        logger.info("Saturday pairing job completed successfully")
        sys.exit(0)
    else:
        logger.error("Saturday pairing job failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
