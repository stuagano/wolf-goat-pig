// frontend/src/components/game/__tests__/SimpleScorekeeper.betting.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import SimpleScorekeeper from '../SimpleScorekeeper';
import syncManager from '../../../services/syncManager';
import {
  createMockTheme,
  createMockPlayers,
  createMockCourseHoles
} from '../../../test-utils/mockFactories';

// Mock fetch globally
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({})
  })
);

// Mock ThemeProvider
vi.mock('../../../theme/Provider', async () => {
  const factories = await import('../../../test-utils/mockFactories');
  return {
    ThemeProvider: ({ children }) => <div>{children}</div>,
    useTheme: () => factories.createMockTheme({
      colors: {
        primary: '#059669',
        textPrimary: '#1f2937',
        textSecondary: '#6b7280',
        border: '#d1d5db',
        paper: '#ffffff',
        backgroundSecondary: '#f3f4f6'
      },
      buttonStyle: {
        padding: '12px 24px',
        borderRadius: '8px',
        border: 'none',
        cursor: 'pointer'
      },
      cardStyle: {
        background: '#ffffff',
        borderRadius: '8px',
        padding: '16px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }
    })
  };
});

// Mock Input component - filter out non-DOM props
vi.mock('../../ui', () => ({
  Input: function Input({ value, onChange, inputStyle, variant, ...props }) {
    return (
      <input
        value={value}
        onChange={onChange}
        style={inputStyle}
        {...props}
      />
    );
  }
}));

// Mock Scorecard component
vi.mock('../Scorecard', () => ({
  default: function MockScorecard() {
    return <div data-testid="mock-scorecard">Scorecard</div>;
  }
}));

// Mock GameCompletionView component
vi.mock('../GameCompletionView', () => ({
  default: function MockGameCompletionView() {
    return <div data-testid="mock-game-completion">Game Complete</div>;
  }
}));

// Mock BadgeNotification
vi.mock('../BadgeNotification', () => ({
  triggerBadgeNotification: vi.fn()
}));

describe('SimpleScorekeeper - Betting Interface', () => {
  const mockPlayers = createMockPlayers(4).map((player, i) => ({
    id: `p${i + 1}`,
    name: ['Alice', 'Bob', 'Charlie', 'Diana'][i],
    handicap: [10, 15, 8, 12][i]
  }));

  const mockCourse = {
    name: 'Test Course',
    holes: createMockCourseHoles(18).map((hole, i) => ({
      hole_number: i + 1,
      par: 4,
      handicap: i + 1,
      yards: 400
    }))
  };

  const defaultProps = {
    gameId: 'test-game-123',
    players: mockPlayers,
    course: mockCourse,
    onHoleComplete: vi.fn(),
    onGameComplete: vi.fn()
  };

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch.mockClear();
  });

  // Helper to find wager display text
  const findWagerText = (wagerValue) => {
    // Look for exact wager value in the Current Wager display
    try {
      const wagerTexts = screen.getAllByText(new RegExp(`${wagerValue}Q`, 'i'));
      return wagerTexts.length > 0;
    } catch (e) {
      return false;
    }
  };

  describe('Basic Betting Controls', () => {
    test('should display betting interface with player name', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      // Find player names in the rotation order display
      // The first player (Alice) should be displayed as the captain with the crown
      expect(screen.getAllByText(/Alice/).length).toBeGreaterThan(0);
    });

    test('should show current wager display', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      // The component shows "Wager" label (not "Current Wager")
      const wagerDisplay = screen.getByText(/^Wager$/i);
      expect(wagerDisplay).toBeInTheDocument();

      // Should show 1Q as default (may appear multiple times)
      expect(findWagerText(1)).toBe(true);
    });

    // Note: +/- wager buttons and high-stakes controls (÷2, Reset) have been removed from the UI.
    // Wager is now controlled via the betting actions panel (Double, Float, Option) with offer/accept flow.
  });

  describe('Active Modifiers Display', () => {
    test('should show Vinnie\'s Variation badge on holes 13-16', () => {
      // This would require advancing to hole 13
      // Placeholder for future implementation
      expect(true).toBe(true);
    });

    test('should show Option badge when captain is losing', () => {
      // This would require setting up losing captain state
      // Placeholder for future implementation
      expect(true).toBe(true);
    });

    test('should show Joe\'s Special badge in Hoepfinger phase', () => {
      // This would require advancing to hole 17/18
      // Placeholder for future implementation
      expect(true).toBe(true);
    });
  });

  describe('Team Mode Display', () => {
    test('Teams & bets starts closed, summarizes edits, and preserves them when reopened', () => {
      render(<SimpleScorekeeper {...defaultProps} />);
      const summary = screen.getByText('Optional hole details').closest('summary');
      const section = summary.closest('details');
      const teamSummary = screen.getByTestId('team-details-summary');
      expect(section).not.toHaveAttribute('open');
      expect(teamSummary).toHaveTextContent('Partners · Choose players');
      expect(screen.getByTestId('go-solo-button')).not.toBeVisible();
      expect(screen.getByText('Special Actions')).not.toBeVisible();
      expect(screen.getByTestId('quarters-input-p1')).toBeVisible();

      fireEvent.click(summary);
      expect(screen.getByTestId('go-solo-button')).toBeVisible();
      expect(screen.getByText('Special Actions')).toBeVisible();
      fireEvent.click(screen.getByTestId('partner-p1'));
      fireEvent.click(screen.getByTestId('partner-p2'));
      expect(teamSummary).toHaveTextContent('Partners · Alice & Bob');
      const specialActions = screen.getByText('Special Actions');
      fireEvent.click(specialActions);
      const specialPanel = specialActions.closest('div').parentElement;
      fireEvent.click(within(specialPanel).getAllByRole('button', { name: 'Alice' })[0]);
      expect(teamSummary).toHaveTextContent('Float: Alice');

      fireEvent.click(summary);
      expect(section).not.toHaveAttribute('open');
      expect(teamSummary).toHaveTextContent('Partners · Alice & Bob');
      fireEvent.click(summary);
      expect(teamSummary).toHaveTextContent('Partners · Alice & Bob');
      expect(teamSummary).toHaveTextContent('Float: Alice');
      fireEvent.click(screen.getByTestId('go-solo-button'));
      expect(teamSummary).toHaveTextContent('Solo');
      expect(screen.getByText(/Call The Duncan/i)).toBeVisible();
    });

    test('should show Partners or Solo indicator', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      // Find Partners/Solo indicator - use queryAllByText since there may be none or multiple
      const partnersIndicators = screen.queryAllByText(/Partners/);
      const soloIndicators = screen.queryAllByText(/Solo/);

      // Should have at least one of these indicators
      expect(partnersIndicators.length + soloIndicators.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    // Note: Direct wager manipulation buttons (+/-, Double, ÷2, Reset) have been removed.
    // Wager changes now happen via the offer/accept flow in useBettingState hook.
    // The following tests validate the current wager display behavior.

    test('should display initial wager correctly', () => {
      render(<SimpleScorekeeper {...defaultProps} />);
      
      // Default wager is 1Q
      expect(findWagerText(1)).toBe(true);
    });

    test('should display wager in lowercase q format', () => {
      render(<SimpleScorekeeper {...defaultProps} />);
      
      // The wager display uses lowercase 'q' (e.g., "1q")
      const wagerDisplay = screen.getByText(/1q/);
      expect(wagerDisplay).toBeInTheDocument();
    });

    test('wager display should be read-only (no direct manipulation buttons)', () => {
      render(<SimpleScorekeeper {...defaultProps} />);
      
      // Verify old controls are not present
      const incrementButton = screen.queryByRole('button', { name: '+' });
      const decrementButton = screen.queryByRole('button', { name: '-' });
      const halveButton = screen.queryByRole('button', { name: /÷2/ });
      const resetButton = screen.queryByRole('button', { name: /^Reset$/i });
      
      expect(incrementButton).not.toBeInTheDocument();
      expect(decrementButton).not.toBeInTheDocument();
      expect(halveButton).not.toBeInTheDocument();
      // Note: "Reset" may exist for other purposes, so we check specifically for wager reset
      // which was removed along with +/- buttons
    });
  });

  describe('Integration with Game Flow', () => {
    test('records quarters and advances without opening optional details or choosing teams', async () => {
      const sync = vi.spyOn(syncManager, 'syncHoleData').mockResolvedValue({ success: true });
      render(<SimpleScorekeeper {...defaultProps} />);
      const details = screen.getByText('Optional hole details').closest('details');
      expect(details).not.toHaveAttribute('open');
      expect(screen.getByText(/^Wager$/i)).not.toBeVisible();
      expect(screen.getByTestId('running-totals')).not.toBeVisible();
      expect(screen.getByTestId('mock-scorecard')).not.toBeVisible();
      expect(screen.getByTestId('scoring-hole-heading')).toHaveTextContent('Hole 1');
      fireEvent.change(screen.getByTestId('quarters-input-p1'), { target: { value: '12' } });
      for (const [id, name] of [['p2', 'Bob'], ['p3', 'Charlie']]) {
        fireEvent.click(screen.getByRole('button', { name: `${name} lost quarters` }));
        fireEvent.change(screen.getByTestId(`quarters-input-${id}`), { target: { value: '4' } });
      }
      fireEvent.click(screen.getByRole('button', { name: 'Fill remaining for Diana: Lost 4' }));
      fireEvent.click(screen.getByRole('button', { name: 'Save & next hole' }));
      await waitFor(() => expect(sync).toHaveBeenCalledWith(
        'test-game-123', { '1': { p1: 12, p2: -4, p3: -4, p4: -4 } }, expect.any(Object), 2,
      ));
      await waitFor(() => expect(screen.getByTestId('scoring-hole-heading')).toHaveTextContent('Hole 2'));
      expect(details).not.toHaveAttribute('open');
      expect(screen.getByTestId('quarters-input-p1')).toHaveValue('');
      sync.mockRestore();
    });

    test('betting interface should be present in scorekeeper', () => {
      const { container } = render(<SimpleScorekeeper {...defaultProps} />);

      // Should find the betting controls container
      const bettingControls = container.querySelector('[style*="display: flex"]');
      expect(bettingControls).toBeInTheDocument();
    });
  });
});
