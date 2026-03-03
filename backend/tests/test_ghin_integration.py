#!/usr/bin/env python3
"""
Test GHIN integration to verify API connection and handicap syncing
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ghin_service import GHINService
from app.database import SessionLocal
from app.models import PlayerProfile
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ghin_connection():
    """Test GHIN API connection and authentication"""
    db = SessionLocal()
    try:
        # Initialize GHIN service
        ghin_service = GHINService(db)
        logger.info("Initializing GHIN service...")
        
        # Test authentication
        success = await ghin_service.initialize()
        
        if success:
            logger.info("✅ GHIN service initialized successfully!")
            logger.info(f"   JWT Token acquired: {ghin_service.jwt_token[:20]}...")
            
            # Try to search for a golfer
            logger.info("\nTesting golfer search...")
            try:
                results = await ghin_service.search_golfers("Smith", per_page=5)
                logger.info(f"✅ Search successful! Found {len(results.get('golfers', []))} golfers")
                
                # Show first result if any
                if results.get('golfers'):
                    first_golfer = results['golfers'][0]
                    logger.info(f"   First result: {first_golfer.get('first_name')} {first_golfer.get('last_name')} - GHIN: {first_golfer.get('ghin')}")
            except Exception as e:
                logger.error(f"❌ Search failed: {e}")
            
            # Try to sync a player's handicap (if any exist with GHIN ID)
            logger.info("\nLooking for players with GHIN IDs...")
            player_with_ghin = db.query(PlayerProfile).filter(
                PlayerProfile.ghin_id.isnot(None)
            ).first()
            
            if player_with_ghin:
                logger.info(f"Found player with GHIN ID: {player_with_ghin.name} ({player_with_ghin.ghin_id})")
                logger.info("Attempting to sync handicap...")
                
                handicap_data = await ghin_service.sync_player_handicap(player_with_ghin.id)
                
                if handicap_data:
                    logger.info(f"✅ Handicap synced successfully!")
                    logger.info(f"   New handicap: {handicap_data.get('handicap_index')}")
                    logger.info(f"   Effective date: {handicap_data.get('effective_date')}")
                else:
                    logger.warning("⚠️ Handicap sync returned no data")
            else:
                logger.info("No players with GHIN IDs found in database")
                
                # Add a test GHIN ID to a player for testing
                test_player = db.query(PlayerProfile).filter(
                    PlayerProfile.name == "Stuart"
                ).first()
                
                if test_player:
                    logger.info(f"\nWould you like to add a GHIN ID to {test_player.name}?")
                    logger.info("You can update the player's GHIN ID in the database for testing")
                
        else:
            logger.error("❌ GHIN service initialization failed!")
            logger.error("   Check your GHIN_USERNAME and GHIN_PASSWORD in .env file")
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

async def test_specific_ghin_lookup(ghin_id: str):
    """Test looking up a specific GHIN ID"""
    db = SessionLocal()
    try:
        ghin_service = GHINService(db)
        
        if await ghin_service.initialize():
            logger.info(f"Looking up GHIN ID: {ghin_id}")
            
            # Fetch handicap directly
            handicap_data = await ghin_service._fetch_handicap_from_ghin(ghin_id)
            
            if handicap_data:
                logger.info(f"✅ Found handicap data:")
                logger.info(f"   Handicap Index: {handicap_data.get('handicap_index')}")
                logger.info(f"   Effective Date: {handicap_data.get('effective_date')}")
            else:
                logger.warning(f"⚠️ No handicap data found for GHIN ID: {ghin_id}")
                
    except Exception as e:
        logger.error(f"❌ Lookup failed: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("GHIN Integration Test")
    logger.info("=" * 60)
    
    # Check if environment variables are set
    if not os.getenv('GHIN_USERNAME'):
        logger.error("❌ GHIN_USERNAME not set in environment")
        sys.exit(1)
    
    if not os.getenv('GHIN_PASSWORD'):
        logger.error("❌ GHIN_PASSWORD not set in environment")
        sys.exit(1)
    
    logger.info(f"GHIN Username: {os.getenv('GHIN_USERNAME')}")
    
    # Run the test
    asyncio.run(test_ghin_connection())
    
    # Optionally test a specific GHIN ID
    # asyncio.run(test_specific_ghin_lookup("1234567"))