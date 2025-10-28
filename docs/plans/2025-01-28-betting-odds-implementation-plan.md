# Betting Odds Integration - Implementation Plan

**Date:** January 28, 2025
**Design Doc:** `2025-01-28-betting-odds-integration.md`
**Estimated Effort:** 6-8 hours
**Complexity:** Medium

## Overview

This plan breaks down the betting odds integration into bite-sized, testable tasks. Each task is designed to be completed independently with clear verification criteria.

**Approach:** Test-Driven Development (TDD)
- Write tests first
- Watch them fail
- Implement minimal code to pass
- Refactor

## Task Breakdown

### Phase 1: Foundation (Setup & Utils)

#### Task 1.1: Create EducationalTooltip Component
**File:** `frontend/src/components/simulation/visual/EducationalTooltip.jsx`
**Estimated Time:** 30 minutes

**Acceptance Criteria:**
- [ ] Component accepts `title` and `content` props
- [ ] Renders InfoIcon button
- [ ] Shows tooltip on hover
- [ ] Uses Material-UI Tooltip with arrow
- [ ] Tooltip placement is configurable (default: "top")

**Test Cases:**
```javascript
// __tests__/EducationalTooltip.test.js
- renders info icon button
- shows tooltip content on hover
- displays title in tooltip
- allows custom placement prop
```

**Implementation Notes:**
- Use Material-UI `Tooltip`, `IconButton`, `InfoIcon`
- Export as default
- Keep styling minimal, leverage MUI defaults

**Verification:**
```bash
npm test -- EducationalTooltip.test.js
```

---

#### Task 1.2: Add Odds Display Utilities
**File:** `frontend/src/components/simulation/visual/utils/oddsHelpers.js`
**Estimated Time:** 30 minutes

**Acceptance Criteria:**
- [ ] `getProbabilityColor(probability)` returns color based on thresholds
- [ ] `formatExpectedValue(value)` formats with +/- sign
- [ ] `getRiskLevelColor(riskLevel)` returns appropriate color
- [ ] `getProbabilityLabel(probability)` returns "Likely"/"Possible"/"Unlikely"

**Test Cases:**
```javascript
// __tests__/oddsHelpers.test.js
- getProbabilityColor returns success for >0.6
- getProbabilityColor returns warning for 0.4-0.6
- getProbabilityColor returns disabled for <0.4
- formatExpectedValue adds + for positive numbers
- formatExpectedValue preserves - for negative numbers
- getRiskLevelColor handles low/medium/high
- getProbabilityLabel returns correct labels
```

**Implementation:**
```javascript
export const getProbabilityColor = (probability) => {
  if (probability > 0.6) return 'success';
  if (probability > 0.4) return 'warning';
  return 'disabled';
};

export const formatExpectedValue = (value) => {
  return value >= 0 ? `+${value.toFixed(1)}` : value.toFixed(1);
};

export const getRiskLevelColor = (riskLevel) => {
  const colors = {
    low: 'success',
    medium: 'warning',
    high: 'error'
  };
  return colors[riskLevel] || 'default';
};

export const getProbabilityLabel = (probability) => {
  if (probability > 0.6) return 'Likely';
  if (probability > 0.4) return 'Possible';
  return 'Unlikely';
};
```

**Verification:**
```bash
npm test -- oddsHelpers.test.js
```

---

#### Task 1.3: Add CSS Styles for Odds Display
**File:** `frontend/src/components/simulation/visual/styles.css`
**Estimated Time:** 20 minutes

**Acceptance Criteria:**
- [ ] `.betting-odds-section` styles added
- [ ] `.probability-bar` styles added
- [ ] `.odds-unavailable` styles added
- [ ] `.expected-value-positive` and `.expected-value-negative` styles added
- [ ] Responsive styles work on mobile

**Implementation:**
Add to existing `styles.css`:
```css
/* Betting Odds Section */
.betting-odds-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.12);
}

.betting-odds-section .MuiTypography-overline {
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Probability Bar */
.probability-bar {
  display: flex;
  gap: 2px;
  height: 4px;
  margin-left: 8px;
}

.probability-dot {
  width: 12px;
  height: 4px;
  border-radius: 2px;
  background-color: rgba(0, 0, 0, 0.12);
  transition: background-color 0.2s;
}

.probability-dot.filled {
  background-color: currentColor;
}

/* Odds States */
.odds-unavailable {
  color: #f57c00;
  font-size: 0.875rem;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 4px;
}

.odds-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(0, 0, 0, 0.6);
}

/* Expected Value */
.expected-value-positive {
  color: #2e7d32;
}

.expected-value-negative {
  color: #d32f2f;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .betting-odds-section {
    font-size: 0.875rem;
  }

  .probability-dot {
    width: 10px;
  }
}
```

**Verification:**
Visual inspection in browser at different screen sizes

---

### Phase 2: Component Enhancements

#### Task 2.1: Create ProbabilityBar Sub-component
**File:** `frontend/src/components/simulation/visual/ProbabilityBar.jsx`
**Estimated Time:** 30 minutes

**Acceptance Criteria:**
- [ ] Accepts `value` prop (0-1)
- [ ] Renders 8 dots
- [ ] Fills dots proportionally based on value
- [ ] Uses color from parent context
- [ ] Handles edge cases (value < 0, value > 1)

**Test Cases:**
```javascript
// __tests__/ProbabilityBar.test.js
- renders 8 dots
- fills 0 dots when value is 0
- fills all 8 dots when value is 1
- fills 5 dots when value is 0.65
- handles negative values gracefully
- handles values > 1 gracefully
```

**Implementation:**
```javascript
import React from 'react';
import { Box } from '@mui/material';

const ProbabilityBar = ({ value }) => {
  // Clamp value between 0 and 1
  const clampedValue = Math.max(0, Math.min(1, value));
  const totalDots = 8;
  const filledDots = Math.round(clampedValue * totalDots);

  return (
    <Box className="probability-bar">
      {Array.from({ length: totalDots }).map((_, index) => (
        <Box
          key={index}
          className={`probability-dot ${index < filledDots ? 'filled' : ''}`}
        />
      ))}
    </Box>
  );
};

export default ProbabilityBar;
```

**Verification:**
```bash
npm test -- ProbabilityBar.test.js
```

---

#### Task 2.2: Enhance BettingCard with Odds Display Section
**File:** `frontend/src/components/simulation/visual/BettingCard.jsx`
**Estimated Time:** 1 hour

**Acceptance Criteria:**
- [ ] Accepts `shotProbabilities` prop with `betting_analysis`
- [ ] Renders odds section when `betting_analysis` exists
- [ ] Shows "Double Likely/Possible/Unlikely" with percentage
- [ ] Shows expected value with +/- and icon
- [ ] Shows risk level with color coding
- [ ] Shows reasoning text
- [ ] Shows "Odds unavailable" when error state
- [ ] Hides odds section when no betting_analysis

**Test Cases:**
```javascript
// __tests__/BettingCard.odds.test.js
- renders odds section when betting_analysis present
- shows probability with correct color
- shows expected value with + sign for positive
- shows expected value with - sign for negative
- shows risk level with correct color
- shows reasoning text
- renders ProbabilityBar component
- shows "Odds unavailable" when error state
- hides odds section when betting_analysis missing
- includes educational tooltip
```

**Implementation Steps:**
1. Import new components and utilities
2. Add odds display helper function
3. Render odds section conditionally
4. Add educational tooltip

**Code Snippet:**
```javascript
import EducationalTooltip from './EducationalTooltip';
import ProbabilityBar from './ProbabilityBar';
import {
  getProbabilityColor,
  formatExpectedValue,
  getRiskLevelColor,
  getProbabilityLabel
} from './utils/oddsHelpers';

const renderBettingOdds = () => {
  const bettingAnalysis = shotProbabilities?.betting_analysis;

  if (!bettingAnalysis) return null;

  if (bettingAnalysis.error) {
    return (
      <Box className="betting-odds-section">
        <Typography variant="caption" className="odds-unavailable">
          ⚠️ Odds temporarily unavailable
        </Typography>
      </Box>
    );
  }

  const {
    offer_double,
    expected_value,
    risk_level,
    reasoning
  } = bettingAnalysis;

  const probabilityColor = getProbabilityColor(offer_double);
  const probabilityLabel = getProbabilityLabel(offer_double);
  const evColor = expected_value >= 0 ? 'success' : 'error';

  return (
    <Box className="betting-odds-section">
      <Box display="flex" alignItems="center" gap={0.5}>
        <Typography variant="overline">📊 Betting Odds</Typography>
        <EducationalTooltip
          title="What are betting odds?"
          content="These probabilities show how likely betting scenarios are based on game state, player positions, and strategic factors."
        />
      </Box>

      <Box display="flex" alignItems="center" gap={1} mt={1}>
        <Typography variant="body2" color={`${probabilityColor}.main`}>
          Double {probabilityLabel}: {Math.round(offer_double * 100)}%
        </Typography>
        <ProbabilityBar value={offer_double} />
      </Box>

      <Typography
        variant="body2"
        className={expected_value >= 0 ? 'expected-value-positive' : 'expected-value-negative'}
        mt={0.5}
      >
        Expected Value: {formatExpectedValue(expected_value)} pts
        {expected_value >= 0 ? ' 📈' : ' 📉'}
      </Typography>

      {risk_level && (
        <Typography variant="body2" color={`${getRiskLevelColor(risk_level)}.main`} mt={0.5}>
          Risk: {risk_level.charAt(0).toUpperCase() + risk_level.slice(1)}
        </Typography>
      )}

      {reasoning && (
        <Typography variant="caption" color="text.secondary" display="block" mt={0.5}>
          ℹ️ {reasoning}
        </Typography>
      )}
    </Box>
  );
};

// In the main component return:
return (
  <Card className="betting-card">
    {/* Existing betting info */}
    {renderBettingOdds()}
  </Card>
);
```

**Verification:**
```bash
npm test -- BettingCard.odds.test.js
npm test -- BettingCard.test.js  # Ensure existing tests still pass
```

---

#### Task 2.3: Enhance DecisionButtons with Odds Hints
**File:** `frontend/src/components/simulation/visual/DecisionButtons.jsx`
**Estimated Time:** 1 hour

**Acceptance Criteria:**
- [ ] Shows probability badge on betting buttons
- [ ] Shows hint text below button
- [ ] Applies colored border based on recommendation
- [ ] Works with `accept_double` action
- [ ] Works with `offer_double` action
- [ ] Handles missing odds gracefully
- [ ] Other buttons (partnership, shot) unaffected

**Test Cases:**
```javascript
// __tests__/DecisionButtons.odds.test.js
- shows probability badge for accept_double
- shows probability badge for offer_double
- shows green border for high-probability accept
- shows red border for negative EV accept
- shows hint text with expected value
- handles missing betting_analysis
- non-betting buttons unaffected
- probability badge uses correct color
```

**Implementation Steps:**
1. Add helper functions for button styling and hints
2. Conditionally render probability badge
3. Conditionally render hint text
4. Apply border styling based on odds

**Code Snippet:**
```javascript
import { Chip } from '@mui/material';
import { formatExpectedValue } from './utils/oddsHelpers';

const getButtonStyling = (action, bettingAnalysis) => {
  if (!bettingAnalysis) {
    return { borderColor: 'divider' };
  }

  const { accept_double, expected_value } = bettingAnalysis;

  if (action === 'accept_double') {
    if (accept_double > 0.6 && expected_value > 0) {
      return {
        borderColor: 'success.main',
        borderWidth: 2,
        sx: { borderStyle: 'solid' }
      };
    }
    if (expected_value < 0) {
      return {
        borderColor: 'error.main',
        borderWidth: 2,
        sx: { borderStyle: 'solid' }
      };
    }
  }

  if (action === 'offer_double') {
    if (expected_value > 1) {
      return { borderColor: 'success.main', borderWidth: 2 };
    }
    if (expected_value < -1) {
      return { borderColor: 'error.main', borderWidth: 2 };
    }
  }

  return { borderColor: 'divider' };
};

const getButtonHint = (action, bettingAnalysis) => {
  if (!bettingAnalysis) return null;

  const { expected_value, risk_level } = bettingAnalysis;

  if (action === 'accept_double') {
    return `Expected: ${formatExpectedValue(expected_value)} pts`;
  }

  if (action === 'offer_double') {
    return `Risk: ${risk_level || 'Unknown'} (${formatExpectedValue(expected_value)} pts expected)`;
  }

  return null;
};

const getProbabilityBadge = (action, bettingAnalysis) => {
  if (!bettingAnalysis) return null;

  const probability = action === 'accept_double'
    ? bettingAnalysis.accept_double
    : action === 'offer_double'
    ? bettingAnalysis.offer_double
    : null;

  if (!probability) return null;

  const color = probability > 0.6 ? 'success' : probability > 0.4 ? 'warning' : 'default';

  return (
    <Chip
      label={`${Math.round(probability * 100)}%`}
      size="small"
      color={color}
    />
  );
};

// In button rendering:
const renderButton = (option) => {
  const bettingAnalysis = shotProbabilities?.betting_analysis;
  const styling = getButtonStyling(option.action, bettingAnalysis);
  const hint = getButtonHint(option.action, bettingAnalysis);
  const probabilityBadge = getProbabilityBadge(option.action, bettingAnalysis);

  return (
    <Button
      key={option.action}
      onClick={() => onDecision(option)}
      disabled={loading}
      variant="outlined"
      sx={{
        ...styling,
        flexDirection: 'column',
        alignItems: 'flex-start',
        p: 2,
        minHeight: 80
      }}
    >
      <Box display="flex" justifyContent="space-between" width="100%" alignItems="center">
        <Typography variant="button">
          {option.icon} {option.label}
        </Typography>
        {probabilityBadge}
      </Box>
      {hint && (
        <Typography variant="caption" color="text.secondary" mt={0.5}>
          {hint}
        </Typography>
      )}
    </Button>
  );
};
```

**Verification:**
```bash
npm test -- DecisionButtons.odds.test.js
npm test -- DecisionButtons.test.js  # Ensure existing tests still pass
```

---

### Phase 3: API Integration

#### Task 3.1: Add Odds Fetching Function to SimulationMode
**File:** `frontend/src/components/simulation/SimulationMode.js`
**Estimated Time:** 45 minutes

**Acceptance Criteria:**
- [ ] `fetchBettingOdds(gameState)` function added
- [ ] Makes POST request to `/api/wgp/quick-odds`
- [ ] Includes game_id, player_id, current_state in body
- [ ] Updates `shotProbabilities` state on success
- [ ] Handles errors gracefully (logs warning, continues)
- [ ] Sets error state in shotProbabilities on failure
- [ ] Includes 5-second timeout

**Test Cases:**
```javascript
// __tests__/SimulationMode.odds.test.js
- fetchBettingOdds makes POST to correct endpoint
- request includes game_id, player_id, current_state
- updates shotProbabilities with betting_analysis
- handles network errors gracefully
- handles timeout errors gracefully
- sets error state in shotProbabilities on failure
- logs warning on error (doesn't throw)
```

**Implementation:**
```javascript
const fetchBettingOdds = async (currentGameState) => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${API_BASE_URL}/wgp/quick-odds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        game_id: currentGameState.game_id,
        player_id: 'human',
        current_state: currentGameState
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      console.warn('Failed to fetch betting odds:', response.status);
      setShotProbabilities(prev => ({
        ...prev,
        betting_analysis: { error: 'unavailable' }
      }));
      return;
    }

    const oddsData = await response.json();

    setShotProbabilities(prev => ({
      ...prev,
      betting_analysis: oddsData.betting_probabilities
    }));

  } catch (error) {
    if (error.name === 'AbortError') {
      console.warn('Betting odds request timed out');
    } else {
      console.warn('Error fetching betting odds:', error);
    }

    setShotProbabilities(prev => ({
      ...prev,
      betting_analysis: { error: 'unavailable' }
    }));
  }
};
```

**Verification:**
```bash
npm test -- SimulationMode.odds.test.js
```

---

#### Task 3.2: Integrate Odds Fetching into makeDecision Flow
**File:** `frontend/src/components/simulation/SimulationMode.js`
**Estimated Time:** 30 minutes

**Acceptance Criteria:**
- [ ] Odds fetched when `interaction_needed.type === 'betting_decision'`
- [ ] Odds cleared when no betting decision needed
- [ ] Odds fetched after game state updated
- [ ] Doesn't block other decision processing
- [ ] Works in mock mode (doesn't fetch)

**Test Cases:**
```javascript
// __tests__/SimulationMode.odds-integration.test.js
- fetches odds when betting_decision interaction needed
- clears odds when no betting decision
- doesn't fetch odds for other interaction types
- doesn't break existing decision flow
- doesn't fetch in mock mode
```

**Implementation:**
```javascript
const makeDecision = async (decision) => {
  setLoading(true);

  // Handle mock mode
  if (isMockMode) {
    handleMockDecision(decision);
    return;
  }

  try {
    // Step 1: Make decision
    const response = await fetch(`${API_BASE_URL}/simulation/play-hole`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        game_id: gameState.game_id,
        decision: decision
      })
    });

    const data = await response.json();

    // Step 2: Update game state
    setGameState(data.game_state);
    setInteractionNeeded(data.interaction_needed || null);
    // ... other state updates

    // Step 3: Fetch betting odds if needed
    if (data.interaction_needed?.type === 'betting_decision') {
      await fetchBettingOdds(data.game_state);
    } else {
      // Clear betting analysis if no betting decision
      setShotProbabilities(prev => ({
        ...prev,
        betting_analysis: null
      }));
    }

    setLoading(false);
  } catch (error) {
    console.error('Decision error:', error);
    addFeedback(`Error making decision: ${error.message}`);
    setLoading(false);
  }
};
```

**Verification:**
```bash
npm test -- SimulationMode.odds-integration.test.js
npm test -- SimulationMode.test.js  # Ensure existing tests pass
```

---

#### Task 3.3: Implement Odds Caching Strategy
**File:** `frontend/src/components/simulation/SimulationMode.js`
**Estimated Time:** 45 minutes

**Acceptance Criteria:**
- [ ] Cache key based on game_id + hole_number + shot_number
- [ ] Returns cached odds if key matches
- [ ] Fetches fresh odds if key doesn't match
- [ ] Logs cache hit/miss for debugging
- [ ] Cache cleared on new shot or hole

**Test Cases:**
```javascript
// __tests__/SimulationMode.caching.test.js
- uses cached odds when same decision point
- fetches new odds when shot changes
- fetches new odds when hole changes
- generates correct cache key
- logs cache hits
- clears cache on playNextShot
```

**Implementation:**
```javascript
// Add state for caching
const [oddsCache, setOddsCache] = useState({
  key: null,
  data: null
});

const getCacheKey = (gameState) => {
  if (!gameState) return null;
  const hole = gameState.hole_state?.hole_number || 0;
  const shot = gameState.hole_state?.current_shot_number || 0;
  return `${gameState.game_id}_${hole}_${shot}`;
};

const fetchBettingOdds = async (currentGameState) => {
  const cacheKey = getCacheKey(currentGameState);

  // Check cache
  if (oddsCache.key === cacheKey && oddsCache.data) {
    console.log('Using cached betting odds');
    setShotProbabilities(prev => ({
      ...prev,
      betting_analysis: oddsCache.data
    }));
    return;
  }

  // Fetch fresh odds (existing implementation)
  try {
    // ... existing fetch logic ...

    // Update cache
    setOddsCache({
      key: cacheKey,
      data: oddsData.betting_probabilities
    });

    setShotProbabilities(prev => ({
      ...prev,
      betting_analysis: oddsData.betting_probabilities
    }));

  } catch (error) {
    // ... existing error handling ...
  }
};

// Clear cache in playNextShot
const playNextShot = async () => {
  // Clear odds cache
  setOddsCache({ key: null, data: null });

  // ... existing playNextShot logic ...
};
```

**Verification:**
```bash
npm test -- SimulationMode.caching.test.js
```

---

### Phase 4: Testing & Verification

#### Task 4.1: Write Integration Tests
**File:** `frontend/src/components/simulation/__tests__/SimulationMode.betting-odds-flow.test.js`
**Estimated Time:** 1 hour

**Acceptance Criteria:**
- [ ] Test complete flow: decision → odds fetch → display
- [ ] Test caching behavior
- [ ] Test error handling scenarios
- [ ] Test interaction with DecisionButtons
- [ ] Test interaction with BettingCard
- [ ] All tests pass

**Test Cases:**
```javascript
describe('Betting Odds Complete Flow', () => {
  test('fetches and displays odds at betting decision', async () => {
    // Setup mocks
    // Render SimulationMode
    // Trigger decision that needs betting
    // Verify odds fetched
    // Verify odds displayed in BettingCard
    // Verify button hints appear
  });

  test('caches odds for same decision point', async () => {
    // Make decision
    // Verify fetch called once
    // User reviews decision (no re-fetch)
    // Verify fetch still called only once
  });

  test('handles API failure gracefully', async () => {
    // Mock API to fail
    // Make decision
    // Verify "Odds unavailable" shown
    // Verify game continues
    // Verify buttons still work
  });

  test('clears odds on new shot', async () => {
    // Show odds
    // Play next shot
    // Verify odds cleared
  });
});
```

**Verification:**
```bash
npm test -- SimulationMode.betting-odds-flow.test.js
```

---

#### Task 4.2: Manual Testing Checklist
**Estimated Time:** 45 minutes

**Checklist:**
- [ ] Start simulation game
- [ ] Play to betting decision point
- [ ] Verify odds display in BettingCard
- [ ] Verify button hints appear
- [ ] Verify colors match probabilities
- [ ] Click educational tooltip, verify content
- [ ] Make decision, verify odds update
- [ ] Test on desktop (>1024px)
- [ ] Test on tablet (768-1024px)
- [ ] Test on mobile (<768px)
- [ ] Simulate API error (block network), verify graceful handling
- [ ] Check console for errors
- [ ] Verify no performance lag

**How to Simulate API Error:**
Open DevTools → Network → Right-click on `/quick-odds` request → Block request URL

**Verification Document:**
Create `docs/manual-testing/betting-odds-verification.md` with results

---

#### Task 4.3: Performance Testing
**Estimated Time:** 30 minutes

**Acceptance Criteria:**
- [ ] Odds fetch completes in <200ms
- [ ] No UI lag during fetch
- [ ] Component renders in <50ms
- [ ] No memory leaks after 100 decisions
- [ ] Browser DevTools performance profile shows no bottlenecks

**How to Test:**
1. Open React DevTools Profiler
2. Make 10 decisions with odds
3. Check render times
4. Open Performance tab in browser DevTools
5. Record decision flow
6. Analyze flamegraph for bottlenecks

**Verification:**
Document results in `docs/performance/betting-odds-profile.md`

---

### Phase 5: Documentation & Cleanup

#### Task 5.1: Add Component Documentation
**File:** `frontend/src/components/simulation/visual/README.md`
**Estimated Time:** 30 minutes

**Acceptance Criteria:**
- [ ] Document BettingCard `shotProbabilities.betting_analysis` prop
- [ ] Document DecisionButtons odds integration
- [ ] Add usage examples
- [ ] Add error state examples
- [ ] Document EducationalTooltip component

**Add to README:**
```markdown
### Betting Odds Integration

The visual interface displays real-time betting odds when available.

#### BettingCard

Shows betting probabilities and recommendations:

**Props:**
- `shotProbabilities.betting_analysis` - Odds data from backend
  ```javascript
  {
    offer_double: 0.65,        // Probability opponent will offer
    accept_double: 0.42,       // Probability accepting is +EV
    expected_value: 2.3,       // Expected points gained/lost
    risk_level: "medium",      // low/medium/high
    reasoning: "You are ahead"
  }
  ```

**Error States:**
- `{ error: 'unavailable' }` - Shows "Odds temporarily unavailable"
- `null` or `undefined` - Hides odds section

#### DecisionButtons

Betting decision buttons show contextual hints:
- Probability badge (e.g., "65%")
- Expected value hint
- Colored borders (green = recommended, red = risky)

#### EducationalTooltip

Provides in-context help:

```javascript
<EducationalTooltip
  title="What are betting odds?"
  content="Explanation text..."
/>
```
```

**Verification:**
Review README for clarity and completeness

---

#### Task 5.2: Update Main README
**File:** `README.md` (root)
**Estimated Time:** 15 minutes

**Acceptance Criteria:**
- [ ] Add "Betting Odds" feature to features list
- [ ] Add screenshot or description
- [ ] Update architecture diagram if needed

**Verification:**
Review with team

---

#### Task 5.3: Create PR Description
**File:** GitHub PR
**Estimated Time:** 20 minutes

**Acceptance Criteria:**
- [ ] Link to design document
- [ ] List all changes
- [ ] Include screenshots/GIFs
- [ ] Testing checklist
- [ ] Deployment notes

**PR Template:**
```markdown
## Betting Odds Integration

Adds real-time betting probability display to simulation interface.

### Design Document
See: `docs/plans/2025-01-28-betting-odds-integration.md`

### Changes
- ✅ Enhanced BettingCard with odds display
- ✅ Enhanced DecisionButtons with hints
- ✅ Added EducationalTooltip component
- ✅ Integrated /wgp/quick-odds API
- ✅ Implemented smart caching
- ✅ Added error handling

### Screenshots
[Add screenshots]

### Testing
- [x] Unit tests pass (46/46)
- [x] Integration tests pass
- [x] Manual testing complete
- [x] Performance profiling done
- [x] Mobile responsive verified

### Deployment Notes
- Feature gracefully degrades if API fails
- No database changes required
- Backend endpoints already exist
- Safe to deploy incrementally
```

---

## Summary

### Total Estimated Time: 10-12 hours

**Breakdown:**
- Phase 1: Foundation (1.5 hours)
- Phase 2: Components (3 hours)
- Phase 3: API Integration (2 hours)
- Phase 4: Testing (2.5 hours)
- Phase 5: Documentation (1 hour)

### Task Dependencies

```
1.1, 1.2, 1.3 (parallel)
   ↓
2.1 (depends on 1.2, 1.3)
   ↓
2.2, 2.3 (parallel, depend on 2.1)
   ↓
3.1 → 3.2 → 3.3 (sequential)
   ↓
4.1, 4.2, 4.3 (parallel)
   ↓
5.1, 5.2, 5.3 (parallel)
```

### Critical Path
1.1 → 1.2 → 2.1 → 2.2 → 3.1 → 3.2 → 4.1

### Quick Start Order
1. Task 1.2 (utilities) - needed by everything
2. Task 1.3 (CSS) - needed for styling
3. Task 2.1 (ProbabilityBar) - simple, builds confidence
4. Task 1.1 (EducationalTooltip) - simple, standalone
5. Task 2.2 (BettingCard) - visible progress
6. Task 3.1 (API fetching) - backend integration
7. Task 3.2 (Integration) - tie it together
8. Task 2.3 (DecisionButtons) - polish
9. Task 3.3 (Caching) - optimization
10. Task 4.x (Testing) - verification

### Success Metrics
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Manual testing checklist complete
- ✅ No console errors
- ✅ No performance regressions
- ✅ Works on desktop, tablet, mobile
- ✅ Gracefully handles API failures
- ✅ Documentation updated

---

**Next Steps:**
1. Review this plan
2. Set up git worktree (optional but recommended)
3. Start with Task 1.2 (utilities)
4. Follow TDD approach for each task
5. Commit after each completed task
6. Run full test suite before Phase 5

**Questions Before Starting:**
- Do you want to use a git worktree for isolation?
- Should we implement all tasks or prioritize MVP?
- Any specific testing requirements?
- Timeline constraints?
