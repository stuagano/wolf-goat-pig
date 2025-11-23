from datetime import datetime

from .database import SessionLocal, init_db
from .models import Course

# Realistic golf course data with proper yards, descriptions, and stroke indexes
DEFAULT_COURSES = [
    {
        "name": "Wing Point Golf & Country Club",
        "description": "Classic parkland course on Bainbridge Island, WA (Est. 1903). Home of the original Wolf Goat Pig game.",
        "total_par": 71,
        "total_yards": 5486,
        "course_rating": 67.4,
        "slope_rating": 120,
        "holes_data": [
            {
                "hole_number": 1,
                "par": 5,
                "yards": 429,
                "stroke_index": 5,
                "description": "Opening Drive - gentle starting hole, slight dogleg right",
                "tee_box": "white"
            },
            {
                "hole_number": 2,
                "par": 3,
                "yards": 158,
                "stroke_index": 15,
                "description": "Short Iron - downhill par 3 with bunkers guarding the green",
                "tee_box": "white"
            },
            {
                "hole_number": 3,
                "par": 4,
                "yards": 310,
                "stroke_index": 1,
                "description": "The Challenge - handicap 1, tough dogleg left requiring precision",
                "tee_box": "white"
            },
            {
                "hole_number": 4,
                "par": 3,
                "yards": 112,
                "stroke_index": 17,
                "description": "Precision - short but tricky par 3",
                "tee_box": "white"
            },
            {
                "hole_number": 5,
                "par": 5,
                "yards": 440,
                "stroke_index": 7,
                "description": "The Long One - reachable par 5 for longer hitters",
                "tee_box": "white"
            },
            {
                "hole_number": 6,
                "par": 4,
                "yards": 327,
                "stroke_index": 9,
                "description": "Mid Iron - strategic placement required off the tee",
                "tee_box": "white"
            },
            {
                "hole_number": 7,
                "par": 4,
                "yards": 291,
                "stroke_index": 13,
                "description": "Risk Reward - short par 4 with risk-reward options",
                "tee_box": "white"
            },
            {
                "hole_number": 8,
                "par": 4,
                "yards": 280,
                "stroke_index": 11,
                "description": "The Turn - another short par 4 before the turn",
                "tee_box": "white"
            },
            {
                "hole_number": 9,
                "par": 4,
                "yards": 316,
                "stroke_index": 3,
                "description": "Home Bound - tough finishing hole for the front nine",
                "tee_box": "white"
            },
            {
                "hole_number": 10,
                "par": 3,
                "yards": 200,
                "stroke_index": 16,
                "description": "Back Nine Starter - long par 3 to start the back nine",
                "tee_box": "white"
            },
            {
                "hole_number": 11,
                "par": 4,
                "yards": 353,
                "stroke_index": 2,
                "description": "The Beast - second toughest hole on the course, Par 4/5 depending on tees",
                "tee_box": "white"
            },
            {
                "hole_number": 12,
                "par": 3,
                "yards": 168,
                "stroke_index": 14,
                "description": "Over Water - beautiful par 3 with water in play",
                "tee_box": "white"
            },
            {
                "hole_number": 13,
                "par": 4,
                "yards": 272,
                "stroke_index": 18,
                "description": "Breathing Room - easiest hole on the course, make your birdie here",
                "tee_box": "white"
            },
            {
                "hole_number": 14,
                "par": 4,
                "yards": 303,
                "stroke_index": 8,
                "description": "Deceptive - looks easy but plays tough",
                "tee_box": "white"
            },
            {
                "hole_number": 15,
                "par": 4,
                "yards": 356,
                "stroke_index": 10,
                "description": "The Stretch - start of the tough finishing stretch",
                "tee_box": "white"
            },
            {
                "hole_number": 16,
                "par": 4,
                "yards": 344,
                "stroke_index": 4,
                "description": "Penultimate - tough hole as you near the finish",
                "tee_box": "white"
            },
            {
                "hole_number": 17,
                "par": 5,
                "yards": 455,
                "stroke_index": 12,
                "description": "The Penultimate - par 5 start of Hoepfinger phase",
                "tee_box": "white"
            },
            {
                "hole_number": 18,
                "par": 4,
                "yards": 372,
                "stroke_index": 6,
                "description": "The Finale - strong finishing par 4, Big Dick opportunity",
                "tee_box": "white"
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
                "stroke_index": 7,
                "description": "Opening hole with wide fairway but challenging approach to elevated green.",
                "tee_box": "championship"
            },
            {
                "hole_number": 2,
                "par": 3,
                "yards": 185,
                "stroke_index": 15,
                "description": "Long par 3 with deep bunkers and wind factor.",
                "tee_box": "championship"
            },
            {
                "hole_number": 3,
                "par": 5,
                "yards": 620,
                "stroke_index": 1,
                "description": "Monster par 5 requiring three solid shots. Water hazard on the right.",
                "tee_box": "championship"
            },
            {
                "hole_number": 4,
                "par": 4,
                "yards": 485,
                "stroke_index": 3,
                "description": "Long par 4 with narrow fairway and difficult green complex.",
                "tee_box": "championship"
            },
            {
                "hole_number": 5,
                "par": 4,
                "yards": 420,
                "stroke_index": 11,
                "description": "Dogleg left with strategic bunkering. Position is key.",
                "tee_box": "championship"
            },
            {
                "hole_number": 6,
                "par": 5,
                "yards": 580,
                "stroke_index": 17,
                "description": "Reachable par 5 with risk/reward second shot over water.",
                "tee_box": "championship"
            },
            {
                "hole_number": 7,
                "par": 4,
                "yards": 465,
                "stroke_index": 5,
                "description": "Long par 4 with out of bounds left and water right.",
                "tee_box": "championship"
            },
            {
                "hole_number": 8,
                "par": 3,
                "yards": 195,
                "stroke_index": 13,
                "description": "Elevated tee with wind factor. Green slopes severely.",
                "tee_box": "championship"
            },
            {
                "hole_number": 9,
                "par": 4,
                "yards": 440,
                "stroke_index": 9,
                "description": "Finishing hole with water hazard and dramatic green setting.",
                "tee_box": "championship"
            },
            {
                "hole_number": 10,
                "par": 4,
                "yards": 470,
                "stroke_index": 2,
                "description": "Challenging par 4 with narrow landing area and difficult approach.",
                "tee_box": "championship"
            },
            {
                "hole_number": 11,
                "par": 5,
                "yards": 600,
                "stroke_index": 16,
                "description": "Long par 5 requiring three solid shots. Strategic layup area.",
                "tee_box": "championship"
            },
            {
                "hole_number": 12,
                "par": 3,
                "yards": 175,
                "stroke_index": 14,
                "description": "Short par 3 with island green. Wind and pressure factor.",
                "tee_box": "championship"
            },
            {
                "hole_number": 13,
                "par": 4,
                "yards": 400,
                "stroke_index": 18,
                "description": "Short par 4, drivable for long hitters. Risk/reward hole.",
                "tee_box": "championship"
            },
            {
                "hole_number": 14,
                "par": 4,
                "yards": 480,
                "stroke_index": 4,
                "description": "Long par 4 with narrow fairway and challenging green.",
                "tee_box": "championship"
            },
            {
                "hole_number": 15,
                "par": 5,
                "yards": 590,
                "stroke_index": 12,
                "description": "Three-shot par 5 with water hazard crossing the fairway.",
                "tee_box": "championship"
            },
            {
                "hole_number": 16,
                "par": 4,
                "yards": 460,
                "stroke_index": 8,
                "description": "Dogleg right with water hazard. Demanding tee shot and approach.",
                "tee_box": "championship"
            },
            {
                "hole_number": 17,
                "par": 3,
                "yards": 165,
                "stroke_index": 10,
                "description": "Short par 3 with deep bunkers and wind factor.",
                "tee_box": "championship"
            },
            {
                "hole_number": 18,
                "par": 4,
                "yards": 655,
                "stroke_index": 6,
                "description": "Epic finishing hole with water hazard and dramatic green setting.",
                "tee_box": "championship"
            }
        ]
    },
    {
        "name": "Executive Course",
        "description": "Shorter executive course perfect for quick rounds and beginners. Emphasis on short game and putting.",
        "total_par": sum(hole['par'] for hole in [
            { "hole_number": 1, "par": 4, "yards": 320, "stroke_index": 9, "description": "Short opening hole with wide fairway. Good for building confidence.", "tee_box": "forward" },
            { "hole_number": 2, "par": 3, "yards": 140, "stroke_index": 17, "description": "Short par 3 with large green. Good for practicing irons.", "tee_box": "forward" },
            { "hole_number": 3, "par": 4, "yards": 350, "stroke_index": 5, "description": "Straightaway par 4 with minimal hazards. Fairway is generous.", "tee_box": "forward" },
            { "hole_number": 4, "par": 4, "yards": 155, "stroke_index": 15, "description": "Elevated tee with wind factor. Green slopes from back to front.", "tee_box": "forward" },
            { "hole_number": 5, "par": 4, "yards": 365, "stroke_index": 3, "description": "Slight dogleg with bunkers protecting the green.", "tee_box": "forward" },
            { "hole_number": 6, "par": 5, "yards": 480, "stroke_index": 11, "description": "Short par 5 reachable in two. Good for practicing long approach shots.", "tee_box": "forward" },
            { "hole_number": 7, "par": 4, "yards": 340, "stroke_index": 7, "description": "Straight par 4 with water hazard on the right.", "tee_box": "forward" },
            { "hole_number": 8, "par": 3, "yards": 150, "stroke_index": 13, "description": "Short par 3 with bunkers around the green.", "tee_box": "forward" },
            { "hole_number": 9, "par": 4, "yards": 355, "stroke_index": 1, "description": "Finishing hole with elevated green. Approach shot requires extra club.", "tee_box": "forward" },
            { "hole_number": 10, "par": 4, "yards": 330, "stroke_index": 8, "description": "Short par 4 with wide fairway. Good scoring opportunity.", "tee_box": "forward" },
            { "hole_number": 11, "par": 4, "yards": 145, "stroke_index": 16, "description": "Short par 4 with large green. Wind can be a factor.", "tee_box": "forward" },
            { "hole_number": 12, "par": 4, "yards": 360, "stroke_index": 4, "description": "Straightaway par 4 with bunkers protecting the green.", "tee_box": "forward" },
            { "hole_number": 13, "par": 4, "yards": 160, "stroke_index": 14, "description": "Elevated tee with wind factor. Green slopes from back to front.", "tee_box": "forward" },
            { "hole_number": 14, "par": 4, "yards": 375, "stroke_index": 2, "description": "Longest par 4 on the course. Requires solid tee shot and approach.", "tee_box": "forward" },
            { "hole_number": 15, "par": 5, "yards": 490, "stroke_index": 12, "description": "Short par 5 reachable in two. Water hazard on the right.", "tee_box": "forward" },
            { "hole_number": 16, "par": 4, "yards": 345, "stroke_index": 6, "description": "Dogleg left with strategic bunkering. Position is key.", "tee_box": "forward" },
            { "hole_number": 17, "par": 4, "yards": 135, "stroke_index": 18, "description": "Shortest hole on the course. Good for practicing short irons.", "tee_box": "forward" },
            { "hole_number": 18, "par": 4, "yards": 350, "stroke_index": 10, "description": "Finishing hole with water hazard and dramatic green setting.", "tee_box": "forward" }
        ]),
        "total_yards": sum(hole['yards'] for hole in [
            { "hole_number": 1, "par": 4, "yards": 320, "stroke_index": 9, "description": "Short opening hole with wide fairway. Good for building confidence.", "tee_box": "forward" },
            { "hole_number": 2, "par": 3, "yards": 140, "stroke_index": 17, "description": "Short par 3 with large green. Good for practicing irons.", "tee_box": "forward" },
            { "hole_number": 3, "par": 4, "yards": 350, "stroke_index": 5, "description": "Straightaway par 4 with minimal hazards. Fairway is generous.", "tee_box": "forward" },
            { "hole_number": 4, "par": 4, "yards": 155, "stroke_index": 15, "description": "Elevated tee with wind factor. Green slopes from back to front.", "tee_box": "forward" },
            { "hole_number": 5, "par": 4, "yards": 365, "stroke_index": 3, "description": "Slight dogleg with bunkers protecting the green.", "tee_box": "forward" },
            { "hole_number": 6, "par": 5, "yards": 480, "stroke_index": 11, "description": "Short par 5 reachable in two. Good for practicing long approach shots.", "tee_box": "forward" },
            { "hole_number": 7, "par": 4, "yards": 340, "stroke_index": 7, "description": "Straight par 4 with water hazard on the right.", "tee_box": "forward" },
            { "hole_number": 8, "par": 3, "yards": 150, "stroke_index": 13, "description": "Short par 3 with bunkers around the green.", "tee_box": "forward" },
            { "hole_number": 9, "par": 4, "yards": 355, "stroke_index": 1, "description": "Finishing hole with elevated green. Approach shot requires extra club.", "tee_box": "forward" },
            { "hole_number": 10, "par": 4, "yards": 330, "stroke_index": 8, "description": "Short par 4 with wide fairway. Good scoring opportunity.", "tee_box": "forward" },
            { "hole_number": 11, "par": 4, "yards": 145, "stroke_index": 16, "description": "Short par 4 with large green. Wind can be a factor.", "tee_box": "forward" },
            { "hole_number": 12, "par": 4, "yards": 360, "stroke_index": 4, "description": "Straightaway par 4 with bunkers protecting the green.", "tee_box": "forward" },
            { "hole_number": 13, "par": 4, "yards": 160, "stroke_index": 14, "description": "Elevated tee with wind factor. Green slopes from back to front.", "tee_box": "forward" },
            { "hole_number": 14, "par": 4, "yards": 375, "stroke_index": 2, "description": "Longest par 4 on the course. Requires solid tee shot and approach.", "tee_box": "forward" },
            { "hole_number": 15, "par": 5, "yards": 490, "stroke_index": 12, "description": "Short par 5 reachable in two. Water hazard on the right.", "tee_box": "forward" },
            { "hole_number": 16, "par": 4, "yards": 345, "stroke_index": 6, "description": "Dogleg left with strategic bunkering. Position is key.", "tee_box": "forward" },
            { "hole_number": 17, "par": 4, "yards": 135, "stroke_index": 18, "description": "Shortest hole on the course. Good for practicing short irons.", "tee_box": "forward" },
            { "hole_number": 18, "par": 4, "yards": 350, "stroke_index": 10, "description": "Finishing hole with water hazard and dramatic green setting.", "tee_box": "forward" }
        ]),
        "course_rating": 68.5,
        "slope_rating": 115,
        "holes_data": [
            {
                "hole_number": 1,
                "par": 4,
                "yards": 320,
                "stroke_index": 9,
                "description": "Short opening hole with wide fairway. Good for building confidence.",
                "tee_box": "forward"
            },
                            {
                    "hole_number": 2,
                    "par": 3,
                    "yards": 140,
                    "stroke_index": 17,
                    "description": "Short par 3 with large green. Good for practicing irons.",
                    "tee_box": "forward"
                },
            {
                "hole_number": 3,
                "par": 4,
                "yards": 350,
                "stroke_index": 5,
                "description": "Straightaway par 4 with minimal hazards. Fairway is generous.",
                "tee_box": "forward"
            },
            {
                "hole_number": 4,
                "par": 4,
                "yards": 155,
                "stroke_index": 15,
                "description": "Elevated tee with wind factor. Green slopes from back to front.",
                "tee_box": "forward"
            },
            {
                "hole_number": 5,
                "par": 4,
                "yards": 365,
                "stroke_index": 3,
                "description": "Slight dogleg with bunkers protecting the green.",
                "tee_box": "forward"
            },
            {
                "hole_number": 6,
                "par": 5,
                "yards": 480,
                "stroke_index": 11,
                "description": "Short par 5 reachable in two. Good for practicing long approach shots.",
                "tee_box": "forward"
            },
            {
                "hole_number": 7,
                "par": 4,
                "yards": 340,
                "stroke_index": 7,
                "description": "Straight par 4 with water hazard on the right.",
                "tee_box": "forward"
            },
                            {
                    "hole_number": 8,
                    "par": 3,
                    "yards": 150,
                    "stroke_index": 13,
                    "description": "Short par 3 with bunkers around the green.",
                    "tee_box": "forward"
                },
            {
                "hole_number": 9,
                "par": 4,
                "yards": 355,
                "stroke_index": 1,
                "description": "Finishing hole with elevated green. Approach shot requires extra club.",
                "tee_box": "forward"
            },
            {
                "hole_number": 10,
                "par": 4,
                "yards": 330,
                "stroke_index": 8,
                "description": "Short par 4 with wide fairway. Good scoring opportunity.",
                "tee_box": "forward"
            },
                            {
                    "hole_number": 11,
                    "par": 4,
                    "yards": 145,
                    "stroke_index": 16,
                    "description": "Short par 4 with large green. Wind can be a factor.",
                    "tee_box": "forward"
                },
            {
                "hole_number": 12,
                "par": 4,
                "yards": 360,
                "stroke_index": 4,
                "description": "Straightaway par 4 with bunkers protecting the green.",
                "tee_box": "forward"
            },
                            {
                    "hole_number": 13,
                    "par": 4,
                    "yards": 160,
                    "stroke_index": 14,
                    "description": "Elevated tee with wind factor. Green slopes from back to front.",
                    "tee_box": "forward"
                },
            {
                "hole_number": 14,
                "par": 4,
                "yards": 375,
                "stroke_index": 2,
                "description": "Longest par 4 on the course. Requires solid tee shot and approach.",
                "tee_box": "forward"
            },
            {
                "hole_number": 15,
                "par": 5,
                "yards": 490,
                "stroke_index": 12,
                "description": "Short par 5 reachable in two. Water hazard on the right.",
                "tee_box": "forward"
            },
            {
                "hole_number": 16,
                "par": 4,
                "yards": 345,
                "stroke_index": 6,
                "description": "Dogleg left with strategic bunkering. Position is key.",
                "tee_box": "forward"
            },
            {
                "hole_number": 17,
                "par": 4,
                "yards": 135,
                "stroke_index": 18,
                "description": "Shortest hole on the course. Good for practicing short irons.",
                "tee_box": "forward"
            },
            {
                "hole_number": 18,
                "par": 4,
                "yards": 350,
                "stroke_index": 10,
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
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

            db.add(course)
            db.flush() # Flush to get the ID for the course before adding holes

            # Add holes for the course
            for hole_detail in course_data["holes_data"]:
                hole = Hole(
                    course_id=course.id,
                    hole_number=hole_detail["hole_number"],
                    par=hole_detail["par"],
                    yards=hole_detail["yards"],
                    handicap=hole_detail["stroke_index"],
                    description=hole_detail.get("description"),
                    tee_box=hole_detail.get("tee_box", "white")
                )
                db.add(hole)

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
