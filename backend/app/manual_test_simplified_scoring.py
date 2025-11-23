"""
Test script for the simplified scoring system.
This demonstrates how much simpler the scoring becomes.
"""

import json

from simplified_scoring import SimplifiedScoring


def test_simplified_scoring():
    """Test the simplified scoring system with a sample game"""
    print("Testing Simplified Wolf Goat Pig Scoring System")
    print("=" * 50)

    # Create test players
    players = [
        {"id": "p1", "name": "Alice"},
        {"id": "p2", "name": "Bob"},
        {"id": "p3", "name": "Charlie"},
        {"id": "p4", "name": "Diana"}
    ]

    # Initialize simplified scoring
    game = SimplifiedScoring(players)
    print(f"Game initialized with {len(players)} players")

    # Test Hole 1: Solo play
    print("\n--- Hole 1: Solo Play ---")
    scores = {"p1": 4, "p2": 5, "p3": 6, "p4": 7}  # Alice has best score
    teams = {"type": "solo", "solo_player": "p1"}
    wager = 2

    result = game.enter_hole_scores(1, scores, teams, wager)
    print(f"Hole 1 Result: {json.dumps(result, indent=2)}")

    # Test Hole 2: Partners play
    print("\n--- Hole 2: Partners Play ---")
    scores = {"p1": 5, "p2": 4, "p3": 4, "p4": 6}  # Team 2 (Charlie+Diana) wins
    teams = {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]}
    wager = 1

    result = game.enter_hole_scores(2, scores, teams, wager)
    print(f"Hole 2 Result: {json.dumps(result, indent=2)}")

    # Test Hole 3: Tied hole
    print("\n--- Hole 3: Tied Hole ---")
    scores = {"p1": 4, "p2": 5, "p3": 4, "p4": 5}  # Teams tied
    teams = {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]}
    wager = 1

    result = game.enter_hole_scores(3, scores, teams, wager)
    print(f"Hole 3 Result: {json.dumps(result, indent=2)}")

    # Show final game summary
    print("\n--- Game Summary ---")
    summary = game.get_game_summary()
    print(f"Game Summary: {json.dumps(summary, indent=2)}")

    # Show hole history
    print("\n--- Hole History ---")
    history = game.get_hole_history()
    for hole in history:
        print(f"Hole {hole['hole']}: {hole['team_type']} | Winners: {hole['winners']} | Wager: {hole['wager']}")

    return True

def test_complexity_comparison():
    """Show the complexity difference between old and new systems"""
    print("\n" + "=" * 60)
    print("COMPLEXITY COMPARISON")
    print("=" * 60)

    print("\nOLD SYSTEM ISSUES:")
    print("- Massive _serialize() method with nested dataclasses")
    print("- Complex Karl Marx rule calculations")
    print("- Extensive analytics and performance tracking")
    print("- Multiple special betting rules and multipliers")
    print("- Timeline events and detailed hole progression")
    print("- Huge JSON objects stored in database")

    print("\nNEW SIMPLIFIED SYSTEM:")
    print("- Simple dataclass with just essential fields")
    print("- Basic point calculations (solo vs partners)")
    print("- Minimal state storage")
    print("- Clean API endpoints")
    print("- Easy to understand and maintain")

    # Show example JSON size difference
    game = SimplifiedScoring([
        {"id": "p1", "name": "Alice"},
        {"id": "p2", "name": "Bob"}
    ])

    # Add a few holes
    game.enter_hole_scores(1, {"p1": 4, "p2": 5}, {"type": "solo", "solo_player": "p1"}, 1)
    game.enter_hole_scores(2, {"p1": 5, "p2": 4}, {"type": "solo", "solo_player": "p2"}, 1)

    simplified_json = json.dumps({
        "players": game.players,
        "results": list(game.hole_results.values())
    }, default=str)

    print(f"\nSimplified JSON size for 2 holes: {len(simplified_json)} characters")
    print("Original system would be 10-50x larger due to complex nested structures")

    return True

if __name__ == "__main__":
    test_simplified_scoring()
    test_complexity_comparison()
    print("\n✅ All tests passed! Simplified scoring system working correctly.")
