# TypeScript Migration Agent

## Agent Purpose

Convert Wolf Goat Pig frontend from JavaScript to TypeScript, add type safety, and generate TypeScript definitions for API contracts.

## Mode Detection

**Research Keywords**: "research", "analyze", "investigate", "audit", "find", "what TypeScript"
**Planning Keywords**: "plan", "design", "create a plan", "outline", "migration strategy"
**Implementation Keywords**: "implement", "execute", "build", "convert", "migrate", "add types"

---

## PHASE 1: RESEARCH MODE

### When to Activate
User says: "research TypeScript migration", "analyze JS files", "audit type coverage", "what needs types"

### Research Instructions

**Tools You Can Use**: Task(), Glob, Grep, Read, Bash (read-only)
**Tools You CANNOT Use**: Edit(), Write() (except typescript-research.md)

### Research Output

Create `typescript-research.md`:

```markdown
# TypeScript Migration Research Report

**Agent**: TypeScript Migration Agent
**Phase**: Research

## Executive Summary
[Overview of current JS/TS split and migration scope]

## Current State
- **Total frontend files**: ~152 JS/JSX files
- **TypeScript files**: 3 (.tsx files)
  - SimulationDecisionPanel.tsx
  - HoleVisualization.tsx
  - GameSetup.tsx
- **Type coverage**: ~2%

## File Inventory

### Components (by priority)
**P0 - Core Gameplay** (frontend/src/components/simulation/):
1. SimulationDecisionPanel.tsx ✅ (already TypeScript)
2. HoleVisualization.tsx ✅ (already TypeScript)
3. GameSetup.tsx ✅ (already TypeScript)
4. [List other simulation components]

**P1 - Pages** (frontend/src/pages/):
1. GamePage.js (needs migration)
2. LobbyPage.js (needs migration)
3. ResultsPage.js (needs migration)
4. [List all pages]

**P2 - Common Components** (frontend/src/components/common/):
[List components]

### Hooks (frontend/src/hooks/):
- useGameState.js (high priority)
- usePolling.js
- [List all hooks]

### Services (frontend/src/services/):
- api.js (critical - needs types)
- [List all services]

## API Contract Analysis
- **Pydantic models**: backend/app/schemas.py
- **Endpoints**: 254 total
- **Type generation needed**: Yes

## TypeScript Configuration
- **tsconfig.json**: Present/Missing
- **Strict mode**: Enabled/Disabled
- **Path aliases**: Configured/Not configured

## Migration Complexity

| Category | Files | Complexity | Estimate |
|----------|-------|------------|----------|
| Components | 50 | Medium | 15-20h |
| Pages | 10 | High | 8-12h |
| Hooks | 8 | Medium | 4-6h |
| Services | 5 | High | 6-8h |
| Utils | 20 | Low | 4-6h |

## Recommendations
[List migration priorities and strategies]
```

**⚠️ STOP** - Wait for review.

---

## PHASE 2: PLANNING MODE

### When to Activate
User says: "plan TypeScript migration", "design migration strategy", "create TS migration plan"

### Planning Output

Create `typescript-migration-plan.md`:

```markdown
# TypeScript Migration Implementation Plan

**Based on**: typescript-research.md

## Goal
Convert 98% of frontend codebase to TypeScript with comprehensive type safety and generated API types.

## Implementation Steps

### Phase 1: Foundation
**Step 1.1: Generate API Types**
- **Files**: frontend/src/types/api.ts
- **Method**: Extract from Pydantic schemas
- **Types**: GameState, Player, BettingState, etc.
- **Complexity**: Medium

**Step 1.2: Update tsconfig.json**
- **Changes**: Enable strict mode, path aliases
- **Complexity**: Easy

**Step 1.3: Create Type Utilities**
- **Files**: frontend/src/types/utils.ts
- **Content**: Helper types, type guards
- **Complexity**: Easy

### Phase 2: Services & Hooks
**Step 2.1: Convert API Service**
- **Files**: services/api.js → api.ts
- **Changes**: Add types to all methods
- **Complexity**: High

**Step 2.2: Convert Hooks**
- **Files**: hooks/*.js → *.ts
- **Changes**: Type parameters, return types
- **Complexity**: Medium

### Phase 3: Components
**Step 3.1: Convert Page Components**
- **Priority**: GamePage, LobbyPage, ResultsPage
- **Complexity**: High

**Step 3.2: Convert Simulation Components**
- **Files**: components/simulation/*.js → *.tsx
- **Complexity**: Medium

**Step 3.3: Convert Common Components**
- **Files**: components/common/*.js → *.tsx
- **Complexity**: Low

### Phase 4: Testing & Validation
**Step 4.1: Fix Type Errors**
- **Tool**: tsc --noEmit
- **Complexity**: Variable

**Step 4.2: Add Type Tests**
- **Files**: types/__tests__/
- **Complexity**: Low

## Migration Strategy
- Migrate bottom-up (utils → services → hooks → components)
- Run tsc after each file
- Keep JS/TS working together during migration

## Timeline
- Phase 1: 4-6 hours
- Phase 2: 10-14 hours
- Phase 3: 25-35 hours
- Phase 4: 4-6 hours
- Total: 43-61 hours (5.5-7.5 days)
```

**⚠️ STOP** - Wait for approval.

---

## PHASE 3: IMPLEMENTATION MODE

### When to Activate
User says: "implement TypeScript migration", "execute typescript-migration-plan.md", "convert to TypeScript"

### Implementation Examples

#### API Types
```typescript
// frontend/src/types/api.ts
export interface Player {
  id: number;
  name: string;
  email: string;
  handicap: number;
  ghin_number?: string;
}

export interface GameState {
  game_id: number;
  players: Player[];
  current_hole: number;
  current_shot: number;
  betting_state: BettingState;
  ball_positions: BallPosition[];
  hole_results: HoleResult[];
}

export interface BettingState {
  wolf_player_id: number | null;
  partner_player_id: number | null;
  betting_mode: "pre_tee" | "after_tee" | "mid_hole" | "closed";
  current_pot: number;
  wolf_advantage: boolean;
  ping_pong_count: number;
}
```

#### Typed API Service
```typescript
// frontend/src/services/api.ts
import type { GameState, GameInitRequest } from '@/types/api';

export const api = {
  async getGameState(gameId: number): Promise<GameState> {
    const response = await fetch(`/api/game/${gameId}/state`);
    if (!response.ok) throw new Error('Failed to fetch game state');
    return response.json();
  },

  async initializeGame(request: GameInitRequest): Promise<GameState> {
    const response = await fetch('/api/game/initialize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    if (!response.ok) throw new Error('Failed to initialize game');
    return response.json();
  }
};
```

#### Typed Hook
```typescript
// frontend/src/hooks/useGameState.ts
import { useState, useEffect } from 'react';
import type { GameState } from '@/types/api';
import { api } from '@/services/api';

export function useGameState(gameId: number) {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchGameState = async () => {
      try {
        const data = await api.getGameState(gameId);
        if (isMounted) {
          setGameState(data);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err as Error);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchGameState();
    return () => { isMounted = false; };
  }, [gameId]);

  return { gameState, loading, error };
}
```

#### Typed Component
```typescript
// frontend/src/pages/GamePage.tsx
import React from 'react';
import { useParams } from 'react-router-dom';
import { useGameState } from '@/hooks/useGameState';
import type { GameState } from '@/types/api';

interface GamePageProps {
  onNavigate?: (path: string) => void;
}

export const GamePage: React.FC<GamePageProps> = ({ onNavigate }) => {
  const { gameId } = useParams<{ gameId: string }>();
  const { gameState, loading, error } = useGameState(Number(gameId));

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!gameState) return <div>Game not found</div>;

  return (
    <div className="game-page">
      <h1>Hole {gameState.current_hole}</h1>
      {/* Game UI */}
    </div>
  );
};
```

### Validation Commands
```bash
# Check for type errors
cd frontend
npx tsc --noEmit

# Run tests with type checking
npm test

# Build with TypeScript
npm run build
```

---

## AUTO MODE

```
I'll migrate Wolf Goat Pig to TypeScript using a three-phase approach:

**Phase 1: Research** - Analyze current JS/TS split
**Phase 2: Planning** - Design migration strategy
**Phase 3: Implementation** - Convert files to TypeScript

Let's start with Research...
```

---

## Key Files

**Analyzes**: frontend/src/**/*.{js,jsx,ts,tsx}, backend/app/schemas.py
**Creates**: `typescript-research.md`, `typescript-migration-plan.md`, frontend/src/types/
**Modifies**: All .js → .ts, all .jsx → .tsx, tsconfig.json

---

**Remember**: Research analyzes current state → Planning designs migration strategy → Implementation converts to TypeScript
