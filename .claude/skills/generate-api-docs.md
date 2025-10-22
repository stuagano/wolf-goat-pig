# Skill: Generate API Documentation

## Description
Generates comprehensive API documentation from the FastAPI backend including OpenAPI spec, Swagger UI, and markdown documentation.

## Usage
Invoke this skill when you need to create or update API documentation for the Wolf Goat Pig backend.

## Steps

### 1. Generate OpenAPI Schema

```bash
cd backend

# Ensure FastAPI is running
# Option A: Extract from running server
curl http://localhost:8000/openapi.json > docs/openapi.json

# Option B: Generate directly from code
python3 << 'EOF'
import json
from app.main import app

openapi_schema = app.openapi()

with open('docs/openapi.json', 'w') as f:
    json.dump(openapi_schema, f, indent=2)

print("OpenAPI schema generated at docs/openapi.json")
EOF
```

### 2. Validate OpenAPI Spec

```bash
# Install validator
npm install -g @apidevtools/swagger-cli

# Validate schema
swagger-cli validate docs/openapi.json

echo "✅ OpenAPI schema is valid"
```

### 3. Generate Markdown Documentation

```bash
# Install openapi-generator
npm install -g @openapitools/openapi-generator-cli

# Generate markdown docs
openapi-generator-cli generate \
  -i docs/openapi.json \
  -g markdown \
  -o docs/api/

echo "Markdown API docs generated at docs/api/"
```

### 4. Generate Postman Collection

```bash
# Install converter
npm install -g openapi-to-postmanv2

# Convert OpenAPI to Postman
openapi2postmanv2 \
  -s docs/openapi.json \
  -o docs/postman-collection.json \
  -p

echo "Postman collection generated at docs/postman-collection.json"
```

### 5. Generate Interactive HTML Documentation

```bash
# Install redoc-cli
npm install -g redoc-cli

# Generate static HTML documentation
redoc-cli bundle docs/openapi.json \
  -o docs/api-documentation.html \
  --title "Wolf Goat Pig API Documentation"

echo "Interactive HTML docs generated at docs/api-documentation.html"
```

### 6. Create API Reference README

```bash
cat > docs/api/README.md << 'EOF'
# Wolf Goat Pig API Reference

## Overview
This is the complete API reference for the Wolf Goat Pig golf betting simulation backend.

## Base URLs
- **Production**: `https://your-app.onrender.com`
- **Staging**: `https://your-app-staging.onrender.com`
- **Local**: `http://localhost:8000`

## Authentication
Most endpoints require authentication via Auth0 JWT tokens.

```bash
# Example: Get authenticated request
curl -H "Authorization: Bearer <your-jwt-token>" \
  https://api.example.com/game/123/state
```

## Quick Start

### 1. Initialize a Game
```bash
curl -X POST http://localhost:8000/game/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "player_ids": [1, 2, 3, 4],
    "course_id": 10,
    "handicap_system": "GHIN"
  }'
```

### 2. Get Game State
```bash
curl http://localhost:8000/game/123/state
```

### 3. Make Wolf Decision
```bash
curl -X POST http://localhost:8000/wgp/make-decision \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": 123,
    "decision": "choose_partner",
    "partner_player_id": 2
  }'
```

## API Endpoints

### Game Management
- `POST /game/initialize` - Create new game
- `GET /game/{game_id}/state` - Get current game state
- `POST /game/{game_id}/advance` - Advance to next shot
- `DELETE /game/{game_id}` - Delete game

### Wolf Goat Pig Specific
- `POST /wgp/make-decision` - Make wolf betting decision
- `GET /wgp/betting-odds` - Get current betting odds
- `POST /wgp/partnership` - Form partnership

### Players
- `GET /players` - List all players
- `POST /players` - Create new player
- `GET /players/{player_id}` - Get player details
- `PUT /players/{player_id}` - Update player
- `DELETE /players/{player_id}` - Delete player

### Courses
- `GET /courses` - List all courses
- `GET /courses/{course_id}` - Get course details

### Analytics
- `GET /analytics/leaderboard` - Get leaderboard
- `GET /analytics/player-stats/{player_id}` - Player statistics
- `GET /analytics/game-history` - Game history

## Response Formats

### Success Response
```json
{
  "data": { ... },
  "message": "Success"
}
```

### Error Response
```json
{
  "error": "ValidationError",
  "message": "Invalid player count",
  "details": [
    {
      "code": "INVALID_PLAYER_COUNT",
      "message": "Player count must be 4-6",
      "field": "player_ids"
    }
  ]
}
```

## Rate Limiting
- 100 requests per minute per IP
- 1000 requests per hour per user

## Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Support
For questions or issues, contact: support@wolfgoatpig.com
EOF

echo "API README created at docs/api/README.md"
```

### 7. Add Endpoint Examples

```bash
# Create examples directory
mkdir -p docs/api/examples

# Create example requests
cat > docs/api/examples/game-initialization.md << 'EOF'
# Game Initialization Examples

## Standard 4-Player Game
```bash
curl -X POST http://localhost:8000/game/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "player_ids": [1, 2, 3, 4],
    "course_id": 10,
    "handicap_system": "GHIN",
    "betting_rules": {
      "ante": 5,
      "wolf_advantage": true
    }
  }'
```

**Response:**
```json
{
  "game_id": 123,
  "players": [...],
  "current_hole": 1,
  "betting_state": {
    "wolf_player_id": 1,
    "betting_mode": "pre_tee",
    "current_pot": 20
  }
}
```

## 6-Player Game with Custom Rules
```bash
curl -X POST http://localhost:8000/game/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "player_ids": [1, 2, 3, 4, 5, 6],
    "course_id": 15,
    "handicap_system": "custom",
    "betting_rules": {
      "ante": 10,
      "wolf_advantage": false,
      "ping_pong": true
    }
  }'
```
EOF

echo "API examples created at docs/api/examples/"
```

### 8. Start Documentation Server

```bash
# Serve documentation locally
cd docs

# Option A: Python simple server
python3 -m http.server 8080

# Option B: npx serve
npx serve .

echo "Documentation available at:"
echo "  - API Docs: http://localhost:8080/api-documentation.html"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - ReDoc: http://localhost:8000/redoc"
```

### 9. Update Documentation in Repository

```bash
# Add documentation to git
git add docs/openapi.json
git add docs/api/
git add docs/api-documentation.html
git add docs/postman-collection.json

git commit -m "docs: update API documentation

- Generate OpenAPI 3.0 spec
- Add markdown API reference
- Create Postman collection
- Generate interactive HTML docs"

git push origin main
```

## FastAPI Documentation Enhancements

### Add Response Examples to Endpoints

```python
# In backend/app/main.py
from fastapi import FastAPI
from pydantic import BaseModel, Field

class GameStateResponse(BaseModel):
    game_id: int = Field(..., description="Unique game identifier")
    current_hole: int = Field(..., ge=1, le=18, description="Current hole number")

    class Config:
        json_schema_extra = {
            "example": {
                "game_id": 123,
                "current_hole": 5,
                "players": [...]
            }
        }

@app.get(
    "/game/{game_id}/state",
    response_model=GameStateResponse,
    summary="Get game state",
    description="Retrieve the current state of a game including players, scores, and betting status",
    responses={
        200: {
            "description": "Game state retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "game_id": 123,
                        "current_hole": 5,
                        "betting_state": {...}
                    }
                }
            }
        },
        404: {"description": "Game not found"}
    }
)
async def get_game_state(game_id: int):
    # Implementation
    pass
```

## Success Indicators
- ✅ OpenAPI schema generated and validated
- ✅ Markdown documentation created
- ✅ Postman collection available
- ✅ Interactive HTML docs generated
- ✅ All endpoints documented with examples
- ✅ Response schemas include examples
- ✅ Documentation hosted and accessible
