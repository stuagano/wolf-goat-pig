# Cross-Device Game Sync — Self-Healing Reconciliation Design

**Date:** 2026-06-16
**Status:** Approved (design)
**Scope:** Frontend (`frontend/src/`) — no backend change

## Problem

The scorekeeper persists game state (`holeHistory`, `currentHole`,
`playerStandings`) to **per-device `localStorage`** and restores it on load.
The restore rule in `SimpleScorekeeper.jsx` prefers local over the
server-provided state whenever local simply has **more** hole entries:

```js
if (localState?.holeHistory &&
    localState.holeHistory.length > initialHoleHistory.length) {
  return localState;   // local wins purely because it's longer
}
```

Consequences (the known correctness risk):
- A device with **stale or duplicated** local state keeps showing it — it never
  reconciles from the server, because "longer" beats "correct."
- A second device sees the server state (possibly diverged), so the two devices
  disagree about the same game.

The backend is already DB-authoritative (`GET /state` returns DB truth) and the
`/scores` endpoint dedups holes. The only thing keeping local corruption alive
is this client-side restore rule.

## Scenario (decided)

**Handoff / resume**, not concurrent multi-device editing: one active
scorekeeper at a time; a game may be resumed or picked up on another device;
offline edits must survive and sync up when back online. No per-hole merge is
needed.

## Principle

**Local is an offline write-buffer; the server (DB) is the source of truth.**
The client trusts its local cache over the server **only while the cache holds
edits not yet pushed**. Otherwise the server wins — and that is what heals a
stale/duplicated cache.

## Components

### 1. Pure reconciliation function — `frontend/src/services/gameReconcile.js` (new)

One responsibility, no React / no `localStorage` — fully unit-testable:

```js
/**
 * Decide which game state the client should display on load.
 * Local is an offline write-buffer: trust it over the server ONLY when it
 * holds edits not yet pushed. Otherwise the server is authoritative (this is
 * what heals stale/duplicated local state).
 *
 * @param {object|null} serverState   - state from GET /state (DB truth)
 * @param {object|null} localState    - cached state from localStorage
 * @param {boolean} hasPendingEdits   - this game has unsynced edits queued
 * @returns {object|null} the state to use (null => caller uses serverState)
 */
export function reconcileGameState({ serverState, localState, hasPendingEdits }) {
  if (hasPendingEdits && localState) return localState;
  return serverState;
}
```

Returning `serverState` (not `null`) keeps the function total and obvious; the
component adapts it to its existing "return local or null" shape.

### 2. Per-game pending check — `frontend/src/services/syncManager.jsx`

The existing `hasPendingSync()` is **global** (`getPendingSyncCount() > 0`) — it
cannot drive a per-game decision (game Y must not prefer its stale cache because
game X has a queued sync). Queue items already carry `gameId`
(`queueSync(gameId, type, payload)`), so add a per-game variant:

```js
export function hasPendingSyncForGame(gameId) {
  return getSyncQueue().some((item) => item.gameId === gameId);
}
```

Export it on the `syncManager` object alongside the existing helpers.

### 3. Restore rule — `frontend/src/components/game/SimpleScorekeeper.jsx`

Replace the length comparison in `restoredState`:

```js
const restoredState = useMemo(() => {
  const localState = syncManager.loadLocalGameState(gameId);
  // serverState: null because the component already uses initialHoleHistory as
  // the server baseline — so "use server" is expressed as returning null.
  const chosen = reconcileGameState({
    serverState: null,
    localState,
    hasPendingEdits: syncManager.hasPendingSyncForGame(gameId),
  });
  // chosen === localState only when this game has unsynced edits; otherwise
  // null => fall back to the server-provided initialHoleHistory.
  return chosen?.holeHistory ? chosen : null;
}, [gameId]);
```

The dependency on `initialHoleHistory.length` is dropped — the decision no
longer depends on how long the local cache is.

### 4. Load: flush + heal — `frontend/src/pages/SimpleScorekeeperPage.jsx`

After the `GET /state` fetch resolves (`setGameData(data)`):

- **Flush:** if `syncManager.hasPendingSyncForGame(gameId)`, kick the sync queue
  (`syncManager.processQueue()` / existing auto-sync) so local edits reach the
  server.
- **Heal:** if **no** pending edits for this game, overwrite the local cache
  with the freshly-fetched server state:
  `syncManager.saveLocalGameState(gameId, serverState)`. This canonicalizes a
  stale/duplicated cache so it can't resurface on the next load.

## Data flow

1. **Load** → fetch `/state` (truth) → `hasPendingSyncForGame?`
   - **yes:** keep local (it's ahead) + flush the queue.
   - **no:** use server + overwrite the local cache with server state (heal).
2. **Edit hole** → optimistic local update + `saveLocalGameState` + queue
   `POST /scores` (pending until acked).
3. **Reload / second device** → same reconcile → once synced (queue empty),
   server wins everywhere → devices converge. Corruption cannot persist: the
   server dedups on `/scores` and the client re-adopts the server result.

## Error handling

- **Sync failure** → item stays queued → `hasPendingSyncForGame` stays true →
  local remains authoritative (no lost work); surfaced by the existing
  pending-sync indicator.
- **`/state` fetch failure on load** → fall back to the local cache; never wipe
  it.
- **Invariant:** never overwrite local with server while pending edits exist for
  this game.

## Testing

**Unit (`gameReconcile.test.js`)** — the pure helper:
- no local → server.
- local + no pending → server (**even when local is longer / duplicated** — the
  regression that motivated this).
- local + pending → local.

**Unit (`syncManager`)** — `hasPendingSyncForGame`:
- true only when the queue has an item with the matching `gameId`; isolates
  games from each other.

**Component (`SimpleScorekeeper` / page)**:
- corrupt-longer local + empty queue → server state is shown on load, and the
  local cache is overwritten with server state (heal).
- local + queued edit → local state is preserved (no lost work).

The pure `reconcileGameState` helper is also a natural caps candidate
(`stale-local-heals-from-server`) once shipped — see [[caps_local_wiring]].

## Out of scope

- Concurrent multi-device per-hole merge (the chosen scenario is handoff).
- Any backend change — `/state` is already DB-authoritative.
- Surfacing a "synced from another device" UI notice (could be a follow-up).
