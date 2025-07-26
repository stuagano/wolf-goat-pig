from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

# Database configuration with environment-specific settings
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production database (PostgreSQL)
    if DATABASE_URL.startswith("postgres://"):
        # Fix for newer SQLAlchemy versions
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
        echo=os.getenv("ENVIRONMENT") == "development"
    )
else:
    # Development/local database (SQLite)
    SQLITE_DATABASE_URL = "sqlite:///./wolf_goat_pig.db"
    engine = create_engine(
        SQLITE_DATABASE_URL, 
        connect_args={"check_same_thread": False},
        echo=os.getenv("ENVIRONMENT") == "development"
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they're registered with SQLAlchemy
        from . import models
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        
        # Test database connection
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise 