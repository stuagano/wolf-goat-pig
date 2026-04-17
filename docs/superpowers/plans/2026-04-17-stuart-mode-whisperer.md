# Stuart Mode Betting Whisperer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Embed a proactive AI chat ("Ask Commissioner 🤫") inside `StuartModePanel` that auto-briefs Stuart on each new hole and supports a running conversation with enriched strategic context.

**Architecture:** All changes are confined to `StuartModePanel.jsx` and its test file. New state (`whispererMessages`, `whispererOpen`, `whispererLoading`, `inputValue`) plus a `useCallback` API helper (`callCommissioner`) that passes enriched `game_state` to the existing `/api/commissioner/chat` endpoint. A `useEffect` watching `currentHole` fires the proactive briefing. A third UI section renders below the standings strip — a collapsible drawer with message history and an input row.

**Tech Stack:** React (useState, useEffect, useCallback, useRef), fetch API, `apiConfig` from `../../../config/api.config`, Jest + React Testing Library.

---

## Files

| Action | Path |
|--------|------|
| Modify | `frontend/src/components/game/scorekeeper/StuartModePanel.jsx` |
| Modify | `frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx` |

---

### Task 1: State, API helper, and proactive briefing

**Files:**
- Modify: `frontend/src/components/game/scorekeeper/StuartModePanel.jsx`
- Modify: `frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx`

This task adds the core machinery: state variables, a `callCommissioner` async helper, and the `useEffect` that fires a briefing prompt every time `currentHole` changes (including on first render). `callCommissioner` accepts a `messagesSnapshot` parameter so callers can pass just-appended messages before React re-renders, ensuring the conversation history sent to the API is always up to date.

The tests in this task verify only what is observable without a UI: that `fetch` is called with the correct URL, prompt text, and enriched `game_state` shape.

Background on the API:
- URL: `` `${apiConfig.baseUrl}/api/commissioner/chat` ``
- Request body: `{ message: string, game_state: object }`
- Response: `json.data.response` (or `json.detail` as fallback)
- `apiConfig` is imported from `'../../../config/api.config'`
- In tests, `window.location.hostname` is `localhost`, so `apiConfig.baseUrl` resolves to `'http://localhost:8000'` — mock `global.fetch` to intercept.

- [ ] **Step 1: Add failing tests for proactive briefing to the test file**

Add the following `describe` block at the bottom of `frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx`.

First, update the import line at the top of the file:

```jsx
import { render, screen, waitFor, act, fireEvent } from '@testing-library/react';
```

Then add at the bottom:

```jsx
// ── Whisperer: proactive briefing ──────────────────────────────────────

describe('whisperer proactive briefing', () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      json: async () => ({ data: { response: 'Hole 5: Watch Steve.' } }),
    });
  });

  afterEach(() => {
    global.fetch = undefined;
  });

  test('calls /api/commissioner/chat on mount', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const [url] = global.fetch.mock.calls[0];
    expect(url).toMatch(/commissioner\/chat/);
  });

  test('sends briefing prompt for the current hole', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body.message).toMatch(/strategic briefing for hole 5/i);
  });

  test('includes whisperer_mode and insights in game_state', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(body.game_state.whisperer_mode).toBe(true);
    expect(body.game_state.insights).toBeDefined();
    expect(Array.isArray(body.game_state.insights.threats)).toBe(true);
    expect(typeof body.game_state.insights.solo_recommendation).toBe('string');
  });

  test('includes conversation_history string in game_state', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const body = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(typeof body.game_state.conversation_history).toBe('string');
  });
});
```

- [ ] **Step 2: Run tests to confirm new tests fail**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig/frontend
CI=true npm test -- --watchAll=false --testPathPattern="StuartModePanel"
```

Expected: 5 existing tests pass, 4 new tests fail (`global.fetch` is undefined or not mocked — the feature doesn't exist yet).

- [ ] **Step 3: Update imports in StuartModePanel.jsx**

In `frontend/src/components/game/scorekeeper/StuartModePanel.jsx`, replace lines 1–4:

```jsx
// frontend/src/components/game/scorekeeper/StuartModePanel.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import { apiConfig } from '../../../config/api.config';
import { generateInsights } from '../../../utils/stuartModeInsights';
```

- [ ] **Step 4: Add state, callCommissioner, and proactive useEffect inside the component**

In `StuartModePanel.jsx`, after the `const badge = SOLO_BADGE[insights.soloRecommendation];` line (currently line 30), add:

```jsx
  // ── Whisperer state ───────────────────────────────────────────────────
  const [whispererMessages, setWhispererMessages] = useState([]);
  const [whispererOpen, setWhispererOpen] = useState(false);
  const [whispererLoading, setWhispererLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  // ── API helper ────────────────────────────────────────────────────────
  // messagesSnapshot must be passed explicitly by the caller so the API
  // receives the latest history even before a state re-render completes.
  const callCommissioner = useCallback(async (prompt, messagesSnapshot) => {
    setWhispererLoading(true);
    setWhispererOpen(true);
    try {
      const resp = await fetch(`${apiConfig.baseUrl}/api/commissioner/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: prompt,
          game_state: {
            players,
            current_hole: currentHole,
            standings: playerStandings,
            stroke_allocation: strokeAllocation,
            current_wager: currentWager,
            course_data: courseData,
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
            conversation_history: messagesSnapshot
              .slice(-10)
              .map(m => `${m.type === 'whisperer' ? 'Commissioner' : 'Stuart'}: ${m.text}`)
              .join('\n'),
          },
        }),
      });
      const json = await resp.json();
      const text = json?.data?.response || json?.detail || 'Sorry, I could not get a response.';
      setWhispererMessages(prev => [...prev, { type: 'whisperer', text, timestamp: new Date() }]);
    } catch {
      setWhispererMessages(prev => [...prev, {
        type: 'whisperer',
        text: 'Connection error — try again.',
        timestamp: new Date(),
      }]);
    } finally {
      setWhispererLoading(false);
    }
  }, [players, currentHole, playerStandings, strokeAllocation, currentWager, courseData, insights]);

  // ── Proactive briefing on hole change ─────────────────────────────────
  useEffect(() => {
    callCommissioner(
      `Give me a quick strategic briefing for hole ${currentHole}. Be direct and specific — focus on who I need to watch, whether to go solo, and any quarter context that matters.`,
      whispererMessages,
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentHole]); // intentionally only re-fires on hole change

  // ── Auto-scroll on new message ────────────────────────────────────────
  useEffect(() => {
    if (messagesEndRef.current?.scrollIntoView) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [whispererMessages]);

  // ── User send handler ─────────────────────────────────────────────────
  const handleSend = async () => {
    if (!inputValue.trim() || whispererLoading) return;
    const text = inputValue.trim();
    setInputValue('');
    const updatedMessages = [...whispererMessages, { type: 'user', text, timestamp: new Date() }];
    setWhispererMessages(updatedMessages);
    await callCommissioner(text, updatedMessages);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
```

- [ ] **Step 5: Run tests to confirm Task 1 tests pass**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig/frontend
CI=true npm test -- --watchAll=false --testPathPattern="StuartModePanel"
```

Expected: All 9 tests pass (5 original + 4 new proactive briefing tests).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/game/scorekeeper/StuartModePanel.jsx \
        frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx
git commit -m "feat: add whisperer state, API helper, and proactive briefing trigger"
```

---

### Task 2: Whisperer UI section

**Files:**
- Modify: `frontend/src/components/game/scorekeeper/StuartModePanel.jsx`
- Modify: `frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx`

This task adds the full UI: a third section below the standings strip containing a collapsible toggle header, a scrollable message history (auto-expands when a briefing arrives), and an input row.

Message rendering:
- `type: 'whisperer'` messages: left-aligned, `🤫` prefix, amber-tinted background (`rgba(245,158,11,0.1)`)
- `type: 'user'` messages: right-aligned, "You" label above text, subtle background (`rgba(0,0,0,0.06)`)
- Loading state: `🤫 ...` typing indicator
- Newest message at bottom; `messagesEndRef` auto-scrolls on each new message

The drawer is initially closed but `callCommissioner` calls `setWhispererOpen(true)`, so it opens as soon as the first briefing arrives.

- [ ] **Step 1: Add failing UI tests to the test file**

Add the following `describe` block at the bottom of `frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx`:

```jsx
// ── Whisperer: UI ──────────────────────────────────────────────────────

describe('whisperer UI', () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      json: async () => ({ data: { response: 'Hole 5: Watch Steve.' } }),
    });
  });

  afterEach(() => {
    global.fetch = undefined;
  });

  test('renders "Ask Commissioner" toggle header', () => {
    render(<StuartModePanel {...baseProps} />);
    expect(screen.getByText(/Ask Commissioner/i)).toBeInTheDocument();
  });

  test('message list is hidden before briefing arrives, shown after', async () => {
    render(<StuartModePanel {...baseProps} />);
    // Before briefing: no messages container
    expect(screen.queryByTestId('whisperer-messages')).not.toBeInTheDocument();
    // After briefing resolves: container appears
    await waitFor(() =>
      expect(screen.getByTestId('whisperer-messages')).toBeInTheDocument()
    );
  });

  test('renders whisperer response with 🤫 prefix', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() =>
      expect(screen.getByText('Hole 5: Watch Steve.')).toBeInTheDocument()
    );
    // The 🤫 emoji should be adjacent in the same message row
    const messages = screen.getByTestId('whisperer-messages');
    expect(messages.textContent).toContain('🤫');
  });

  test('toggle button collapses the open drawer', async () => {
    render(<StuartModePanel {...baseProps} />);
    // Wait for drawer to auto-open
    await waitFor(() =>
      expect(screen.getByTestId('whisperer-messages')).toBeInTheDocument()
    );
    // Click toggle to close
    await act(async () => {
      fireEvent.click(screen.getByTestId('whisperer-toggle'));
    });
    expect(screen.queryByTestId('whisperer-messages')).not.toBeInTheDocument();
  });

  test('user message appears with "You" label after send', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

    const input = screen.getByPlaceholderText(/ask something/i);
    await act(async () => {
      fireEvent.change(input, { target: { value: 'Should I go solo?' } });
      fireEvent.click(screen.getByTestId('whisperer-send'));
    });

    expect(screen.getByText('Should I go solo?')).toBeInTheDocument();
    expect(screen.getByText('You')).toBeInTheDocument();
  });

  test('input is disabled while loading', async () => {
    global.fetch = jest.fn().mockReturnValue(new Promise(() => {})); // never resolves
    render(<StuartModePanel {...baseProps} />);
    const input = screen.getByPlaceholderText(/ask something/i);
    expect(input).toBeDisabled();
  });

  test('Enter key sends message', async () => {
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

    const input = screen.getByPlaceholderText(/ask something/i);
    await act(async () => {
      fireEvent.change(input, { target: { value: 'Double down?' } });
      fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    });

    await waitFor(() =>
      expect(screen.getByText('Double down?')).toBeInTheDocument()
    );
  });

  test('shows error message on API failure', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));
    render(<StuartModePanel {...baseProps} />);
    await waitFor(() =>
      expect(screen.getByText('Connection error — try again.')).toBeInTheDocument()
    );
  });
});
```

- [ ] **Step 2: Run tests to confirm new tests fail**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig/frontend
CI=true npm test -- --watchAll=false --testPathPattern="StuartModePanel"
```

Expected: 9 existing tests pass, 8 new UI tests fail (the DOM elements don't exist yet).

- [ ] **Step 3: Add the whisperer UI section to StuartModePanel.jsx**

In `StuartModePanel.jsx`, add the following JSX as a third `<div>` block inside the outer container, directly after the closing `</div>` of the standings strip section (currently line 176, just before the outer closing `</div>`):

```jsx
      {/* ── Whisperer: Ask Commissioner ────────────────────────────────── */}
      <div style={{ borderTop: '1px solid rgba(245,158,11,0.3)' }}>

        {/* Toggle header */}
        <button
          data-testid="whisperer-toggle"
          onClick={() => setWhispererOpen(o => !o)}
          style={{
            width: '100%',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '8px 16px',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            color: theme.colors.textPrimary,
          }}
        >
          <span style={{ fontSize: '12px', fontWeight: 'bold' }}>Ask Commissioner 🤫</span>
          <span style={{ fontSize: '11px', color: theme.colors.textSecondary }}>
            {whispererOpen ? '▲' : '▼'}
          </span>
        </button>

        {/* Message history (shown when open) */}
        {whispererOpen && (
          <div
            data-testid="whisperer-messages"
            style={{
              maxHeight: '220px',
              overflowY: 'auto',
              padding: '0 8px 4px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            {whispererMessages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start',
                  alignItems: 'flex-start',
                  gap: '4px',
                }}
              >
                {msg.type === 'whisperer' && (
                  <span style={{ fontSize: '14px', flexShrink: 0 }}>🤫</span>
                )}
                <div
                  style={{
                    background: msg.type === 'whisperer'
                      ? 'rgba(245,158,11,0.1)'
                      : 'rgba(0,0,0,0.06)',
                    borderRadius: '8px',
                    padding: '6px 10px',
                    maxWidth: '85%',
                    fontSize: '13px',
                    lineHeight: 1.4,
                    color: theme.colors.textPrimary,
                  }}
                >
                  {msg.type === 'user' && (
                    <div style={{
                      fontSize: '10px',
                      fontWeight: 'bold',
                      marginBottom: '2px',
                      textAlign: 'right',
                      color: theme.colors.textSecondary,
                    }}>
                      You
                    </div>
                  )}
                  {msg.text}
                </div>
              </div>
            ))}

            {whispererLoading && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 0',
              }}>
                <span style={{ fontSize: '14px' }}>🤫</span>
                <span style={{ fontSize: '13px', color: theme.colors.textSecondary }}>...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input row */}
        <div style={{
          display: 'flex',
          gap: '8px',
          padding: '8px 12px 10px',
          alignItems: 'center',
        }}>
          <input
            type="text"
            placeholder="Ask something..."
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={whispererLoading}
            style={{
              flex: 1,
              border: `1px solid rgba(245,158,11,${whispererLoading ? '0.2' : '0.5'})`,
              borderRadius: '8px',
              padding: '6px 10px',
              fontSize: '13px',
              outline: 'none',
              background: 'transparent',
              color: theme.colors.textPrimary,
              opacity: whispererLoading ? 0.5 : 1,
            }}
          />
          <button
            data-testid="whisperer-send"
            onClick={handleSend}
            disabled={whispererLoading || !inputValue.trim()}
            style={{
              background: '#F59E0B',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '6px 12px',
              fontSize: '14px',
              cursor: whispererLoading || !inputValue.trim() ? 'not-allowed' : 'pointer',
              opacity: whispererLoading || !inputValue.trim() ? 0.5 : 1,
              flexShrink: 0,
            }}
          >
            →
          </button>
        </div>

      </div>
```

- [ ] **Step 4: Run tests to confirm all tests pass**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig/frontend
CI=true npm test -- --watchAll=false --testPathPattern="StuartModePanel"
```

Expected: All 17 tests pass (5 original + 4 proactive briefing + 8 UI).

- [ ] **Step 5: Run full frontend test suite to check for regressions**

```bash
cd /Users/stuart.gano/Documents/wolf-goat-pig/frontend
CI=true npm test -- --watchAll=false
```

Expected: All tests pass (pre-existing failures in unrelated test files are OK — the pre-existing failures are in `test_progression` and `test_advanced_rules` on the backend, not frontend).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/game/scorekeeper/StuartModePanel.jsx \
        frontend/src/components/game/scorekeeper/__tests__/StuartModePanel.test.jsx
git commit -m "feat: add whisperer UI section with toggle, message history, and input row"
```
