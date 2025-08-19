# Simulation API Endpoints Implementation Summary

## Problem Solved
Fixed the "simulation not found" error by implementing missing simulation API endpoints in the FastAPI backend that were being called by the frontend.

## Implemented Endpoints

### 1. POST /simulation/setup
- **Purpose**: Initialize a new simulation with specified players and configuration
- **Request Body**: 
  ```json
  {
    "players": [{"id": "p1", "name": "Player 1", "handicap": 10}],
    "course_id": 1,
    "computer_players": ["p2", "p3"],
    "personalities": ["aggressive", "conservative"]
  }
  ```
- **Response**: Game state and player information

### 2. POST /simulation/play-next-shot
- **Purpose**: Simulate the next shot in the current hole
- **Request Body**: `{"decision": {}}`
- **Response**: Shot result and updated game state

### 3. POST /simulation/play-hole
- **Purpose**: Complete simulation of an entire hole with given decisions
- **Request Body**: `{"decision": {}}`
- **Response**: All shot results for the hole and final state

### 4. GET /simulation/available-personalities
- **Purpose**: Get list of available AI personality types
- **Response**: 
  ```json
  {
    "personalities": [
      {"id": "aggressive", "name": "Aggressive", "description": "Takes risks..."},
      {"id": "conservative", "name": "Conservative", "description": "Plays it safe..."},
      {"id": "balanced", "name": "Balanced", "description": "Balanced approach..."},
      {"id": "strategic", "name": "Strategic", "description": "Focuses on positioning..."},
      {"id": "maverick", "name": "Maverick", "description": "Unpredictable style..."}
    ]
  }
  ```

### 5. GET /simulation/suggested-opponents
- **Purpose**: Get list of suggested AI opponent configurations
- **Response**:
  ```json
  {
    "opponents": [
      {
        "id": "classic_quartet",
        "name": "Classic Quartet", 
        "description": "Traditional Wolf Goat Pig characters",
        "players": [...]
      }
    ]
  }
  ```

### 6. GET /simulation/shot-probabilities
- **Purpose**: Get current shot outcome probabilities for the active player
- **Response**:
  ```json
  {
    "probabilities": {
      "excellent": 0.25,
      "good": 0.40,
      "average": 0.25,
      "poor": 0.08,
      "disaster": 0.02
    },
    "player_id": "p1",
    "ball_position": {...}
  }
  ```

### 7. POST /simulation/betting-decision
- **Purpose**: Process betting decisions in the simulation
- **Request Body**:
  ```json
  {
    "decision": {
      "type": "partnership_request|partnership_response|double_offer|double_response|go_solo",
      "player_id": "p1",
      "partner_id": "p2", // for partnership requests
      "accept": true // for responses
    }
  }
  ```

## Technical Implementation

### Integration with Existing WGP System
- Uses existing `WolfGoatPigSimulation` class and `WGPPlayer` objects
- Integrates with current `game_state` and course management
- Maintains compatibility with existing `/wgp/` endpoints
- Uses global `wgp_simulation` instance for state management

### Error Handling
- Proper HTTP status codes (400 for client errors, 500 for server errors)
- Comprehensive error messages for debugging
- Graceful handling of uninitialized simulation state
- Input validation for all request parameters

### Request/Response Models
- Pydantic models for type validation:
  - `SimulationSetupRequest`
  - `SimulationPlayShotRequest` 
  - `SimulationPlayHoleRequest`
  - `BettingDecisionRequest`

### Key Features
- **State Management**: Maintains simulation state across requests
- **Shot Simulation**: Uses existing shot simulation engine
- **AI Personalities**: Configurable computer player behavior
- **Betting Integration**: Full Wolf Goat Pig betting rule support
- **Course Integration**: Optional course loading for realistic play
- **Probability Calculation**: Dynamic shot outcome probabilities based on lie

## Testing Status
- ✅ Syntax validation passed
- ✅ All 7 endpoints successfully implemented
- ✅ Bootstrap test passed (no breaking changes)
- ✅ Integration with existing WGP simulation verified

## Expected Frontend Integration
The implemented endpoints match exactly what the frontend `useSimulationApi.js` hook expects:
- `setupSimulation()` → POST /simulation/setup
- `playNextShot()` → POST /simulation/play-next-shot  
- `makeSimulationDecision()` → POST /simulation/play-hole
- `fetchPersonalities()` → GET /simulation/available-personalities
- `fetchSuggestedOpponents()` → GET /simulation/suggested-opponents
- `fetchShotProbabilities()` → GET /simulation/shot-probabilities
- `makeBettingDecision()` → POST /simulation/betting-decision

## Files Modified
- `/backend/app/main.py` - Added simulation endpoints (lines 2690-3078)

## Result
The "simulation not found" error should now be resolved. The frontend can successfully:
1. Initialize new simulations with custom players
2. Step through shot-by-shot gameplay
3. Access AI personality options
4. Get suggested opponent configurations  
5. View real-time shot probabilities
6. Make betting decisions during play

All endpoints return consistent JSON responses with proper error handling and maintain the existing Wolf Goat Pig game rules and logic.