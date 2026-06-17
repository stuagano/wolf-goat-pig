# Cross-Device Game Sync — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop the scorekeeper from preferring a longer-but-stale local cache over server truth, so a game self-heals from the DB on load and devices converge.

**Architecture:** A pure `reconcileGameState` decision function (local wins only when the device has unsynced edits) drives `SimpleScorekeeper.restoredState`; a `reconcileOnLoad` side-effecting helper flushes pending edits or overwrites the stale cache with server state. No backend change — `/state` is already DB-authoritative.

**Tech Stack:** React + Vite, vitest (jsdom), `frontend/src/services/syncManager.jsx`.

**Spec:** `docs/superpowers/specs/2026-06-16-cross-device-game-sync-design.md`

**Key facts:**
- Local cache shape is **camelCase**: `{ holeHistory, currentHole, playerStandings }` (written by `useScorekeeperSync` and `saveLocalGameState`).
- `GET /state` returns **snake_case**: `{ hole_history, current_hole, standings, ... }`. The heal step MUST map server→local shape before caching.
- `syncManager.hasPendingSync()` is **global** (do not use it per-game). Queue items carry `gameId` (`queueSync(gameId, type, payload)`).
- Run frontend commands from `frontend/`. Gate: `npm run typecheck && npx vitest run && npm run build`.

---

## File Structure

- **Create** `frontend/src/services/gameReconcile.js` — the pure decision function. One responsibility, no React/localStorage.
- **Create** `frontend/src/services/__tests__/gameReconcile.test.js` — its tests.
- **Modify** `frontend/src/services/syncManager.jsx` — add `hasPendingSyncForGame(gameId)` and `reconcileOnLoad(gameId, serverState)`; export both.
- **Create** `frontend/src/services/__tests__/syncManager.reconcile.test.js` — tests for the two new functions.
- **Modify** `frontend/src/components/game/SimpleScorekeeper.jsx` — `restoredState` uses the helper.
- **Modify** `frontend/src/pages/SimpleScorekeeperPage.jsx` — call `reconcileOnLoad` after the `/state` fetch.

---

## Task 1: Pure `reconcileGameState` helper

**Files:**
- Create: `frontend/src/services/gameReconcile.js`
- Test: `frontend/src/services/__tests__/gameReconcile.test.js`

- [ ] **Step 1: Write the failing test**

Create `frontend/src/services/__tests__/gameReconcile.test.js`:

```js
import { reconcileGameState } from '../gameReconcile';

const local = { holeHistory: [{ hole: 1 }, { hole: 1 }, { hole: 2 }] }; // longer + duplicate
const server = { holeHistory: [{ hole: 1 }, { hole: 2 }] };

describe('reconcileGameState', () => {
  test('no local -> server', () => {
    expect(reconcileGameState({ serverState: server, localState: null, hasPendingEdits: false }))
      .toBe(server);
  });

  test('local + no pending edits -> server (heals, even when local is longer/duplicated)', () => {
    expect(reconcileGameState({ serverState: server, localState: local, hasPendingEdits: false }))
      .toBe(server);
  });

  test('local + pending edits -> local (unsynced work is preserved)', () => {
    expect(reconcileGameState({ serverState: server, localState: local, hasPendingEdits: true }))
      .toBe(local);
  });

  test('pending edits but no local -> server (nothing to prefer)', () => {
    expect(reconcileGameState({ serverState: server, localState: null, hasPendingEdits: true }))
      .toBe(server);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/services/__tests__/gameReconcile.test.js`
Expected: FAIL — `Failed to resolve import "../gameReconcile"`.

- [ ] **Step 3: Write minimal implementation**

Create `frontend/src/services/gameReconcile.js`:

```js
// Decide which game state to display on load.
//
// Local is an offline write-buffer: trust it over the server ONLY when this
// game has edits not yet pushed. Otherwise the server (DB) is authoritative —
// this is what heals stale/duplicated local state instead of letting a
// longer-but-wrong cache win. See
// docs/superpowers/specs/2026-06-16-cross-device-game-sync-design.md
export function reconcileGameState({ serverState, localState, hasPendingEdits }) {
  if (hasPendingEdits && localState) return localState;
  return serverState;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/services/__tests__/gameReconcile.test.js`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/gameReconcile.js frontend/src/services/__tests__/gameReconcile.test.js
git commit -m "feat(sync): pure reconcileGameState decision helper"
```

---

## Task 2: Per-game pending check + `reconcileOnLoad` in syncManager

**Files:**
- Modify: `frontend/src/services/syncManager.jsx` (add two functions; add to the `syncManager` object at lines 597-617)
- Test: `frontend/src/services/__tests__/syncManager.reconcile.test.js`

Context: `getSyncQueue()` returns the queue array (items shaped `{ gameId, type, payload, ... }`). `saveLocalGameState(gameId, state)` and `loadLocalGameState(gameId)` round-trip the camelCase cache. `processQueue()` flushes the queue (network).

- [ ] **Step 1: Write the failing test**

Create `frontend/src/services/__tests__/syncManager.reconcile.test.js`:

```js
import syncManager, {
  hasPendingSyncForGame,
  reconcileOnLoad,
} from '../syncManager';

beforeEach(() => {
  syncManager.clearQueue();
  syncManager.clearLocalGameState('g1');
  syncManager.clearLocalGameState('g2');
});

describe('hasPendingSyncForGame', () => {
  test('false when the queue has no item for this game', () => {
    expect(hasPendingSyncForGame('g1')).toBe(false);
  });

  test('true only for the game with a queued item (isolates games)', () => {
    syncManager.queueSync('g1', 'scores', { holes: [] });
    expect(hasPendingSyncForGame('g1')).toBe(true);
    expect(hasPendingSyncForGame('g2')).toBe(false);
  });
});

describe('reconcileOnLoad', () => {
  test('no pending edits -> overwrites the cache with server state (heals)', () => {
    // a corrupt/duplicated local cache
    syncManager.saveLocalGameState('g1', {
      holeHistory: [{ hole: 1 }, { hole: 1 }, { hole: 2 }],
    });
    const server = { holeHistory: [{ hole: 1 }, { hole: 2 }], currentHole: 3 };

    reconcileOnLoad('g1', server);

    const healed = syncManager.loadLocalGameState('g1');
    expect(healed.holeHistory).toEqual(server.holeHistory); // duplicate gone
    expect(healed.currentHole).toBe(3);
  });

  test('pending edits -> leaves the local cache untouched (no lost work)', () => {
    syncManager.saveLocalGameState('g1', { holeHistory: [{ hole: 1 }, { hole: 2 }] });
    syncManager.queueSync('g1', 'scores', { holes: [] }); // unsynced edit

    reconcileOnLoad('g1', { holeHistory: [{ hole: 1 }] }); // shorter server

    const kept = syncManager.loadLocalGameState('g1');
    expect(kept.holeHistory).toEqual([{ hole: 1 }, { hole: 2 }]); // local preserved
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/services/__tests__/syncManager.reconcile.test.js`
Expected: FAIL — `hasPendingSyncForGame`/`reconcileOnLoad` are not exported.

- [ ] **Step 3: Write the implementation**

In `frontend/src/services/syncManager.jsx`, add these two exported functions (place them just above `const syncManager = {` at ~line 597):

```js
/**
 * True iff this specific game has an edit queued for sync. Per-game, unlike the
 * global hasPendingSync(). Drives the "local is authoritative only while it
 * holds unsynced work" rule.
 */
export function hasPendingSyncForGame(gameId) {
  return getSyncQueue().some((item) => item.gameId === gameId);
}

/**
 * Reconcile local cache vs server truth on load.
 * - Pending edits for this game: flush them up; leave the local cache (it's
 *   ahead) so no unsynced work is lost.
 * - No pending edits: the server is authoritative — overwrite the local cache
 *   with the server state so stale/duplicated local can't resurface.
 *
 * `serverState` MUST already be in the local cache shape
 * ({ holeHistory, currentHole, playerStandings }), mapped from GET /state.
 */
export function reconcileOnLoad(gameId, serverState) {
  if (hasPendingSyncForGame(gameId)) {
    processQueue();
    return;
  }
  if (serverState) {
    saveLocalGameState(gameId, serverState);
  }
}
```

Then add both names to the `syncManager` object literal (lines 597-617), after `getNewerLocalState,`:

```js
  getNewerLocalState,
  hasPendingSyncForGame,
  reconcileOnLoad,
};
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/services/__tests__/syncManager.reconcile.test.js`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/syncManager.jsx frontend/src/services/__tests__/syncManager.reconcile.test.js
git commit -m "feat(sync): per-game pending check + reconcileOnLoad (flush-or-heal)"
```

---

## Task 3: Wire the decision into `SimpleScorekeeper.restoredState`

**Files:**
- Modify: `frontend/src/components/game/SimpleScorekeeper.jsx` (import at line 25 area; `restoredState` at lines 109-119)

- [ ] **Step 1: Add the import**

After line 25 (`import syncManager from "../../services/syncManager";`), add:

```js
import { reconcileGameState } from "../../services/gameReconcile";
```

- [ ] **Step 2: Replace `restoredState`**

Replace the current block (lines ~109-119):

```js
  // Try to restore from local storage first (survives page refresh)
  const restoredState = useMemo(() => {
    const localState = syncManager.loadLocalGameState(gameId);
    if (
      localState?.holeHistory &&
      localState.holeHistory.length > initialHoleHistory.length
    ) {
      return localState;
    }
    return null;
  }, [gameId, initialHoleHistory.length]);
```

with:

```js
  // Local is an offline write-buffer: prefer it over the server-provided
  // initialHoleHistory ONLY when this game has unsynced edits. Otherwise the
  // server is authoritative — returning null falls back to initialHoleHistory.
  // This stops a longer-but-stale/duplicated local cache from winning.
  const restoredState = useMemo(() => {
    const localState = syncManager.loadLocalGameState(gameId);
    const chosen = reconcileGameState({
      serverState: null, // "use server" is expressed as null (initialHoleHistory)
      localState,
      hasPendingEdits: syncManager.hasPendingSyncForGame(gameId),
    });
    return chosen?.holeHistory ? chosen : null;
  }, [gameId]);
```

- [ ] **Step 3: Run the existing scorekeeper tests (no regression)**

Run: `cd frontend && npx vitest run src/components/game/__tests__/`
Expected: PASS (all existing SimpleScorekeeper/Scorecard suites still pass).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/game/SimpleScorekeeper.jsx
git commit -m "fix(scorekeeper): restore local only when it has unsynced edits (heal from server otherwise)"
```

---

## Task 4: Flush-or-heal on load in `SimpleScorekeeperPage`

**Files:**
- Modify: `frontend/src/pages/SimpleScorekeeperPage.jsx` (imports at top; load effect at lines 22-44)

- [ ] **Step 1: Add the syncManager import**

After line 8 (`import { apiConfig } from '../config/api.config';`), add:

```js
import syncManager from '../services/syncManager';
```

- [ ] **Step 2: Call `reconcileOnLoad` after the fetch**

In the load effect, replace:

```js
        const data = await response.json();
        setGameData(data);
        setLoading(false);
```

with:

```js
        const data = await response.json();
        // Reconcile the local cache against server truth: flush unsynced edits,
        // or heal a stale/duplicated cache by overwriting it with server state.
        // Map GET /state (snake_case) into the local cache shape (camelCase).
        syncManager.reconcileOnLoad(gameId, {
          holeHistory: data.hole_history || [],
          currentHole: data.current_hole,
          playerStandings: data.standings || {},
        });
        setGameData(data);
        setLoading(false);
```

- [ ] **Step 3: Verify it builds and the scorekeeper page suite (if any) passes**

Run: `cd frontend && npx vitest run src/pages 2>/dev/null; npx vitest run src/components/game/__tests__/`
Expected: PASS (no page-specific suite is required; the component suites must stay green).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/SimpleScorekeeperPage.jsx
git commit -m "fix(scorekeeper): reconcile local cache vs server on game load"
```

---

## Task 5: Full frontend gate

**Files:** none (verification only)

- [ ] **Step 1: Run the full gate (mirrors CI)**

Run:
```bash
cd frontend && npm run typecheck && npx vitest run && npm run build
```
Expected: typecheck clean; all vitest suites pass (incl. the 8 new tests); build succeeds.
Note: `src/sentry.test.js` fails locally only (the `@sentry/react` dep isn't installed on the local npm mirror) — it passes in CI. Everything else must be green.

- [ ] **Step 2: Commit (if the gate surfaced any formatting/lint fixes)**

```bash
git add -A frontend/src
git commit -m "chore(scorekeeper): gate green for cross-device sync reconciliation"
```

(If nothing changed, skip this commit.)

---

## Optional follow-up (local caps, not part of the gate)

Once shipped, the pure helper is a natural capability:
```
PYTHONPATH=.ctk backend/venv/bin/python -m caps add \
  --id stale-local-heals-from-server --tier cheap \
  --description "the scorekeeper adopts server state on load unless local has unsynced edits (stale/duplicated local heals)" \
  --given "a corrupt/longer local cache with no queued edits" \
  --when "the game loads" --then "server state is used and the local cache is overwritten" \
  --deps frontend/src/services/gameReconcile.js --deps frontend/src/services/syncManager.jsx \
  --shell "cd frontend && npx vitest run src/services/__tests__/gameReconcile.test.js src/services/__tests__/syncManager.reconcile.test.js"
```

---

## Self-Review

- **Spec coverage:** pure `reconcileGameState` (Task 1) ✓; per-game `hasPendingSyncForGame` (Task 2) ✓; `reconcileOnLoad` flush+heal (Task 2) ✓; restore-rule wiring (Task 3) ✓; page flush+heal wiring with snake→camel mapping (Task 4) ✓; tests for all four behaviors (Tasks 1-2) ✓; "never overwrite local while pending" invariant — covered by Task 2's "pending -> untouched" test ✓; offline path (pending → local) — same test path ✓.
- **No backend change** — confirmed; nothing in the plan touches `backend/`.
- **Type/shape consistency:** local cache is camelCase everywhere (`holeHistory`, `currentHole`, `playerStandings`); the only snake_case is the raw `/state` response, mapped exactly once in Task 4. `reconcileGameState`'s `serverState: null` convention is consistent between its definition (Task 1) and its only caller (Task 3).
- **Placeholder scan:** none.
