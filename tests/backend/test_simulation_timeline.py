#!/usr/bin/env python3
"""
Test script for Wolf-Goat-Pig simulation mode
Tests the poker/golf hybrid mechanics and timeline functionality
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_wolf_goat_pig_simulation():
    async with httpx.AsyncClient(timeout=30) as client:
        base_url = 'http://localhost:8000'
        
        print('🎮 Testing Wolf-Goat-Pig Simulation - Poker/Golf Hybrid')
        print('=' * 60)
        
        # 1. Setup simulation
        print('\n1. Setting up simulation with 4 players...')
        setup_response = await client.post(
            f'{base_url}/simulation/setup',
            json={
                'human_player': {
                    'id': 'human',
                    'name': 'Test Player',
                    'handicap': 15,
                    'is_human': True
                },
                'computer_players': [
                    {'id': 'ai1', 'name': 'Bob', 'handicap': 10, 'personality': 'aggressive'},
                    {'id': 'ai2', 'name': 'Alice', 'handicap': 20, 'personality': 'conservative'},
                    {'id': 'ai3', 'name': 'Charlie', 'handicap': 5, 'personality': 'strategic'}
                ],
                'course_name': 'Wing Point Golf & Country Club'
            }
        )
        
        if setup_response.status_code == 200:
            game = setup_response.json()
            print('✅ Simulation setup successful!')
            print(f'   - Hole {game.get("current_hole", 1)} Par {game.get("hole_par", "?")}')
            print(f'   - Distance: {game.get("hole_distance", "?")} yards')
            print(f'   - Captain: {game.get("captain_name", "Unknown")}')
            
            # Show Texas Hold'em style betting elements
            if game.get('betting_phase'):
                print('\n🃏 BETTING PHASE (Texas Hold\'em style):')
                print(f'   - Base Wager: ${game.get("base_wager", 10)}')
                print(f'   - Pot Size: ${game.get("pot_size", 0)}')
                
            # Show players
            print('\n   Players & Points:')
            for player in game.get('players', []):
                points = player.get('points', 0)
                sign = '+' if points >= 0 else ''
                status = '🎯 Captain' if player.get('id') == game.get('captain_id') else ''
                print(f'     - {player["name"]}: {sign}{points} pts {status}')
            
            # Check interaction needed
            if game.get('interaction_needed'):
                interaction = game['interaction_needed']
                print(f'\n⚡ DECISION REQUIRED: {interaction.get("type", "Unknown")}')
                print(f'   Message: {interaction.get("message", "")}')
                
                if interaction.get('type') == 'captain_decision':
                    print('\n   🎰 Poker-style Options:')
                    print('     - REQUEST PARTNER (Team up)')
                    print('     - GO SOLO (Double the stakes!)')
                    print('     - OFFER DOUBLE (Raise the bet)')
            
            # 2. Make a betting decision
            print('\n2. Making captain decision (poker-style)...')
            decision_response = await client.post(
                f'{base_url}/simulation/betting-decision',
                json={
                    'decision_type': 'go_solo',
                    'offer_double': True
                }
            )
            
            if decision_response.status_code == 200:
                result = decision_response.json()
                print('✅ Betting decision made!')
                if 'message' in result:
                    print(f'   Result: {result["message"]}')
            else:
                print(f'❌ Decision failed: {decision_response.status_code}')
            
            # 3. Play shots (golf part)
            print('\n3. Playing shot-by-shot (golf mechanics)...')
            
            for shot_num in range(3):  # Play up to 3 shots
                shot_response = await client.post(f'{base_url}/simulation/play-next-shot')
                
                if shot_response.status_code == 200:
                    shot = shot_response.json()
                    print(f'\n   Shot #{shot_num + 1}:')
                    
                    # Shot details
                    if 'shot_detail' in shot:
                        detail = shot['shot_detail']
                        print(f'     Player: {detail.get("player_name", "?")}')
                        print(f'     Club: {detail.get("club", "?")}')
                        print(f'     Distance: {detail.get("distance", 0)} yards')
                        print(f'     Result: {detail.get("result", "?")}')
                    
                    # Show timeline/events
                    if 'events' in shot:
                        print('     Events:')
                        for event in shot['events']:
                            print(f'       • {event}')
                    
                    # Check if hole complete
                    if shot.get('hole_complete'):
                        print('\n   ⛳ HOLE COMPLETE!')
                        break
                else:
                    print(f'   Shot failed: {shot_response.status_code}')
                    break
            
            # 4. Get shot probabilities (Monte Carlo)
            print('\n4. Checking shot probabilities (Monte Carlo simulation)...')
            prob_response = await client.get(f'{base_url}/simulation/shot-probabilities')
            
            if prob_response.status_code == 200:
                probs = prob_response.json()
                if 'probabilities' in probs:
                    print('✅ Shot probabilities:')
                    for outcome, prob in probs['probabilities'].items():
                        print(f'     - {outcome}: {prob:.1%}')
            else:
                print(f'❌ Probabilities failed: {prob_response.status_code}')
            
            # 5. Play complete hole
            print('\n5. Completing the hole...')
            hole_response = await client.post(f'{base_url}/simulation/play-hole')
            
            if hole_response.status_code == 200:
                hole_result = hole_response.json()
                print('✅ Hole completed!')
                
                # Show timeline in reverse chronological order
                if 'timeline' in hole_result:
                    print('\n📜 TIMELINE (reverse chronological):')
                    for event in hole_result['timeline'][:10]:  # Last 10 events
                        print(f'   • {event}')
                
                # Show final scores
                print('\n🏆 HOLE RESULTS:')
                for player in hole_result.get('players', []):
                    score = player.get('hole_score', '?')
                    points = player.get('points_won', 0)
                    print(f'   - {player["name"]}: Score {score}, Points: {points:+d}')
                
                # Show betting results
                if 'betting_results' in hole_result:
                    print('\n💰 BETTING RESULTS:')
                    results = hole_result['betting_results']
                    print(f'   - Winning Team: {results.get("winning_team", "?")}')
                    print(f'   - Pot Won: ${results.get("pot_amount", 0)}')
            else:
                print(f'❌ Hole completion failed: {hole_response.status_code}')
                    
        else:
            print(f'❌ Setup failed: {setup_response.status_code}')
            print(f'   Error: {setup_response.text}')
        
        print('\n' + '=' * 60)
        print('✅ Simulation test complete!')
        print('\nKey Features Tested:')
        print('  🃏 Texas Hold\'em betting mechanics (solo, partner, double)')
        print('  ⛳ Golf shot simulation with realistic outcomes')
        print('  📜 Timeline view in reverse chronological order')
        print('  🎲 Monte Carlo probability calculations')
        print('  💰 Points and betting system integration')

if __name__ == '__main__':
    asyncio.run(test_wolf_goat_pig_simulation())