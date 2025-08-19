#!/usr/bin/env python3
"""
Test script for Monte Carlo simulation functionality
"""

import requests
import json
import time

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_monte_carlo_simulation():
    """Test the Monte Carlo simulation endpoint"""
    print("🎲 Testing Monte Carlo Simulation")
    print("=" * 50)
    
    # Test configuration
    stuart_config = {
        "human_player": {
            "id": "human",
            "name": "Stuart",
            "handicap": 10.0
        },
        "computer_players": [
            {
                "id": "comp1",
                "name": "Tiger Bot",
                "handicap": 2.0,
                "personality": "aggressive"
            },
            {
                "id": "comp2", 
                "name": "Strategic Sam",
                "handicap": 8.5,
                "personality": "strategic"
            },
            {
                "id": "comp3",
                "name": "Conservative Carl", 
                "handicap": 15.0,
                "personality": "conservative"
            }
        ],
        "num_simulations": 25,  # Start with smaller number for testing
        "course_name": None
    }
    
    print(f"Testing with {stuart_config['num_simulations']} simulations...")
    print(f"Stuart (handicap {stuart_config['human_player']['handicap']}) vs:")
    for comp in stuart_config['computer_players']:
        print(f"  - {comp['name']} (handicap {comp['handicap']}, {comp['personality']})")
    print()
    
    try:
        # Run Monte Carlo simulation
        print("🚀 Running Monte Carlo simulation...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/simulation/monte-carlo",
            json=stuart_config,
            headers={"Content-Type": "application/json"}
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Simulation completed in {duration:.2f} seconds")
            print()
            
            # Display results
            print("📊 SIMULATION RESULTS")
            print("=" * 30)
            
            # Key insights
            print("🎯 Key Insights:")
            for insight in results['insights']:
                print(f"  • {insight}")
            print()
            
            # Player statistics
            print("🏆 Player Statistics:")
            stats = results['summary']['player_statistics']
            
            # Sort players by average score
            sorted_players = sorted(stats.items(), 
                                  key=lambda x: x[1]['average_score'], 
                                  reverse=True)
            
            for rank, (player_id, player_stats) in enumerate(sorted_players, 1):
                player_name = stuart_config['human_player']['name'] if player_id == 'human' else \
                             next(cp['name'] for cp in stuart_config['computer_players'] if cp['id'] == player_id)
                
                print(f"  #{rank} {player_name}:")
                print(f"    • Wins: {player_stats['wins']} ({player_stats['win_percentage']:.1f}%)")
                print(f"    • Average Score: {player_stats['average_score']:+.1f}")
                print(f"    • Best Game: {player_stats['best_score']:+d}")
                print(f"    • Worst Game: {player_stats['worst_score']:+d}")
                
                # Show top 3 most common scores
                score_dist = player_stats['score_distribution']
                top_scores = sorted(score_dist.items(), key=lambda x: x[1], reverse=True)[:3]
                if top_scores:
                    print(f"    • Common Scores: ", end="")
                    score_strings = [f"{score}({count}x)" for score, count in top_scores]
                    print(", ".join(score_strings))
                print()
            
            # Analysis
            stuart_stats = stats['human']
            print("📈 ANALYSIS FOR STUART:")
            print("=" * 25)
            
            # Win rate analysis
            if stuart_stats['win_percentage'] > 30:
                print("🎯 Excellent performance! You're competing well at this level.")
            elif stuart_stats['win_percentage'] > 20:
                print("👍 Good performance. You're holding your own against these opponents.")
            elif stuart_stats['win_percentage'] > 10:
                print("📚 Room for improvement. Focus on partnership selection and course management.")
            else:
                print("🎯 Consider playing with opponents closer to your handicap level.")
            
            # Scoring analysis
            avg_score = stuart_stats['average_score']
            if avg_score > 2:
                print(f"💰 Strong scoring average: {avg_score:+.1f} points per game")
            elif avg_score > 0:
                print(f"✅ Positive scoring average: {avg_score:+.1f} points per game")
            elif avg_score > -3:
                print(f"📉 Slightly negative average: {avg_score:+.1f} points per game")
            else:
                print(f"🔄 Work on strategy. Average: {avg_score:+.1f} points per game")
            
            # Consistency analysis
            score_range = stuart_stats['best_score'] - stuart_stats['worst_score']
            if score_range < 8:
                print("📊 Very consistent performance across games")
            elif score_range < 15:
                print("📈 Reasonably consistent performance")
            else:
                print("🎢 Variable performance - work on consistent strategy")
            
            print()
            print("💡 RECOMMENDATIONS:")
            if stuart_stats['win_percentage'] < 15:
                print("  • Focus on partnership selection with players closer to your handicap")
                print("  • Be more conservative on difficult holes (stroke index 1-6)")
            if stuart_stats['average_score'] < -1:
                print("  • Avoid going solo without stroke advantage")
                print("  • Be selective about accepting doubles")
            if score_range > 12:
                print("  • Develop more consistent betting strategy")
                print("  • Pay attention to hole difficulty and your stroke advantages")
            
        else:
            print(f"❌ Simulation failed with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the backend server is running on port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_larger_simulation():
    """Test with a larger number of simulations"""
    print("\n" + "="*60)
    print("🎲 LARGER MONTE CARLO SIMULATION (100 games)")
    print("="*60)
    
    # Configuration for larger test
    config = {
        "human_player": {
            "id": "human",
            "name": "Stuart",
            "handicap": 12.0  # Slightly higher handicap
        },
        "computer_players": [
            {
                "id": "comp1",
                "name": "Pro Player",
                "handicap": 3.0,
                "personality": "strategic"
            },
            {
                "id": "comp2",
                "name": "Club Champion", 
                "handicap": 7.0,
                "personality": "aggressive"
            },
            {
                "id": "comp3",
                "name": "Weekend Warrior",
                "handicap": 16.0,
                "personality": "conservative"
            }
        ],
        "num_simulations": 100,
        "course_name": None
    }
    
    try:
        print("🚀 Running 100-game simulation...")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/simulation/monte-carlo",
            json=config,
            headers={"Content-Type": "application/json"}
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ 100-game simulation completed in {duration:.2f} seconds")
            
            # Quick summary
            stats = results['summary']['player_statistics']
            stuart_stats = stats['human']
            
            print(f"\n📊 QUICK RESULTS FOR STUART:")
            print(f"  • Win Rate: {stuart_stats['win_percentage']:.1f}%")
            print(f"  • Average Score: {stuart_stats['average_score']:+.1f}")
            print(f"  • Score Range: {stuart_stats['worst_score']:+d} to {stuart_stats['best_score']:+d}")
            
            # Expected outcomes based on handicap differences
            print(f"\n🎯 HANDICAP ANALYSIS:")
            print(f"  Stuart (12.0) vs Pro Player (3.0): {9.0} stroke difference")
            print(f"  Stuart (12.0) vs Club Champion (7.0): {5.0} stroke difference") 
            print(f"  Stuart (12.0) vs Weekend Warrior (16.0): {4.0} stroke advantage")
            print(f"  Expected: Stuart should struggle against pros, compete with similar handicaps")
            
            # Performance vs expectations
            if stuart_stats['win_percentage'] > 20:
                print("  ✅ Performing better than handicap would suggest!")
            elif stuart_stats['win_percentage'] > 15:
                print("  👍 Competitive performance given handicap differences")
            else:
                print("  📚 Consider more conservative strategy against lower handicap players")
                
        else:
            print(f"❌ Large simulation failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error in large simulation: {e}")

if __name__ == "__main__":
    print("🎮 Wolf Goat Pig Monte Carlo Simulation Test")
    print("🚀 Starting backend test suite...")
    print()
    
    # Test smaller simulation first
    test_monte_carlo_simulation()
    
    # Ask if user wants to run larger simulation
    response = input("\nRun larger 100-game simulation? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        test_larger_simulation()
    
    print("\n✅ Monte Carlo testing complete!")
    print("\n💡 To access the web interface:")
    print("   1. Make sure backend is running: cd backend && python -m uvicorn app.main:app --reload")
    print("   2. Start frontend: cd frontend && npm start") 
    print("   3. Navigate to: http://localhost:3000/monte-carlo")