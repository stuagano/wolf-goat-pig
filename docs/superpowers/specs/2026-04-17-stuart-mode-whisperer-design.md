# Stuart Mode — Betting Whisperer Design Spec

**Date:** 2026-04-17
**Status:** Approved

## Overview

Extends Stuart Mode with a proactive betting whisperer embedded in `StuartModePanel`. The whisperer auto-briefs Stuart on each new hole and maintains a running conversation throughout the round. It uses the existing `/api/commissioner/chat` endpoint with enriched context — no backend changes required.

---

## Architecture

### No new files

All changes are in `frontend/src/components/game/scorekeeper/StuartModePanel.jsx`.

### State added to `StuartModePanel`

| State | Type | Purpose |
|-------|------|---------|
| `whispererMessages` | `Array<{type, text, timestamp}>` | Full conversation history for the round |
| `whispererOpen` | `boolean` | Whether the chat drawer is expanded |
| `whispererLoading` | `boolean` | Typing indicator while waiting for API response |

### Proactive trigger

A `useEffect` watches `currentHole`. When it changes:
1. Auto-fires a call to `/api/commissioner/chat` with a system briefing prompt
2. The prompt is not shown in the chat UI as a "sent" message — it's a silent trigger
3. The response appears as a new whisperer message
4. The drawer auto-expands if it was closed

**Briefing prompt sent to API:**
> "Give me a quick strategic briefing for hole [N]. Be direct and specific — focus on who I need to watch, whether to go solo, and any quarter context that matters."

### Context enrichment

`game_state` sent to `/api/commissioner/chat` on every call (both proactive and user-initiated):

```js
{
  // Standard fields
  players,
  current_hole: currentHole,
  standings: playerStandings,
  stroke_allocation: strokeAllocation,
  current_wager: currentWager,
  course_data: courseData,

  // Stuart Mode enrichment
  whisperer_mode: true,
  insights: {
    headline: insights.headline,
    solo_recommendation: insights.soloRecommendation,
    threats: insights.threats.map(t => ({
      name: t.player.name,
      handicap: t.player.handicap,
      threat_score: t.threatScore,
      stroke_situation: t.strokeSituation,
      hungry: t.hungry,
      quarters: t.quarters,
    })),
  },

  // Historical context (last 10 messages)
  conversation_history: whispererMessages
    .slice(-10)
    .map(m => `${m.type === 'whisperer' ? 'Commissioner' : 'Stuart'}: ${m.text}`)
    .join('\n'),
}
```

The backend LLM already builds its prompt from `game_state` fields — the extra fields give it Stuart's full strategic picture and running conversation thread.

---

## UI Layout

Added as a third section at the bottom of `StuartModePanel`, below the standings strip:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Ask Commissioner 🤫              [▲]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🤫  Hole 5 coming up — SI 4, you get a stroke
      but Steve (1 hdcp) is still your biggest
      threat. You're down 4q — going solo makes
      sense here if you trust your game.

  You  Should I offer a double early?

  🤫  With Steve in the field, doubling early is
      risky — wait to see his tee shot first...

  ─────────────────────────────────────
  [Ask something...              ] [→]
```

### Toggle button

- Header row: "Ask Commissioner 🤫 [▼/▲]" — tapping toggles `whispererOpen`
- Auto-expands when a proactive briefing arrives (first message of each hole)

### Message rendering

- `type: 'whisperer'` messages: 🤫 prefix, left-aligned, amber-tinted background
- `type: 'user'` messages: "You" label, right-aligned, subtle background
- Loading state: 🤫 with animated "..." typing indicator
- Scrollable history, newest at bottom, auto-scroll on new message

### Input row

- Text input + send button (→)
- Enter key sends (no shift+enter newlines needed — these are short strategic questions)
- Input disabled while `whispererLoading` is true

---

## Behavior Details

### Hole change flow

1. `currentHole` changes (user navigates to new hole)
2. `useEffect` fires: set `whispererLoading = true`, send briefing prompt to API
3. Response arrives: append to `whispererMessages`, set `whispererLoading = false`, auto-expand drawer
4. User can immediately follow up or just read the briefing

### User message flow

1. User types question, hits send or Enter
2. Append `{ type: 'user', text }` to `whispererMessages`
3. Clear input, set `whispererLoading = true`
4. Send to API with enriched context including full conversation history
5. Append response as `{ type: 'whisperer', text }`, set `whispererLoading = false`

### Error handling

On API failure, append a whisperer message: *"Connection error — try again."* No crash, no lost history.

### First load

On initial mount (hole 1, Stuart Mode just turned on), the proactive trigger fires immediately — Stuart gets a briefing for the current hole the moment he opens the panel.

---

## Props changes to `StuartModePanel`

One new prop required:

| Prop | Type | Purpose |
|------|------|---------|
| `strokeAllocation` | `Object` | Already passed — needed for enriched context (was already a prop) |

No new props needed. `strokeAllocation`, `courseData`, `currentWager`, `playerStandings`, `players`, `currentHole` are all already received.

---

## Testing

- Proactive briefing fires on `currentHole` change
- Drawer auto-expands when briefing arrives
- User message appended to history before API call
- Enriched `game_state` includes `whisperer_mode`, `insights`, `conversation_history`
- Error state appends error message without crashing
- Loading state disables input
- Enter key sends message
