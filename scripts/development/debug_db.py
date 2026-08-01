#!/usr/bin/env python3
"""
Database connection debugging script
"""

import os
import sys
from urllib.parse import urlparse

def debug_database_connection():
    """Debug database connection issues"""
    print("🔍 Database Connection Debug")
    print("=" * 50)
    
    # Check environment variables
    database_url = os.environ.get("DATABASE_URL")
    print(f"📋 DATABASE_URL: {'Set' if database_url else 'Not set'}")
    
    if database_url:
        # Parse the URL to check components
        try:
            parsed = urlparse(database_url)
            print(f"🔗 Protocol: {parsed.scheme}")
            print(f"🌐 Host: {parsed.hostname}")
            print(f"🚪 Port: {parsed.port}")
            print(f"📁 Database: {parsed.path[1:] if parsed.path else 'None'}")
            print(f"👤 Username: {parsed.username}")
            print(f"🔑 Password: {'Set' if parsed.password else 'Not set'}")
            
        except Exception as e:
            print(f"❌ Error parsing DATABASE_URL: {e}")
    else:
        print("❌ DATABASE_URL environment variable is not set")
        print("💡 This will cause the app to fall back to SQLite")
    
    # Check other relevant environment variables
    print(f"\n📋 PYTHON_VERSION: {os.environ.get('PYTHON_VERSION', 'Not set')}")
    print(f"📋 PORT: {os.environ.get('PORT', 'Not set')}")
    
    # Try to import and test database connection
    print(f"\n🧪 Testing Database Connection...")
    try:
        from app.database import engine, init_db
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful!")
            
        # Test initialization
        init_db()
        print("✅ Database initialization successful!")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        
        if "could not translate host name" in str(e):
            print("\n💡 **SOLUTION**: This is a DNS resolution issue.")
            print("   - Your database service might be down or restarting")
            print("   - Check Cloud SQL instance and connector status")
            print("   - The database URL might have changed")
            print("   - Verify the DATABASE_URL secret version")
            
        elif "connection refused" in str(e):
            print("\n💡 **SOLUTION**: Database service is not accepting connections.")
            print("   - Database might be starting up")
            print("   - Check if the Cloud SQL instance is running")
            
        elif "authentication failed" in str(e):
            print("\n💡 **SOLUTION**: Authentication credentials are incorrect.")
            print("   - Check your DATABASE_URL credentials")
            print("   - Database password might have changed")
            
        else:
            print(f"\n💡 **GENERIC ERROR**: {type(e).__name__}")
            print("   - Check your Cloud Run service logs")
            print("   - Verify database service is running")
    
    print(f"\n🎯 **NEXT STEPS**:")
    print("1. Check Cloud SQL instance status")
    print("2. Verify the DATABASE_URL in your service environment variables")
    print("3. Check the Cloud SQL connector and networking")
    print("4. Verify the Cloud Run DATABASE_URL secret mapping")

if __name__ == "__main__":
    debug_database_connection() 