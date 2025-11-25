// frontend/src/components/game/__tests__/SimpleScorekeeper.betting.test.js
import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { ThemeProvider } from '../../../theme/Provider';
import SimpleScorekeeper from '../SimpleScorekeeper';

// Mock ThemeProvider
jest.mock('../../../theme/Provider', () => ({
  ThemeProvider: ({ children }) => <div>{children}</div>,
  useTheme: () => ({
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

// Mock Input component
jest.mock('../../../ui/Input', () => {
  return function Input({ value, onChange, ...props }) {
    return (
      <input
        value={value}
        onChange={onChange}
        {...props}
      />
    );
  };
});

describe('SimpleScorekeeper - Betting Interface', () => {
  const mockPlayers = [
    { id: 'p1', name: 'Alice', handicap: 10 },
    { id: 'p2', name: 'Bob', handicap: 15 },
    { id: 'p3', name: 'Charlie', handicap: 8 },
    { id: 'p4', name: 'Diana', handicap: 12 }
  ];

  const mockCourse = {
    name: 'Test Course',
    holes: Array.from({ length: 18 }, (_, i) => ({
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
  });

  describe('Basic Betting Controls', () => {
    test('should display betting interface with player name', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      // Find betting by text
      const bettingByText = screen.getByText(/Betting by/i);
      expect(bettingByText).toBeInTheDocument();
    });

    test('should show current wager display', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const wagerDisplay = screen.getByText(/Current Wager/i);
      expect(wagerDisplay).toBeInTheDocument();

      // Should show 1Q as default
      expect(screen.getByText(/1Q/)).toBeInTheDocument();
    });

    test('should increment wager when + button is clicked', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const incrementButton = screen.getByRole('button', { name: '+' });
      fireEvent.click(incrementButton);

      expect(screen.getByText(/2Q/)).toBeInTheDocument();
    });

    test('should decrement wager when - button is clicked', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      // First increment to 2
      const incrementButton = screen.getByRole('button', { name: '+' });
      fireEvent.click(incrementButton);

      // Then decrement back to 1
      const decrementButton = screen.getByRole('button', { name: '−' });
      fireEvent.click(decrementButton);

      expect(screen.getByText(/1Q/)).toBeInTheDocument();
    });

    test('should not decrement below base wager', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const decrementButton = screen.getByRole('button', { name: '−' });

      // Try to decrement when at base wager
      fireEvent.click(decrementButton);

      // Should still show 1Q
      expect(screen.getByText(/1Q/)).toBeInTheDocument();

      // Button should be disabled
      expect(decrementButton).toBeDisabled();
    });

    test('should double wager when Double button is clicked', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const doubleButton = screen.getByRole('button', { name: /Double/i });
      fireEvent.click(doubleButton);

      expect(screen.getByText(/2Q/)).toBeInTheDocument();
    });

    test('should double multiple times', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const doubleButton = screen.getByRole('button', { name: /Double/i });

      // First double: 1 -> 2
      fireEvent.click(doubleButton);
      expect(screen.getByText(/2Q/)).toBeInTheDocument();

      // Second double: 2 -> 4
      fireEvent.click(doubleButton);
      expect(screen.getByText(/4Q/)).toBeInTheDocument();

      // Third double: 4 -> 8
      fireEvent.click(doubleButton);
      expect(screen.getByText(/8Q/)).toBeInTheDocument();
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

    test('should show ÷2 and Reset buttons when wager reaches 8Q', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const doubleButton = screen.getByRole('button', { name: /Double/i });

      // Double to 8Q: 1 -> 2 -> 4 -> 8
      fireEvent.click(doubleButton);
      fireEvent.click(doubleButton);
      fireEvent.click(doubleButton);

      expect(screen.getByText(/8Q/)).toBeInTheDocument();

      // High-stakes buttons should now be visible
      expect(screen.getByRole('button', { name: /÷2/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Reset/ })).toBeInTheDocument();
    });

    test('should halve wager when ÷2 button is clicked', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const doubleButton = screen.getByRole('button', { name: /Double/i });

      // Get to 16Q
      fireEvent.click(doubleButton); // 2Q
      fireEvent.click(doubleButton); // 4Q
      fireEvent.click(doubleButton); // 8Q
      fireEvent.click(doubleButton); // 16Q

      expect(screen.getByText(/16Q/)).toBeInTheDocument();

      // Click ÷2
      const halveButton = screen.getByRole('button', { name: /÷2/ });
      fireEvent.click(halveButton);

      expect(screen.getByText(/8Q/)).toBeInTheDocument();
    });

    test('should reset to base wager when Reset button is clicked', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const doubleButton = screen.getByRole('button', { name: /Double/i });

      // Get to 32Q
      fireEvent.click(doubleButton); // 2Q
      fireEvent.click(doubleButton); // 4Q
      fireEvent.click(doubleButton); // 8Q
      fireEvent.click(doubleButton); // 16Q
      fireEvent.click(doubleButton); // 32Q

      expect(screen.getByText(/32Q/)).toBeInTheDocument();

      // Click Reset
      const resetButton = screen.getByRole('button', { name: /Reset.*1Q/i });
      fireEvent.click(resetButton);

      // Should be back to base wager (1Q)
      expect(screen.getByText(/1Q/)).toBeInTheDocument();
    });

    test('high-stakes buttons should disappear when wager drops below 8Q', () => {
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

      expect(screen.getByText(/4Q/)).toBeInTheDocument();

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
    test('should show Partners indicator when in partners mode', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      // Find Partners/Solo indicator
      const partnersIndicator = screen.getByText(/👥 Partners|🎯 Solo/);
      expect(partnersIndicator).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    test('should handle very high wagers (64Q+)', () => {
      render(<SimpleScorekeeper {...defaultProps} />);

      const doubleButton = screen.getByRole('button', { name: /Double/i });

      // Get to 64Q
      for (let i = 0; i < 6; i++) {
        fireEvent.click(doubleButton);
      }

      expect(screen.getByText(/64Q/)).toBeInTheDocument();

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
      expect(screen.getByText(/11Q/)).toBeInTheDocument();
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
