#!/usr/bin/env python3
"""
Simple test script for the Player class.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.domain.player import Player, HandicapCategory, StrengthLevel


def test_player_creation():
    """Test basic player creation and validation."""
    print("🧪 Testing Player Creation...")
    
    # Test valid player creation
    player = Player(id="p1", name="Bob", handicap=10.5)
    assert player.id == "p1"
    assert player.name == "Bob"
    assert player.handicap == 10.5
    assert player.points == 0
    print("✅ Valid player creation works")
    
    # Test handicap category
    assert player.get_handicap_category() == HandicapCategory.LOW
    print("✅ Handicap category calculation works")
    
    # Test strength level
    assert player.get_strength_level() == StrengthLevel.AVERAGE  # 10.5 handicap is > 10, so AVERAGE
    print("✅ Strength level calculation works")
    
    # Test expected drive distance
    assert player.get_expected_drive_distance() == 245
    print("✅ Expected drive distance calculation works")


def test_player_validation():
    """Test player validation rules."""
    print("\n🧪 Testing Player Validation...")
    
    # Test empty ID
    try:
        Player(id="", name="Bob", handicap=10)
        assert False, "Should have raised ValueError for empty ID"
    except ValueError:
        print("✅ Empty ID validation works")
    
    # Test empty name
    try:
        Player(id="p1", name="", handicap=10)
        assert False, "Should have raised ValueError for empty name"
    except ValueError:
        print("✅ Empty name validation works")
    
    # Test negative handicap
    try:
        Player(id="p1", name="Bob", handicap=-1)
        assert False, "Should have raised ValueError for negative handicap"
    except ValueError:
        print("✅ Negative handicap validation works")
    
    # Test excessive handicap
    try:
        Player(id="p1", name="Bob", handicap=55)
        assert False, "Should have raised ValueError for excessive handicap"
    except ValueError:
        print("✅ Excessive handicap validation works")


def test_player_methods():
    """Test player methods and state management."""
    print("\n🧪 Testing Player Methods...")
    
    player = Player(id="p1", name="Bob", handicap=15)
    
    # Test points management
    player.add_points(5)
    assert player.points == 5
    assert player.get_points_change() == 5
    print("✅ Points management works")
    
    # Test hole score recording
    player.record_hole_score(1, 4)
    assert player.get_hole_score(1) == 4
    assert player.get_hole_score(2) is None
    print("✅ Hole score management works")
    
    # Test float usage
    assert player.can_use_float() == True
    assert player.use_float() == True
    assert player.can_use_float() == False
    assert player.use_float() == False
    player.reset_float()
    assert player.can_use_float() == True
    print("✅ Float management works")


def test_player_serialization():
    """Test player serialization and deserialization."""
    print("\n🧪 Testing Player Serialization...")
    
    player = Player(id="p1", name="Bob", handicap=12)
    player.add_points(3)
    player.record_hole_score(1, 4)
    
    # Test to_dict
    player_dict = player.to_dict()
    assert player_dict["id"] == "p1"
    assert player_dict["name"] == "Bob"
    assert player_dict["handicap"] == 12
    assert player_dict["points"] == 3
    assert player_dict["hole_scores"] == {1: 4}
    print("✅ to_dict works")
    
    # Test from_dict
    new_player = Player.from_dict(player_dict)
    assert new_player.id == player.id
    assert new_player.name == player.name
    assert new_player.handicap == player.handicap
    assert new_player.points == player.points
    assert new_player.get_hole_score(1) == 4
    print("✅ from_dict works")


def test_player_comparison():
    """Test player comparison and hashing."""
    print("\n🧪 Testing Player Comparison...")
    
    player1 = Player(id="p1", name="Bob", handicap=10)
    player2 = Player(id="p1", name="Bob", handicap=10)
    player3 = Player(id="p2", name="Alice", handicap=15)
    
    # Test equality
    assert player1 == player2
    assert player1 != player3
    print("✅ Player equality works")
    
    # Test hashing
    player_set = {player1, player2, player3}
    assert len(player_set) == 2  # player1 and player2 are equal
    print("✅ Player hashing works")


def test_handicap_categories():
    """Test different handicap categories."""
    print("\n🧪 Testing Handicap Categories...")
    
    # Test scratch golfer
    scratch = Player(id="s1", name="Scratch", handicap=2)
    assert scratch.get_handicap_category() == HandicapCategory.SCRATCH
    assert scratch.get_strength_level() == StrengthLevel.EXCELLENT
    print("✅ Scratch golfer classification works")
    
    # Test beginner
    beginner = Player(id="b1", name="Beginner", handicap=30)
    assert beginner.get_handicap_category() == HandicapCategory.BEGINNER
    assert beginner.get_strength_level() == StrengthLevel.POOR
    print("✅ Beginner classification works")


if __name__ == "__main__":
    print("🚀 Starting Player Class Tests...\n")
    
    try:
        test_player_creation()
        test_player_validation()
        test_player_methods()
        test_player_serialization()
        test_player_comparison()
        test_handicap_categories()
        
        print("\n🎉 All Player class tests passed!")
        print("✅ Player class is ready for integration")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 