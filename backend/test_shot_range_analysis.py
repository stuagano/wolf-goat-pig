#!/usr/bin/env python3
"""
Test the poker-style shot range analysis system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.domain.player import Player
from app.domain.shot_result import ShotResult
from app.domain.shot_range_analysis import (
    ShotRangeAnalyzer, RiskProfile, ShotType, 
    ShotRangeMatrix, analyze_shot_decision
)
import json


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f"🎯 {title}")
    print(f"{'=' * 60}")


def test_basic_range_analysis():
    """Test basic shot range analysis"""
    print_section("Basic Shot Range Analysis")
    
    # Create a test player
    player = Player(id="p1", name="Tiger Woods", handicap=0.0)
    
    # Create a shot result (approach from fairway)
    shot = ShotResult(
        player=player,
        drive=280,
        lie="fairway",
        remaining=150,
        shot_quality="good",
        hole_number=10
    )
    
    # Get range analysis
    analysis = shot.get_shot_range_analysis()
    
    print(f"\n📊 Shot Situation:")
    print(f"   Player: {player.name} (HC: {player.handicap})")
    print(f"   Lie: {shot.lie}")
    print(f"   Distance: {shot.remaining} yards")
    
    print(f"\n🎰 Recommended Shot:")
    rec = analysis["recommended_shot"]
    print(f"   Type: {rec['type']}")
    print(f"   Success Rate: {rec['success_rate']}")
    print(f"   Risk Level: {rec['risk_level']}")
    print(f"   Expected Value: {rec['expected_value']:+.2f} strokes")
    print(f"   Equity vs Field: {rec['equity_vs_field']}")
    
    print(f"\n📈 All Available Ranges:")
    for r in analysis["all_ranges"]:
        print(f"   {r['type']}: {r['success_rate']} success, {r['risk']} risk, EV: {r['ev']}")
    
    print(f"\n🎯 Player Style: {analysis['player_style']['profile']}")
    print(f"   {analysis['player_style']['description']}")


def test_pressure_situations():
    """Test range analysis in pressure situations"""
    print_section("Pressure Situation Analysis")
    
    situations = [
        {
            "name": "18th Hole, Tournament on the Line",
            "lie": "rough",
            "distance": 175,
            "handicap": 5.0,
            "hole_number": 18,
            "score_differential": -1
        },
        {
            "name": "Safe Lead, Protect Mode",
            "lie": "fairway",
            "distance": 100,
            "handicap": 10.0,
            "hole_number": 17,
            "score_differential": 3
        },
        {
            "name": "Desperate Comeback Needed",
            "lie": "fairway",
            "distance": 200,
            "handicap": 15.0,
            "hole_number": 16,
            "score_differential": -4
        }
    ]
    
    for sit in situations:
        print(f"\n🎭 Scenario: {sit['name']}")
        
        analysis = analyze_shot_decision(
            current_lie=sit["lie"],
            distance=sit["distance"],
            player_handicap=sit["handicap"],
            hole_number=sit["hole_number"],
            score_differential=sit["score_differential"]
        )
        
        rec = analysis["recommended_shot"]
        print(f"   Recommended: {rec['type']} ({rec['risk_level']} risk)")
        print(f"   Success Rate: {rec['success_rate']}")
        print(f"   Expected Value: {rec['expected_value']:+.2f}")
        
        # Show GTO vs Exploitative
        print(f"   GTO Play: {analysis['gto_recommendation']['type']}")
        print(f"   Exploitative: {analysis['exploitative_play']['type']}")
        
        # Strategic advice
        print(f"   Advice:")
        for advice in analysis["strategic_advice"][:2]:
            print(f"     - {advice}")


def test_player_styles():
    """Test different player risk profiles"""
    print_section("Player Style Analysis")
    
    styles = [
        (RiskProfile.NIT, 25.0, "High Handicap Conservative"),
        (RiskProfile.TAG, 12.0, "Mid Handicap Balanced"),
        (RiskProfile.LAG, 5.0, "Low Handicap Aggressive"),
        (RiskProfile.MANIAC, 0.0, "Scratch Player Full Range")
    ]
    
    # Same situation, different player styles
    game_situation = {
        "hole_number": 9,
        "partnership_formed": True,
        "match_critical": False,
        "hazards_present": True
    }
    
    print(f"\n📍 Situation: 150 yards from fairway, water hazard in play")
    
    for style, handicap, desc in styles:
        print(f"\n🎲 {desc}:")
        
        matrix = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=150,
            player_handicap=handicap,
            game_situation=game_situation
        )
        
        recommended = matrix.get_recommended_range(style)
        if recommended:
            print(f"   Plays: {recommended.shot_type.value}")
            print(f"   Success: {recommended.success_probability * 100:.1f}%")
            print(f"   Risk Factor: {recommended.risk_factor * 100:.0f}%")
            print(f"   Pot Odds Required: {recommended.pot_odds_required * 100:.0f}%")
        
        # Show range distribution
        dist = matrix.get_range_distribution()
        print(f"   Range Width: {len([d for d in dist.values() if d > 0])} different shots")


def test_3bet_ranges():
    """Test ultra-aggressive '3-bet' ranges"""
    print_section("3-Bet Range Analysis (Ultra-Aggressive Plays)")
    
    # Scenario where aggression might pay off
    game_situation = {
        "hole_number": 13,
        "partnership_formed": False,
        "match_critical": True,
        "trailing_significantly": True,
        "hero_shot_possible": True
    }
    
    analysis = ShotRangeAnalyzer.analyze_shot_selection(
        lie_type="fairway",
        distance_to_pin=240,
        player_handicap=8.0,
        game_situation=game_situation
    )
    
    print(f"\n🔥 Situation: Must make a move, 240 yards out")
    print(f"\n💪 3-Bet Ranges (Maximum Aggression):")
    
    for r in analysis["3bet_ranges"]:
        print(f"   {r['type']}:")
        print(f"     - Fold Equity: {r['fold_equity']}")
        print(f"     - Bluff Frequency: {r['bluff_frequency']}")
    
    # Show all ranges with poker metrics
    print(f"\n📊 Complete Range Analysis:")
    for r in analysis["all_ranges"]:
        print(f"\n   {r['type']}:")
        print(f"     Success: {r['success_rate']} | Risk: {r['risk']}")
        print(f"     EV: {r['ev']} | Equity: {r['equity']}")
        print(f"     Pot Odds Needed: {r['pot_odds_needed']}")


def test_shot_progression_integration():
    """Test integration with shot progression"""
    print_section("Shot Progression with Range Analysis")
    
    # Simulate a few shots with range analysis
    player = Player(id="human", name="Phil Mickelson", handicap=2.0)
    
    shots = [
        ("fairway", 450, "First shot - Driver decision"),
        ("fairway", 180, "Approach shot - Risk the water?"),
        ("rough", 40, "Short game - Flop shot or safe chip?")
    ]
    
    for lie, distance, desc in shots:
        print(f"\n🏌️ {desc}")
        
        shot = ShotResult(
            player=player,
            drive=450 - distance if lie == "fairway" else 230,
            lie=lie,
            remaining=distance,
            shot_quality="average",
            hole_number=12,
            pressure_factor=0.6
        )
        
        analysis = shot.get_shot_range_analysis()
        
        # Show recommended play
        rec = analysis["recommended_shot"]
        print(f"   Recommended: {rec['type']}")
        print(f"   Risk/Reward: {rec['risk_level']} risk for {rec['expected_value']:+.2f} EV")
        
        # Show top 3 options
        print(f"   Options:")
        for i, r in enumerate(analysis["all_ranges"][:3]):
            print(f"     {i+1}. {r['type']}: {r['equity']} equity")


def main():
    """Run all tests"""
    print("\n🎰 WOLF GOAT PIG - POKER STYLE SHOT RANGE ANALYSIS")
    print("=" * 60)
    
    test_basic_range_analysis()
    test_pressure_situations()
    test_player_styles()
    test_3bet_ranges()
    test_shot_progression_integration()
    
    print(f"\n{'=' * 60}")
    print("✅ Shot range analysis complete!")
    print("🎯 Players now have poker-style decision making for shot selection")
    print("=" * 60)


if __name__ == "__main__":
    main()