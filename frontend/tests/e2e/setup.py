import os
import sys
import asyncio

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../backend')))

from app.database import init_db
from app.seed_data import seed_all_data

async def main():
    print("--- Starting test database setup (Python) ---")
    
    # Initialize the database
    print("Initializing database...")
    init_db()
    print("Database initialized.")
    
    # Seed the database
    print("Seeding database...")
    seed_all_data(force_reseed=True)
    print("Database seeded.")
    
    print("--- Test database setup complete (Python) ---")

if __name__ == "__main__":
    asyncio.run(main())
