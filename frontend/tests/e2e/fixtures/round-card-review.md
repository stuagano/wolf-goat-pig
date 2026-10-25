# Completed-round review: local browser fixture

This fixture serves in-memory test data only. It never proxies to a real backend and contains no real credentials. Restarting the fixture resets corrections. This verifies the frontend's existing `/scores` payload and read-after-write flow, not database durability.

From the repository root, start the fixture:

```bash
node frontend/tests/e2e/fixtures/round-card-review-server.mjs
```

In `frontend/`, start the real SPA:

```bash
VITE_API_URL=http://127.0.0.1:8334 VITE_AUTH0_DOMAIN=test.auth0.com VITE_AUTH0_CLIENT_ID=test-e2e-client-id npm start -- --host 127.0.0.1 --port 3110 --strictPort
```

From the repository root, launch a dedicated browser session (use an absolute init-script path):

```bash
agent-browser --session round-card-review --init-script "$PWD/frontend/tests/e2e/fixtures/round-card-review-auth.js" open http://127.0.0.1:3110/game/review-fixture
agent-browser --session round-card-review set viewport 1440 1000
agent-browser --session round-card-review wait --text 'Edit scores'
agent-browser --session round-card-review find role button click --name 'Edit scores' --exact
agent-browser --session round-card-review find role button click --name 'Edit hole 1' --exact
agent-browser --session round-card-review fill '[aria-label="Alice strokes"]' 6
agent-browser --session round-card-review find role button click --name Save --exact
agent-browser --session round-card-review wait --fn '!document.querySelector("[aria-label=\"Alice strokes\"]")'
agent-browser --session round-card-review reload
```

Reopen the editor and assert Alice's strokes are `6`. `GET http://127.0.0.1:8334/fixture/evidence` exposes the received request and resulting state: 18 holes, current hole 19, corrected gross score, unchanged quarters. Use `GET /fixture/reset` to reset.

## Responsive checks

- Desktop: 1440×1000; tablet: 820×1180. Photo is left of scores and still usable while the inline editor is open.
- Phone: set device `iPhone 15`, then explicitly set viewport `393 852`. Reload so the app's existing mobile navigation recalculates. An existing desktop-nav overflow at 820px is unrelated to the review panes.
- Zoom in, pan the scroll region, then reset. Reset restores 100% width and zero scroll offsets.
- Resize the phone panel via the range control (click `input[type="range"]`, then press `Home`/`End`; do not use text-fill on a range control). The maximum height is bounded by the viewport so centered inputs remain tappable.
- At a 320×422 CSS viewport (zoom/reflow case), assert the `Pan scorecard photo` region is at least 80px tall; the photo viewport keeps a 160px floor for wrapped controls plus usable image space. Recheck the maximum-height panel at 393×852 to ensure centered correction inputs are not covered.
- Save a phone correction, reload, reopen, and read it back.
- `/game/readonly-fixture`: photo/results visible, no Edit scores control.
- `/game/missing-fixture`: no-photo message; scores remain visible.
- `/game/error-fixture`: load-error message and Retry photo; scores remain visible.

## Automated coverage

```bash
cd frontend
npm run typecheck
npx vitest run
npm run build
```

Focused tests cover embedded zoom/reset, photo load/missing/error/retry, resize state, permission gating, cancel without saving, and inline save/reopen through the supplied existing handler. Browser evidence is separate from these component tests.

Known pre-existing limitation: `handleEditModalSave` does not propagate every sync failure. These tests deliberately verify a successful save, not offline/server-rejection semantics. No backend or sync behavior changes are included.
