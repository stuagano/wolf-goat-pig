from .database import SessionLocal, init_db
from .models import Rule

# List of rules to insert (add as many as you want)
RULES = [
    {
        "title": "Order of Play",
        "description": "The Captain is determined randomly on the first tee. The order rotates each hole."
    },
    {
        "title": "Going Solo",
        "description": "Each player must go solo at least once in the first 16 holes in a 4-man game."
    },
    {
        "title": "Aardvark Rule",
        "description": "In a 5-man game, the fifth player is the Aardvark and may join a team or go solo."
    },
    {
        "title": "Hoepfinger Phase",
        "description": "Special phase where the player furthest down chooses their spot in the rotation."
    },
    {
        "title": "Betting - Double",
        "description": "Teams may offer to double the stakes at any time after teams are formed."
    },
    {
        "title": "Carry-Over",
        "description": "If a hole is halved, the wager is carried over and doubled for the next hole."
    },
    {
        "title": "Joe's Special",
        "description": "During Hoepfinger, the Goat may set the starting value of the hole to 2, 4, or 8 quarters."
    },
    {
        "title": "Good But Not In",
        "description": "A conceded putt is 'good' for score but betting may continue until a ball is holed."
    },
    {
        "title": "Handicaps",
        "description": "Handicaps are calculated as the difference from the lowest player's handicap."
    },
    {
        "title": "Creecher Feature",
        "description": "Highest 6 handicap holes are played at half stroke for each player."
    }
]

def main():
    init_db()
    db = SessionLocal()
    for rule in RULES:
        # Avoid duplicate insertion by checking for existing title
        if not db.query(Rule).filter_by(title=rule["title"]).first():
            db.add(Rule(title=rule["title"], description=rule["description"]))
    db.commit()
    db.close()
    print("Rules seeded successfully.")

if __name__ == "__main__":
    main()
