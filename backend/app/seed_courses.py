from .database import SessionLocal, init_db
from .models import Course
from datetime import datetime
import json

# Realistic golf course data with proper yards, descriptions, and stroke indexes
DEFAULT_COURSES = [
    {
        "name": "Wing Point Golf & Country Club",
        "description": "Classic parkland course on Bainbridge Island, WA. Home of the original Wolf Goat Pig game.",
        "total_par": 72,
        "total_yards": 7050,
        "course_rating": 73.2,
        "slope_rating": 135,
        "holes_data": [
            {
                "hole_number": 1,
                "par": 4,
                "yards": 420,
                "handicap": 5,
                "description": "Dogleg right with water hazard on the right side. Requires accurate tee shot to avoid trouble.",
                "tee_box": "regular"
            },
            {
                "hole_number": 2,
                "par": 4,
                "yards": 385,
                "handicap": 13,
                "description": "Straightaway par 4 with slight uphill approach. Fairway bunkers guard the landing area.",
                "tee_box": "regular"
            },
            {
                "hole_number": 3,
                "par": 5,
                "yards": 580,
                "handicap": 1,
                "description": "Long par 5 with fairway bunkers and water hazard. Three-shot hole for most players.",
                "tee_box": "regular"
            },
            {
                "hole_number": 4,
                "par": 3,
                "yards": 165,
                "handicap": 17,
                "description": "Short par 3 over water to an elevated green. Wind can be a significant factor.",
                "tee_box": "regular"
            },
            {
                "hole_number": 5,
                "par": 4,
                "yards": 445,
                "handicap": 7,
                "description": "Long par 4 with out of bounds left. Demanding tee shot and approach.",
                "tee_box": "regular"
            },
            {
                "hole_number": 6,
                "par": 4,
                "yards": 395,
                "handicap": 11,
                "description": "Slight dogleg left with trees lining both sides. Position off the tee is key.",
                "tee_box": "regular"
            },
            {
                "hole_number": 7,
                "par": 5,
                "yards": 520,
                "handicap": 15,
                "description": "Reachable par 5 in two for long hitters. Risk/reward second shot over water.",
                "tee_box": "regular"
            },
            {
                "hole_number": 8,
                "par": 3,
                "yards": 185,
                "handicap": 3,
                "description": "Long par 3 with deep bunkers protecting the green. Club selection is crucial.",
                "tee_box": "regular"
            },
            {
                "hole_number": 9,
                "par": 4,
                "yards": 410,
                "handicap": 9,
                "description": "Finishing hole with elevated green. Approach shot requires extra club.",
                "tee_box": "regular"
            },
            {
                "hole_number": 10,
                "par": 4,
                "yards": 455,
                "handicap": 2,
                "description": "Championship tee makes this a very challenging par 4. Narrow landing area.",
                "tee_box": "regular"
            },
            {
                "hole_number": 11,
                "par": 5,
                "yards": 545,
                "handicap": 16,
                "description": "Three-shot par 5 with creek crossing the fairway. Strategic layup required.",
                "tee_box": "regular"
            },
            {
                "hole_number": 12,
                "par": 3,
                "yards": 175,
                "handicap": 8,
                "description": "Elevated tee with wind factor. Green slopes from back to front.",
                "tee_box": "regular"
            },
            {
                "hole_number": 13,
                "par": 4,
                "yards": 375,
                "handicap": 14,
                "description": "Short par 4, drivable green for long hitters. Bunkers protect the green.",
                "tee_box": "regular"
            },
            {
                "hole_number": 14,
                "par": 4,
                "yards": 435,
                "handicap": 4,
                "description": "Narrow fairway with difficult approach shot. Trees and bunkers create challenge.",
                "tee_box": "regular"
            },
            {
                "hole_number": 15,
                "par": 5,
                "yards": 565,
                "handicap": 18,
                "description": "Longest hole on course. Generous fairway but long approach to elevated green.",
                "tee_box": "regular"
            },
            {
                "hole_number": 16,
                "par": 4,
                "yards": 425,
                "handicap": 10,
                "description": "Risk/reward hole with water hazard. Aggressive play can pay off.",
                "tee_box": "regular"
            },
            {
                "hole_number": 17,
                "par": 3,
                "yards": 155,
                "handicap": 12,
                "description": "Island green signature hole. Short but intimidating with water all around.",
                "tee_box": "regular"
            },
            {
                "hole_number": 18,
                "par": 4,
                "yards": 415,
                "handicap": 6,
                "description": "Dramatic finishing hole with water hazard and elevated green. Classic risk/reward.",
                "tee_box": "regular"
            }
        ]
    },
    {
        "name": "Championship Links",
        "description": "Challenging championship course designed for tournament play. Longer and more demanding than typical courses.",
        "total_par": 72,
        "total_yards": 8895,
        "course_rating": 78.5,
        "slope_rating": 145,
        "holes_data": [
            {
                "hole_number": 1,
                "par": 4,
                "yards": 450,
                "handicap": 7,
                "description": "Opening hole with wide fairway but challenging approach to elevated green.",
                "tee_box": "championship"
            },
            {
                "hole_number": 2,
                "par": 3,
                "yards": 185,
                "handicap": 15,
                "description": "Long par 3 with deep bunkers and wind factor.",
                "tee_box": "championship"
            },
            {
                "hole_number": 3,
                "par": 5,
                "yards": 620,
                "handicap": 1,
                "description": "Monster par 5 requiring three solid shots. Water hazard on the right.",
                "tee_box": "championship"
            },
            {
                "hole_number": 4,
                "par": 4,
                "yards": 485,
                "handicap": 3,
                "description": "Long par 4 with narrow fairway and difficult green complex.",
                "tee_box": "championship"
            },
            {
                "hole_number": 5,
                "par": 4,
                "yards": 420,
                "handicap": 11,
                "description": "Dogleg left with strategic bunkering. Position is key.",
                "tee_box": "championship"
            },
            {
                "hole_number": 6,
                "par": 5,
                "yards": 580,
                "handicap": 17,
                "description": "Reachable par 5 with risk/reward second shot over water.",
                "tee_box": "championship"
            },
            {
                "hole_number": 7,
                "par": 4,
                "yards": 465,
                "handicap": 5,
                "description": "Long par 4 with out of bounds left and water right.",
                "tee_box": "championship"
            },
            {
                "hole_number": 8,
                "par": 3,
                "yards": 195,
                "handicap": 13,
                "description": "Elevated tee with wind factor. Green slopes severely.",
                "tee_box": "championship"
            },
            {
                "hole_number": 9,
                "par": 4,
                "yards": 440,
                "handicap": 9,
                "description": "Finishing hole with water hazard and dramatic green setting.",
                "tee_box": "championship"
            },
            {
                "hole_number": 10,
                "par": 4,
                "yards": 470,
                "handicap": 2,
                "description": "Challenging par 4 with narrow landing area and difficult approach.",
                "tee_box": "championship"
            },
            {
                "hole_number": 11,
                "par": 5,
                "yards": 600,
                "handicap": 16,
                "description": "Long par 5 requiring three solid shots. Strategic layup area.",
                "tee_box": "championship"
            },
            {
                "hole_number": 12,
                "par": 3,
                "yards": 175,
                "handicap": 14,
                "description": "Short par 3 with island green. Wind and pressure factor.",
                "tee_box": "championship"
            },
            {
                "hole_number": 13,
                "par": 4,
                "yards": 400,
                "handicap": 18,
                "description": "Short par 4, drivable for long hitters. Risk/reward hole.",
                "tee_box": "championship"
            },
            {
                "hole_number": 14,
                "par": 4,
                "yards": 480,
                "handicap": 4,
                "description": "Long par 4 with narrow fairway and challenging green.",
                "tee_box": "championship"
            },
            {
                "hole_number": 15,
                "par": 5,
                "yards": 590,
                "handicap": 12,
                "description": "Three-shot par 5 with water hazard crossing the fairway.",
                "tee_box": "championship"
            },
            {
                "hole_number": 16,
                "par": 4,
                "yards": 460,
                "handicap": 8,
                "description": "Dogleg right with water hazard. Demanding tee shot and approach.",
                "tee_box": "championship"
            },
            {
                "hole_number": 17,
                "par": 3,
                "yards": 165,
                "handicap": 10,
                "description": "Short par 3 with deep bunkers and wind factor.",
                "tee_box": "championship"
            },
            {
                "hole_number": 18,
                "par": 4,
                "yards": 655,
                "handicap": 6,
                "description": "Epic finishing hole with water hazard and dramatic green setting.",
                "tee_box": "championship"
            }
        ]
    },
    {
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
]

def main():
    """Seed the database with default golf courses."""
    init_db()
    db = SessionLocal()
    
    try:
        for course_data in DEFAULT_COURSES:
            # Check if course already exists
            existing_course = db.query(Course).filter_by(name=course_data["name"]).first()
            
            if existing_course:
                print(f"Course '{course_data['name']}' already exists, skipping...")
                continue
            
            # Create new course
            course = Course(
                name=course_data["name"],
                description=course_data["description"],
                total_par=course_data["total_par"],
                total_yards=course_data["total_yards"],
                course_rating=course_data.get("course_rating"),
                slope_rating=course_data.get("slope_rating"),
                holes_data=course_data["holes_data"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            db.add(course)
            print(f"Added course: {course_data['name']} ({course_data['total_par']} par, {course_data['total_yards']} yards)")
        
        db.commit()
        print(f"\nSuccessfully seeded {len(DEFAULT_COURSES)} courses!")
        
        # Print summary statistics
        print("\nCourse Summary:")
        for course_data in DEFAULT_COURSES:
            par_3_count = sum(1 for hole in course_data["holes_data"] if hole["par"] == 3)
            par_4_count = sum(1 for hole in course_data["holes_data"] if hole["par"] == 4)
            par_5_count = sum(1 for hole in course_data["holes_data"] if hole["par"] == 5)
            avg_yards = course_data["total_yards"] / 18
            
            print(f"  {course_data['name']}:")
            print(f"    Par: {course_data['total_par']} ({par_3_count} par 3s, {par_4_count} par 4s, {par_5_count} par 5s)")
            print(f"    Yards: {course_data['total_yards']} (avg: {avg_yards:.1f} per hole)")
            print(f"    Rating: {course_data.get('course_rating', 'N/A')} / {course_data.get('slope_rating', 'N/A')}")
            print()
            
    except Exception as e:
        db.rollback()
        print(f"Error seeding courses: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main() 