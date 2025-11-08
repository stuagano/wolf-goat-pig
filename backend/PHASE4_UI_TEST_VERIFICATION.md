# Phase 4 UI - Manual Test Verification Guide

**Date:** January 8, 2025
**Status:** Ready for Testing
**Game ID Created:** `eae84f9f-17e8-4ed8-adeb-6efd9881db5f`

## Overview

This document provides step-by-step instructions to manually verify all Phase 4 (Advanced Features) UI components are working correctly.

## Prerequisites

### Start Services
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm start
```

**Frontend URL:** http://localhost:3001
**Backend URL:** http://localhost:8000

## Test Setup

### Create Test Game
```bash
# Create 5-player test game
curl -X POST http://localhost:8000/games/create-test?player_count=5
```

**Response:**
```json
{
  "game_id": "eae84f9f-17e8-4ed8-adeb-6efd9881db5f",
  "join_code": "0UBY40",
  "player_count": 5,
  "players": [
    {"id": "test-player-1", "name": "Test Player 1"},
    {"id": "test-player-2", "name": "Test Player 2"},
    {"id": "test-player-3", "name": "Test Player 3"},
    {"id": "test-player-4", "name": "Test Player 4"},
    {"id": "test-player-5", "name": "Test Player 5"}
  ]
}
```

### Navigate to Scorekeeper
```
http://localhost:3001/game/eae84f9f-17e8-4ed8-adeb-6efd9881db5f/scorekeeper
```

Or use the join code: `0UBY40`

---

## Test 1: The Aardvark UI (5-Player Partners Mode)

### ✅ Test 1.1: Aardvark UI Visibility

**Steps:**
1. Navigate to scorekeeper for 5-player game
2. Ensure "Partners" mode is selected (default)
3. Scroll down to team selection area

**Expected Result:**
- Green card with title "🦘 THE AARDVARK (Player 5)" appears
- Card has border: `2px solid #4CAF50`
- Background: `#E8F5E9`

**Screenshot Location:** `SimpleScorekeeper.jsx:1750-1902`

### ✅ Test 1.2: Aardvark Team Request

**Steps:**
1. In the Aardvark card, locate "Aardvark requests to join:" section
2. Click "Team 1" button
3. Verify button highlights in blue (#00bcd4)
4. Click "Team 2" button
5. Verify button highlights in orange (#ff9800)

**Expected Result:**
- Only one team button can be selected at a time
- Selected button shows team color background
- Unselected buttons show white background

### ✅ Test 1.3: Aardvark Accept/Toss

**Steps:**
1. Select a team (Team 1 or Team 2)
2. "Team Response:" section appears below
3. Click "✓ Accept" button
4. Verify button turns green (#4CAF50)
5. Click "✗ Toss (2x)" button
6. Verify button turns red (#FF5722)

**Expected Result:**
- Accept button: Green background when selected
- Toss button: Red background when selected
- Text shows "(2x)" multiplier indication

### ✅ Test 1.4: Ping Pong Checkbox

**Steps:**
1. Select Aardvark team
2. Click "✗ Toss (2x)" button
3. Orange checkbox card appears below
4. Check "🏓 Ping Pong! Other team also tosses (4x multiplier)"
5. Verify checkbox is checked

**Expected Result:**
- Ping Pong checkbox only appears when "Toss" is selected
- Background: `#FFF3E0` (light orange)
- Border: `2px solid #FF9800`
- Checkbox text clearly shows "4x multiplier"

---

## Test 2: The Tunkarri (Aardvark Solo)

### ✅ Test 2.1: Tunkarri Checkbox Visibility

**Steps:**
1. Switch to "Solo" mode (click Solo button)
2. Select "Test Player 5" as captain (Aardvark is always player 5)
3. Scroll down below Solo/Partners buttons

**Expected Result:**
- Blue card appears with "🦘 The Tunkarri (Aardvark solo - 3-for-2 payout)"
- Background: `#E3F2FD`
- Border: `2px solid #1976D2`
- Checkbox is unchecked by default

**Screenshot Location:** `SimpleScorekeeper.jsx:1659-1686`

### ✅ Test 2.2: Tunkarri Checkbox Functionality

**Steps:**
1. With Test Player 5 as captain in solo mode
2. Check the Tunkarri checkbox
3. Verify checkbox becomes checked
4. Uncheck it
5. Verify checkbox becomes unchecked

**Expected Result:**
- Checkbox toggles correctly
- Only appears when captain is player 5 (Aardvark) in solo mode
- Does NOT appear for other players as captain

---

## Test 3: The Big Dick (Hole 18 Special)

### ✅ Test 3.1: Navigate to Hole 18

**Steps:**
1. Complete holes 1-17 OR manually set game to hole 18
2. Scroll to top of scorekeeper

**API Method (Quick):**
```bash
# Complete 17 holes quickly
for i in {1..17}; do
  curl -X POST http://localhost:8000/games/eae84f9f-17e8-4ed8-adeb-6efd9881db5f/holes/complete \
  -H "Content-Type: application/json" \
  -d '{
    "hole_number": '$i',
    "rotation_order": ["test-player-1","test-player-2","test-player-3","test-player-4","test-player-5"],
    "captain_index": 0,
    "teams": {"type": "partners", "team1": ["test-player-1","test-player-2"], "team2": ["test-player-3","test-player-4","test-player-5"]},
    "final_wager": 2,
    "winner": "team1",
    "scores": {"test-player-1": 4, "test-player-2": 4, "test-player-3": 5, "test-player-4": 5, "test-player-5": 5},
    "hole_par": 4
  }'
done
```

### ✅ Test 3.2: Big Dick UI Visibility

**Steps:**
1. On hole 18, check for red dramatic card
2. Verify current hole number shows "18"

**Expected Result:**
- Red card appears with "🎯 THE BIG DICK - HOLE 18 SPECIAL"
- Background: `#FFEBEE` (light red)
- Border: `3px solid #D32F2F` (thick red border)
- Box shadow visible
- Centered text layout

**Screenshot Location:** `SimpleScorekeeper.jsx:1904-1983`

### ✅ Test 3.3: Big Dick Player Selection

**Steps:**
1. View all 5 player buttons
2. Click on "Test Player 1"
3. Verify button turns red (#D32F2F background)
4. Verify team mode automatically switches to "Solo"
5. Verify Test Player 1 is now the captain
6. Click "Clear" button
7. Verify selection is reset

**Expected Result:**
- Each player button can be clicked
- Selected player shows red background
- Automatically sets solo mode with selected player as captain
- Clear button resets the selection
- All other players become opponents

---

## Test 4: State Submission Verification

### ✅ Test 4.1: Complete Hole with Advanced Features

**Steps:**
1. Set up 5-player partners mode
2. Select Aardvark team: "Team 1"
3. Select "✗ Toss (2x)"
4. Select teams (2 vs 3)
5. Enter scores for all players
6. Select winner
7. Click "Complete Hole"
8. Check browser DevTools Network tab

**Expected Payload:**
```json
{
  "hole_number": 1,
  "aardvark_requested_team": "team1",
  "aardvark_tossed": true,
  "aardvark_ping_ponged": false,
  "tunkarri_invoked": false,
  "big_dick_invoked_by": null,
  ...
}
```

### ✅ Test 4.2: Verify Backend Response

**Expected:**
- API returns 200 OK
- `hole_result` contains advanced feature flags
- Points correctly apply 2x multiplier for tossed Aardvark

---

## Test 5: Conditional Rendering

### ✅ Test 5.1: Aardvark UI - 4 Player Game

**Steps:**
1. Create 4-player test game
```bash
curl -X POST http://localhost:8000/games/create-test?player_count=4
```
2. Navigate to scorekeeper
3. Verify Aardvark UI does NOT appear

**Expected:**
- Green Aardvark card is hidden
- Only standard team selection visible

### ✅ Test 5.2: Tunkarri - Non-Aardvark Captain

**Steps:**
1. 5-player game, solo mode
2. Select "Test Player 1" as captain
3. Verify Tunkarri checkbox does NOT appear

**Expected:**
- Blue Tunkarri card only appears when player 5 is captain

### ✅ Test 5.3: Big Dick - Non-18th Hole

**Steps:**
1. On holes 1-17, verify Big Dick UI does NOT appear
2. Only on hole 18 should red Big Dick card appear

**Expected:**
- Red Big Dick card only on hole 18
- Hidden on all other holes

---

## Test 6: UI Polish & Styling

### ✅ Test 6.1: Color Consistency

**Verify color scheme:**
- **Aardvark:** Green (#4CAF50, #E8F5E9)
- **Tunkarri:** Blue (#1976D2, #E3F2FD)
- **Big Dick:** Red (#D32F2F, #FFEBEE)
- **Ping Pong:** Orange (#FF9800, #FFF3E0)

### ✅ Test 6.2: Emojis

**Verify emojis:**
- Aardvark: 🦘
- Tunkarri: 🦘
- Big Dick: 🎯
- Ping Pong: 🏓

### ✅ Test 6.3: Responsive Design

**Test on different screen sizes:**
- Desktop (1920x1080)
- Tablet (768x1024)
- Mobile (375x667)

**Expected:**
- Cards stack vertically on mobile
- Buttons remain touchable (minimum 44x44px)
- Text remains readable

---

## Test 7: State Reset Between Holes

### ✅ Test 7.1: Advanced Features Reset

**Steps:**
1. Set Aardvark team to "Team 1"
2. Check "Toss" and "Ping Pong"
3. Complete the hole
4. Start next hole
5. Verify all advanced feature states reset

**Expected Reset Values:**
- `aardvarkRequestedTeam`: null
- `aardvarkTossed`: false
- `aardvarkPingPonged`: false
- `tunkarriInvoked`: false
- `bigDickInvokedBy`: null

---

## Quick Visual Checklist

Copy and paste this into your testing notes:

```
Phase 4 UI Features - Visual Verification
==========================================

5-Player Game - Partners Mode:
[ ] 🦘 Aardvark card visible (green)
[ ] Team 1 / Team 2 buttons work
[ ] Accept / Toss buttons toggle
[ ] Ping Pong checkbox appears after Toss
[ ] Ping Pong shows "4x multiplier" text

5-Player Game - Solo Mode (Aardvark Captain):
[ ] 🦘 Tunkarri checkbox visible (blue)
[ ] Checkbox toggles correctly
[ ] Only shows when player 5 is captain

Hole 18:
[ ] 🎯 Big Dick card visible (red, dramatic)
[ ] All 5 player buttons shown
[ ] Clicking player auto-sets solo mode
[ ] Clear button resets selection

Data Submission:
[ ] Advanced features included in POST /holes/complete
[ ] Backend returns 200 OK
[ ] Multipliers applied correctly (2x, 4x)

Conditional Rendering:
[ ] Aardvark hidden in 4-player games
[ ] Tunkarri hidden for non-Aardvark captains
[ ] Big Dick hidden on holes 1-17

State Reset:
[ ] All features reset to default after completing hole
[ ] Next hole starts with clean state
```

---

## Known Issues

### Non-Blocking Issues
1. **ESLint Warnings:** Variables declared but flagged as unused in initial render
   - Variables ARE used in UI components
   - Can be ignored or add `// eslint-disable-next-line`

### Browser Compatibility
- ✅ Chrome/Edge (Tested)
- ✅ Firefox (Expected to work)
- ✅ Safari (Expected to work)
- ⚠️ IE11 (Not supported)

---

## Success Criteria

### All Tests Pass When:
1. ✅ Aardvark UI appears only in 5-player partners mode
2. ✅ Tunkarri checkbox appears only when Aardvark is solo captain
3. ✅ Big Dick UI appears only on hole 18
4. ✅ All state variables submit correctly to backend
5. ✅ Multipliers (2x, 4x) apply correctly
6. ✅ UI is responsive and touch-friendly
7. ✅ Colors and styling match design spec
8. ✅ State resets properly between holes

---

## Automated Test Recommendations

### Future E2E Tests (Playwright/Cypress)
```javascript
describe('Phase 4 UI - Aardvark', () => {
  it('shows Aardvark UI in 5-player partners mode', () => {
    // Navigate to 5-player game
    // Verify Aardvark card visible
    // Test team selection
    // Test toss/accept
    // Test ping pong
  });
});

describe('Phase 4 UI - Big Dick', () => {
  it('shows Big Dick UI on hole 18 only', () => {
    // Navigate to hole 18
    // Verify Big Dick card visible
    // Test player declaration
    // Verify solo mode auto-set
  });
});
```

---

## Conclusion

All Phase 4 (Advanced Features) UI components are **ready for manual testing**. Follow this guide to verify each feature works as designed.

**Estimated Testing Time:** 30-45 minutes for complete verification

**Report Issues:** Create GitHub issues with:
- Feature name (Aardvark, Tunkarri, Big Dick, Ping Pong)
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
