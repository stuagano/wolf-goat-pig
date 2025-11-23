#!/usr/bin/env python3
"""
Database Migration Script for Player Profiles

This script creates the necessary database tables for the player profile
and statistics tracking system. It can be run independently or as part
of the application startup process.

Usage:
    python migrate_player_profiles.py [--drop-existing]
    
Options:
    --drop-existing    Drop existing tables before creating new ones (DANGEROUS!)
"""

import argparse
import logging
import sys
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from .database import engine

# Import models to ensure they're registered with SQLAlchemy
from .models import Base, PlayerProfile, PlayerStatistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(engine, table_name):
    """Check if a table exists in the database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """))
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking if table {table_name} exists: {e}")
        return False

def create_player_profile_tables(engine, drop_existing=False):
    """Create all player profile related tables."""

    tables_to_create = [
        'player_profiles',
        'player_statistics',
        'game_records',
        'game_player_results',
        'player_achievements'
    ]

    try:
        logger.info("Starting player profile database migration...")

        # Check existing tables
        existing_tables = []
        for table_name in tables_to_create:
            if check_table_exists(engine, table_name):
                existing_tables.append(table_name)

        if existing_tables:
            logger.info(f"Found existing tables: {existing_tables}")

            if drop_existing:
                logger.warning("Dropping existing tables as requested...")
                with engine.connect() as conn:
                    # Drop tables in reverse dependency order
                    drop_order = [
                        'player_achievements',
                        'game_player_results',
                        'game_records',
                        'player_statistics',
                        'player_profiles'
                    ]

                    for table_name in drop_order:
                        if table_name in existing_tables:
                            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                            logger.info(f"Dropped table: {table_name}")

                    conn.commit()
            else:
                logger.info("Existing tables found. Use --drop-existing to recreate them.")
                logger.info("Will only create missing tables...")

        # Create all tables (SQLAlchemy will skip existing ones)
        logger.info("Creating player profile tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Player profile tables created successfully!")

        # Verify table creation
        logger.info("Verifying table creation...")
        for table_name in tables_to_create:
            if check_table_exists(engine, table_name):
                logger.info(f"✓ Table '{table_name}' exists")
            else:
                logger.error(f"✗ Table '{table_name}' was not created")
                return False

        # Create indexes for better performance
        create_performance_indexes(engine)

        # Insert sample data if requested
        if len(sys.argv) > 1 and '--sample-data' in sys.argv:
            create_sample_data(engine)

        logger.info("Player profile migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_performance_indexes(engine):
    """Create database indexes for better query performance."""
    try:
        logger.info("Creating performance indexes...")

        indexes = [
            # Player profiles
            "CREATE INDEX IF NOT EXISTS idx_player_profiles_name ON player_profiles(name)",
            "CREATE INDEX IF NOT EXISTS idx_player_profiles_active ON player_profiles(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_player_profiles_last_played ON player_profiles(last_played)",

            # Player statistics
            "CREATE INDEX IF NOT EXISTS idx_player_statistics_player_id ON player_statistics(player_id)",
            "CREATE INDEX IF NOT EXISTS idx_player_statistics_games_played ON player_statistics(games_played)",
            "CREATE INDEX IF NOT EXISTS idx_player_statistics_total_earnings ON player_statistics(total_earnings)",

            # Game records
            "CREATE INDEX IF NOT EXISTS idx_game_records_game_id ON game_records(game_id)",
            "CREATE INDEX IF NOT EXISTS idx_game_records_created_at ON game_records(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_game_records_course ON game_records(course_name)",

            # Game player results
            "CREATE INDEX IF NOT EXISTS idx_game_player_results_game_id ON game_player_results(game_record_id)",
            "CREATE INDEX IF NOT EXISTS idx_game_player_results_player_id ON game_player_results(player_profile_id)",
            "CREATE INDEX IF NOT EXISTS idx_game_player_results_position ON game_player_results(final_position)",
            "CREATE INDEX IF NOT EXISTS idx_game_player_results_created_at ON game_player_results(created_at)",

            # Player achievements
            "CREATE INDEX IF NOT EXISTS idx_player_achievements_player_id ON player_achievements(player_profile_id)",
            "CREATE INDEX IF NOT EXISTS idx_player_achievements_type ON player_achievements(achievement_type)",
            "CREATE INDEX IF NOT EXISTS idx_player_achievements_date ON player_achievements(earned_date)"
        ]

        with engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.debug(f"Created index: {index_sql.split()[-1]}")
                except Exception as e:
                    logger.warning(f"Could not create index: {e}")

            conn.commit()

        logger.info("Performance indexes created successfully!")

    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

def create_sample_data(engine):
    """Create sample player profiles and statistics for testing."""
    try:
        logger.info("Creating sample data...")

        # Create a database session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Sample player profiles
        sample_profiles = [
            {
                "name": "Test Player",
                "handicap": 12.0,
                "preferences": {
                    "ai_difficulty": "medium",
                    "preferred_game_modes": ["wolf_goat_pig"],
                    "preferred_player_count": 4,
                    "betting_style": "moderate",
                    "display_hints": True
                }
            },
            {
                "name": "Demo User",
                "handicap": 18.0,
                "preferences": {
                    "ai_difficulty": "easy",
                    "preferred_game_modes": ["wolf_goat_pig"],
                    "preferred_player_count": 4,
                    "betting_style": "conservative",
                    "display_hints": True
                }
            }
        ]

        created_profiles = []
        for profile_data in sample_profiles:
            # Check if profile already exists
            existing = db.query(PlayerProfile).filter(
                PlayerProfile.name == profile_data["name"]
            ).first()

            if not existing:
                profile = PlayerProfile(
                    name=profile_data["name"],
                    handicap=profile_data["handicap"],
                    created_date=datetime.now().isoformat(),
                    preferences=profile_data["preferences"]
                )
                db.add(profile)
                db.flush()  # Get the ID

                # Create initial statistics
                stats = PlayerStatistics(
                    player_id=profile.id,
                    last_updated=datetime.now().isoformat()
                )
                db.add(stats)

                created_profiles.append(profile)
                logger.info(f"Created sample profile: {profile.name}")
            else:
                logger.info(f"Sample profile already exists: {profile_data['name']}")

        db.commit()
        db.close()

        logger.info(f"Created {len(created_profiles)} sample profiles")

    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()

def verify_migration(engine):
    """Verify that the migration was successful."""
    try:
        logger.info("Verifying migration...")

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Test basic queries
        profile_count = db.query(PlayerProfile).count()
        stats_count = db.query(PlayerStatistics).count()

        logger.info(f"Found {profile_count} player profiles")
        logger.info(f"Found {stats_count} statistics records")

        # Test a sample query
        if profile_count > 0:
            sample_profile = db.query(PlayerProfile).first()
            logger.info(f"Sample profile: {sample_profile.name} (Handicap: {sample_profile.handicap})")

        db.close()

        logger.info("Migration verification completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Error during verification: {e}")
        if 'db' in locals():
            db.close()
        return False

def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description='Migrate player profile database tables')
    parser.add_argument('--drop-existing', action='store_true',
                        help='Drop existing tables before creating new ones (DANGEROUS!)')
    parser.add_argument('--sample-data', action='store_true',
                        help='Create sample player profiles for testing')
    parser.add_argument('--verify-only', action='store_true',
                        help='Only verify existing tables, do not create new ones')

    args = parser.parse_args()

    if args.drop_existing:
        response = input("This will DROP existing player profile tables and ALL DATA will be lost! Are you sure? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            logger.info("Migration cancelled by user")
            return

    try:
        if args.verify_only:
            success = verify_migration(engine)
        else:
            success = create_player_profile_tables(engine, drop_existing=args.drop_existing)
            if success:
                success = verify_migration(engine)

        if success:
            logger.info("✅ Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Migration failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
