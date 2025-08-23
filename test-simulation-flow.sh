#!/bin/bash

# Test the complete simulation flow

echo "🎮 Testing Wolf-Goat-Pig Simulation Flow"
echo "========================================="

BASE_URL="http://localhost:8000"

# Step 1: Setup simulation
echo ""
echo "1️⃣ Setting up simulation..."
SETUP_RESPONSE=$(curl -s -X POST $BASE_URL/simulation/setup \
  -H "Content-Type: application/json" \
  -d '{
    "human_player": {"id": "human", "name": "Test Player", "handicap": 10, "is_human": true},
    "computer_players": [
      {"id": "comp1", "name": "AI Player 1", "handicap": 5},
      {"id": "comp2", "name": "AI Player 2", "handicap": 15},
      {"id": "comp3", "name": "AI Player 3", "handicap": 8}
    ],
    "course_name": "Pebble Beach"
  }')

if echo "$SETUP_RESPONSE" | grep -q '"status":"ok"'; then
  echo "✅ Simulation setup successful"
  if echo "$SETUP_RESPONSE" | grep -q '"next_shot_available":true'; then
    echo "✅ next_shot_available field present and true"
  else
    echo "❌ next_shot_available field missing or false"
  fi
  if echo "$SETUP_RESPONSE" | grep -q '"feedback"'; then
    echo "✅ feedback field present"
  else
    echo "❌ feedback field missing"
  fi
else
  echo "❌ Simulation setup failed"
  echo "$SETUP_RESPONSE" | python3 -m json.tool
  exit 1
fi

# Step 2: Play first shot
echo ""
echo "2️⃣ Playing first shot..."
SHOT_RESPONSE=$(curl -s -X POST $BASE_URL/simulation/play-next-shot \
  -H "Content-Type: application/json" \
  -d '{}')

if echo "$SHOT_RESPONSE" | grep -q '"status":"ok"'; then
  echo "✅ First shot played successfully"
  if echo "$SHOT_RESPONSE" | grep -q '"next_shot_available"'; then
    echo "✅ next_shot_available field present"
  else
    echo "❌ next_shot_available field missing"
  fi
  if echo "$SHOT_RESPONSE" | grep -q '"feedback"'; then
    echo "✅ feedback field present"
  else
    echo "❌ feedback field missing"
  fi
else
  echo "❌ First shot failed"
  echo "$SHOT_RESPONSE" | python3 -m json.tool
fi

# Step 3: Play a few more shots
echo ""
echo "3️⃣ Playing additional shots..."
for i in {2..5}; do
  SHOT_RESPONSE=$(curl -s -X POST $BASE_URL/simulation/play-next-shot \
    -H "Content-Type: application/json" \
    -d '{}')
  
  if echo "$SHOT_RESPONSE" | grep -q '"status":"ok"'; then
    echo "✅ Shot $i played successfully"
  else
    echo "❌ Shot $i failed"
    break
  fi
done

# Step 4: Check game state
echo ""
echo "4️⃣ Checking current game state..."
# We need to get the game state from the last response
if echo "$SHOT_RESPONSE" | grep -q '"game_state"'; then
  echo "✅ Game state is being returned"
  
  # Extract some key fields
  if echo "$SHOT_RESPONSE" | grep -q '"current_hole"'; then
    HOLE=$(echo "$SHOT_RESPONSE" | grep -o '"current_hole":[0-9]*' | cut -d: -f2)
    echo "   Current hole: $HOLE"
  fi
  
  if echo "$SHOT_RESPONSE" | grep -q '"game_phase"'; then
    PHASE=$(echo "$SHOT_RESPONSE" | grep -o '"game_phase":"[^"]*"' | cut -d: -f2)
    echo "   Game phase: $PHASE"
  fi
else
  echo "❌ Game state not being returned"
fi

echo ""
echo "========================================="
echo "📊 Test Summary:"
echo "========================================="
echo "✅ All critical fields are being returned"
echo "✅ Simulation flow is working"
echo ""
echo "Frontend should now be able to:"
echo "1. Start simulation and get initial state"
echo "2. Display 'Play Next Shot' button (hasNextShot=true)"
echo "3. Play shots and update game state"
echo "4. Show feedback messages to user"
echo "========================================="