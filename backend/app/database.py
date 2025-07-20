from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

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

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize database with error handling"""
    try:
        # This will create all tables, including GameStateModel
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        if "could not translate host name" in str(e):
            print("💡 This appears to be a database connection issue. Check your DATABASE_URL environment variable.")
        raise e 