from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time
import logging

logger = logging.getLogger(__name__)

# Use DATABASE_URL from environment (Render provides this for PostgreSQL)
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    # Render's DATABASE_URL may start with 'postgres://', SQLAlchemy expects 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
else:
    # Fallback to SQLite for local development
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Configure engine with better connection handling
if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
    # PostgreSQL configuration for production
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
        pool_size=5,         # Connection pool size
        max_overflow=10,     # Allow up to 10 extra connections
        echo=False           # Set to True for SQL debugging
    )
else:
    # SQLite configuration for development
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db(max_retries=3, retry_delay=5):
    """Initialize database with error handling and retries"""
    for attempt in range(max_retries):
        try:
            # This will create all tables, including GameStateModel
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database initialized successfully")
            
            # Test connection
            with SessionLocal() as session:
                session.execute("SELECT 1")
            logger.info("✅ Database connection test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed (attempt {attempt + 1}/{max_retries}): {e}")
            
            if "could not translate host name" in str(e):
                logger.warning("💡 This appears to be a database connection issue. Check your DATABASE_URL environment variable.")
            elif "does not exist" in str(e):
                logger.warning("💡 Database does not exist. This is normal for first deployment.")
            elif "permission denied" in str(e):
                logger.warning("💡 Database permission issue. Check your database credentials.")
            
            if attempt < max_retries - 1:
                logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("❌ All database initialization attempts failed")
                # Don't raise exception in production - let the service start
                if os.environ.get("ENVIRONMENT") == "production":
                    logger.warning("🚨 Starting service anyway in production mode")
                    return False
                else:
                    raise e
    
    return False

def get_db():
    """Get database session with error handling"""
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close() if 'db' in locals() else None 