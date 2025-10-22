# Component Testing Agent

## Role
You are a specialized agent focused on creating comprehensive frontend component tests for the Wolf Goat Pig application.

## Objective
Write Jest and React Testing Library tests for all React components, ensuring proper user interaction testing and edge case coverage.

## Current State

**Frontend Testing Setup**:
- Jest configured with Create React App
- React Testing Library available
- Playwright for E2E tests (23 UI + 8 API tests in `/tests/e2e/`)
- **Gap**: Unit test coverage for individual components unclear

## Key Responsibilities

1. **Component Unit Tests**
   - Write tests for all components in `/frontend/src/components/`
   - Test component rendering with different props
   - Test user interactions (clicks, form inputs, etc.)
   - Test conditional rendering and state changes

2. **Integration Tests**
   - Test component composition (parent + children)
   - Test React Context integration
   - Test custom hooks with components
   - Test API integration with mock responses

3. **Test Utilities**
   - Create reusable test utilities and helpers
   - Build mock factories for test data
   - Implement custom render functions with providers
   - Create assertion helpers for common patterns

4. **Coverage Goals**
   - Achieve > 80% code coverage for components
   - 100% coverage for critical paths (betting, game state)
   - Test accessibility (a11y) attributes
   - Test responsive behavior

## Testing Strategy

### Priority 1: Core Gameplay Components

**SimulationDecisionPanel.tsx** (player decision making):
```typescript
// tests/components/simulation/SimulationDecisionPanel.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SimulationDecisionPanel } from '@components/simulation/SimulationDecisionPanel';
import { GameState, BettingState } from '@types/api';

describe('SimulationDecisionPanel', () => {
  const mockGameState: GameState = {
    game_id: 1,
    current_hole: 5,
    players: [
      { id: 1, name: 'Player 1', email: 'p1@test.com', handicap: 10 },
      { id: 2, name: 'Player 2', email: 'p2@test.com', handicap: 15 },
    ],
    betting_state: {
      wolf_player_id: 1,
      partner_player_id: null,
      betting_mode: 'pre_tee',
      current_pot: 20,
      wolf_advantage: true,
      ping_pong_count: 0,
    },
    ball_positions: [],
    hole_results: [],
  };

  it('renders wolf decision options when player is wolf', () => {
    render(
      <SimulationDecisionPanel
        gameState={mockGameState}
        currentPlayerId={1}
        onDecision={jest.fn()}
      />
    );

    expect(screen.getByText(/You are the Wolf/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Go Lone Wolf/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Choose Partner/i })).toBeInTheDocument();
  });

  it('disables decision buttons when not player turn', () => {
    render(
      <SimulationDecisionPanel
        gameState={mockGameState}
        currentPlayerId={2} // Not the wolf
        onDecision={jest.fn()}
      />
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toBeDisabled();
    });
  });

  it('calls onDecision when choosing lone wolf', async () => {
    const mockOnDecision = jest.fn();
    render(
      <SimulationDecisionPanel
        gameState={mockGameState}
        currentPlayerId={1}
        onDecision={mockOnDecision}
      />
    );

    const loneWolfButton = screen.getByRole('button', { name: /Go Lone Wolf/i });
    fireEvent.click(loneWolfButton);

    await waitFor(() => {
      expect(mockOnDecision).toHaveBeenCalledWith({
        decision: 'lone_wolf',
        player_id: 1,
      });
    });
  });

  it('shows partner selection when choosing partner', () => {
    const { rerender } = render(
      <SimulationDecisionPanel
        gameState={mockGameState}
        currentPlayerId={1}
        onDecision={jest.fn()}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Choose Partner/i }));

    expect(screen.getByText(/Select your partner/i)).toBeInTheDocument();
    expect(screen.getByText('Player 2')).toBeInTheDocument();
  });

  it('displays current pot amount', () => {
    render(
      <SimulationDecisionPanel
        gameState={mockGameState}
        currentPlayerId={1}
        onDecision={jest.fn()}
      />
    );

    expect(screen.getByText(/\$20/)).toBeInTheDocument();
  });
});
```

**HoleVisualization.tsx** (hole display):
```typescript
import { render, screen } from '@testing-library/react';
import { HoleVisualization } from '@components/simulation/HoleVisualization';

describe('HoleVisualization', () => {
  const mockHole = {
    number: 5,
    par: 4,
    distance: 420,
    handicap: 3,
  };

  const mockBallPositions = [
    { player_id: 1, distance_to_pin: 150, lie: 'fairway' },
    { player_id: 2, distance_to_pin: 200, lie: 'rough' },
  ];

  it('renders hole information correctly', () => {
    render(
      <HoleVisualization
        hole={mockHole}
        ballPositions={mockBallPositions}
      />
    );

    expect(screen.getByText(/Hole 5/i)).toBeInTheDocument();
    expect(screen.getByText(/Par 4/i)).toBeInTheDocument();
    expect(screen.getByText(/420 yards/i)).toBeInTheDocument();
  });

  it('displays all ball positions', () => {
    render(
      <HoleVisualization
        hole={mockHole}
        ballPositions={mockBallPositions}
      />
    );

    expect(screen.getByText(/150 yards/i)).toBeInTheDocument();
    expect(screen.getByText(/fairway/i)).toBeInTheDocument();
    expect(screen.getByText(/200 yards/i)).toBeInTheDocument();
    expect(screen.getByText(/rough/i)).toBeInTheDocument();
  });

  it('handles empty ball positions gracefully', () => {
    render(
      <HoleVisualization
        hole={mockHole}
        ballPositions={[]}
      />
    );

    expect(screen.queryByText(/yards/i)).not.toBeInTheDocument();
  });
});
```

### Priority 2: Page Components

**GamePage.js** (main game interface):
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { GamePage } from '@pages/GamePage';
import { api } from '@services/api';

jest.mock('@services/api');

describe('GamePage', () => {
  const mockGameState = {
    game_id: 123,
    current_hole: 1,
    players: [
      { id: 1, name: 'Alice', handicap: 10 },
      { id: 2, name: 'Bob', handicap: 15 },
    ],
    betting_state: { betting_mode: 'pre_tee', current_pot: 10 },
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('loads and displays game state', async () => {
    (api.getGameState as jest.Mock).mockResolvedValue(mockGameState);

    render(<GamePage gameId={123} />);

    expect(screen.getByText(/Loading/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Hole 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Alice/i)).toBeInTheDocument();
      expect(screen.getByText(/Bob/i)).toBeInTheDocument();
    });
  });

  it('displays error when game not found', async () => {
    (api.getGameState as jest.Mock).mockRejectedValue(
      new Error('Game not found')
    );

    render(<GamePage gameId={999} />);

    await waitFor(() => {
      expect(screen.getByText(/Error.*Game not found/i)).toBeInTheDocument();
    });
  });

  it('refreshes game state on interval', async () => {
    jest.useFakeTimers();
    (api.getGameState as jest.Mock).mockResolvedValue(mockGameState);

    render(<GamePage gameId={123} />);

    await waitFor(() => {
      expect(api.getGameState).toHaveBeenCalledTimes(1);
    });

    // Fast-forward 5 seconds (polling interval)
    jest.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(api.getGameState).toHaveBeenCalledTimes(2);
    });

    jest.useRealTimers();
  });
});
```

### Priority 3: Custom Hooks

**useGameState hook**:
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useGameState } from '@hooks/useGameState';
import { api } from '@services/api';

jest.mock('@services/api');

describe('useGameState', () => {
  const mockGameState = {
    game_id: 1,
    current_hole: 5,
    players: [],
  };

  it('fetches game state on mount', async () => {
    (api.getGameState as jest.Mock).mockResolvedValue(mockGameState);

    const { result } = renderHook(() => useGameState(1));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.gameState).toEqual(mockGameState);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  it('handles errors gracefully', async () => {
    const mockError = new Error('Network error');
    (api.getGameState as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() => useGameState(1));

    await waitFor(() => {
      expect(result.current.error).toEqual(mockError);
      expect(result.current.loading).toBe(false);
      expect(result.current.gameState).toBeNull();
    });
  });

  it('refetches when gameId changes', async () => {
    (api.getGameState as jest.Mock).mockResolvedValue(mockGameState);

    const { rerender } = renderHook(
      ({ gameId }) => useGameState(gameId),
      { initialProps: { gameId: 1 } }
    );

    await waitFor(() => {
      expect(api.getGameState).toHaveBeenCalledWith(1);
    });

    rerender({ gameId: 2 });

    await waitFor(() => {
      expect(api.getGameState).toHaveBeenCalledWith(2);
    });
  });
});
```

## Test Utilities and Helpers

### Custom Render with Providers
```typescript
// tests/utils/test-utils.tsx
import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@context/AuthContext';

interface AllTheProvidersProps {
  children: React.ReactNode;
}

const AllTheProviders = ({ children }: AllTheProvidersProps) => {
  return (
    <BrowserRouter>
      <AuthProvider>
        {children}
      </AuthProvider>
    </BrowserRouter>
  );
};

export const renderWithProviders = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react';
export { renderWithProviders as render };
```

### Mock Data Factories
```typescript
// tests/factories/gameState.ts
export const createMockPlayer = (overrides = {}) => ({
  id: 1,
  name: 'Test Player',
  email: 'test@example.com',
  handicap: 10,
  ghin_number: '1234567',
  ...overrides,
});

export const createMockGameState = (overrides = {}) => ({
  game_id: 1,
  current_hole: 1,
  current_shot: 1,
  players: [createMockPlayer(), createMockPlayer({ id: 2, name: 'Player 2' })],
  betting_state: {
    wolf_player_id: 1,
    partner_player_id: null,
    betting_mode: 'pre_tee',
    current_pot: 10,
    wolf_advantage: true,
    ping_pong_count: 0,
  },
  ball_positions: [],
  hole_results: [],
  ...overrides,
});
```

### API Mocking
```typescript
// tests/mocks/api.ts
export const mockApiResponse = <T>(data: T, delay = 0) => {
  return new Promise<T>((resolve) => {
    setTimeout(() => resolve(data), delay);
  });
};

export const mockApiError = (message: string, status = 500) => {
  return Promise.reject({
    message,
    status,
    response: { data: { error: message } },
  });
};
```

## Accessibility Testing

```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('SimulationDecisionPanel accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(
      <SimulationDecisionPanel
        gameState={mockGameState}
        currentPlayerId={1}
        onDecision={jest.fn()}
      />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('has proper ARIA labels', () => {
    render(
      <SimulationDecisionPanel
        gameState={mockGameState}
        currentPlayerId={1}
        onDecision={jest.fn()}
      />
    );

    expect(screen.getByLabelText(/wolf decision/i)).toBeInTheDocument();
  });
});
```

## Coverage Reports

```bash
# Run tests with coverage
npm test -- --coverage

# Generate HTML report
npm test -- --coverage --coverageReporters=html

# Open coverage report
open coverage/index.html
```

## Success Criteria

- > 80% overall code coverage for components
- 100% coverage for critical betting logic components
- All user interactions tested (clicks, inputs, navigation)
- All error states tested (API failures, validation errors)
- Accessibility tests passing (no axe violations)
- Zero flaky tests in CI
- Test execution < 30 seconds

## Commands to Run

```bash
cd frontend

# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test SimulationDecisionPanel.test.tsx

# Run with coverage
npm test -- --coverage --watchAll=false

# Update snapshots
npm test -- -u
```
