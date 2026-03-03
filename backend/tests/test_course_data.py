#!/usr/bin/env python3
"""
Test script to display and verify the course data.
"""

import sys
import os
import json

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Course

def display_course_data():
    """Display all course data from the database."""
    db = SessionLocal()
    
    try:
        courses = db.query(Course).all()
        
        print("🏌️  Golf Course Database Contents:")
        print("=" * 60)
        
        for course in courses:
            print(f"\n📋 {course.name}")
            print(f"   Description: {course.description}")
            print(f"   Total Par: {course.total_par}")
            print(f"   Total Yards: {course.total_yards:,}")
            print(f"   Course Rating: {course.course_rating}")
            print(f"   Slope Rating: {course.slope_rating}")
            
            # Analyze hole data
            holes = course.holes_data
            par_3_count = sum(1 for hole in holes if hole["par"] == 3)
            par_4_count = sum(1 for hole in holes if hole["par"] == 4)
            par_5_count = sum(1 for hole in holes if hole["par"] == 5)
            
            print(f"   Hole Breakdown: {par_3_count} par 3s, {par_4_count} par 4s, {par_5_count} par 5s")
            
            # Show a few sample holes
            print(f"   Sample Holes:")
            for i, hole in enumerate(holes[:3]):  # Show first 3 holes
                print(f"     Hole {hole['hole_number']}: Par {hole['par']}, {hole['yards']} yards, "
                      f"Handicap {hole['handicap']}")
                print(f"       {hole['description']}")
            
            if len(holes) > 3:
                print(f"     ... and {len(holes) - 3} more holes")
            
            print("-" * 60)
        
        # Show course comparison
        print("\n📊 Course Comparison:")
        print("=" * 60)
        
        for course in courses:
            avg_yards = course.total_yards / 18
            difficulty_factor = (course.course_rating - 67) / 10  # Rough difficulty scale
            
            print(f"  {course.name}:")
            print(f"    Average Yards: {avg_yards:.1f}")
            print(f"    Difficulty: {'Easy' if difficulty_factor < 0.5 else 'Medium' if difficulty_factor < 1.0 else 'Hard'}")
            print(f"    Total Length: {'Short' if course.total_yards < 6000 else 'Medium' if course.total_yards < 7500 else 'Long'}")
            print()
            
    except Exception as e:
        print(f"Error reading course data: {e}")
    finally:
        db.close()

def test_course_validation():
    """Test that all courses meet validation requirements."""
    db = SessionLocal()
    
    try:
        courses = db.query(Course).all()
        
        print("🔍 Course Validation Check:")
        print("=" * 60)
        
        for course in courses:
            print(f"\nChecking {course.name}:")
            
            # Check hole count
            hole_count = len(course.holes_data)
            if hole_count == 18:
                print("  ✅ Has exactly 18 holes")
            else:
                print(f"  ❌ Has {hole_count} holes (should be 18)")
            
            # Check total par
            total_par = sum(hole["par"] for hole in course.holes_data)
            if 70 <= total_par <= 74:
                print(f"  ✅ Total par {total_par} is within valid range (70-74)")
            else:
                print(f"  ❌ Total par {total_par} is outside valid range (70-74)")
            
            # Check handicap uniqueness
            handicaps = [hole["handicap"] for hole in course.holes_data]
            if len(set(handicaps)) == 18:
                print("  ✅ All handicaps are unique (1-18)")
            else:
                print(f"  ❌ Handicaps are not unique: {handicaps}")
            
            # Check hole numbers
            hole_numbers = [hole["hole_number"] for hole in course.holes_data]
            if sorted(hole_numbers) == list(range(1, 19)):
                print("  ✅ Hole numbers are 1-18 and sequential")
            else:
                print(f"  ❌ Hole numbers are not sequential: {hole_numbers}")
            
            # Check yards validation
            invalid_yards = [hole for hole in course.holes_data if hole["yards"] < 100 or hole["yards"] > 700]
            if not invalid_yards:
                print("  ✅ All hole yards are within valid range (100-700)")
            else:
                print(f"  ❌ Some holes have invalid yards: {invalid_yards}")
            
    except Exception as e:
        print(f"Error during validation: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing golf course data...")
    display_course_data()
    test_course_validation()
    print("\n✅ Course data test completed!") 