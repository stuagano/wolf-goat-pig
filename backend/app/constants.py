"""
Application constants and configuration values
"""
from typing import Dict, List

# Default player configuration
DEFAULT_PLAYERS = [
    {"id": "p1", "name": "Bob", "points": 0, "handicap": 10.5, "strength": "Average"},
    {"id": "p2", "name": "Scott", "points": 0, "handicap": 15, "strength": "Average"},
    {"id": "p3", "name": "Vince", "points": 0, "handicap": 8, "strength": "Average"},
    {"id": "p4", "name": "Mike", "points": 0, "handicap": 20.5, "strength": "Average"},
]

# Example stroke index for 18 holes (1 = hardest, 18 = easiest)
DEFAULT_HOLE_STROKE_INDEXES = [1, 15, 7, 13, 3, 17, 9, 11, 5, 2, 16, 8, 14, 4, 18, 10, 12, 6]

# Enhanced course data with yards for simulation mode
DEFAULT_COURSES = {
    "Wing Point": [
        {"hole_number": 1, "stroke_index": 5, "par": 4, "yards": 420, "description": "Dogleg right with water on right"},
        {"hole_number": 2, "stroke_index": 13, "par": 4, "yards": 385, "description": "Straight away, slight uphill"},
        {"hole_number": 3, "stroke_index": 1, "par": 5, "yards": 580, "description": "Long par 5 with fairway bunkers"},
        {"hole_number": 4, "stroke_index": 17, "par": 3, "yards": 165, "description": "Short par 3 over water"},
        {"hole_number": 5, "stroke_index": 7, "par": 4, "yards": 445, "description": "Long par 4 with OB left"},
        {"hole_number": 6, "stroke_index": 11, "par": 4, "yards": 395, "description": "Slight dogleg left"},
        {"hole_number": 7, "stroke_index": 15, "par": 5, "yards": 520, "description": "Reachable par 5 in two"},
        {"hole_number": 8, "stroke_index": 3, "par": 3, "yards": 185, "description": "Long par 3 with deep bunkers"},
        {"hole_number": 9, "stroke_index": 9, "par": 4, "yards": 410, "description": "Finishing hole with elevated green"},
        {"hole_number": 10, "stroke_index": 2, "par": 4, "yards": 455, "description": "Championship tee, very challenging"},
        {"hole_number": 11, "stroke_index": 16, "par": 5, "yards": 545, "description": "Three-shot par 5 with creek"},
        {"hole_number": 12, "stroke_index": 8, "par": 3, "yards": 175, "description": "Elevated tee, wind factor"},
        {"hole_number": 13, "stroke_index": 14, "par": 4, "yards": 375, "description": "Short par 4, drivable green"},
        {"hole_number": 14, "stroke_index": 4, "par": 4, "yards": 435, "description": "Narrow fairway, difficult approach"},
        {"hole_number": 15, "stroke_index": 18, "par": 5, "yards": 565, "description": "Longest hole on course"},
        {"hole_number": 16, "stroke_index": 10, "par": 4, "yards": 425, "description": "Risk/reward hole"},
        {"hole_number": 17, "stroke_index": 12, "par": 3, "yards": 155, "description": "Island green signature hole"},
        {"hole_number": 18, "stroke_index": 6, "par": 4, "yards": 415, "description": "Dramatic finishing hole"},
    ],
    "Championship Links": [
        {"hole_number": i+1, "stroke_index": ((i * 7) % 18) + 1, "par": 4 if i % 3 != 1 else (3 if i % 6 == 1 else 5), 
         "yards": 350 + (i * 15) + (50 if i % 3 == 2 else 0), "description": f"Hole {i+1} championship layout"} 
        for i in range(18)
    ],
}

# Game configuration constants
GAME_CONSTANTS = {
    "MAX_HOLES": 18,
    "MIN_PLAYERS": 4,
    "MAX_PLAYERS": 6,
    "DEFAULT_BASE_WAGER": 1,
    "HOEPFINGER_START_HOLE": 17,  # 4-man game
    "VINNIE_VARIATION_START_HOLE": 13,
    "DEFAULT_GAME_PHASE": "Regular",
    "DEFAULT_STATUS_MESSAGE": "Time to toss the tees!",
}

# Validation constants
VALIDATION_LIMITS = {
    "MIN_PAR": 3,
    "MAX_PAR": 6,
    "MIN_HANDICAP": 1,
    "MAX_HANDICAP": 18,
    "MIN_YARDS": 100,
    "MAX_YARDS": 700,
    "MIN_COURSE_NAME_LENGTH": 3,
    "MIN_TOTAL_PAR": 70,
    "MAX_TOTAL_PAR": 74,
    "MIN_SIMULATIONS": 1,
    "MAX_SIMULATIONS": 1000,
    "MIN_DETAILED_GAMES": 1,
    "MAX_DETAILED_GAMES": 100,
}

# Player strength mappings
STRENGTH_THRESHOLDS = {
    "Expert": (0, 5),
    "Strong": (5, 12),
    "Average": (12, 20),
    "Beginner": (20, 36),
}

# Computer player personalities
PERSONALITY_DESCRIPTIONS = {
    "aggressive": "Takes risks, offers doubles frequently, goes solo when behind",
    "conservative": "Plays it safe, selective about partnerships and doubles",
    "balanced": "Makes steady, reasonable decisions with some variance",
    "strategic": "Considers game situation, hole difficulty, and position carefully"
}

# Suggested computer opponents
SUGGESTED_OPPONENTS = [
    {
        "name": "Tiger Bot",
        "handicap": 2.0,
        "personality": "aggressive",
        "description": "Low handicap player who takes risks and puts pressure on opponents"
    },
    {
        "name": "Strategic Sam",
        "handicap": 8.5,
        "personality": "strategic", 
        "description": "Mid-handicap player who makes calculated decisions"
    },
    {
        "name": "Conservative Carl",
        "handicap": 15.0,
        "personality": "conservative",
        "description": "Higher handicap player who plays it safe and steady"
    },
    {
        "name": "Balanced Betty",
        "handicap": 12.0,
        "personality": "balanced",
        "description": "Well-rounded player with consistent decision making"
    },
    {
        "name": "Risky Rick",
        "handicap": 18.5,
        "personality": "aggressive",
        "description": "High handicap player who compensates with bold betting"
    },
    {
        "name": "Steady Steve",
        "handicap": 10.0,
        "personality": "conservative", 
        "description": "Reliable mid-handicap player who avoids unnecessary risks"
    }
]

# Expected yards by par for difficulty calculations
EXPECTED_YARDS_BY_PAR = {3: 150, 4: 400, 5: 550}