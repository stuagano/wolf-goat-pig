# Stuart Mode — Design Spec

**Date:** 2026-04-17  
**Status:** Approved  

## Overview

A toggleable strategy panel for the scoring screen that gives the authenticated user (Stuart) real-time, personalized advice during a Wolf Goat Pig round. It answers two questions on every hole: *who do I need to watch out for?* and *does going solo make sense right now?*

---

## Architecture

### New files

| File | Purpose |
|------|---------|
| `frontend/src/utils/stuartModeInsights.js` | Pure functions that compute tips from game state. No React, fully unit-testable. |
| `frontend/src/components/game/scorekeeper/StuartModePanel.jsx` | Display component. Renders below `HoleHeader` when Stuart Mode is on. |

### Modified files

| File | Change |
|------|--------|
| `frontend/src/hooks/useUIState.js` | Add `stuartMode` boolean + `toggleStuartMode`, persisted to `localStorage` key `wgp_stuart_mode`. |
| `frontend/src/components/game/SimpleScorekeeper.jsx` | Add toggle button to toolbar; render `<StuartModePanel>` between `HoleHeader` and score inputs when `stuartMode` is true. |
| `frontend/src/components/game/scorekeeper/index.js` | Export `StuartModePanel`. |

---

## Player Identification

Stuart is identified as `players.find(p => p.is_authenticated)`. This is already set via Auth0 and displayed in the app (🔒 badge). No new auth work needed.

---

## Threat Score

For each player on the current hole:

```
threatScore = handicap − (fullStrokes + halfStrokes × 0.5)
```

Where:
- `fullStrokes` = `Math.floor(strokeAllocation[playerId][currentHole])`
- `halfStrokes` = `strokeAllocation[playerId][currentHole] % 1 >= 0.4 ? 1 : 0` (Creecher half-stroke)

Lower threat score = more dangerous opponent. Bands:

| Score | Label | Example |
|-------|-------|---------|
| ≤ 4 | **High threat** | Steve (1 hdcp, no stroke) → score 1 |
| 5–10 | **Moderate** | Dan (8 hdcp, no stroke) → score 8 |
| > 10 | **Favored** | Mike (14 hdcp, no stroke) → score 14 |

Stuart's own score is computed the same way so comparisons are relative.

---

## Tip Logic (`stuartModeInsights.js`)

`generateInsights({ stuartPlayer, players, currentHole, strokeAllocation, playerStandings, courseData, currentWager })` returns:

```js
{
  headline: string,       // bold summary line
  detail: string,         // 1–2 sentence explanation
  threats: [              // sorted high → low threat
    { player, threatScore, strokeSituation }
  ],
  soloRecommendation: 'go' | 'caution' | 'avoid'
}
```

### Tip priority (evaluated in order, can combine)

1. **Stroke situation** — describe Stuart's strokes (full / Creecher / none) and contrast with each opponent's strokes
2. **High-threat callouts** — name every opponent with threatScore ≤ 4, explain why ("Steve is a 1 — the Creecher barely dents his advantage")
3. **Quarter standing context** — if Stuart is down > 3q: "You're down X quarters — higher-variance play makes sense"; if up > 3q: "You're up X — a partner reduces risk"
4. **Hungry opponent callout** — opponent who is both a high threat AND down in quarters gets `⚠️ hungry` flag (they'll play aggressively)
5. **Hole difficulty fallback** — if SI ≤ 6 and no clear stroke advantage: "Tough hole — partnership reduces exposure at Xq"

### Solo recommendation logic

| Condition | Recommendation |
|-----------|---------------|
| Stuart has full stroke AND no high-threat opponents | `go` |
| Stuart has full stroke BUT ≥ 1 high-threat opponent | `caution` |
| Stuart has Creecher AND ≥ 1 high-threat opponent | `caution` |
| Stuart has no stroke AND ≥ 1 high-threat opponent | `avoid` |
| Stuart is down > 3q (overrides caution → go) | bumps up one level |

---

## Panel Layout (`StuartModePanel.jsx`)

Renders as two stacked sections below `HoleHeader`:

### Strategy tip card (amber/gold accent)
```
🧠 Stuart Mode
────────────────────────────────
[soloRecommendation badge]  [headline]
[detail text]
```

Solo recommendation badge:
- `go` → green "Solo ✓"
- `caution` → amber "Solo ⚠"  
- `avoid` → red "Solo ✗"

### Standings strip (compact)
One row per player, sorted by current quarter total descending:

```
Stuart   +7q  🟢
Steve    -4q  🔴  ⚠️ hungry
Dan       0q  ⚪
Mike     -3q  🔴
```

- Green = positive quarters, red = negative, neutral = 0
- `⚠️ hungry` callout for players who are down AND are a high threat this hole

---

## Toggle

- Small button in the `SimpleScorekeeper` toolbar row (same row as photo/sync buttons)
- Label: `🧠 Stuart` when off, active style when on
- State: `stuartMode` boolean in `useUIState`, persisted to `localStorage('wgp_stuart_mode')`
- Default: off

---

## Data Flow

`SimpleScorekeeper` already has all required data in scope:
- `players` (includes `handicap`, `is_authenticated`)
- `strokeAllocation` (includes half-strokes from Creecher)
- `playerStandings` (live quarter totals, recalculated from `holeHistory`)
- `currentHole`, `courseData`, `currentWager`

All of these are passed as props to `StuartModePanel`. `stuartModeInsights.js` receives them as plain objects.

---

## Testing

- `stuartModeInsights.js` — unit tests covering: full stroke advantage, Creecher-only advantage, high-threat opponent (low handicap), hungry opponent (down in quarters + high threat), combined scenarios, solo recommendation logic
- `StuartModePanel.jsx` — render test: panel shows/hides correctly, standings strip reflects player data
