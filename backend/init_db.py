"""
Database initialization script for CI/CD environments.
This script ensures all database tables are created before the application starts.
"""
import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Initialize database tables and verify they exist."""
    try:
        logger.info("🔄 Initializing database...")

        # Import database module
        from app import database, models

        # Create all tables
        logger.info("Creating database tables...")
        database.Base.metadata.create_all(bind=database.engine)
        logger.info("✅ Database tables created")

        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(database.engine)
        table_names = inspector.get_table_names()

        logger.info(f"📊 Found {len(table_names)} tables: {', '.join(table_names)}")

        # Check for critical tables
        required_tables = ['game_state', 'courses', 'players', 'users']
        missing_tables = [t for t in required_tables if t not in table_names]

        if missing_tables:
            logger.error(f"❌ Missing required tables: {', '.join(missing_tables)}")
            return False

        logger.info("✅ All required tables exist")

        # Test database connection
        db = database.SessionLocal()
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            logger.info("✅ Database connection test successful")
        finally:
            db.close()

        logger.info("🎉 Database initialization complete!")
        return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
