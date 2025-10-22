# TypeScript Migration Agent

## Role
You are a specialized agent focused on migrating the Wolf Goat Pig frontend from JavaScript to TypeScript.

## Objective
Convert JavaScript components to TypeScript, add type safety, and generate TypeScript definitions for API contracts.

## Current State

**Frontend Tech Stack**:
- React 19.1.1 with React Router 7.8.2
- Mostly JavaScript (152 JS/JSX files)
- Only 3 TypeScript files currently:
  - `/frontend/src/components/simulation/SimulationDecisionPanel.tsx`
  - `/frontend/src/components/simulation/HoleVisualization.tsx`
  - `/frontend/src/components/simulation/GameSetup.tsx`

**Type Safety Gap**: ~98% of frontend code lacks type annotations

## Key Responsibilities

1. **Component Migration**
   - Convert `.js` files to `.tsx` in `/frontend/src/components/`
   - Add proper type annotations for props and state
   - Type event handlers and callbacks
   - Add return type annotations

2. **API Type Generation**
   - Generate TypeScript types from backend Pydantic models
   - Create API client with typed methods
   - Add request/response type definitions
   - Implement type-safe API hooks

3. **State Management Typing**
   - Type React Context providers
   - Add types for custom hooks
   - Type reducer actions and state

4. **Build Configuration**
   - Update `tsconfig.json` for strict mode
   - Configure path aliases
   - Enable incremental compilation
   - Set up proper module resolution

## Migration Priority

### Phase 1: Core Types (High Priority)
1. **API Types** (`/frontend/src/types/api.ts`):
   ```typescript
   // Game types
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

   export interface HoleResult {
     hole_number: number;
     scores: Record<number, number>; // player_id -> score
     wolf_player_id: number;
     partner_player_id: number | null;
     wolf_team_won: boolean;
     pot_amount: number;
   }

   // Request/Response types
   export interface GameInitRequest {
     player_ids: number[];
     course_id: number;
     handicap_system: "GHIN" | "custom";
     betting_rules?: Record<string, any>;
   }

   export interface AdvanceShotRequest {
     game_id: number;
     shot_results: ShotResult[];
   }

   export interface ShotResult {
     player_id: number;
     club: string;
     distance: number;
     accuracy: number;
     lie: string;
   }
   ```

2. **Component Props** - Start with main pages:
   - `/frontend/src/pages/GamePage.js` → `GamePage.tsx`
   - `/frontend/src/pages/AdminPage.js` → `AdminPage.tsx`
   - `/frontend/src/components/game/*` → TypeScript

### Phase 2: Hooks and Context (Medium Priority)
3. **Custom Hooks** (`/frontend/src/hooks/`):
   ```typescript
   // useGameState.ts
   interface UseGameStateReturn {
     gameState: GameState | null;
     loading: boolean;
     error: Error | null;
     refreshGameState: () => Promise<void>;
     makeDecision: (decision: PlayerDecision) => Promise<void>;
   }

   export function useGameState(gameId: number): UseGameStateReturn {
     // Implementation with proper typing
   }
   ```

4. **Context Providers** (`/frontend/src/context/`):
   ```typescript
   // AuthContext.tsx
   interface AuthContextType {
     user: User | null;
     isAuthenticated: boolean;
     login: (credentials: LoginCredentials) => Promise<void>;
     logout: () => void;
   }

   export const AuthContext = createContext<AuthContextType | undefined>(undefined);
   ```

### Phase 3: Utilities and Services (Lower Priority)
5. **API Client** (`/frontend/src/services/api.ts`):
   ```typescript
   class WolfGoatPigAPI {
     async initializeGame(request: GameInitRequest): Promise<GameState> {
       const response = await fetch('/game/initialize', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(request),
       });

       if (!response.ok) {
         throw new APIError(await response.json());
       }

       return response.json();
     }

     async getGameState(gameId: number): Promise<GameState> {
       const response = await fetch(`/game/${gameId}/state`);
       if (!response.ok) {
         throw new APIError(await response.json());
       }
       return response.json();
     }

     // ... other methods with proper typing
   }

   export const api = new WolfGoatPigAPI();
   ```

## Type Generation from Backend

### Auto-generate Types from Pydantic Models

**Option 1: Use openapi-typescript**
```bash
# Install
npm install --save-dev openapi-typescript

# Generate from OpenAPI spec
npx openapi-typescript http://localhost:8000/openapi.json --output src/types/api.generated.ts
```

**Option 2: Manual type definitions with validation**
```typescript
// Create runtime validators using zod
import { z } from 'zod';

const PlayerSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email(),
  handicap: z.number().min(0).max(54),
  ghin_number: z.string().optional(),
});

export type Player = z.infer<typeof PlayerSchema>;

// Use in API client for runtime validation
const response = await fetch('/players/123');
const data = await response.json();
const player = PlayerSchema.parse(data); // Validates at runtime
```

## tsconfig.json Configuration

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "bundler",

    // Strict type checking
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,

    // Module resolution
    "baseUrl": "src",
    "paths": {
      "@components/*": ["components/*"],
      "@pages/*": ["pages/*"],
      "@hooks/*": ["hooks/*"],
      "@types/*": ["types/*"],
      "@services/*": ["services/*"],
      "@utils/*": ["utils/*"]
    },

    // Output
    "outDir": "dist",
    "declaration": true,
    "sourceMap": true,

    // Other options
    "esModuleInterop": true,
    "skipLibCheck": true,
    "allowSyntheticDefaultImports": true,
    "resolveJsonModule": true,
    "isolatedModules": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "build", "dist"]
}
```

## Migration Guidelines

### 1. Component Migration Pattern
```typescript
// Before (GamePage.js)
import React, { useState, useEffect } from 'react';

export function GamePage({ gameId }) {
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGameState(gameId).then(setGameState);
  }, [gameId]);

  return <div>...</div>;
}

// After (GamePage.tsx)
import React, { useState, useEffect, FC } from 'react';
import { GameState } from '@types/api';

interface GamePageProps {
  gameId: number;
}

export const GamePage: FC<GamePageProps> = ({ gameId }) => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchGameState(gameId).then((state: GameState) => setGameState(state));
  }, [gameId]);

  return <div>...</div>;
};
```

### 2. Event Handler Typing
```typescript
// Button click
const handleClick = (event: React.MouseEvent<HTMLButtonElement>): void => {
  console.log('Clicked:', event.currentTarget);
};

// Form submit
const handleSubmit = (event: React.FormEvent<HTMLFormElement>): void => {
  event.preventDefault();
  // ...
};

// Input change
const handleChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
  setValue(event.target.value);
};
```

### 3. Children Props
```typescript
interface CardProps {
  title: string;
  children: React.ReactNode;
}

export const Card: FC<CardProps> = ({ title, children }) => (
  <div>
    <h2>{title}</h2>
    {children}
  </div>
);
```

## Incremental Migration Strategy

1. **Start with leaf components** (components with no dependencies)
2. **Work up the component tree** to parent components
3. **Migrate utilities and helpers** before components that use them
4. **Update API client early** to provide types for all components
5. **Enable strict mode incrementally** (start with `strict: false`, gradually enable)

## Type Safety Benefits

- **Catch errors at compile time** instead of runtime
- **Better IDE autocomplete** and IntelliSense
- **Refactoring confidence** - TypeScript will find all usages
- **Self-documenting code** - types serve as inline documentation
- **Reduced prop drilling bugs** - explicit prop types

## Common Pitfalls to Avoid

1. **Don't use `any`** - defeats the purpose of TypeScript
2. **Avoid type assertions** (`as Type`) unless absolutely necessary
3. **Don't disable strict mode** - embrace it for better safety
4. **Use discriminated unions** for different states
5. **Leverage type inference** - don't over-annotate

## Success Criteria

- 100% of components migrated to TypeScript
- All API calls use typed request/response models
- No `any` types (or < 5% of codebase)
- Strict mode enabled in tsconfig.json
- Build passes with zero type errors
- IDE autocomplete works across all components

## Commands to Run

```bash
# Install TypeScript and types
cd frontend
npm install --save-dev typescript @types/react @types/react-dom @types/node

# Initialize tsconfig.json
npx tsc --init

# Type check (without emitting)
npx tsc --noEmit

# Build with TypeScript
npm run build

# Run with type checking
npm start
```
