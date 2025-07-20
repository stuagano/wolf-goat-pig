#!/usr/bin/env python3
"""
Script to update the Executive Course with corrected par values.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Course
from datetime import datetime

def update_executive_course():
    """Update the Executive Course with corrected par values."""
    db = SessionLocal()
    
    try:
        # Find the Executive Course
        course = db.query(Course).filter_by(name="Executive Course").first()
        
        if not course:
            print("Executive Course not found!")
            return
        
        # Delete the existing course
        db.delete(course)
        db.commit()
        print("Deleted existing Executive Course")
        
        # Create new Executive Course with corrected data
        new_course_data = {
            "name": "Executive Course",
            "description": "Shorter executive course perfect for quick rounds and beginners. Emphasis on short game and putting.",
            "total_par": 72,
            "total_yards": 5200,
            "course_rating": 68.5,
            "slope_rating": 115,
            "holes_data": [
                {
                    "hole_number": 1,
                    "par": 4,
                    "yards": 320,
                    "handicap": 9,
                    "description": "Short opening hole with wide fairway. Good for building confidence.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 2,
                    "par": 3,
                    "yards": 140,
                    "handicap": 17,
                    "description": "Short par 3 with large green. Good for practicing irons.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 3,
                    "par": 4,
                    "yards": 350,
                    "handicap": 5,
                    "description": "Straightaway par 4 with minimal hazards. Fairway is generous.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 4,
                    "par": 4,
                    "yards": 155,
                    "handicap": 15,
                    "description": "Elevated tee with wind factor. Green slopes from back to front.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 5,
                    "par": 4,
                    "yards": 365,
                    "handicap": 3,
                    "description": "Slight dogleg with bunkers protecting the green.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 6,
                    "par": 5,
                    "yards": 480,
                    "handicap": 11,
                    "description": "Short par 5 reachable in two. Good for practicing long approach shots.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 7,
                    "par": 4,
                    "yards": 340,
                    "handicap": 7,
                    "description": "Straight par 4 with water hazard on the right.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 8,
                    "par": 3,
                    "yards": 150,
                    "handicap": 13,
                    "description": "Short par 3 with bunkers around the green.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 9,
                    "par": 4,
                    "yards": 355,
                    "handicap": 1,
                    "description": "Finishing hole with elevated green. Approach shot requires extra club.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 10,
                    "par": 4,
                    "yards": 330,
                    "handicap": 8,
                    "description": "Short par 4 with wide fairway. Good scoring opportunity.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 11,
                    "par": 4,
                    "yards": 145,
                    "handicap": 16,
                    "description": "Short par 4 with large green. Wind can be a factor.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 12,
                    "par": 4,
                    "yards": 360,
                    "handicap": 4,
                    "description": "Straightaway par 4 with bunkers protecting the green.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 13,
                    "par": 4,
                    "yards": 160,
                    "handicap": 14,
                    "description": "Elevated tee with wind factor. Green slopes from back to front.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 14,
                    "par": 4,
                    "yards": 375,
                    "handicap": 2,
                    "description": "Longest par 4 on the course. Requires solid tee shot and approach.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 15,
                    "par": 5,
                    "yards": 490,
                    "handicap": 12,
                    "description": "Short par 5 reachable in two. Water hazard on the right.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 16,
                    "par": 4,
                    "yards": 345,
                    "handicap": 6,
                    "description": "Dogleg left with strategic bunkering. Position is key.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 17,
                    "par": 4,
                    "yards": 135,
                    "handicap": 18,
                    "description": "Shortest hole on the course. Good for practicing short irons.",
                    "tee_box": "forward"
                },
                {
                    "hole_number": 18,
                    "par": 4,
                    "yards": 350,
                    "handicap": 10,
                    "description": "Finishing hole with water hazard and dramatic green setting.",
                    "tee_box": "forward"
                }
            ]
        }
        
        # Create new course
        new_course = Course(
            name=new_course_data["name"],
            description=new_course_data["description"],
            total_par=new_course_data["total_par"],
            total_yards=new_course_data["total_yards"],
            course_rating=new_course_data["course_rating"],
            slope_rating=new_course_data["slope_rating"],
            holes_data=new_course_data["holes_data"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        db.add(new_course)
        db.commit()
        
        print("✅ Executive Course updated successfully!")
        print(f"   Total Par: {new_course_data['total_par']}")
        print(f"   Total Yards: {new_course_data['total_yards']}")
        
        # Verify the update
        par_3_count = sum(1 for hole in new_course_data["holes_data"] if hole["par"] == 3)
        par_4_count = sum(1 for hole in new_course_data["holes_data"] if hole["par"] == 4)
        par_5_count = sum(1 for hole in new_course_data["holes_data"] if hole["par"] == 5)
        
        print(f"   Hole Breakdown: {par_3_count} par 3s, {par_4_count} par 4s, {par_5_count} par 5s")
        
    except Exception as e:
        db.rollback()
        print(f"Error updating Executive Course: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🔄 Updating Executive Course...")
    update_executive_course()
    print("✅ Update completed!") 