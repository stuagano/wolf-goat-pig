# Wolf Goat Pig API Contracts

This directory contains the **single source of truth** for all API data structures used between the frontend and backend.

## Purpose

Prevent frontend-backend data contract mismatches by maintaining shared type definitions and schemas.

## Structure

- `game-state.schema.json` - JSON Schema for game state responses
- `game-state.types.ts` - TypeScript interfaces (generated from JSON Schema)
- `game-state.py` - Python Pydantic models (should match JSON Schema)

## Usage

### Frontend (TypeScript/React)
```typescript
import { GameState, HoleState, BettingState } from '../api-contracts/game-state.types';

// Use the types
const gameState: GameState = await fetch('/games/{id}/state').then(r => r.json());
```

### Backend (Python/FastAPI)
```python
from api_contracts.game_state import GameStateResponse

@app.get("/games/{game_id}/state", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    # FastAPI will validate the response matches the schema
    return game_state
```

## Generating Types

When you update the JSON Schema:

1. Generate TypeScript types:
   ```bash
   npm run generate-types
   ```

2. Manually update Python Pydantic models to match
   (or use json-schema-to-pydantic if needed)

## Rules

1. **Always update the JSON Schema first** - it's the source of truth
2. **Regenerate TypeScript types** after schema changes
3. **Update Python models** to match the schema
4. **Run validation tests** to ensure frontend/backend compatibility
5. **Never access nested properties without checking the schema first**

## Current Schemas

- `game-state` - Complete game state structure including hole state, betting, teams, players
- `join-game` - Request/response for joining games
- `create-game` - Request/response for creating games
- `lobby` - Lobby state before game starts
