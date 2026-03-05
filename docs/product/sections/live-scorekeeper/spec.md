# Live Scorekeeper Specification

## Overview
The core hole-by-hole interface for tracking a Wolf Goat Pig round. Users enter scores, form teams (partners or solo/captain), record betting actions, and track quarters won/lost. The system handles complex betting rules like Float, Option, Duncan, and special variations.

## User Flows
- Select current hole (1-18) and view par from course data
- Form teams: Partners mode (split into Team 1 vs Team 2) or Solo mode (Captain vs Opponents)
- Enter golf scores for each player (gross strokes)
- Enter quarters won/lost for each player (zero-sum validation)
- Invoke betting actions: Float, Option, Duncan, Vinnie's Variation
- Submit hole and advance to next
- Edit previous holes if needed
- View/edit player names inline
- Track betting history for current hole
- Complete game after 18 holes → Game Completion View

## UI Requirements
- Hole header showing current hole number and par
- Collapsible team selection panel (auto-collapses when teams set)
- Player buttons for team assignment (toggle Team 1/Team 2 or Captain)
- Score input fields per player (gross strokes)
- Quarters input fields per player with zero-sum validation
- Betting action buttons (Float, Option, Duncan, etc.)
- Current wager display with multiplier indicators
- Expandable betting history panel
- Player standings sidebar (quarters, solo/float/option counts)
- Commissioner Chat panel (collapsible)
- Notes field for hole comments
- Submit button with validation
- Edit mode for reviewing/updating past holes
- Game completion view with winner announcement and final standings

## Configuration
- shell: true
