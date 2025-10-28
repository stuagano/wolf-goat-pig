# Betting Odds Integration Design

**Date:** January 28, 2025
**Author:** Claude Code
**Status:** Design Phase
**Related:** Simulation Visual Interface (2025-01-27)

## Executive Summary

Integrate real-time betting odds display into the Wolf-Goat-Pig simulation interface to help players make informed betting decisions. This feature will leverage the existing backend `OddsCalculator` service to provide probability-based recommendations directly in the UI.

**Goals:**
- Display betting probabilities at decision points
- Provide educational context for odds
- Enhance decision-making without overwhelming the interface
- Maintain game flow and performance

**Non-Goals:**
- Automated betting decisions
- Historical odds tracking
- Multi-scenario comparisons
- Performance analytics dashboard

## Background

### Current State

The backend already has a comprehensive `OddsCalculator` service with three endpoints:
- `/api/wgp/calculate-odds` - Full Monte Carlo analysis
- `/api/wgp/quick-odds` - Fast heuristic-based odds
- `/api/wgp/betting-opportunities` - Strategic analysis

The frontend simulation interface does not currently display these odds to users.

### User Need

Players struggle to make optimal betting decisions because they lack:
1. **Context** - Is offering a double strategically sound right now?
2. **Probabilities** - How likely is the opponent to offer me a double?
3. **Expected Value** - What are the points implications of accepting?

This information exists in the backend but is invisible to users.

## Design Overview

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SimulationMode                          │
│                                                             │
│  1. User makes decision                                     │
│     └─> POST /simulation/play-hole                         │
│                                                             │
│  2. Check response for betting decision needed              │
│     ├─> interactionNeeded.type === 'betting_decision'?     │
│     └─> If YES: Fetch odds                                 │
│                                                             │
│  3. Fetch betting odds                                      │
│     └─> POST /wgp/quick-odds                               │
│         ├─ game_id, player_id, current_state               │
│         └─> Returns: betting_probabilities                 │
│                                                             │
│  4. Merge odds into state                                   │
│     └─> setShotProbabilities({                             │
│           ...existing,                                      │
│           betting_analysis: odds.betting_probabilities      │
│         })                                                  │
│                                                             │
│  5. Components render with odds                             │
│     ├─> BettingCard: Shows probabilities and EV            │
│     └─> DecisionButtons: Shows hints and recommendations   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**Input:** Game state at betting decision point
**Process:** Fetch odds from `/wgp/quick-odds` endpoint
**Output:** Enhanced UI with probability-based recommendations

### Caching Strategy

**Smart Caching:**
- Fetch odds only when `interactionNeeded.type === 'betting_decision'`
- Cache in `shotProbabilities.betting_analysis`
- Clear cache when new shot is played
- Don't re-fetch if user just wants to review same decision

**Rationale:** Minimizes API calls while ensuring fresh data at decision points.

## Component Changes

### 1. BettingCard Component

**File:** `frontend/src/components/simulation/visual/BettingCard.jsx`

**New Props:**
```javascript
shotProbabilities: {
  betting_analysis: {
    offer_double: 0.65,        // Probability opponent will offer double
    accept_double: 0.42,       // Probability accepting is +EV
    expected_value: +2.3,      // Expected points gained/lost
    risk_level: "medium",      // low/medium/high
    confidence: 0.78,          // Model confidence (0-1)
    reasoning: "You are ahead and opponent is under pressure"
  }
}
```

**Visual Enhancements:**

Add new "Betting Odds" section:

```
┌──────────────────────────────────────────┐
│ BETTING                                  │
├──────────────────────────────────────────┤
│ Current Wager: 20 pts                    │
│ Base Wager: 10 pts                       │
│ Pot: 80 pts                              │
├──────────────────────────────────────────┤
│ 📊 BETTING ODDS                          │
│                                          │
│ Double Likely: 65% ●●●●●○○○              │  ← Green
│ Expected Value: +2.3 pts 📈              │  ← Green if +, red if -
│ Risk Level: Medium ⚠️                    │  ← Color-coded
│                                          │
│ ℹ️ Opponent under pressure               │  ← Reasoning
└──────────────────────────────────────────┘
```

**Color Coding:**
- Green (>60%): "Double Likely"
- Yellow (40-60%): "Double Possible"
- Gray (<40%): "Double Unlikely"

**Implementation Notes:**
```javascript
// In BettingCard.jsx
const getBettingOddsDisplay = (bettingAnalysis) => {
  if (!bettingAnalysis) return null;

  const { offer_double, expected_value, risk_level, reasoning } = bettingAnalysis;

  // Determine color based on probability
  const probabilityColor =
    offer_double > 0.6 ? 'success' :
    offer_double > 0.4 ? 'warning' :
    'disabled';

  const evColor = expected_value >= 0 ? 'success' : 'error';

  return (
    <Box className="betting-odds-section">
      <Typography variant="overline">📊 Betting Odds</Typography>

      <Box display="flex" alignItems="center" gap={1}>
        <Typography color={probabilityColor}>
          Double {offer_double > 0.6 ? 'Likely' : offer_double > 0.4 ? 'Possible' : 'Unlikely'}:
          {Math.round(offer_double * 100)}%
        </Typography>
        <ProbabilityBar value={offer_double} />
      </Box>

      <Typography color={evColor}>
        Expected Value: {expected_value >= 0 ? '+' : ''}{expected_value.toFixed(1)} pts
        {expected_value >= 0 ? ' 📈' : ' 📉'}
      </Typography>

      <Typography variant="caption" color="text.secondary">
        ℹ️ {reasoning}
      </Typography>
    </Box>
  );
};
```

### 2. DecisionButtons Component

**File:** `frontend/src/components/simulation/visual/DecisionButtons.jsx`

**Enhanced Button Display:**

Each betting decision button shows contextual hints:

```
┌─────────────────────────────────────────────┐
│ 🤝 Accept Double                      [65%] │  ← Green border
│ Expected: +2.3 pts                          │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 💰 Offer Double                       [12%] │  ← Red border
│ Risk: High (-1.8 pts expected)              │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 🚫 Pass                                     │  ← Neutral
│ No betting this hole                        │
└─────────────────────────────────────────────┘
```

**Button Styling Logic:**
```javascript
const getButtonStyling = (action, bettingAnalysis) => {
  if (!bettingAnalysis || action !== 'accept_double' && action !== 'offer_double') {
    return { borderColor: 'divider', variant: 'outlined' };
  }

  const { accept_double, expected_value } = bettingAnalysis;

  if (action === 'accept_double') {
    // Green border if accepting is +EV with high probability
    if (accept_double > 0.6) {
      return { borderColor: 'success.main', variant: 'outlined', borderWidth: 2 };
    }
    // Red border if accepting is -EV
    if (expected_value < 0) {
      return { borderColor: 'error.main', variant: 'outlined', borderWidth: 2 };
    }
  }

  if (action === 'offer_double') {
    // Green if offering has positive EV
    if (expected_value > 1) {
      return { borderColor: 'success.main', variant: 'outlined', borderWidth: 2 };
    }
    // Red if offering has negative EV
    if (expected_value < -1) {
      return { borderColor: 'error.main', variant: 'outlined', borderWidth: 2 };
    }
  }

  return { borderColor: 'divider', variant: 'outlined' };
};

const getButtonHint = (action, bettingAnalysis) => {
  if (!bettingAnalysis) return null;

  const { accept_double, expected_value, risk_level } = bettingAnalysis;

  if (action === 'accept_double') {
    return `Expected: ${expected_value >= 0 ? '+' : ''}${expected_value.toFixed(1)} pts`;
  }

  if (action === 'offer_double') {
    return `Risk: ${risk_level} (${expected_value >= 0 ? '+' : ''}${expected_value.toFixed(1)} pts expected)`;
  }

  return null;
};
```

**Implementation:**
```javascript
// In DecisionButtons.jsx
const renderBettingButton = (option) => {
  const bettingAnalysis = shotProbabilities?.betting_analysis;
  const styling = getButtonStyling(option.action, bettingAnalysis);
  const hint = getButtonHint(option.action, bettingAnalysis);
  const probability = option.action === 'accept_double' ?
    bettingAnalysis?.accept_double :
    bettingAnalysis?.offer_double;

  return (
    <Button
      key={option.action}
      onClick={() => onDecision(option)}
      disabled={loading}
      sx={{
        ...styling,
        flexDirection: 'column',
        alignItems: 'flex-start',
        p: 2,
      }}
    >
      <Box display="flex" justifyContent="space-between" width="100%">
        <Typography variant="button">
          {option.icon} {option.label}
        </Typography>
        {probability && (
          <Chip
            label={`${Math.round(probability * 100)}%`}
            size="small"
            color={probability > 0.6 ? 'success' : probability > 0.4 ? 'warning' : 'default'}
          />
        )}
      </Box>
      {hint && (
        <Typography variant="caption" color="text.secondary">
          {hint}
        </Typography>
      )}
    </Button>
  );
};
```

### 3. Educational Tooltips

**Add EducationalTooltip component:**

```javascript
// frontend/src/components/simulation/visual/EducationalTooltip.jsx
import React from 'react';
import { Tooltip, IconButton, Typography, Box } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';

const EducationalTooltip = ({ title, content }) => {
  return (
    <Tooltip
      title={
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            {title}
          </Typography>
          <Typography variant="body2">
            {content}
          </Typography>
        </Box>
      }
      arrow
      placement="top"
    >
      <IconButton size="small">
        <InfoIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  );
};

export default EducationalTooltip;
```

**Usage in BettingCard:**
```javascript
<Box display="flex" alignItems="center" gap={0.5}>
  <Typography variant="overline">📊 Betting Odds</Typography>
  <EducationalTooltip
    title="What are betting odds?"
    content="These probabilities show how likely betting scenarios are based on game state, player positions, and strategic factors. Use them to make informed decisions."
  />
</Box>
```

## API Integration

### 1. SimulationMode.js Changes

**Add odds fetching logic:**

```javascript
// In SimulationMode.js makeDecision function

const makeDecision = async (decision) => {
  setLoading(true);

  try {
    // Step 1: Make the decision
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

    // Step 3: Check if betting decision is needed
    if (data.interaction_needed?.type === 'betting_decision') {
      // Fetch betting odds
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
    setLoading(false);
  }
};

const fetchBettingOdds = async (currentGameState) => {
  try {
    const response = await fetch(`${API_BASE_URL}/wgp/quick-odds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        game_id: currentGameState.game_id,
        player_id: 'human',
        current_state: currentGameState
      })
    });

    if (!response.ok) {
      console.warn('Failed to fetch betting odds');
      return;
    }

    const oddsData = await response.json();

    // Merge betting analysis into shotProbabilities
    setShotProbabilities(prev => ({
      ...prev,
      betting_analysis: oddsData.betting_probabilities
    }));

  } catch (error) {
    console.warn('Error fetching betting odds:', error);
    // Gracefully degrade - game continues without odds
  }
};
```

### 2. API Response Format

**Expected response from `/wgp/quick-odds`:**

```json
{
  "status": "success",
  "betting_probabilities": {
    "offer_double": 0.65,
    "accept_double": 0.42,
    "expected_value": 2.3,
    "risk_level": "medium",
    "confidence": 0.78,
    "reasoning": "You are ahead and opponent is under pressure",
    "calculation_time_ms": 45
  }
}
```

### 3. Caching Strategy

**Implementation:**
- Cache in `shotProbabilities.betting_analysis`
- Key: `${gameState.game_id}_${gameState.hole_state.hole_number}_${gameState.hole_state.current_shot_number}`
- TTL: Until next shot or decision
- Clear on: New shot played, hole completed

```javascript
// Add cache key tracking
const [oddsCache, setOddsCache] = useState({
  key: null,
  data: null
});

const getCacheKey = (gameState) => {
  if (!gameState) return null;
  return `${gameState.game_id}_${gameState.hole_state?.hole_number}_${gameState.hole_state?.current_shot_number}`;
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

  // Fetch fresh odds
  try {
    const response = await fetch(`${API_BASE_URL}/wgp/quick-odds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        game_id: currentGameState.game_id,
        player_id: 'human',
        current_state: currentGameState
      })
    });

    if (!response.ok) {
      console.warn('Failed to fetch betting odds');
      return;
    }

    const oddsData = await response.json();

    // Update cache
    setOddsCache({
      key: cacheKey,
      data: oddsData.betting_probabilities
    });

    // Update state
    setShotProbabilities(prev => ({
      ...prev,
      betting_analysis: oddsData.betting_probabilities
    }));

  } catch (error) {
    console.warn('Error fetching betting odds:', error);
  }
};
```

## Error Handling

### API Failure Scenarios

**1. Network Error:**
```javascript
catch (error) {
  console.warn('Network error fetching betting odds:', error);
  // Game continues without odds display
  // Show subtle "Odds unavailable" indicator in BettingCard
  setShotProbabilities(prev => ({
    ...prev,
    betting_analysis: { error: 'unavailable' }
  }));
}
```

**UI Response:**
```
┌──────────────────────────────────────────┐
│ BETTING                                  │
├──────────────────────────────────────────┤
│ Current Wager: 20 pts                    │
│ 📊 BETTING ODDS                          │
│ ⚠️ Odds temporarily unavailable          │
└──────────────────────────────────────────┘
```

**2. Timeout:**
```javascript
const fetchBettingOddsWithTimeout = async (currentGameState, timeout = 5000) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${API_BASE_URL}/wgp/quick-odds`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ /* ... */ }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);
    // ... rest of handling
  } catch (error) {
    if (error.name === 'AbortError') {
      console.warn('Betting odds request timed out');
      // Show timeout indicator
    }
  }
};
```

**3. Stale Data:**
```javascript
// In BettingCard component
const isStaleData = (bettingAnalysis) => {
  if (!bettingAnalysis?.timestamp) return false;
  const ageSeconds = (Date.now() - bettingAnalysis.timestamp) / 1000;
  return ageSeconds > 10;
};

// Show indicator for stale data
{isStaleData(bettingAnalysis) && (
  <Typography variant="caption" color="warning.main">
    ⏱️ Recalculating odds...
  </Typography>
)}
```

**4. Missing Data:**
```javascript
// Graceful degradation in components
const bettingAnalysis = shotProbabilities?.betting_analysis;

if (!bettingAnalysis || bettingAnalysis.error) {
  // Don't show odds section
  return null;
}

// Continue with normal rendering
```

### User Experience

**Principles:**
- Never block gameplay due to odds fetch failure
- Show subtle indicators when odds unavailable
- Allow all decisions to proceed without odds
- Log errors for debugging but don't alert user

## Testing Strategy

### Unit Tests

**BettingCard Tests:**
```javascript
// frontend/src/components/simulation/visual/__tests__/BettingCard.odds.test.js

describe('BettingCard with Betting Odds', () => {
  test('renders odds section when betting_analysis present', () => {
    const props = {
      betting: { current_wager: 20 },
      baseWager: 10,
      shotProbabilities: {
        betting_analysis: {
          offer_double: 0.65,
          expected_value: 2.3,
          risk_level: 'medium'
        }
      }
    };

    render(<BettingCard {...props} />);

    expect(screen.getByText(/Double Likely/i)).toBeInTheDocument();
    expect(screen.getByText(/\+2.3 pts/i)).toBeInTheDocument();
  });

  test('renders error state when odds unavailable', () => {
    const props = {
      betting: { current_wager: 20 },
      shotProbabilities: {
        betting_analysis: { error: 'unavailable' }
      }
    };

    render(<BettingCard {...props} />);

    expect(screen.getByText(/Odds temporarily unavailable/i)).toBeInTheDocument();
  });

  test('does not render odds section when betting_analysis missing', () => {
    const props = {
      betting: { current_wager: 20 },
      shotProbabilities: {}
    };

    render(<BettingCard {...props} />);

    expect(screen.queryByText(/Betting Odds/i)).not.toBeInTheDocument();
  });
});
```

**DecisionButtons Tests:**
```javascript
// frontend/src/components/simulation/visual/__tests__/DecisionButtons.odds.test.js

describe('DecisionButtons with Betting Odds', () => {
  test('shows green border for high-probability accept_double', () => {
    const props = {
      interactionNeeded: {
        type: 'betting_decision',
        options: [{ action: 'accept_double', label: 'Accept Double' }]
      },
      shotProbabilities: {
        betting_analysis: {
          accept_double: 0.75,
          expected_value: 3.2
        }
      },
      onDecision: jest.fn()
    };

    const { container } = render(<DecisionButtons {...props} />);
    const button = screen.getByText(/Accept Double/i).closest('button');

    expect(button).toHaveStyle({ borderColor: expect.stringContaining('success') });
  });

  test('shows hint text with expected value', () => {
    const props = {
      interactionNeeded: {
        type: 'betting_decision',
        options: [{ action: 'accept_double', label: 'Accept Double' }]
      },
      shotProbabilities: {
        betting_analysis: {
          expected_value: 2.3
        }
      },
      onDecision: jest.fn()
    };

    render(<DecisionButtons {...props} />);

    expect(screen.getByText(/Expected: \+2.3 pts/i)).toBeInTheDocument();
  });
});
```

**SimulationMode API Integration Tests:**
```javascript
// frontend/src/components/simulation/__tests__/SimulationMode.odds.test.js

describe('SimulationMode Odds Integration', () => {
  test('fetches odds when betting decision needed', async () => {
    const mockOddsResponse = {
      betting_probabilities: {
        offer_double: 0.65,
        expected_value: 2.3
      }
    };

    fetch.mockImplementation((url) => {
      if (url.includes('/play-hole')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            game_state: { status: 'active' },
            interaction_needed: { type: 'betting_decision' }
          })
        });
      }
      if (url.includes('/quick-odds')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOddsResponse)
        });
      }
    });

    render(<SimulationMode />);

    fireEvent.click(screen.getByText(/Make Decision/i));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/quick-odds'),
        expect.any(Object)
      );
    });
  });

  test('handles odds fetch failure gracefully', async () => {
    fetch.mockImplementation((url) => {
      if (url.includes('/play-hole')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            game_state: { status: 'active' },
            interaction_needed: { type: 'betting_decision' }
          })
        });
      }
      if (url.includes('/quick-odds')) {
        return Promise.reject(new Error('Network error'));
      }
    });

    render(<SimulationMode />);

    fireEvent.click(screen.getByText(/Make Decision/i));

    // Should not crash, game continues
    await waitFor(() => {
      expect(screen.getByText(/Make Decision/i)).toBeInTheDocument();
    });
  });
});
```

### Integration Tests

**Full Flow Test:**
```javascript
describe('Betting Odds Full Flow', () => {
  test('complete betting decision with odds display', async () => {
    // Setup: Game state with betting decision
    const mockGameState = {
      game_id: 'test-123',
      hole_state: { hole_number: 1, current_shot_number: 3 },
      betting: { current_wager: 20 }
    };

    const mockOdds = {
      betting_probabilities: {
        offer_double: 0.65,
        accept_double: 0.42,
        expected_value: 2.3,
        risk_level: 'medium',
        reasoning: 'You are ahead'
      }
    };

    // Mock API calls
    fetch.mockImplementation((url) => {
      if (url.includes('/play-hole')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            game_state: mockGameState,
            interaction_needed: {
              type: 'betting_decision',
              options: [
                { action: 'accept_double', label: 'Accept Double' },
                { action: 'pass', label: 'Pass' }
              ]
            }
          })
        });
      }
      if (url.includes('/quick-odds')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOdds)
        });
      }
    });

    // Render and trigger decision
    render(<SimulationMode />);
    fireEvent.click(screen.getByText(/Play Next Shot/i));

    // Wait for odds to load and display
    await waitFor(() => {
      expect(screen.getByText(/Double Likely: 65%/i)).toBeInTheDocument();
    });

    // Verify all odds information displayed
    expect(screen.getByText(/Expected Value: \+2.3 pts/i)).toBeInTheDocument();
    expect(screen.getByText(/You are ahead/i)).toBeInTheDocument();

    // Verify button has recommendation styling
    const acceptButton = screen.getByText(/Accept Double/i).closest('button');
    expect(acceptButton).toHaveStyle({ borderWidth: '2px' });
  });
});
```

### Manual Testing Checklist

- [ ] Odds display at betting decision point
- [ ] Odds update correctly after each decision
- [ ] Green/yellow/gray color coding works
- [ ] Expected value shows with correct sign
- [ ] Educational tooltips are clear
- [ ] Button hints are helpful
- [ ] API failure shows "unavailable" gracefully
- [ ] Timeout shows "calculating" indicator
- [ ] No UI lag from API calls
- [ ] Caching prevents duplicate fetches
- [ ] Odds clear when new shot played
- [ ] Mobile responsive layout works
- [ ] Tooltips readable on small screens

## Performance Considerations

### API Call Optimization

**Current Performance:**
- `/wgp/quick-odds` response time: ~50-100ms
- UI update time: ~10ms
- Total perceived latency: <150ms

**Optimization Strategies:**

1. **Parallel Fetching:**
```javascript
// Fetch odds in parallel with other decision processing
const [gameResponse, oddsResponse] = await Promise.all([
  fetch('/simulation/play-hole', { /* ... */ }),
  fetch('/wgp/quick-odds', { /* ... */ })
]);
```

2. **Optimistic Updates:**
```javascript
// Show "Calculating odds..." immediately
setShotProbabilities(prev => ({
  ...prev,
  betting_analysis: { loading: true }
}));

// Fetch in background
fetchBettingOdds(gameState);
```

3. **Request Debouncing:**
```javascript
// Prevent rapid duplicate requests
const debouncedFetchOdds = debounce(fetchBettingOdds, 300);
```

### Render Optimization

**Component Memoization:**
```javascript
// Memoize BettingCard to prevent unnecessary re-renders
export default React.memo(BettingCard, (prevProps, nextProps) => {
  return (
    prevProps.betting === nextProps.betting &&
    prevProps.shotProbabilities?.betting_analysis === nextProps.shotProbabilities?.betting_analysis
  );
});
```

**Lazy Loading:**
```javascript
// Only render odds section when data available
{bettingAnalysis && <BettingOddsSection data={bettingAnalysis} />}
```

## Deployment Plan

### Phase 1: Backend Verification
- [ ] Verify `/wgp/quick-odds` endpoint works in production
- [ ] Test response format matches expected schema
- [ ] Load test endpoint with concurrent requests

### Phase 2: Frontend Implementation
- [ ] Implement BettingCard odds display
- [ ] Implement DecisionButtons hints
- [ ] Add educational tooltips
- [ ] Write unit tests

### Phase 3: Integration
- [ ] Add API fetching logic to SimulationMode
- [ ] Implement caching strategy
- [ ] Add error handling
- [ ] Write integration tests

### Phase 4: Testing
- [ ] Run full test suite
- [ ] Manual testing of all scenarios
- [ ] Performance testing
- [ ] Mobile device testing

### Phase 5: Deployment
- [ ] Deploy to staging environment
- [ ] User acceptance testing
- [ ] Deploy to production
- [ ] Monitor error rates and performance

## Rollback Plan

If issues arise:

1. **Quick Rollback:** Add feature flag to disable odds display
```javascript
const ENABLE_BETTING_ODDS = process.env.REACT_APP_ENABLE_BETTING_ODDS === 'true';

if (ENABLE_BETTING_ODDS && data.interaction_needed?.type === 'betting_decision') {
  await fetchBettingOdds(data.game_state);
}
```

2. **Gradual Rollout:** Enable for percentage of users
```javascript
const shouldShowOdds = () => {
  const userId = getUserId();
  return hashCode(userId) % 100 < ROLLOUT_PERCENTAGE;
};
```

3. **Full Revert:** Remove odds fetching, keep components dormant
   - Components gracefully handle missing data
   - No visual impact if `betting_analysis` is null

## Future Enhancements

**Not in Scope for v1:**

1. **Historical Odds Tracking**
   - Store odds over time
   - Show trends in betting decisions
   - Analyze optimal vs. actual decisions

2. **Multi-Scenario Comparison**
   - "What if I had doubled earlier?"
   - Compare different strategic paths
   - Monte Carlo simulation visualization

3. **Performance Analytics**
   - Track decision accuracy
   - Show learning progress
   - Personalized recommendations

4. **Advanced Odds Display**
   - Probability distribution graphs
   - Confidence intervals
   - Risk/reward heatmaps

5. **Automated Suggestions**
   - "Recommended action" indicator
   - Auto-play mode for learning
   - Strategy coaching

## Appendix

### Backend API Reference

**Endpoint:** `/api/wgp/quick-odds`

**Method:** POST

**Request:**
```json
{
  "game_id": "abc-123",
  "player_id": "human",
  "current_state": {
    "game_id": "abc-123",
    "players": [...],
    "hole_state": {...},
    "betting": {...}
  }
}
```

**Response:**
```json
{
  "status": "success",
  "betting_probabilities": {
    "offer_double": 0.65,
    "accept_double": 0.42,
    "expected_value": 2.3,
    "risk_level": "medium",
    "confidence": 0.78,
    "reasoning": "You are ahead and opponent is under pressure",
    "calculation_time_ms": 45
  }
}
```

**Error Response:**
```json
{
  "status": "error",
  "error": "Invalid game state",
  "message": "Game not found"
}
```

### Component File Structure

```
frontend/src/components/simulation/visual/
├── BettingCard.jsx                    # Enhanced with odds display
├── DecisionButtons.jsx                # Enhanced with hints
├── EducationalTooltip.jsx             # New component
├── __tests__/
│   ├── BettingCard.odds.test.js      # New tests
│   ├── DecisionButtons.odds.test.js  # New tests
│   └── EducationalTooltip.test.js    # New tests
└── styles.css                         # Add odds section styles
```

### CSS Additions

```css
/* Add to frontend/src/components/simulation/visual/styles.css */

.betting-odds-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--divider);
}

.betting-odds-section .probability-bar {
  display: flex;
  gap: 2px;
  height: 4px;
}

.betting-odds-section .probability-dot {
  width: 12px;
  height: 4px;
  border-radius: 2px;
  background-color: var(--secondary);
}

.betting-odds-section .probability-dot.filled {
  background-color: var(--success);
}

.odds-unavailable {
  color: var(--warning);
  font-size: 0.875rem;
  font-style: italic;
}

.expected-value-positive {
  color: var(--success);
}

.expected-value-negative {
  color: var(--error);
}

/* Button styling enhancements */
.decision-button-with-odds {
  position: relative;
}

.decision-button-with-odds .odds-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 0.75rem;
  font-weight: 600;
}

.decision-button-hint {
  margin-top: 4px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}
```

---

**Document Version:** 1.0
**Last Updated:** January 28, 2025
**Next Review:** After Phase 2 completion
