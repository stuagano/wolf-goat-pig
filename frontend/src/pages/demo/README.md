# Demo Pages

This folder contains demo and test pages that are not used in the production application.

## Pages

### GamePage.js
**Purpose:** Backend-driven MVP/demo interface for testing the game engine

**Architecture:**
- Server-side game state management
- Uses the simulation system
- Frequent API calls to `/game/state`, `/game/action`, `/game/tips`
- Thin client that displays backend-provided state

**Usage:** Demo/testing only - not routed in production app

**Replaced by:** `SimpleScorekeeperPage` (production interface at `/game/:gameId`)

---

### TestMultiplayerPage.js
**Purpose:** Test page for multiplayer functionality

**Usage:** Development and testing only

---

## Production Game Interface

For the actual production game interface, see:
- **SimpleScorekeeperPage** (`/src/pages/SimpleScorekeeperPage.js`)
- **SimpleScorekeeper** (`/src/components/game/SimpleScorekeeper.jsx`)

The production interface uses client-side game logic with minimal backend calls, providing a rich, interactive experience for authenticated users.
