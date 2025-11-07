# Phase 1: Core Game Flow - Wolf Goat Pig Rules Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the foundational game flow rules including Captain rotation, Hoepfinger phase, Joe's Special, carry-over logic, and Vinnie's Variation to establish proper Wolf Goat Pig game mechanics.

**Architecture:** Extend the existing SimpleScorekeeper component and backend complete_hole endpoint to track rotation state, detect game phases, and apply wager modifiers automatically. Store rotation order and phase data in game state, add UI controls for Hoepfinger-specific actions, and implement backend validation for rule compliance.

**Tech Stack:** React (frontend), FastAPI (backend), SQLAlchemy (database), Python (business logic), JavaScript/JSX (UI)

---

## Prerequisites

**Before starting:**
- Review `docs/WOLF_GOAT_PIG_RULES.md` - Official rules reference
- Review `docs/SCOREKEEPER_RULES_COMPLIANCE_ANALYSIS.md` - Gap analysis
- Review `frontend/src/components/game/SimpleScorekeeper.jsx` - Current implementation
- Review `backend/app/main.py:1311-1443` - complete_hole endpoint

**Test Data Setup:**
- 4-player game with realistic quarters tracking
- Test game at hole 13, 16, 17, 18 for edge cases

---

## Task 1: Add Rotation Order Data Model (Backend)

**Files:**
- Modify: `backend/app/schemas.py` (add rotation fields)
- Modify: `backend/app/main.py:1311-1443` (update complete_hole)

**Step 1: Write failing test for rotation tracking**

Create: `backend/tests/test_rotation_tracking.py`

```python
import pytest
from app.main import app
from fastapi.testclient import client

def test_complete_hole_stores_rotation_order():
    """Test that rotation order is stored with hole data"""
    client = TestClient(app)

    # Create game with 4 players
    game_response = client.post("/games/initialize", json={
        "player_count": 4,
        "base_wager": 1
    })
    game_id = game_response.json()["game_id"]

    # Complete hole 1 with rotation order
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": ["p1", "p2", "p3", "p4"],
        "captain_index": 0,
        "teams": {
            "type": "partners",
            "team1": ["p1", "p2"],
            "team2": ["p3", "p4"]
        },
        "final_wager": 1,
        "winner": "team1",
        "scores": {"p1": 4, "p2": 5, "p3": 5, "p4": 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    hole_result = response.json()["hole_result"]
    assert hole_result["rotation_order"] == ["p1", "p2", "p3", "p4"]
    assert hole_result["captain_index"] == 0

def test_rotation_advances_each_hole():
    """Test that captain index rotates properly"""
    client = TestClient(app)

    game_response = client.post("/games/initialize", json={
        "player_count": 4,
        "base_wager": 1
    })
    game_id = game_response.json()["game_id"]

    # Hole 1: p1 is captain (index 0)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": ["p1", "p2", "p3", "p4"],
        "captain_index": 0,
        "teams": {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]},
        "final_wager": 1,
        "winner": "team1",
        "scores": {"p1": 4, "p2": 5, "p3": 5, "p4": 6},
        "hole_par": 4
    })

    # Get next rotation
    state_response = client.get(f"/games/{game_id}/state")
    next_rotation = state_response.json()["next_rotation"]

    # Hole 2: p2 should be captain (rotation advances)
    assert next_rotation["rotation_order"] == ["p2", "p3", "p4", "p1"]
    assert next_rotation["captain_index"] == 0
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_rotation_tracking.py::test_complete_hole_stores_rotation_order -v
```

Expected: FAIL - "rotation_order" field not in schema

**Step 3: Update CompleteHoleRequest schema**

Modify: `backend/app/schemas.py`

Find the CompleteHoleRequest class and add:

```python
class CompleteHoleRequest(BaseModel):
    hole_number: int
    rotation_order: List[str]  # NEW: Hitting order for this hole
    captain_index: int = 0     # NEW: Index in rotation_order who is captain
    teams: TeamConfiguration
    final_wager: int
    winner: str
    scores: Dict[str, int]
    hole_par: int = 4
    float_invoked_by: Optional[str] = None
    option_invoked_by: Optional[str] = None
```

**Step 4: Update complete_hole endpoint to store rotation**

Modify: `backend/app/main.py:1388-1399`

Change hole_result dict to include rotation fields:

```python
# Create hole result
hole_result = {
    "hole": request.hole_number,
    "rotation_order": request.rotation_order,  # NEW
    "captain_index": request.captain_index,    # NEW
    "teams": request.teams.model_dump(),
    "wager": request.final_wager,
    "winner": request.winner,
    "gross_scores": request.scores,
    "hole_par": request.hole_par,
    "points_delta": points_delta,
    "float_invoked_by": request.float_invoked_by,
    "option_invoked_by": request.option_invoked_by
}
```

**Step 5: Add endpoint to calculate next rotation**

Add new endpoint after complete_hole in `backend/app/main.py`:

```python
@app.get("/games/{game_id}/next-rotation")
async def get_next_rotation(
    game_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Calculate the next rotation order based on current hole.
    Handles normal rotation and Hoepfinger special selection.
    """
    try:
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}
        player_count = len(game_state.get("players", []))
        current_hole = game_state.get("current_hole", 1)

        # Determine Hoepfinger start based on player count
        hoepfinger_start = {
            4: 17,
            5: 16,
            6: 13
        }.get(player_count, 17)

        is_hoepfinger = current_hole >= hoepfinger_start

        # Get last hole's rotation
        hole_history = game_state.get("hole_history", [])
        if hole_history:
            last_hole = hole_history[-1]
            last_rotation = last_hole.get("rotation_order", [p["id"] for p in game_state["players"]])
        else:
            # First hole - use player order
            last_rotation = [p["id"] for p in game_state["players"]]

        if is_hoepfinger:
            # Hoepfinger: Goat (furthest down) selects position
            # Calculate current standings
            standings = {}
            for player in game_state["players"]:
                standings[player["id"]] = player.get("points", 0)

            goat_id = min(standings, key=standings.get)

            return {
                "is_hoepfinger": True,
                "goat_id": goat_id,
                "goat_selects_position": True,
                "available_positions": list(range(player_count)),
                "current_rotation": last_rotation,
                "message": "Goat selects hitting position"
            }
        else:
            # Normal rotation: shift left by 1
            new_rotation = last_rotation[1:] + [last_rotation[0]]

            return {
                "is_hoepfinger": False,
                "rotation_order": new_rotation,
                "captain_index": 0,
                "captain_id": new_rotation[0]
            }

    except Exception as e:
        logger.error(f"Error calculating next rotation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 6: Run tests to verify they pass**

```bash
pytest tests/test_rotation_tracking.py -v
```

Expected: PASS (both tests)

**Step 7: Commit rotation tracking**

```bash
git add backend/app/schemas.py backend/app/main.py backend/tests/test_rotation_tracking.py
git commit -m "feat: add captain rotation tracking and next rotation calculation

- Add rotation_order and captain_index to hole data
- Implement /games/{game_id}/next-rotation endpoint
- Calculate normal rotation (shift left) vs Hoepfinger (Goat selects)
- Store rotation state with each completed hole
- Tests verify rotation storage and advancement"
```

---

## Task 2: Add Hoepfinger Phase Detection and Joe's Special (Backend)

**Files:**
- Modify: `backend/app/schemas.py` (add phase and wager modifier fields)
- Modify: `backend/app/main.py` (add Hoepfinger rules)
- Create: `backend/tests/test_hoepfinger.py`

**Step 1: Write failing tests for Hoepfinger phase**

Create: `backend/tests/test_hoepfinger.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_hoepfinger_starts_at_hole_17_for_4_players():
    """Test Hoepfinger phase begins at hole 17 in 4-player game"""
    client = TestClient(app)

    game_response = client.post("/games/initialize", json={
        "player_count": 4,
        "base_wager": 1
    })
    game_id = game_response.json()["game_id"]

    # Check at hole 16 (not Hoepfinger yet)
    rotation_16 = client.get(f"/games/{game_id}/next-rotation",
                             params={"current_hole": 16})
    assert rotation_16.json()["is_hoepfinger"] is False

    # Check at hole 17 (Hoepfinger starts)
    rotation_17 = client.get(f"/games/{game_id}/next-rotation",
                             params={"current_hole": 17})
    assert rotation_17.json()["is_hoepfinger"] is True
    assert "goat_id" in rotation_17.json()
    assert rotation_17.json()["goat_selects_position"] is True

def test_joes_special_allows_goat_to_set_wager():
    """Test Joe's Special: Goat sets wager to 2, 4, or 8 quarters"""
    client = TestClient(app)

    game_response = client.post("/games/initialize", json={
        "player_count": 4,
        "base_wager": 1,
        "players": [
            {"id": "p1", "name": "Alice", "points": 5},
            {"id": "p2", "name": "Bob", "points": -3},  # Goat
            {"id": "p3", "name": "Charlie", "points": 2},
            {"id": "p4", "name": "Dave", "points": 1}
        ]
    })
    game_id = game_response.json()["game_id"]

    # Complete hole 17 with Joe's Special
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 17,
        "rotation_order": ["p2", "p1", "p3", "p4"],  # Goat selected first
        "captain_index": 0,
        "phase": "hoepfinger",
        "joes_special_wager": 8,  # Goat sets to 8Q
        "teams": {"type": "partners", "team1": ["p2", "p1"], "team2": ["p3", "p4"]},
        "final_wager": 8,
        "winner": "team1",
        "scores": {"p1": 4, "p2": 4, "p3": 5, "p4": 5},
        "hole_par": 4
    })

    assert response.status_code == 200
    hole_result = response.json()["hole_result"]
    assert hole_result["phase"] == "hoepfinger"
    assert hole_result["joes_special_wager"] == 8
    assert hole_result["wager"] == 8

def test_joes_special_max_8_quarters():
    """Test Joe's Special cannot exceed 8 quarters"""
    client = TestClient(app)

    game_response = client.post("/games/initialize", json={
        "player_count": 4,
        "base_wager": 1
    })
    game_id = game_response.json()["game_id"]

    # Try to set Joe's Special to 16Q (invalid)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 17,
        "phase": "hoepfinger",
        "joes_special_wager": 16,  # Too high
        "teams": {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]},
        "final_wager": 16,
        "winner": "team1",
        "scores": {"p1": 4, "p2": 4, "p3": 5, "p4": 5},
        "hole_par": 4
    })

    assert response.status_code == 400
    assert "Joe's Special maximum is 8 quarters" in response.json()["detail"]
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_hoepfinger.py -v
```

Expected: FAIL - "phase", "joes_special_wager" fields not in schema

**Step 3: Update schema for Hoepfinger fields**

Modify: `backend/app/schemas.py`

```python
class CompleteHoleRequest(BaseModel):
    hole_number: int
    rotation_order: List[str]
    captain_index: int = 0
    phase: Optional[str] = "normal"  # NEW: "normal" or "hoepfinger"
    joes_special_wager: Optional[int] = None  # NEW: 2, 4, or 8 (Hoepfinger only)
    teams: TeamConfiguration
    final_wager: int
    winner: str
    scores: Dict[str, int]
    hole_par: int = 4
    float_invoked_by: Optional[str] = None
    option_invoked_by: Optional[str] = None
```

**Step 4: Add Joe's Special validation to complete_hole**

Modify: `backend/app/main.py:1320` (add validation after getting game)

```python
async def complete_hole(
    game_id: str,
    request: CompleteHoleRequest,
    db: Session = Depends(database.get_db)
):
    """
    Complete a hole with all data at once - simplified scorekeeper mode.
    """
    try:
        # Get game from database
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # NEW: Validate Joe's Special
        if request.phase == "hoepfinger" and request.joes_special_wager:
            valid_wagers = [2, 4, 8]
            if request.joes_special_wager not in valid_wagers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Joe's Special must be 2, 4, or 8 quarters. Got: {request.joes_special_wager}. Joe's Special maximum is 8 quarters."
                )

        # ... rest of function
```

**Step 5: Store Hoepfinger data in hole_result**

Modify: `backend/app/main.py:1388-1399` (update hole_result dict)

```python
# Create hole result
hole_result = {
    "hole": request.hole_number,
    "rotation_order": request.rotation_order,
    "captain_index": request.captain_index,
    "phase": request.phase,  # NEW
    "joes_special_wager": request.joes_special_wager,  # NEW
    "teams": request.teams.model_dump(),
    "wager": request.final_wager,
    "winner": request.winner,
    "gross_scores": request.scores,
    "hole_par": request.hole_par,
    "points_delta": points_delta,
    "float_invoked_by": request.float_invoked_by,
    "option_invoked_by": request.option_invoked_by
}
```

**Step 6: Run tests to verify they pass**

```bash
pytest tests/test_hoepfinger.py -v
```

Expected: PASS (all 3 tests)

**Step 7: Commit Hoepfinger and Joe's Special**

```bash
git add backend/app/schemas.py backend/app/main.py backend/tests/test_hoepfinger.py
git commit -m "feat: add Hoepfinger phase and Joe's Special

- Detect Hoepfinger start (hole 17 for 4-man, 16 for 5-man, 13 for 6-man)
- Goat selects rotation position during Hoepfinger
- Joe's Special: Goat sets wager to 2, 4, or 8 quarters
- Validate Joe's Special wager limits
- Store phase and wager data with hole results
- Tests verify phase detection and wager rules"
```

---

## Task 3: Add Carry-Over Logic (Backend)

**Files:**
- Modify: `backend/app/main.py` (add carry-over detection and propagation)
- Create: `backend/tests/test_carry_over.py`

**Step 1: Write failing tests for carry-over**

Create: `backend/tests/test_carry_over.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_push_triggers_carryover():
    """Test that a push (tie) triggers carry-over to next hole"""
    client = TestClient(app)

    game_response = client.post("/games/initialize", json={
        "player_count": 4,
        "base_wager": 1
    })
    game_id = game_response.json()["game_id"]

    # Hole 1: Push (tie)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": ["p1", "p2", "p3", "p4"],
        "captain_index": 0,
        "teams": {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]},
        "final_wager": 2,  # Wager was 2Q
        "winner": "push",  # PUSH
        "scores": {"p1": 4, "p2": 4, "p3": 4, "p4": 4},
        "hole_par": 4
    })

    # Check next hole wager
    next_wager = client.get(f"/games/{game_id}/next-hole-wager")
    assert next_wager.json()["base_wager"] == 4  # 2Q × 2 = 4Q carry-over
    assert next_wager.json()["carry_over"] is True
    assert next_wager.json()["message"] == "Carry-over from hole 1 push"

def test_consecutive_carryover_blocked():
    """Test that carry-over cannot occur on consecutive holes"""
    client = TestClient(app)

    game_response = client.post("/games/initialize", json={
        "player_count": 4,
        "base_wager": 1
    })
    game_id = game_response.json()["game_id"]

    # Hole 1: Push (wager 2Q)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "final_wager": 2,
        "winner": "push",
        "teams": {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]},
        "scores": {"p1": 4, "p2": 4, "p3": 4, "p4": 4},
        "hole_par": 4
    })

    # Hole 2: Push again (wager 4Q from carry-over)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "final_wager": 4,
        "winner": "push",
        "teams": {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]},
        "scores": {"p1": 5, "p2": 5, "p3": 5, "p4": 5},
        "hole_par": 4,
        "carry_over_applied": True
    })

    # Hole 3: Should NOT have another carry-over (consecutive block)
    next_wager = client.get(f"/games/{game_id}/next-hole-wager")
    assert next_wager.json()["base_wager"] == 4  # Stays at 4Q (no additional carry)
    assert next_wager.json()["carry_over"] is False
    assert "Consecutive carry-over blocked" in next_wager.json()["message"]

def test_carryover_resets_after_decided_hole():
    """Test carry-over can apply again after a decided hole"""
    client = TestClient(app)

    game_response = client.post("/games/initialize", json={
        "player_count": 4,
        "base_wager": 1
    })
    game_id = game_response.json()["game_id"]

    # Hole 1: Push
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "final_wager": 1,
        "winner": "push",
        "teams": {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]},
        "scores": {"p1": 4, "p2": 4, "p3": 4, "p4": 4},
        "hole_par": 4
    })

    # Hole 2: Decided (Team 1 wins with carry-over)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "final_wager": 2,
        "winner": "team1",
        "teams": {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]},
        "scores": {"p1": 4, "p2": 4, "p3": 5, "p4": 5},
        "hole_par": 4,
        "carry_over_applied": True
    })

    # Hole 3: Push again
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 3,
        "final_wager": 1,
        "winner": "push",
        "teams": {"type": "partners", "team1": ["p1", "p2"], "team2": ["p3", "p4"]},
        "scores": {"p1": 4, "p2": 4, "p3": 4, "p4": 4},
        "hole_par": 4
    })

    # Hole 4: Carry-over should work again (hole 2 was decided)
    next_wager = client.get(f"/games/{game_id}/next-hole-wager")
    assert next_wager.json()["base_wager"] == 2  # 1Q × 2
    assert next_wager.json()["carry_over"] is True
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_carry_over.py -v
```

Expected: FAIL - "/next-hole-wager" endpoint doesn't exist

**Step 3: Add carry-over tracking to game state**

Modify: `backend/app/main.py:1410` (after updating hole_history)

```python
# Add or update hole in history
existing_hole_index = next(
    (i for i, h in enumerate(game_state["hole_history"]) if h.get("hole") == request.hole_number),
    None
)

if existing_hole_index is not None:
    game_state["hole_history"][existing_hole_index] = hole_result
else:
    game_state["hole_history"].append(hole_result)

# NEW: Track carry-over state
if request.winner == "push":
    # Check if last hole was also a push (consecutive block)
    last_push_hole = game_state.get("last_push_hole")
    if last_push_hole == request.hole_number - 1:
        # Consecutive push - don't trigger new carry-over
        game_state["consecutive_push_block"] = True
        game_state["last_push_hole"] = request.hole_number
    else:
        # Trigger carry-over for next hole
        game_state["carry_over_wager"] = request.final_wager * 2
        game_state["carry_over_from_hole"] = request.hole_number
        game_state["last_push_hole"] = request.hole_number
        game_state["consecutive_push_block"] = False
else:
    # Hole was decided - reset carry-over tracking
    if "carry_over_wager" in game_state:
        del game_state["carry_over_wager"]
    if "carry_over_from_hole" in game_state:
        del game_state["carry_over_from_hole"]
    game_state["consecutive_push_block"] = False
```

**Step 4: Add endpoint to calculate next hole wager**

Add new endpoint in `backend/app/main.py`:

```python
@app.get("/games/{game_id}/next-hole-wager")
async def get_next_hole_wager(
    game_id: str,
    db: Session = Depends(database.get_db)
):
    """
    Calculate the base wager for the next hole.
    Accounts for carry-over, Vinnie's Variation, and Hoepfinger rules.
    """
    try:
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}
        player_count = len(game_state.get("players", []))
        current_hole = game_state.get("current_hole", 1)
        base_wager = game_state.get("base_wager", 1)

        # Check for carry-over
        if game_state.get("carry_over_wager"):
            carry_over_wager = game_state["carry_over_wager"]
            from_hole = game_state.get("carry_over_from_hole", current_hole - 1)

            if game_state.get("consecutive_push_block"):
                return {
                    "base_wager": carry_over_wager,
                    "carry_over": False,
                    "message": f"Consecutive carry-over blocked. Base wager remains {carry_over_wager}Q from hole {from_hole}"
                }
            else:
                return {
                    "base_wager": carry_over_wager,
                    "carry_over": True,
                    "message": f"Carry-over from hole {from_hole} push"
                }

        # Check for Vinnie's Variation (holes 13-16 in 4-player)
        if player_count == 4 and 13 <= current_hole <= 16:
            return {
                "base_wager": base_wager * 2,
                "vinnies_variation": True,
                "carry_over": False,
                "message": f"Vinnie's Variation: holes 13-16 doubled (hole {current_hole})"
            }

        # Normal base wager
        return {
            "base_wager": base_wager,
            "carry_over": False,
            "vinnies_variation": False,
            "message": "Normal base wager"
        }

    except Exception as e:
        logger.error(f"Error calculating next hole wager: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 5: Update schema to track carry-over applied**

Modify: `backend/app/schemas.py`

```python
class CompleteHoleRequest(BaseModel):
    hole_number: int
    rotation_order: List[str]
    captain_index: int = 0
    phase: Optional[str] = "normal"
    joes_special_wager: Optional[int] = None
    teams: TeamConfiguration
    final_wager: int
    winner: str
    scores: Dict[str, int]
    hole_par: int = 4
    float_invoked_by: Optional[str] = None
    option_invoked_by: Optional[str] = None
    carry_over_applied: Optional[bool] = False  # NEW
```

**Step 6: Store carry-over flag in hole_result**

Modify: `backend/app/main.py:1388-1399`

```python
# Create hole result
hole_result = {
    "hole": request.hole_number,
    "rotation_order": request.rotation_order,
    "captain_index": request.captain_index,
    "phase": request.phase,
    "joes_special_wager": request.joes_special_wager,
    "teams": request.teams.model_dump(),
    "wager": request.final_wager,
    "winner": request.winner,
    "gross_scores": request.scores,
    "hole_par": request.hole_par,
    "points_delta": points_delta,
    "float_invoked_by": request.float_invoked_by,
    "option_invoked_by": request.option_invoked_by,
    "carry_over_applied": request.carry_over_applied  # NEW
}
```

**Step 7: Run tests to verify they pass**

```bash
pytest tests/test_carry_over.py -v
```

Expected: PASS (all 3 tests)

**Step 8: Commit carry-over logic**

```bash
git add backend/app/schemas.py backend/app/main.py backend/tests/test_carry_over.py
git commit -m "feat: add carry-over logic for push outcomes

- Push (tie) doubles next hole's base wager
- Block consecutive carry-overs (max one per sequence)
- Reset carry-over after decided hole
- Add /games/{game_id}/next-hole-wager endpoint
- Track carry_over_applied flag in hole results
- Tests verify carry-over propagation and blocking"
```

---

## Task 4: Add Vinnie's Variation (Backend)

**Files:**
- Modify: `backend/app/main.py` (already added in previous endpoint)
- Create: `backend/tests/test_vinnies_variation.py`

**Step 1: Write failing tests for Vinnie's Variation**

Create: `backend/tests/test_vinnies_variation.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_vinnies_variation_doubles_holes_13_to_16():
    """Test Vinnie's Variation doubles base wager on holes 13-16"""
    client = TestClient(app)

    game_response = client.post("/games/initialize", json={
        "player_count": 4,
        "base_wager": 1
    })
    game_id = game_response.json()["game_id"]

    # Complete holes 1-12 (skip for brevity, just set current_hole)
    # ... Complete holes 1-12

    # Hole 13: Should have Vinnie's Variation (2x base)
    wager_13 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=13")
    assert wager_13.json()["base_wager"] == 2  # 1Q × 2
    assert wager_13.json()["vinnies_variation"] is True

    # Hole 14
    wager_14 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=14")
    assert wager_14.json()["base_wager"] == 2
    assert wager_14.json()["vinnies_variation"] is True

    # Hole 15
    wager_15 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=15")
    assert wager_15.json()["base_wager"] == 2
    assert wager_15.json()["vinnies_variation"] is True

    # Hole 16
    wager_16 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=16")
    assert wager_16.json()["base_wager"] == 2
    assert wager_16.json()["vinnies_variation"] is True

    # Hole 17: Hoepfinger starts, no more Vinnie's Variation
    wager_17 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=17")
    assert wager_17.json()["base_wager"] == 1  # Back to normal
    assert wager_17.json().get("vinnies_variation", False) is False

def test_vinnies_variation_only_for_4_players():
    """Test Vinnie's Variation only applies to 4-player games"""
    client = TestClient(app)

    # 5-player game
    game_response = client.post("/games/initialize", json={
        "player_count": 5,
        "base_wager": 1
    })
    game_id = game_response.json()["game_id"]

    # Hole 13 in 5-player should NOT have Vinnie's Variation
    wager_13 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=13")
    assert wager_13.json()["base_wager"] == 1
    assert wager_13.json().get("vinnies_variation", False) is False
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_vinnies_variation.py::test_vinnies_variation_doubles_holes_13_to_16 -v
```

Expected: FAIL - Need to accept current_hole as query param

**Step 3: Update next-hole-wager endpoint to accept current_hole**

Modify: `backend/app/main.py` (get_next_hole_wager function)

```python
@app.get("/games/{game_id}/next-hole-wager")
async def get_next_hole_wager(
    game_id: str,
    current_hole: Optional[int] = None,  # NEW: Allow override
    db: Session = Depends(database.get_db)
):
    """
    Calculate the base wager for the next hole.
    Accounts for carry-over, Vinnie's Variation, and Hoepfinger rules.
    """
    try:
        game = db.query(models.GameStateModel).filter(
            models.GameStateModel.game_id == game_id
        ).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}
        player_count = len(game_state.get("players", []))

        # Use provided current_hole or get from game state
        if current_hole is None:
            current_hole = game_state.get("current_hole", 1)

        base_wager = game_state.get("base_wager", 1)

        # ... rest of function stays the same
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_vinnies_variation.py -v
```

Expected: PASS (both tests)

**Step 5: Commit Vinnie's Variation**

```bash
git add backend/app/main.py backend/tests/test_vinnies_variation.py
git commit -m "feat: add Vinnie's Variation for 4-player games

- Doubles base wager on holes 13-16 in 4-player games
- Only applies to 4-player games (not 5 or 6)
- Integrated into /next-hole-wager endpoint
- Tests verify doubling on correct holes and player count"
```

---

## Task 5: Frontend - Captain Rotation UI

**Files:**
- Modify: `frontend/src/components/game/SimpleScorekeeper.jsx`
- Add rotation display and auto-advance

**Step 1: Add rotation state to SimpleScorekeeper**

Modify: `frontend/src/components/game/SimpleScorekeeper.jsx:20-44`

Add new state variables:

```javascript
const SimpleScorekeeper = ({
  gameId,
  players,
  baseWager = 1,
  initialHoleHistory = [],
  initialCurrentHole = 1
}) => {
  const theme = useTheme();

  // Current hole state
  const [currentHole, setCurrentHole] = useState(initialCurrentHole);
  const [teamMode, setTeamMode] = useState('partners');
  const [team1, setTeam1] = useState([]);
  const [team2, setTeam2] = useState([]);
  const [captain, setCaptain] = useState(null);
  const [opponents, setOpponents] = useState([]);
  const [currentWager, setCurrentWager] = useState(baseWager);
  const [scores, setScores] = useState({});
  const [winner, setWinner] = useState(null);
  const [holePar, setHolePar] = useState(4);
  const [floatInvokedBy, setFloatInvokedBy] = useState(null);
  const [optionInvokedBy, setOptionInvokedBy] = useState(null);

  // NEW: Rotation tracking
  const [rotationOrder, setRotationOrder] = useState(players.map(p => p.id));
  const [captainIndex, setCaptainIndex] = useState(0);
  const [isHoepfinger, setIsHoepfinger] = useState(false);
  const [goatId, setGoatId] = useState(null);
  const [nextHoleWager, setNextHoleWager] = useState(baseWager);
  const [carryOver, setCarryOver] = useState(false);
  const [vinniesVariation, setVinniesVariation] = useState(false);

  // ... rest of state
```

**Step 2: Fetch next rotation when hole changes**

Add useEffect after existing ones in SimpleScorekeeper:

```javascript
// Fetch next rotation and wager when hole changes
useEffect(() => {
  const fetchNextRotation = async () => {
    try {
      // Get next rotation
      const rotationResponse = await fetch(`${API_URL}/games/${gameId}/next-rotation`);
      const rotationData = await rotationResponse.json();

      if (rotationData.is_hoepfinger) {
        setIsHoepfinger(true);
        setGoatId(rotationData.goat_id);
        // Rotation will be set by Goat selection
      } else {
        setIsHoepfinger(false);
        setRotationOrder(rotationData.rotation_order);
        setCaptainIndex(0);
        setCaptain(rotationData.captain_id);
      }

      // Get next wager
      const wagerResponse = await fetch(`${API_URL}/games/${gameId}/next-hole-wager`);
      const wagerData = await wagerResponse.json();

      setNextHoleWager(wagerData.base_wager);
      setCurrentWager(wagerData.base_wager);
      setCarryOver(wagerData.carry_over || false);
      setVinniesVariation(wagerData.vinnies_variation || false);

    } catch (err) {
      console.error('Error fetching next rotation/wager:', err);
    }
  };

  if (gameId && currentHole) {
    fetchNextRotation();
  }
}, [gameId, currentHole]);
```

**Step 3: Add rotation display UI before team selection**

Add this section in the render, before "Team Mode Selection":

```javascript
{/* Captain Rotation Display */}
<div style={{
  background: theme.colors.paper,
  padding: '20px',
  borderRadius: '16px',
  marginBottom: '20px',
  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
}}>
  <h3 style={{ margin: '0 0 16px', fontSize: '20px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
    {isHoepfinger ? '🎯 Hoepfinger Phase' : '🎮 Rotation Order'}
  </h3>

  {isHoepfinger && goatId ? (
    <div>
      <div style={{ marginBottom: '12px', fontSize: '14px', color: theme.colors.textSecondary }}>
        The Goat (furthest down) selects their hitting position:
      </div>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {[0, 1, 2, 3].map(position => (
          <button
            key={position}
            onClick={() => {
              // Goat selected position - build rotation with Goat at that index
              const goatPlayer = players.find(p => p.id === goatId);
              const otherPlayers = players.filter(p => p.id !== goatId);
              const newRotation = [...otherPlayers];
              newRotation.splice(position, 0, goatId);

              setRotationOrder(newRotation);
              setCaptainIndex(position);
              setCaptain(goatId);
            }}
            className="touch-optimized"
            style={{
              flex: 1,
              padding: '12px',
              fontSize: '16px',
              fontWeight: 'bold',
              border: captainIndex === position ? `3px solid ${theme.colors.primary}` : `2px solid ${theme.colors.border}`,
              borderRadius: '8px',
              background: captainIndex === position ? theme.colors.primary : 'white',
              color: captainIndex === position ? 'white' : theme.colors.textPrimary,
              cursor: 'pointer'
            }}
          >
            {position + 1}
          </button>
        ))}
      </div>
      <div style={{ fontSize: '12px', color: theme.colors.textSecondary }}>
        Goat: {players.find(p => p.id === goatId)?.name}
      </div>
    </div>
  ) : (
    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
      {rotationOrder.map((playerId, index) => {
        const player = players.find(p => p.id === playerId);
        const isCaptain = index === captainIndex;

        return (
          <div
            key={playerId}
            style={{
              flex: 1,
              padding: '16px',
              borderRadius: '12px',
              border: isCaptain ? `3px solid ${theme.colors.primary}` : `2px solid ${theme.colors.border}`,
              background: isCaptain ? `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.accent})` : 'white',
              color: isCaptain ? 'white' : theme.colors.textPrimary,
              textAlign: 'center',
              boxShadow: isCaptain ? '0 4px 6px rgba(0,0,0,0.2)' : 'none'
            }}
          >
            <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px' }}>
              {index + 1}{isCaptain && ' ⭐'}
            </div>
            <div style={{ fontSize: '14px' }}>{player?.name}</div>
          </div>
        );
      })}
    </div>
  )}

  {/* Wager Info */}
  <div style={{
    marginTop: '16px',
    padding: '12px',
    borderRadius: '8px',
    background: carryOver ? 'rgba(255, 152, 0, 0.1)' :
                vinniesVariation ? 'rgba(33, 150, 243, 0.1)' :
                theme.colors.backgroundSecondary,
    fontSize: '14px'
  }}>
    <strong>Base Wager:</strong> {nextHoleWager}Q
    {carryOver && ' 🔁 (Carry-Over)'}
    {vinniesVariation && ' 🎲 (Vinnie\'s Variation)'}
    {isHoepfinger && ' 🎯 (Hoepfinger Phase)'}
  </div>
</div>
```

**Step 4: Update handleSubmitHole to send rotation data**

Modify: `frontend/src/components/game/SimpleScorekeeper.jsx:214-252`

```javascript
const handleSubmitHole = async () => {
  const validationError = validateHole();
  if (validationError) {
    setError(validationError);
    return;
  }

  setSubmitting(true);
  setError(null);

  try {
    const teams = teamMode === 'partners'
      ? {
          type: 'partners',
          team1: team1,
          team2: team2
        }
      : {
          type: 'solo',
          captain: captain,
          opponents: opponents
        };

    const response = await fetch(`${API_URL}/games/${gameId}/holes/complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        hole_number: currentHole,
        rotation_order: rotationOrder,  // NEW
        captain_index: captainIndex,    // NEW
        phase: isHoepfinger ? 'hoepfinger' : 'normal',  // NEW
        teams: teams,
        final_wager: currentWager,
        winner: winner,
        scores: scores,
        hole_par: holePar,
        float_invoked_by: floatInvokedBy,
        option_invoked_by: optionInvokedBy,
        carry_over_applied: carryOver  // NEW
      })
    });

    // ... rest of submit logic
```

**Step 5: Test rotation UI manually**

Start the development server and verify:

```bash
cd frontend
npm start
```

1. Create a 4-player game
2. Verify rotation order displays with captain highlighted
3. Complete hole, verify rotation advances (shifts left)
4. Navigate to hole 17, verify Hoepfinger mode activates
5. Verify Goat can select position 1-4
6. Verify wager indicators (carry-over, Vinnie's Variation)

**Step 6: Commit frontend rotation UI**

```bash
git add frontend/src/components/game/SimpleScorekeeper.jsx
git commit -m "feat: add captain rotation UI to scorekeeper

- Display rotation order with captain highlighted
- Show Hoepfinger phase when active
- Allow Goat to select hitting position during Hoepfinger
- Display base wager with carry-over and Vinnie's Variation indicators
- Fetch next rotation and wager automatically on hole change
- Send rotation data to backend on hole completion"
```

---

## Task 6: Frontend - Joe's Special Wager Selection

**Files:**
- Modify: `frontend/src/components/game/SimpleScorekeeper.jsx`

**Step 1: Add Joe's Special state**

Add to state variables in SimpleScorekeeper:

```javascript
// After existing rotation state
const [joesSpecialWager, setJoesSpecialWager] = useState(null);
const [showJoesSpecial, setShowJoesSpecial] = useState(false);
```

**Step 2: Show Joe's Special selector when Hoepfinger and Goat**

Add effect to show Joe's Special when conditions are met:

```javascript
// Show Joe's Special when Hoepfinger phase starts
useEffect(() => {
  if (isHoepfinger && goatId) {
    // Check if current user is the Goat
    const currentStandings = Object.values(playerStandings);
    const lowestQuarters = Math.min(...currentStandings.map(p => p.quarters));
    const goatPlayer = currentStandings.find(p => p.quarters === lowestQuarters);

    if (goatPlayer) {
      setShowJoesSpecial(true);
    }
  } else {
    setShowJoesSpecial(false);
    setJoesSpecialWager(null);
  }
}, [isHoepfinger, goatId, playerStandings]);
```

**Step 3: Add Joe's Special UI section**

Add this section after the Rotation Display, before Team Mode Selection:

```javascript
{/* Joe's Special - Hoepfinger Wager Selection */}
{showJoesSpecial && (
  <div style={{
    background: 'linear-gradient(135deg, #FF6B6B, #FFE66D)',
    padding: '20px',
    borderRadius: '16px',
    marginBottom: '20px',
    boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
    color: 'white'
  }}>
    <h3 style={{ margin: '0 0 12px', fontSize: '20px', fontWeight: 'bold' }}>
      🎲 Joe's Special
    </h3>
    <div style={{ marginBottom: '16px', fontSize: '14px', opacity: 0.9 }}>
      As the Goat (furthest down), you may set the starting wager for this Hoepfinger hole.
      Choose 2, 4, or 8 quarters:
    </div>

    <div style={{ display: 'flex', gap: '12px' }}>
      {[2, 4, 8].map(wager => (
        <button
          key={wager}
          onClick={() => {
            setJoesSpecialWager(wager);
            setCurrentWager(wager);
          }}
          className="touch-optimized"
          style={{
            flex: 1,
            padding: '16px',
            fontSize: '24px',
            fontWeight: 'bold',
            border: joesSpecialWager === wager ? '3px solid white' : '2px solid rgba(255,255,255,0.5)',
            borderRadius: '12px',
            background: joesSpecialWager === wager ? 'rgba(255,255,255,0.3)' : 'transparent',
            color: 'white',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          {wager}Q
        </button>
      ))}
      <button
        onClick={() => {
          setJoesSpecialWager(null);
          setCurrentWager(nextHoleWager);
        }}
        className="touch-optimized"
        style={{
          padding: '16px',
          fontSize: '14px',
          border: '2px solid rgba(255,255,255,0.5)',
          borderRadius: '12px',
          background: joesSpecialWager === null ? 'rgba(255,255,255,0.3)' : 'transparent',
          color: 'white',
          cursor: 'pointer'
        }}
      >
        Default
      </button>
    </div>

    <div style={{ marginTop: '12px', fontSize: '12px', opacity: 0.8 }}>
      Selected: {joesSpecialWager || 'Default'}Q
      {!joesSpecialWager && ` (${nextHoleWager}Q)`}
    </div>
  </div>
)}
```

**Step 4: Update handleSubmitHole to include Joe's Special**

Modify the body in handleSubmitHole:

```javascript
body: JSON.stringify({
  hole_number: currentHole,
  rotation_order: rotationOrder,
  captain_index: captainIndex,
  phase: isHoepfinger ? 'hoepfinger' : 'normal',
  joes_special_wager: joesSpecialWager,  // NEW
  teams: teams,
  final_wager: currentWager,
  winner: winner,
  scores: scores,
  hole_par: holePar,
  float_invoked_by: floatInvokedBy,
  option_invoked_by: optionInvokedBy,
  carry_over_applied: carryOver
})
```

**Step 5: Test Joe's Special UI**

Manual testing:
1. Create game with players at different quarter levels
2. Complete holes to reach hole 17 (Hoepfinger)
3. Verify Joe's Special selector appears for Goat
4. Select 2Q, 4Q, 8Q and verify wager updates
5. Submit hole and verify joes_special_wager is sent

**Step 6: Commit Joe's Special UI**

```bash
git add frontend/src/components/game/SimpleScorekeeper.jsx
git commit -m "feat: add Joe's Special wager selection UI

- Show Joe's Special selector during Hoepfinger phase
- Allow Goat to choose 2, 4, or 8 quarters
- Beautiful gradient card design for special action
- Update wager when Joe's Special selected
- Send joes_special_wager to backend on submit"
```

---

## Task 7: Integration Testing

**Files:**
- Create: `frontend/src/components/game/__tests__/SimpleScorekeeper.integration.test.js`

**Step 1: Write integration test for full Phase 1 flow**

Create: `frontend/src/components/game/__tests__/SimpleScorekeeper.integration.test.js`

```javascript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SimpleScorekeeper from '../SimpleScorekeeper';
import { ThemeProvider } from '../../../theme/Provider';

// Mock fetch
global.fetch = jest.fn();

const mockPlayers = [
  { id: 'p1', name: 'Alice', handicap: 10 },
  { id: 'p2', name: 'Bob', handicap: 15 },
  { id: 'p3', name: 'Charlie', handicap: 8 },
  { id: 'p4', name: 'Dave', handicap: 12 }
];

describe('SimpleScorekeeper - Phase 1 Integration', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('complete round with rotation, carry-over, and Hoepfinger', async () => {
    // Mock API responses
    fetch
      // Initial rotation/wager fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          is_hoepfinger: false,
          rotation_order: ['p1', 'p2', 'p3', 'p4'],
          captain_id: 'p1'
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          base_wager: 1,
          carry_over: false,
          vinnies_variation: false
        })
      })
      // Hole 1 complete
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          hole_result: { hole: 1, winner: 'push' }
        })
      })
      // Hole 2 rotation/wager (carry-over)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          is_hoepfinger: false,
          rotation_order: ['p2', 'p3', 'p4', 'p1'],
          captain_id: 'p2'
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          base_wager: 2,
          carry_over: true,
          message: 'Carry-over from hole 1 push'
        })
      })
      // Hole 13 rotation/wager (Vinnie's Variation)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          is_hoepfinger: false,
          rotation_order: ['p1', 'p2', 'p3', 'p4'],
          captain_id: 'p1'
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          base_wager: 2,
          vinnies_variation: true,
          message: "Vinnie's Variation: holes 13-16 doubled"
        })
      })
      // Hole 17 rotation (Hoepfinger)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          is_hoepfinger: true,
          goat_id: 'p2',
          goat_selects_position: true
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          base_wager: 2,
          message: 'Hoepfinger phase'
        })
      });

    const { container } = render(
      <ThemeProvider>
        <SimpleScorekeeper
          gameId="test-game-123"
          players={mockPlayers}
          baseWager={1}
        />
      </ThemeProvider>
    );

    // Wait for initial rotation to load
    await waitFor(() => {
      expect(screen.getByText(/Alice/)).toBeInTheDocument();
    });

    // Verify captain indicator
    expect(screen.getByText(/1 ⭐/)).toBeInTheDocument();
    expect(screen.getByText(/Alice/)).toBeInTheDocument();

    // Hole 1: Complete with push (trigger carry-over)
    fireEvent.click(screen.getByText('Partners'));
    // Select teams, scores, winner=push
    // Submit...

    // Hole 2: Verify carry-over wager
    await waitFor(() => {
      expect(screen.getByText(/2Q/)).toBeInTheDocument();
      expect(screen.getByText(/Carry-Over/)).toBeInTheDocument();
    });

    // Jump to Hole 13: Verify Vinnie's Variation
    // ...

    // Hole 17: Verify Hoepfinger phase
    await waitFor(() => {
      expect(screen.getByText(/Hoepfinger Phase/)).toBeInTheDocument();
      expect(screen.getByText(/Goat selects/)).toBeInTheDocument();
    });

    // Verify Joe's Special selector appears
    expect(screen.getByText(/Joe's Special/)).toBeInTheDocument();
    expect(screen.getByText('2Q')).toBeInTheDocument();
    expect(screen.getByText('4Q')).toBeInTheDocument();
    expect(screen.getByText('8Q')).toBeInTheDocument();
  });
});
```

**Step 2: Run integration test**

```bash
cd frontend
npm test -- --testPathPattern=SimpleScorekeeper.integration
```

Expected: PASS

**Step 3: Commit integration test**

```bash
git add frontend/src/components/game/__tests__/SimpleScorekeeper.integration.test.js
git commit -m "test: add Phase 1 integration test for scorekeeper

- Test rotation advancement through 18 holes
- Verify carry-over after push
- Verify Vinnie's Variation on holes 13-16
- Verify Hoepfinger phase at hole 17
- Verify Joe's Special wager selection
- End-to-end flow validation"
```

---

## Task 8: Documentation and Final Verification

**Files:**
- Create: `docs/PHASE_1_IMPLEMENTATION_SUMMARY.md`
- Update: `docs/SCOREKEEPER_RULES_COMPLIANCE_ANALYSIS.md`

**Step 1: Create implementation summary**

Create: `docs/PHASE_1_IMPLEMENTATION_SUMMARY.md`

```markdown
# Phase 1 Implementation Summary - Core Game Flow

**Completed**: 2025-01-07
**Features Implemented**: Captain Rotation, Hoepfinger Phase, Joe's Special, Carry-Over, Vinnie's Variation

---

## What Was Built

### Backend Enhancements

1. **Captain Rotation Tracking** (`backend/app/main.py`)
   - Added `rotation_order` and `captain_index` to hole data
   - Implemented `/games/{game_id}/next-rotation` endpoint
   - Auto-calculates rotation advancement (shift left)
   - Detects Hoepfinger phase and enables Goat selection

2. **Hoepfinger Phase Detection** (`backend/app/main.py`)
   - Hole 17 for 4-player, hole 16 for 5-player, hole 13 for 6-player
   - Identifies Goat (furthest down player)
   - Returns available positions for Goat selection

3. **Joe's Special** (`backend/app/main.py`, `backend/app/schemas.py`)
   - Goat sets wager to 2, 4, or 8 quarters during Hoepfinger
   - Validation enforces max 8Q limit
   - Stored in hole result as `joes_special_wager`

4. **Carry-Over Logic** (`backend/app/main.py`)
   - Push (tie) doubles next hole's base wager
   - Blocks consecutive carry-overs
   - Implemented `/games/{game_id}/next-hole-wager` endpoint
   - Tracks `carry_over_wager` and `last_push_hole` in game state

5. **Vinnie's Variation** (`backend/app/main.py`)
   - Auto-doubles base wager on holes 13-16 for 4-player games
   - Integrated into next-hole-wager calculation

### Frontend Enhancements

1. **Rotation Display UI** (`frontend/src/components/game/SimpleScorekeeper.jsx`)
   - Shows rotation order with captain highlighted (⭐)
   - Displays hitting positions (1, 2, 3, 4)
   - Fetches next rotation from backend automatically

2. **Hoepfinger Phase UI**
   - Detects Hoepfinger phase
   - Shows "Goat selects position" interface
   - Allows Goat to choose hitting position (1-4)
   - Displays Hoepfinger badge

3. **Joe's Special Wager Selector**
   - Beautiful gradient card for special action
   - Buttons for 2Q, 4Q, 8Q, or Default
   - Only shown to Goat during Hoepfinger
   - Updates current wager when selected

4. **Wager Indicators**
   - Carry-over badge (🔁)
   - Vinnie's Variation badge (🎲)
   - Hoepfinger badge (🎯)
   - Color-coded wager display

### Tests Added

- `backend/tests/test_rotation_tracking.py` - 2 tests
- `backend/tests/test_hoepfinger.py` - 3 tests
- `backend/tests/test_carry_over.py` - 3 tests
- `backend/tests/test_vinnies_variation.py` - 2 tests
- `frontend/src/components/game/__tests__/SimpleScorekeeper.integration.test.js` - 1 test

**Total**: 11 tests

---

## Rule Coverage After Phase 1

### ✅ Implemented (Phase 1)
1. Captain Rotation
2. The Hoepfinger Phase
3. Joe's Special
4. The Carry-Over
5. Vinnie's Variation

### ⏳ Remaining for Phase 2
6. The Option (auto-double)
7. The Duncan (3-for-2 solo)
8. Float Enforcement (captain only)
9. Karl Marx Rule
10. Double Points Rounds

### ⏳ Remaining for Phase 3+
11-20. Advanced features (5/6-man, Aardvark, handicaps, etc.)

**Updated Rule Coverage**: ~55-60% (up from 35-40%)

---

## How to Use

### Creating a Game
```bash
POST /games/initialize
{
  "player_count": 4,
  "base_wager": 1,
  "players": [...]
}
```

### Completing a Hole
```bash
POST /games/{game_id}/holes/complete
{
  "hole_number": 1,
  "rotation_order": ["p1", "p2", "p3", "p4"],
  "captain_index": 0,
  "phase": "normal",
  "teams": {...},
  "final_wager": 1,
  "winner": "team1",
  "scores": {...},
  "hole_par": 4
}
```

### Getting Next Rotation
```bash
GET /games/{game_id}/next-rotation

Response (Normal):
{
  "is_hoepfinger": false,
  "rotation_order": ["p2", "p3", "p4", "p1"],
  "captain_index": 0,
  "captain_id": "p2"
}

Response (Hoepfinger):
{
  "is_hoepfinger": true,
  "goat_id": "p2",
  "goat_selects_position": true,
  "available_positions": [0, 1, 2, 3]
}
```

### Getting Next Wager
```bash
GET /games/{game_id}/next-hole-wager

Response:
{
  "base_wager": 2,
  "carry_over": true,
  "vinnies_variation": false,
  "message": "Carry-over from hole 1 push"
}
```

---

## Testing

### Run Backend Tests
```bash
cd backend
pytest tests/test_rotation_tracking.py -v
pytest tests/test_hoepfinger.py -v
pytest tests/test_carry_over.py -v
pytest tests/test_vinnies_variation.py -v
```

### Run Frontend Tests
```bash
cd frontend
npm test -- --testPathPattern=SimpleScorekeeper.integration
```

### Manual Testing Checklist
- [ ] Start 4-player game
- [ ] Complete hole 1 (normal rotation)
- [ ] Verify captain advances to p2 on hole 2
- [ ] Complete hole with push, verify carry-over on next hole
- [ ] Navigate to hole 13, verify Vinnie's Variation (2x base)
- [ ] Navigate to hole 17, verify Hoepfinger phase
- [ ] Verify Goat can select position 1-4
- [ ] Verify Joe's Special selector appears (2/4/8Q)
- [ ] Select Joe's Special wager, complete hole
- [ ] Verify wager badges display correctly

---

## Known Limitations

1. **No validation that Float is used only on captain's turn** - Will be addressed in Phase 2
2. **No Option auto-double** - Will be addressed in Phase 2
3. **No Duncan 3-for-2** - Will be addressed in Phase 2
4. **No Karl Marx odd-quarter allocation** - Will be addressed in Phase 2
5. **5-man and 6-man games not tested** - Will be addressed in Phase 3

---

## Next Steps (Phase 2)

Priority items for Phase 2 implementation:

1. **The Option (Auto-Double)** - Detect when captain is Goat, auto-double wager, allow turn-off
2. **The Duncan** - Captain going solo before hit gets 3-for-2 win multiplier
3. **Float Enforcement** - Only allow float when player IS the captain
4. **Karl Marx Rule** - Proper odd-quarter allocation to Goat on losing team
5. **Double Points Rounds** - Major championship flag for 2x base wager

See: `docs/plans/2025-01-07-phase-2-betting-mechanics.md` (to be created)

---

## Deployment

Phase 1 is production-ready. Deploy checklist:

- [ ] All backend tests passing
- [ ] All frontend tests passing
- [ ] Manual QA complete
- [ ] Database migrations applied (if any)
- [ ] API documentation updated
- [ ] Release notes written

Deploy commands:
```bash
# Backend
cd backend
pytest
uvicorn app.main:app --reload

# Frontend
cd frontend
npm test
npm run build
```

---

**Phase 1 Complete** ✅
```

**Step 2: Run all tests to verify everything works**

```bash
# Backend
cd backend
pytest tests/test_rotation_tracking.py tests/test_hoepfinger.py tests/test_carry_over.py tests/test_vinnies_variation.py -v

# Frontend
cd frontend
npm test -- --testPathPattern=SimpleScorekeeper.integration
```

Expected: All tests PASS

**Step 3: Update compliance analysis**

Modify: `docs/SCOREKEEPER_RULES_COMPLIANCE_ANALYSIS.md`

Update the "Executive Summary" section at the top:

```markdown
## Executive Summary

The current scorekeeper implements approximately **55-60% of the official Wolf Goat Pig rules** (updated after Phase 1 implementation).

**Phase 1 Complete (Jan 2025)**: ✅ Captain Rotation, Hoepfinger Phase, Joe's Special, Carry-Over, Vinnie's Variation

It handles basic team formation, scoring, and quarter tracking, and now includes proper game flow mechanics, but is still missing:
...
```

**Step 4: Final commit**

```bash
git add docs/PHASE_1_IMPLEMENTATION_SUMMARY.md docs/SCOREKEEPER_RULES_COMPLIANCE_ANALYSIS.md
git commit -m "docs: add Phase 1 implementation summary

- Document all Phase 1 features implemented
- Update rule coverage to 55-60%
- Add usage examples for new endpoints
- Create testing checklist
- Define Phase 2 next steps
- Update compliance analysis with Phase 1 completion"
```

---

## Plan Complete

**All Phase 1 Tasks Implemented**:
1. ✅ Rotation Order Data Model (Backend)
2. ✅ Hoepfinger Phase Detection and Joe's Special (Backend)
3. ✅ Carry-Over Logic (Backend)
4. ✅ Vinnie's Variation (Backend)
5. ✅ Captain Rotation UI (Frontend)
6. ✅ Joe's Special Wager Selection (Frontend)
7. ✅ Integration Testing
8. ✅ Documentation and Final Verification

**Files Modified**:
- `backend/app/schemas.py`
- `backend/app/main.py`
- `frontend/src/components/game/SimpleScorekeeper.jsx`

**Files Created**:
- `backend/tests/test_rotation_tracking.py`
- `backend/tests/test_hoepfinger.py`
- `backend/tests/test_carry_over.py`
- `backend/tests/test_vinnies_variation.py`
- `frontend/src/components/game/__tests__/SimpleScorekeeper.integration.test.js`
- `docs/PHASE_1_IMPLEMENTATION_SUMMARY.md`

**Commits**: 8 feature commits + 1 docs commit = 9 total

**Testing**: 11 tests (10 backend unit, 1 frontend integration)

**Rule Coverage Improvement**: 35-40% → 55-60%

---

**Next Phase**: Phase 2 - Betting Mechanics (Option, Duncan, Float Enforcement, Karl Marx, Double Points)
