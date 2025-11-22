
import os
import sys
import asyncio

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../backend')))

from app.database import engine, Base

async def main():
    print("--- Starting test database teardown (Python) ---")
    
    # Drop all tables
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("All tables dropped.")
    
    print("--- Test database teardown complete (Python) ---")

if __name__ == "__main__":
    asyncio.run(main())
