#!/usr/bin/env python3
"""
Script to seed the database with realistic golf courses.
Run this script to populate the database with default courses.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.seed_courses import main

if __name__ == "__main__":
    print("🌱 Seeding golf courses into database...")
    main()
    print("✅ Course seeding completed!") 