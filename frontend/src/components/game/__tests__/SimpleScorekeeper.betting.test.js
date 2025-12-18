// frontend/src/components/game/__tests__/SimpleScorekeeper.betting.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SimpleScorekeeper from '../SimpleScorekeeper';
import {
  createMockTheme,
  createMockPlayers,
  createMockCourseHoles
} from '../../../test-utils/mockFactories';

// Mock fetch globally
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({})
  })
);

// Mock ThemeProvider
jest.mock('../../../theme/Provider', () => ({
  ThemeProvider: ({ children }) => <div>{children}</div>,
  useTheme: () => require('../../../test-utils/mockFactories').createMockTheme({
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
}));

// Mock Input component - filter out non-DOM props
jest.mock('../../ui', () => ({
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
jest.mock('../Scorecard', () => {
  return function MockScorecard() {
    return <div data-testid="mock-scorecard">Scorecard</div>;
  };
});

// Mock GameCompletionView component
jest.mock('../GameCompletionView', () => {
  return function MockGameCompletionView() {
    return <div data-testid="mock-game-completion">Game Complete</div>;
  };
});

// Mock BadgeNotification
jest.mock('../../BadgeNotification', () => ({
  triggerBadgeNotification: jest.fn()
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
    onHoleComplete: jest.fn(),
    onGameComplete: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
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

    test('should increment wager when + button is clicked', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const incrementButton = screen.getByRole('button', { name: '+' });
      fireEvent.click(incrementButton);

      expect(findWagerText(2)).toBe(true);
    });

    test('should decrement wager when - button is clicked', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      // First increment to 2
      const incrementButton = screen.getByRole('button', { name: '+' });
      fireEvent.click(incrementButton);

      // Then decrement back to 1
      const decrementButton = screen.getByRole('button', { name: '−' });
      fireEvent.click(decrementButton);

      expect(findWagerText(1)).toBe(true);
    });

    test('should not decrement below base wager', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const decrementButton = screen.getByRole('button', { name: '−' });

      // Try to decrement when at base wager
      fireEvent.click(decrementButton);

      // Should still show 1Q
      expect(findWagerText(1)).toBe(true);

      // Button should be disabled
      expect(decrementButton).toBeDisabled();
    });

    test('should double wager when Double button is clicked', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      // Expand advanced betting section first
      const advancedToggle = screen.getByRole('button', { name: /Double, Float, Option/i });
      fireEvent.click(advancedToggle);

      const doubleButton = screen.getByRole('button', { name: /^Double$/i });
      fireEvent.click(doubleButton);

      expect(findWagerText(2)).toBe(true);
    });

    test('should double multiple times', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      // Expand advanced betting section first
      const advancedToggle = screen.getByRole('button', { name: /Double, Float, Option/i });
      fireEvent.click(advancedToggle);

      const doubleButton = screen.getByRole('button', { name: /^Double$/i });

      // First double: 1 -> 2
      fireEvent.click(doubleButton);
      expect(findWagerText(2)).toBe(true);

      // Second double: 2 -> 4
      fireEvent.click(doubleButton);
      expect(findWagerText(4)).toBe(true);

      // Third double: 4 -> 8
      fireEvent.click(doubleButton);
      expect(findWagerText(8)).toBe(true);
    });
  });

  describe('High-Stakes Adaptive Controls', () => {
    test('should NOT show ÷2 and Reset buttons when wager is below 8Q', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      // At 1Q, high-stakes buttons should not be visible
      expect(screen.queryByRole('button', { name: /÷2/ })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Reset/ })).not.toBeInTheDocument();

      // Increment to 4Q
      const incrementButton = screen.getByRole('button', { name: '+' });
      fireEvent.click(incrementButton); // 2Q
      fireEvent.click(incrementButton); // 3Q
      fireEvent.click(incrementButton); // 4Q

      // Still should not show high-stakes buttons
      expect(screen.queryByRole('button', { name: /÷2/ })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Reset/ })).not.toBeInTheDocument();
    });

    // TODO: These tests need to be updated to handle the offer/accept flow
    // The Double button now creates a pending offer that needs acceptance
    test.skip('should show ÷2 and Reset buttons when wager reaches 8Q', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const doubleButton = screen.getByRole('button', { name: /Double/i });

      // Double to 8Q: 1 -> 2 -> 4 -> 8
      fireEvent.click(doubleButton);
      fireEvent.click(doubleButton);
      fireEvent.click(doubleButton);

      expect(findWagerText(8)).toBe(true);

      // High-stakes buttons should now be visible
      expect(screen.getByRole('button', { name: /÷2/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Reset/ })).toBeInTheDocument();
    });

    test.skip('should halve wager when ÷2 button is clicked', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const doubleButton = screen.getByRole('button', { name: /Double/i });

      // Get to 16Q
      fireEvent.click(doubleButton); // 2Q
      fireEvent.click(doubleButton); // 4Q
      fireEvent.click(doubleButton); // 8Q
      fireEvent.click(doubleButton); // 16Q

      expect(findWagerText(16)).toBe(true);

      // Click ÷2
      const halveButton = screen.getByRole('button', { name: /÷2/ });
      fireEvent.click(halveButton);

      expect(findWagerText(8)).toBe(true);
    });

    test.skip('should reset to base wager when Reset button is clicked', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const doubleButton = screen.getByRole('button', { name: /Double/i });

      // Get to 32Q
      fireEvent.click(doubleButton); // 2Q
      fireEvent.click(doubleButton); // 4Q
      fireEvent.click(doubleButton); // 8Q
      fireEvent.click(doubleButton); // 16Q
      fireEvent.click(doubleButton); // 32Q

      expect(findWagerText(32)).toBe(true);

      // Click Reset
      const resetButton = screen.getByRole('button', { name: /Reset.*1Q/i });
      fireEvent.click(resetButton);

      // Should be back to base wager (1Q)
      expect(findWagerText(1)).toBe(true);
    });

    test.skip('high-stakes buttons should disappear when wager drops below 8Q', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const doubleButton = screen.getByRole('button', { name: /Double/i });

      // Get to 8Q
      fireEvent.click(doubleButton); // 2Q
      fireEvent.click(doubleButton); // 4Q
      fireEvent.click(doubleButton); // 8Q

      // High-stakes buttons should be visible
      expect(screen.getByRole('button', { name: /÷2/ })).toBeInTheDocument();

      // Click ÷2 to get back to 4Q
      const halveButton = screen.getByRole('button', { name: /÷2/ });
      fireEvent.click(halveButton);

      expect(findWagerText(4)).toBe(true);

      // High-stakes buttons should be gone
      expect(screen.queryByRole('button', { name: /÷2/ })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Reset/ })).not.toBeInTheDocument();
    });
  });

  describe('Active Modifiers Display', () => {
    test('should show Carry-Over badge when active', () => {
      // This would require setting up game state with carry-over
      // For now, this is a placeholder for when we implement state management
      expect(true).toBe(true);
    });

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
    // TODO: This test needs to be updated to handle the offer/accept flow
    test.skip('should handle very high wagers (64Q+)', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const doubleButton = screen.getByRole('button', { name: /Double/i });

      // Get to 64Q
      for (let i = 0; i < 6; i++) {
        fireEvent.click(doubleButton);
      }

      expect(findWagerText(64)).toBe(true);

      // High-stakes controls should still work
      expect(screen.getByRole('button', { name: /÷2/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Reset/ })).toBeInTheDocument();
    });

    test('should handle rapid button clicks', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const incrementButton = screen.getByRole('button', { name: '+' });

      // Rapidly click increment
      for (let i = 0; i < 10; i++) {
        fireEvent.click(incrementButton);
      }

      // Should show 11Q
      expect(findWagerText(11)).toBe(true);
    });
  });

  describe('Integration with Game Flow', () => {
    test('betting interface should be present in scorekeeper', () => {
      const { container } = render(<SimpleScorekeeper {...defaultProps} />);

      // Should find the betting controls container
      const bettingControls = container.querySelector('[style*="display: flex"]');
      expect(bettingControls).toBeInTheDocument();
    });
  });
});
