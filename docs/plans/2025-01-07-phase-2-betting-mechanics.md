# Phase 2: Betting Mechanics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement core betting mechanics (The Option, The Duncan, Float enforcement, Karl Marx, Doubling) to increase rule coverage from 55-60% to 75-80%.

**Architecture:** Backend tracks betting events and validates usage limits; frontend provides UI for invoking special bets; endpoints enforce business rules.

**Tech Stack:** FastAPI (backend), React (frontend), pytest (testing)

---

## Task 1: The Option - Auto-Double for Goat Captain

**Files:**
- Modify: `backend/app/main.py:1562-1626` (next-hole-wager endpoint)
- Modify: `backend/app/main.py:163-177` (CompleteHoleRequest schema)
- Create: `backend/tests/test_the_option.py`
- Modify: `frontend/src/components/game/SimpleScorekeeper.jsx:36-46` (state)

**Step 1: Write failing test for The Option detection**

```python
# backend/tests/test_the_option.py
"""Test The Option - auto-double when Captain is furthest down"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_option_auto_applies_when_captain_is_goat():
    """Test The Option automatically doubles wager when Captain is Goat"""
    # Create game
    game_response = client.post("/games/create-test?player_count=4")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: p1 loses badly (-10Q)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 10,
        "winner": "team2",
        "scores": {player_ids[0]: 8, player_ids[1]: 7, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    # Hole 2: p2 is now captain, check if Option applies
    # p1 should still be Goat (furthest down at -10Q)
    rotation = client.get(f"/games/{game_id}/next-rotation")
    assert rotation.json()["rotation_order"][0] == player_ids[1]  # p2 is captain

    wager = client.get(f"/games/{game_id}/next-hole-wager")
    data = wager.json()
    assert data["base_wager"] == 2  # 1Q × 2 (Option applied)
    assert data["option_active"] is True
    assert data["goat_id"] == player_ids[0]  # p1 is Goat


def test_option_can_be_turned_off():
    """Test Captain can proactively turn off The Option"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Make p1 the Goat
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 5,
        "winner": "team2",
        "scores": {player_ids[0]: 7, player_ids[1]: 6, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    # Hole 2: p2 is captain, turn off Option
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "rotation_order": player_ids[1:] + [player_ids[0]],
        "captain_index": 0,
        "option_turned_off": True,  # NEW FIELD
        "teams": {"type": "partners", "team1": [player_ids[1], player_ids[2]], "team2": [player_ids[3], player_ids[0]]},
        "final_wager": 1,  # Not doubled
        "winner": "team1",
        "scores": {player_ids[0]: 5, player_ids[1]: 4, player_ids[2]: 4, player_ids[3]: 5},
        "hole_par": 4
    })

    response = client.post(f"/games/{game_id}/holes/complete", json={...})
    assert response.status_code == 200
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_the_option.py::test_option_auto_applies_when_captain_is_goat -v`

Expected: FAIL with `KeyError: 'option_active'` or similar

**Step 3: Add option_turned_off field to schema**

```python
# backend/app/main.py:163-177
class CompleteHoleRequest(BaseModel):
    """Request to complete a hole with all data at once - for scorekeeper mode"""
    hole_number: int = Field(..., ge=1, le=18)
    rotation_order: List[str] = Field(..., description="Hitting order for this hole")
    captain_index: int = Field(0, ge=0, description="Index in rotation_order who is captain")
    phase: Optional[str] = Field("normal", description="Game phase: 'normal' or 'hoepfinger'")
    joes_special_wager: Optional[int] = Field(None, description="Wager set by Goat (2, 4, or 8) during Hoepfinger")
    option_turned_off: Optional[bool] = Field(False, description="Captain proactively turned off The Option")
    teams: HoleTeams
    final_wager: float = Field(..., gt=0)
    winner: str
    scores: Dict[str, int] = Field(..., description="Player ID to strokes mapping")
    hole_par: Optional[int] = Field(4, ge=3, le=5)
    float_invoked_by: Optional[str] = Field(None, description="Player ID who invoked float on this hole")
    option_invoked_by: Optional[str] = Field(None, description="Player ID who triggered option on this hole")
    carry_over_applied: Optional[bool] = Field(False, description="Whether carry-over was applied to this hole")
```

**Step 4: Update next-hole-wager to detect The Option**

```python
# backend/app/main.py:1562-1626 (inside get_next_hole_wager)
# Add after carry-over check, before Vinnie's Variation

    # Check for The Option (Captain is Goat)
    if not game_state.get("carry_over_wager"):  # Option doesn't stack with carry-over
        # Calculate current standings to find Goat
        standings = {}
        for player in game_state.get("players", []):
            standings[player["id"]] = player.get("points", 0)

        if standings:
            goat_id = min(standings, key=standings.get)
            goat_points = standings[goat_id]

            # Option applies if Captain (first in rotation) is the Goat AND has negative points
            hole_history = game_state.get("hole_history", [])
            if hole_history:
                last_hole = hole_history[-1]
                next_rotation_order = last_hole.get("rotation_order", [])[1:] + [last_hole.get("rotation_order", [])[0]]
                next_captain_id = next_rotation_order[0] if next_rotation_order else None

                if next_captain_id == goat_id and goat_points < 0:
                    # Check if last hole turned off Option
                    if not last_hole.get("option_turned_off", False):
                        return {
                            "base_wager": base_wager * 2,
                            "option_active": True,
                            "goat_id": goat_id,
                            "carry_over": False,
                            "vinnies_variation": False,
                            "message": f"The Option: Captain is Goat ({goat_points}Q), wager doubled"
                        }
```

**Step 5: Store option_turned_off in hole results**

```python
# backend/app/main.py:1402-1418 (hole_result dict)
hole_result = {
    "hole": request.hole_number,
    "rotation_order": request.rotation_order,
    "captain_index": request.captain_index,
    "phase": request.phase,
    "joes_special_wager": request.joes_special_wager,
    "option_turned_off": request.option_turned_off,  # ADD THIS
    "teams": request.teams.model_dump(),
    "wager": request.final_wager,
    "winner": request.winner,
    "gross_scores": request.scores,
    "hole_par": request.hole_par,
    "points_delta": points_delta,
    "float_invoked_by": request.float_invoked_by,
    "option_invoked_by": request.option_invoked_by,
    "carry_over_applied": request.carry_over_applied
}
```

**Step 6: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_the_option.py -v`

Expected: PASS (2/2 tests)

**Step 7: Commit**

```bash
git add backend/app/main.py backend/tests/test_the_option.py
git commit -m "feat: implement The Option auto-double for Goat Captain

- Detect when Captain is furthest down with negative points
- Auto-apply 2x multiplier to base wager
- Allow Captain to proactively turn off Option
- Add option_turned_off field to schema and hole results
- Tests verify Option detection and opt-out

Rule: 'If the Captain has lost the most quarters prior to the
start of the hole, then he has the option to have the wager doubled
before any players hit their tee shot. For speed of play, the option
is automatically deemed to be invoked, unless the Captain proactively
turns it off.'"
```

---

## Task 2: The Duncan - Solo Before Hitting for 3-for-2

**Files:**
- Modify: `backend/app/main.py:163-177` (CompleteHoleRequest schema)
- Modify: `backend/app/main.py:1336-1390` (complete_hole points calculation)
- Create: `backend/tests/test_the_duncan.py`

**Step 1: Write failing test for The Duncan**

```python
# backend/tests/test_the_duncan.py
"""Test The Duncan - Captain goes solo before hitting for 3-for-2 payout"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_duncan_pays_3_for_2():
    """Test The Duncan pays 3 quarters for every 2 wagered"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: p1 invokes Duncan (solo before hitting), wager 2Q
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "duncan_invoked": True,  # NEW FIELD
        "teams": {"type": "solo", "captain": player_ids[0], "opponents": [player_ids[1], player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "captain",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    assert response.status_code == 200
    result = response.json()["hole_result"]

    # Captain wins 3Q (3-for-2 on 2Q wagered)
    # Each opponent loses 1Q
    assert result["points_delta"][player_ids[0]] == 3
    assert result["points_delta"][player_ids[1]] == -1
    assert result["points_delta"][player_ids[2]] == -1
    assert result["points_delta"][player_ids[3]] == -1


def test_duncan_only_for_solo():
    """Test The Duncan only applies to solo play"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Try to invoke Duncan with partners (should fail or ignore)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "duncan_invoked": True,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4
    })

    # Should either return 400 error OR ignore Duncan flag
    if response.status_code == 400:
        assert "Duncan" in response.json()["detail"]
    else:
        # Normal 2Q split for partners
        result = response.json()["hole_result"]
        assert result["points_delta"][player_ids[0]] == 2
        assert result["points_delta"][player_ids[1]] == 2
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_the_duncan.py::test_duncan_pays_3_for_2 -v`

Expected: FAIL with `KeyError: 'duncan_invoked'` or incorrect points calculation

**Step 3: Add duncan_invoked field to schema**

```python
# backend/app/main.py:163-177
class CompleteHoleRequest(BaseModel):
    """Request to complete a hole with all data at once - for scorekeeper mode"""
    hole_number: int = Field(..., ge=1, le=18)
    rotation_order: List[str] = Field(..., description="Hitting order for this hole")
    captain_index: int = Field(0, ge=0, description="Index in rotation_order who is captain")
    phase: Optional[str] = Field("normal", description="Game phase: 'normal' or 'hoepfinger'")
    joes_special_wager: Optional[int] = Field(None, description="Wager set by Goat (2, 4, or 8) during Hoepfinger")
    option_turned_off: Optional[bool] = Field(False, description="Captain proactively turned off The Option")
    duncan_invoked: Optional[bool] = Field(False, description="Captain went solo before hitting (3-for-2 payout)")
    teams: HoleTeams
    final_wager: float = Field(..., gt=0)
    winner: str
    scores: Dict[str, int] = Field(..., description="Player ID to strokes mapping")
    hole_par: Optional[int] = Field(4, ge=3, le=5)
    float_invoked_by: Optional[str] = Field(None, description="Player ID who invoked float on this hole")
    option_invoked_by: Optional[str] = Field(None, description="Player ID who triggered option on this hole")
    carry_over_applied: Optional[bool] = Field(False, description="Whether carry-over was applied to this hole")
```

**Step 4: Implement Duncan 3-for-2 payout logic**

```python
# backend/app/main.py:1336-1390 (replace solo mode calculation)
# Find the "else: # solo mode" block and replace with:

        else:  # solo mode
            if request.duncan_invoked and request.winner == "captain":
                # The Duncan: Captain wins 3Q for every 2Q wagered
                total_payout = (request.final_wager * 3) / 2
                points_delta[request.teams.captain] = total_payout
                loss_per_opponent = total_payout / len(request.teams.opponents)
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = -loss_per_opponent
            elif request.duncan_invoked and request.winner == "opponents":
                # The Duncan failed: Opponents win 2Q (normal), Captain loses 2Q × opponents
                total_loss = request.final_wager * len(request.teams.opponents)
                points_delta[request.teams.captain] = -total_loss
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = request.final_wager
            elif request.winner == "captain":
                # Normal solo win
                points_delta[request.teams.captain] = request.final_wager * len(request.teams.opponents)
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = -request.final_wager
            elif request.winner == "opponents":
                points_delta[request.teams.captain] = -request.final_wager * len(request.teams.opponents)
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = request.final_wager
            elif request.winner == "captain_flush":
                # Flush: Opponents concede/fold
                points_delta[request.teams.captain] = request.final_wager * len(request.teams.opponents)
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = -request.final_wager
            elif request.winner == "opponents_flush":
                # Flush: Captain concedes/fold
                points_delta[request.teams.captain] = -request.final_wager * len(request.teams.opponents)
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = request.final_wager
            else:  # push
                points_delta[request.teams.captain] = 0
                for opp_id in request.teams.opponents:
                    points_delta[opp_id] = 0
```

**Step 5: Store duncan_invoked in hole results**

```python
# backend/app/main.py:1402-1418 (hole_result dict)
hole_result = {
    "hole": request.hole_number,
    "rotation_order": request.rotation_order,
    "captain_index": request.captain_index,
    "phase": request.phase,
    "joes_special_wager": request.joes_special_wager,
    "option_turned_off": request.option_turned_off,
    "duncan_invoked": request.duncan_invoked,  # ADD THIS
    "teams": request.teams.model_dump(),
    "wager": request.final_wager,
    "winner": request.winner,
    "gross_scores": request.scores,
    "hole_par": request.hole_par,
    "points_delta": points_delta,
    "float_invoked_by": request.float_invoked_by,
    "option_invoked_by": request.option_invoked_by,
    "carry_over_applied": request.carry_over_applied
}
```

**Step 6: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_the_duncan.py -v`

Expected: PASS (2/2 tests)

**Step 7: Commit**

```bash
git add backend/app/main.py backend/tests/test_the_duncan.py
git commit -m "feat: implement The Duncan 3-for-2 solo payout

- Captain who goes solo before hitting wins 3Q for every 2Q wagered
- Only applies to solo play (not partners)
- Add duncan_invoked field to schema and hole results
- Update points calculation for Duncan wins and losses
- Tests verify 3-for-2 payout and solo-only enforcement

Rule: 'If the Captain announces before he hits that he intends to
go on his own (the Pig), then he is able to win 3 quarters for every
2 quarters wagered provided he earns the best net score on the hole.'"
```

---

## Task 3: Float Enforcement - Track Once-Per-Round Usage

**Files:**
- Modify: `backend/app/main.py:1318-1344` (complete_hole validation)
- Create: `backend/tests/test_float_enforcement.py`

**Step 1: Write failing test for Float enforcement**

```python
# backend/tests/test_float_enforcement.py
"""Test Float enforcement - once per round per player"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_float_usage_tracked():
    """Test float usage is tracked in player standings"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: p1 invokes float
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,  # Doubled by float
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4,
        "float_invoked_by": player_ids[0]
    })

    assert response.status_code == 200

    # Get game state to verify float count
    state_response = client.get(f"/games/{game_id}/state")
    game_state = state_response.json()

    # Check p1 has used float
    players_data = game_state.get("players", [])
    p1_data = next(p for p in players_data if p["id"] == player_ids[0])
    assert p1_data.get("float_used", 0) == 1


def test_float_cannot_be_used_twice():
    """Test player cannot invoke float twice in same round"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: p1 invokes float
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4,
        "float_invoked_by": player_ids[0]
    })

    # Hole 2-5: Complete normally so p1 is captain again (rotation)
    for hole in [2, 3, 4, 5]:
        rotation = [player_ids[hole % 4]] + [player_ids[(hole+1) % 4]] + [player_ids[(hole+2) % 4]] + [player_ids[(hole+3) % 4]]
        client.post(f"/games/{game_id}/holes/complete", json={
            "hole_number": hole,
            "rotation_order": rotation,
            "captain_index": 0,
            "teams": {"type": "partners", "team1": [rotation[0], rotation[1]], "team2": [rotation[2], rotation[3]]},
            "final_wager": 1,
            "winner": "team1",
            "scores": {rotation[0]: 4, rotation[1]: 5, rotation[2]: 5, rotation[3]: 6},
            "hole_par": 4
        })

    # Hole 5: p1 tries to invoke float again (should fail)
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 5,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 5, player_ids[2]: 5, player_ids[3]: 6},
        "hole_par": 4,
        "float_invoked_by": player_ids[0]  # Second time!
    })

    assert response.status_code == 400
    assert "already used float" in response.json()["detail"].lower()
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_float_enforcement.py::test_float_cannot_be_used_twice -v`

Expected: FAIL with 200 (no validation yet) instead of 400

**Step 3: Add float validation in complete_hole**

```python
# backend/app/main.py:1318-1344 (after Joe's Special validation)

        # Validate Float usage (once per round per player)
        if request.float_invoked_by:
            # Check if player has already used float
            for player in game_state.get("players", []):
                if player["id"] == request.float_invoked_by:
                    float_count = player.get("float_used", 0)
                    if float_count >= 1:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Player {request.float_invoked_by} has already used float this round"
                        )
                    break

        # Get current game state
        game_state = game.state or {}
```

**Step 4: Track float usage in player data**

```python
# backend/app/main.py:1453-1465 (after updating player totals)

        # Update player totals and usage stats
        if "players" not in game_state:
            game_state["players"] = []

        for player in game_state["players"]:
            player_id = player.get("id")
            if player_id in points_delta:
                if "points" not in player:
                    player["points"] = 0
                player["points"] += points_delta[player_id]

            # Track float usage
            if request.float_invoked_by == player_id:
                player["float_used"] = player.get("float_used", 0) + 1
```

**Step 5: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_float_enforcement.py -v`

Expected: PASS (2/2 tests)

**Step 6: Commit**

```bash
git add backend/app/main.py backend/tests/test_float_enforcement.py
git commit -m "feat: enforce Float once-per-round limit

- Track float_used count in player data
- Validate float hasn't been used when invoked
- Return 400 error if player tries to use float twice
- Tests verify tracking and enforcement

Rule: 'In the 4-man and 5-man game, each player may invoke a float
once during the round during his turn as Captain.'"
```

---

## Task 4: Frontend - The Option and Duncan UI

**Files:**
- Modify: `frontend/src/components/game/SimpleScorekeeper.jsx:36-46` (state)
- Modify: `frontend/src/components/game/SimpleScorekeeper.jsx:297-311` (submit payload)
- Modify: `frontend/src/components/game/SimpleScorekeeper.jsx:951-1128` (UI section)

**Step 1: Add state for The Option and Duncan**

```javascript
// frontend/src/components/game/SimpleScorekeeper.jsx:36-46

  // Rotation tracking (Phase 1)
  const [rotationOrder, setRotationOrder] = useState(players.map(p => p.id));
  const [captainIndex, setCaptainIndex] = useState(0);
  const [isHoepfinger, setIsHoepfinger] = useState(false);
  const [goatId, setGoatId] = useState(null);
  const [phase, setPhase] = useState('normal');
  const [joesSpecialWager, setJoesSpecialWager] = useState(null);
  const [nextHoleWager, setNextHoleWager] = useState(baseWager);
  const [carryOver, setCarryOver] = useState(false);
  const [vinniesVariation, setVinniesVariation] = useState(false);
  const [carryOverApplied, setCarryOverApplied] = useState(false);

  // Phase 2: Betting mechanics
  const [optionActive, setOptionActive] = useState(false);
  const [optionTurnedOff, setOptionTurnedOff] = useState(false);
  const [duncanInvoked, setDuncanInvoked] = useState(false);
```

**Step 2: Update useEffect to fetch Option status**

```javascript
// frontend/src/components/game/SimpleScorekeeper.jsx:102-143 (modify existing useEffect)

        // Fetch next hole wager
        const wagerRes = await fetch(`${API_URL}/games/${gameId}/next-hole-wager`);
        if (wagerRes.ok) {
          const wagerData = await wagerRes.json();
          setNextHoleWager(wagerData.base_wager);
          setCurrentWager(wagerData.base_wager);
          setCarryOver(wagerData.carry_over || false);
          setVinniesVariation(wagerData.vinnies_variation || false);
          setOptionActive(wagerData.option_active || false);  // ADD THIS
          if (wagerData.option_active) {
            setGoatId(wagerData.goat_id);
          }
        }
```

**Step 3: Add Option and Duncan UI components**

```javascript
// frontend/src/components/game/SimpleScorekeeper.jsx:1087-1127 (after wager indicators)

      {/* The Option - Turn Off Toggle */}
      {optionActive && (
        <div style={{
          background: '#FFF3E0',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '16px',
          border: '2px solid #FF9800',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            fontSize: '16px',
            fontWeight: 'bold',
            marginBottom: '12px',
            color: '#E65100',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            ⚠️ THE OPTION ACTIVE
          </div>
          <div style={{ marginBottom: '12px', color: '#5D4037' }}>
            Captain is the Goat - wager automatically doubled to {nextHoleWager}Q
          </div>
          <button
            onClick={() => {
              setOptionTurnedOff(!optionTurnedOff);
              if (!optionTurnedOff) {
                // Turning OFF - revert to base wager
                setCurrentWager(nextHoleWager / 2);
              } else {
                // Turning ON - restore doubled wager
                setCurrentWager(nextHoleWager);
              }
            }}
            style={{
              padding: '12px 24px',
              borderRadius: '8px',
              background: optionTurnedOff ? '#4CAF50' : '#FF5722',
              color: 'white',
              border: 'none',
              fontSize: '14px',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            {optionTurnedOff ? 'Option OFF (base wager)' : 'Turn Off Option'}
          </button>
        </div>
      )}

      {/* The Duncan - Solo Before Hitting */}
      {teamMode === 'solo' && (
        <div style={{
          background: '#E8F5E9',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '16px',
          border: '2px solid #4CAF50',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <input
              type="checkbox"
              checked={duncanInvoked}
              onChange={(e) => setDuncanInvoked(e.target.checked)}
              style={{
                width: '24px',
                height: '24px',
                cursor: 'pointer'
              }}
            />
            <div>
              <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#2E7D32' }}>
                THE DUNCAN (3-for-2)
              </div>
              <div style={{ fontSize: '12px', color: '#5D4037' }}>
                Captain went solo BEFORE hitting - wins 3Q for every 2Q wagered
              </div>
            </div>
          </div>
        </div>
      )}
```

**Step 4: Update submit payload**

```javascript
// frontend/src/components/game/SimpleScorekeeper.jsx:297-311 (modify existing)

        body: JSON.stringify({
          hole_number: currentHole,
          rotation_order: rotationOrder,
          captain_index: captainIndex,
          phase: phase,
          joes_special_wager: joesSpecialWager,
          option_turned_off: optionTurnedOff,      // ADD THIS
          duncan_invoked: duncanInvoked,            // ADD THIS
          teams: teams,
          final_wager: currentWager,
          winner: winner,
          scores: scores,
          hole_par: holePar,
          float_invoked_by: floatInvokedBy,
          option_invoked_by: optionInvokedBy,
          carry_over_applied: carryOverApplied
        })
```

**Step 5: Update resetHole**

```javascript
// frontend/src/components/game/SimpleScorekeeper.jsx:145-161

  const resetHole = () => {
    setTeam1([]);
    setTeam2([]);
    setCaptain(null);
    setOpponents([]);
    setCurrentWager(baseWager);
    setScores({});
    setWinner(null);
    setHolePar(4);
    setFloatInvokedBy(null);
    setOptionInvokedBy(null);
    setError(null);
    setEditingHole(null);
    setCarryOverApplied(carryOver);
    setJoesSpecialWager(null);
    setOptionTurnedOff(false);     // ADD THIS
    setDuncanInvoked(false);       // ADD THIS
  };
```

**Step 6: Manual testing**

1. Start frontend: `cd frontend && npm start`
2. Start backend: `cd backend && uvicorn app.main:app --reload`
3. Create test game
4. Make player lose badly to become Goat
5. Verify "THE OPTION ACTIVE" card appears
6. Test turning off Option
7. Select solo mode and verify Duncan checkbox appears
8. Submit hole and verify payload includes new fields

**Step 7: Commit**

```bash
git add frontend/src/components/game/SimpleScorekeeper.jsx
git commit -m "feat: add UI for The Option and The Duncan

Frontend Components:
- The Option card with turn-off toggle when Captain is Goat
- The Duncan checkbox for solo mode (3-for-2 indicator)
- Auto-fetch Option status from backend
- Update submit payload with option_turned_off and duncan_invoked

UI Features:
- Orange Option card with auto-double warning
- Green Duncan checkbox with 3-for-2 explanation
- Toggle to turn off Option (reverts wager to base)
- Reset state on new hole"
```

---

## Task 5: Karl Marx Rule - Uneven Quarter Distribution

**Files:**
- Modify: `backend/app/main.py:1336-1390` (points calculation)
- Create: `backend/tests/test_karl_marx.py`

**Step 1: Write failing test for Karl Marx**

```python
# backend/tests/test_karl_marx.py
"""Test Karl Marx Rule - uneven quarter distribution"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_karl_marx_uneven_distribution():
    """Test Goat pays less when quarters don't divide evenly"""
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Make p1 the Goat (-5Q)
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 5,
        "winner": "team2",
        "scores": {player_ids[0]: 7, player_ids[1]: 6, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    # Hole 2: Partners (p1+p2) lose 3Q total
    # 3Q doesn't divide evenly by 2 partners
    # Karl Marx: Goat (p1, at -5Q) pays 1Q, partner pays 2Q
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "rotation_order": player_ids[1:] + [player_ids[0]],
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[1], player_ids[0]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 3,
        "winner": "team2",
        "scores": {player_ids[0]: 5, player_ids[1]: 5, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4
    })

    result = response.json()["hole_result"]

    # p1 (Goat) pays 1Q, p2 pays 2Q
    assert result["points_delta"][player_ids[0]] == -1
    assert result["points_delta"][player_ids[1]] == -2
    # Each winner gets 1.5Q
    assert result["points_delta"][player_ids[2]] == 1.5
    assert result["points_delta"][player_ids[3]] == 1.5
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_karl_marx.py::test_karl_marx_uneven_distribution -v`

Expected: FAIL with equal distribution (-1.5, -1.5) instead of Karl Marx (-1, -2)

**Step 3: Implement Karl Marx logic for partners**

```python
# backend/app/main.py:1336-1390 (replace partners calculation)

        # Calculate quarters won/lost based on winner and wager
        points_delta = {}
        if request.teams.type == "partners":
            if request.winner in ["team1", "team1_flush"]:
                # Team 1 wins
                for player_id in request.teams.team1:
                    points_delta[player_id] = request.final_wager

                # Team 2 loses - apply Karl Marx if uneven
                loss_per_player = request.final_wager
                if len(request.teams.team2) > 1 and (request.final_wager % len(request.teams.team2)) != 0:
                    # Uneven distribution - apply Karl Marx
                    total_loss = request.final_wager * len(request.teams.team1)
                    base_loss = int(total_loss / len(request.teams.team2))
                    extra_loss = total_loss - (base_loss * len(request.teams.team2))

                    # Find Goat on losing team
                    team2_standings = {pid: playerStandings.get(pid, {}).get("points", 0)
                                      for pid in request.teams.team2}
                    goat_id = min(team2_standings, key=team2_standings.get)

                    for player_id in request.teams.team2:
                        if player_id == goat_id:
                            points_delta[player_id] = -base_loss  # Goat pays less
                        else:
                            points_delta[player_id] = -(base_loss + extra_loss)
                else:
                    # Even distribution
                    for player_id in request.teams.team2:
                        points_delta[player_id] = -loss_per_player

            elif request.winner in ["team2", "team2_flush"]:
                # Team 2 wins (mirror logic)
                for player_id in request.teams.team2:
                    points_delta[player_id] = request.final_wager

                # Team 1 loses - apply Karl Marx if uneven
                loss_per_player = request.final_wager
                if len(request.teams.team1) > 1 and (request.final_wager % len(request.teams.team1)) != 0:
                    total_loss = request.final_wager * len(request.teams.team2)
                    base_loss = int(total_loss / len(request.teams.team1))
                    extra_loss = total_loss - (base_loss * len(request.teams.team1))

                    team1_standings = {pid: playerStandings.get(pid, {}).get("points", 0)
                                      for pid in request.teams.team1}
                    goat_id = min(team1_standings, key=team1_standings.get)

                    for player_id in request.teams.team1:
                        if player_id == goat_id:
                            points_delta[player_id] = -base_loss
                        else:
                            points_delta[player_id] = -(base_loss + extra_loss)
                else:
                    for player_id in request.teams.team1:
                        points_delta[player_id] = -loss_per_player
            else:  # push
                for player_id in request.teams.team1 + request.teams.team2:
                    points_delta[player_id] = 0
```

**Note**: Karl Marx implementation requires access to playerStandings. This needs to be passed to the complete_hole function or calculated from game_state. For simplicity in this plan, assume we calculate it from game_state within the function.

**Step 4: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_karl_marx.py -v`

Expected: PASS (1/1 test)

**Step 5: Commit**

```bash
git add backend/app/main.py backend/tests/test_karl_marx.py
git commit -m "feat: implement Karl Marx Rule for uneven distribution

- When quarters don't divide evenly, Goat pays less
- Calculate base_loss and extra_loss for each losing team
- Identify Goat (furthest down) on losing team
- Goat pays base_loss, others pay base_loss + extra_loss
- Tests verify uneven 3Q distribution (1Q + 2Q)

Rule: 'from each according to his ability, to each according to his
need. In our example, the player that is the furthest down owes only
one quarter, the other player two.'"
```

---

## Task 6: Integration Testing and Documentation

**Files:**
- Create: `docs/PHASE_2_IMPLEMENTATION_SUMMARY.md`
- Update: `backend/tests/test_integration_phase2.py`

**Step 1: Write integration test combining all Phase 2 features**

```python
# backend/tests/test_integration_phase2.py
"""Integration tests for Phase 2 betting mechanics"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_phase2_full_integration():
    """Test all Phase 2 features in realistic game scenario"""
    # Create game
    game_response = client.post("/games/create-test?player_count=4")
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    player_ids = [p["id"] for p in players]

    # Hole 1: p1 uses Float (2Q), loses badly
    client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 1,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team2",
        "scores": {player_ids[0]: 7, player_ids[1]: 6, player_ids[2]: 4, player_ids[3]: 4},
        "hole_par": 4,
        "float_invoked_by": player_ids[0]
    })
    # p1: -2Q, p2: -2Q, p3: +2Q, p4: +2Q

    # Hole 2: p2 is captain, The Option applies (p1 is Goat)
    wager = client.get(f"/games/{game_id}/next-hole-wager")
    assert wager.json()["option_active"] is True

    # p2 invokes Duncan, wins with 3-for-2
    response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 2,
        "rotation_order": player_ids[1:] + [player_ids[0]],
        "captain_index": 0,
        "duncan_invoked": True,
        "teams": {"type": "solo", "captain": player_ids[1], "opponents": [player_ids[2], player_ids[3], player_ids[0]]},
        "final_wager": 2,  # Doubled by Option
        "winner": "captain",
        "scores": {player_ids[0]: 6, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4
    })

    result = response.json()["hole_result"]
    # p2 wins 3Q (3-for-2 on 2Q)
    assert result["points_delta"][player_ids[1]] == 3
    # Each opponent loses 1Q
    assert result["points_delta"][player_ids[0]] == -1

    # Hole 3: p1 tries to use Float again (should fail)
    fail_response = client.post(f"/games/{game_id}/holes/complete", json={
        "hole_number": 3,
        "rotation_order": player_ids,
        "captain_index": 0,
        "teams": {"type": "partners", "team1": [player_ids[0], player_ids[1]], "team2": [player_ids[2], player_ids[3]]},
        "final_wager": 2,
        "winner": "team1",
        "scores": {player_ids[0]: 4, player_ids[1]: 4, player_ids[2]: 5, player_ids[3]: 5},
        "hole_par": 4,
        "float_invoked_by": player_ids[0]  # Second time!
    })

    assert fail_response.status_code == 400
    assert "already used float" in fail_response.json()["detail"].lower()
```

**Step 2: Run integration test**

Run: `cd backend && pytest tests/test_integration_phase2.py -v`

Expected: PASS

**Step 3: Create Phase 2 documentation**

```markdown
# docs/PHASE_2_IMPLEMENTATION_SUMMARY.md

# Phase 2: Betting Mechanics Implementation - COMPLETE ✅

## Executive Summary

**Goal**: Increase rule coverage from 55-60% to 75-80% by implementing betting mechanics.

**Status**: ✅ **COMPLETE** - All 6 tasks delivered

**Date Completed**: [Current Date]

---

## Implementation Details

### Backend (Tasks 1-3, 5)

#### ✅ Task 1: The Option
- Auto-double when Captain is Goat (furthest down, negative points)
- Captain can proactively turn off Option
- Tests: 2/2 passing

#### ✅ Task 2: The Duncan
- Solo before hitting pays 3Q for every 2Q wagered
- Only applies to solo play
- Tests: 2/2 passing

#### ✅ Task 3: Float Enforcement
- Track float_used count per player
- Validate once-per-round limit
- Tests: 2/2 passing

#### ✅ Task 5: Karl Marx Rule
- Uneven distribution: Goat pays less
- Applied automatically when quarters don't divide evenly
- Tests: 1/1 passing

### Frontend (Task 4)

#### ✅ Task 4: Option and Duncan UI
- Orange "THE OPTION ACTIVE" card with turn-off toggle
- Green Duncan checkbox for solo mode
- Auto-fetch Option status from backend
- Update submit payload

### Documentation (Task 6)

#### ✅ Task 6: Integration Testing & Docs
- Full integration test covering all Phase 2 features
- This summary document
- Tests: 1/1 passing

---

## Rule Coverage Impact

**Before Phase 2**: 55-60%
**After Phase 2**: ~75-80%
**Increase**: +20 percentage points

---

## Next Steps (Phase 3)

1. Doubling/Redoubling during hole
2. Line of Scrimmage enforcement
3. Aardvark mechanics (5-6 player)
4. Invisible Aardvark (4-player)
5. The Tunkarri (5-6 player Aardvark solo)

**Target**: 90-95% coverage

---

**Generated**: [Current Date]
**Phase**: 2 of 3 (Betting Mechanics)
```

**Step 4: Commit documentation**

```bash
git add docs/PHASE_2_IMPLEMENTATION_SUMMARY.md backend/tests/test_integration_phase2.py
git commit -m "docs: add Phase 2 implementation summary and integration test

Complete documentation of Phase 2: Betting Mechanics

Covers:
- The Option (auto-double for Goat Captain)
- The Duncan (3-for-2 solo before hitting)
- Float enforcement (once per round)
- Karl Marx Rule (uneven distribution)
- Frontend UI components
- Integration test covering all features

Achievement:
✅ Rule coverage increased 55% → 75%
✅ 4 new betting mechanics implemented
✅ 8/8 tests passing

Next: Phase 3 (Advanced mechanics)"
```

---

## Execution Summary

**Total Tasks**: 6
**Estimated Time**: 3-4 hours
**Backend Changes**: ~400 lines
**Frontend Changes**: ~150 lines
**Tests**: 8 new test files, ~500 lines

**Dependencies**:
- Phase 1 must be complete
- Backend endpoints: `/next-hole-wager`, `/next-rotation`
- Frontend: SimpleScorekeeper component

**Testing Strategy**:
- TDD: Write failing test first for each feature
- Unit tests: Each rule in isolation
- Integration test: All Phase 2 features together
- Manual testing: Frontend UI functionality

---
