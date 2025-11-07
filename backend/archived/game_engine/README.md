# Archived Game Engine

This directory contains the original Wolf Goat Pig game engine that was archived on 2025-11-04.

## Why Archived

The game engine was designed for multiplayer real-time gameplay with:
- Complex state machine (phases: CAPTAIN_DECISION, PARTNERSHIP_FORMATION, BETTING, PLAYING, HOLE_COMPLETE)
- Action-based architecture (request_partner, accept_partner, go_solo, offer_double, etc.)
- Async decision flow (one player makes decision, others respond)

This architecture was overly complex for the primary use case: a single scorekeeper recording golf game data.

## What Replaced It

A simplified scorekeeper interface that:
- Uses client-side state for betting UI during the hole
- Sends one complete hole record when the hole is finished
- No state machine validation
- Direct CRUD operations for hole data

## Files Archived

- `wolf_goat_pig_simulation.py` - Original game engine with state machine

## If You Need This Again

The multiplayer real-time game mode can be restored by:
1. Moving these files back to app/
2. Re-enabling the action-based endpoints in main.py
3. Using the multiplayer routes (/lobby/:gameId, /join, etc.)

For now, the simplified scorekeeper mode is the focus.
