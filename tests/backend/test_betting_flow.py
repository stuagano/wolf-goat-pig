#!/usr/bin/env python3
"""Test the improved betting/partnership flow integration"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.wolf_goat_pig_simulation import WolfGoatPigSimulation, WGPPlayer

def test_realistic_user_journey():
    """Test the realistic Wolf-Goat-Pig user journey"""
    
    # Create simulation with 4 players (classic Wolf-Goat-Pig)
    players = [
        WGPPlayer(id="human", name="Stuart", handicap=18),
        WGPPlayer(id="player2", name="Alex", handicap=5), 
        WGPPlayer(id="player3", name="Sam", handicap=18),
        WGPPlayer(id="player4", name="Ace", handicap=3)
    ]
    
    sim = WolfGoatPigSimulation(player_count=4, players=players)
    sim.enable_shot_progression()
    
    print("🏌️ Wolf-Goat-Pig Realistic User Journey Test")
    print("=" * 60)
    print("Scenario: All players on tee box, Stuart is captain")
    print()
    
    # Simulate the realistic flow:
    # 1. Captain hits first (Stuart)
    # 2. Next player hits (Alex) 
    # 3. Partnership decision opportunity
    # 4. Continue with doubles/flushes during play
    
    hole_state = sim.hole_states.get(sim.current_hole)
    if not hole_state:
        print("❌ No hole state found")
        return
    
    captain_id = hole_state.teams.captain
    captain_name = sim._get_player_name(captain_id)
    print(f"👑 Captain: {captain_name} ({captain_id})")
    print(f"🎯 Teams status: {hole_state.teams.type}")
    print()
    
    # Step 1: Captain hits tee shot  
    print("Step 1: Captain hits tee shot")
    print("-" * 30)
    result1 = sim.simulate_shot(captain_id)
    shot1 = result1["shot_result"]
    print(f"🏌️ {captain_name} hits {shot1['shot_quality']} tee shot → {shot1['distance_to_pin']:.0f} yards")
    
    if shot1['made_shot']:
        print("   🎉 Holed out! (rare but happens)")
    print()
    
    # Step 2: Next player hits 
    print("Step 2: Next player hits")
    print("-" * 30)
    
    next_player = hole_state.next_player_to_hit
    if next_player:
        result2 = sim.simulate_shot(next_player)
        shot2 = result2["shot_result"] 
        player_name = sim._get_player_name(next_player)
        print(f"🏌️ {player_name} hits {shot2['shot_quality']} tee shot → {shot2['distance_to_pin']:.0f} yards")
        print()
        
        # Step 3: Partnership decision should now be available
        print("Step 3: Partnership Decision Time")
        print("-" * 35)
        
        # Check team status
        updated_hole_state = sim.hole_states.get(sim.current_hole)
        tee_shots = sum(1 for ball in updated_hole_state.ball_positions.values() if ball and ball.shot_count >= 1)
        
        print(f"✅ Tee shots completed: {tee_shots}")
        print(f"🎯 Teams status: {updated_hole_state.teams.type}")
        
        if updated_hole_state.teams.type == "pending" and tee_shots >= 2:
            print("✅ Partnership decision window is OPEN!")
            
            # Show available partners
            captain_name = sim._get_player_name(captain_id)
            available_partners = []
            
            for player in sim.players:
                if player.id != captain_id and updated_hole_state.can_request_partnership(captain_id, player.id):
                    if player.id in updated_hole_state.ball_positions and updated_hole_state.ball_positions[player.id]:
                        partner_ball = updated_hole_state.ball_positions[player.id]
                        available_partners.append({
                            "name": player.name,
                            "distance": partner_ball.distance_to_pin,
                            "handicap": player.handicap
                        })
            
            if available_partners:
                print(f"🤝 {captain_name} can partner with:")
                for partner in available_partners:
                    print(f"   • {partner['name']}: {partner['distance']:.0f} yards (handicap {partner['handicap']})")
                print(f"   • Or go SOLO (1v3)")
                print()
        else:
            print("❌ Partnership decision not available yet")
            print()
    
    # Step 4: Continue shots to test betting opportunities
    print("Step 4: Continue hole to test betting opportunities")
    print("-" * 45)
    
    # Simulate a few more shots to create betting scenarios
    shots_taken = 0
    max_shots = 6  # Limit for test
    
    while shots_taken < max_shots and not hole_state.hole_complete:
        current_hole_state = sim.hole_states.get(sim.current_hole)
        next_player = current_hole_state.next_player_to_hit
        
        if not next_player:
            break
            
        shots_taken += 1
        result = sim.simulate_shot(next_player)
        
        if result.get("hole_complete"):
            print("🏁 Hole completed!")
            break
            
        shot = result["shot_result"]
        player_name = sim._get_player_name(next_player)
        print(f"Shot {shots_taken + 2}: {player_name} hits {shot['shot_quality']} shot → {shot['distance_to_pin']:.0f} yards")
        
        # Check for betting opportunities
        if shot['shot_quality'] in ['excellent', 'terrible']:
            print(f"   🎲 Betting opportunity! {shot['shot_quality']} shot creates action")
            
            # Show who could offer doubles
            betting_eligible = []
            for player in sim.players:
                if current_hole_state.can_offer_double(player.id):
                    betting_eligible.append(player.name)
            
            if betting_eligible:
                print(f"   💰 Players who can offer doubles: {', '.join(betting_eligible)}")
        print()
    
    print("=" * 60)
    print("✅ User Journey Test Complete!")
    print()
    
    # Summary
    final_hole_state = sim.hole_states.get(sim.current_hole)
    print("📊 Final Summary:")
    print(f"   • Teams formed: {final_hole_state.teams.type}")
    print(f"   • Shots taken: {sum(ball.shot_count for ball in final_hole_state.ball_positions.values() if ball)}")
    print(f"   • Current wager: {final_hole_state.betting.current_wager} quarters")
    print(f"   • Doubled: {'Yes' if final_hole_state.betting.doubled else 'No'}")

if __name__ == "__main__":
    test_realistic_user_journey()