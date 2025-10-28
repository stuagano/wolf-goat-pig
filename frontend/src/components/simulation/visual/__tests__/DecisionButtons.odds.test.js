// frontend/src/components/simulation/visual/__tests__/DecisionButtons.odds.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import DecisionButtons from '../DecisionButtons';
import ThemeProvider from '../../../../theme/Provider';

const renderWithTheme = (component) => {
  return render(<ThemeProvider>{component}</ThemeProvider>);
};

describe('DecisionButtons with Odds Hints', () => {
  const mockGameState = {
    players: [
      { id: 'p1', name: 'Alice' },
      { id: 'p2', name: 'Bob' },
      { id: 'p3', name: 'Charlie' }
    ]
  };

  describe('offer_double decision with odds', () => {
    test('shows probability badge for offer double button', () => {
      const props = {
        interactionNeeded: { type: 'offer_double' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            offer_double: 0.75,
            expected_value: 3.2,
            risk_level: 'low'
          }
        },
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      // Should show probability hint
      expect(screen.getByText(/75%/i)).toBeInTheDocument();
    });

    test('shows expected value hint for offer double', () => {
      const props = {
        interactionNeeded: { type: 'offer_double' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            offer_double: 0.65,
            expected_value: 2.5,
            risk_level: 'low'
          }
        },
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      expect(screen.getByText(/\+2.5/i)).toBeInTheDocument();
    });

    test('shows negative EV hint', () => {
      const props = {
        interactionNeeded: { type: 'offer_double' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            offer_double: 0.3,
            expected_value: -1.8,
            risk_level: 'high'
          }
        },
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      expect(screen.getByText(/-1.8/i)).toBeInTheDocument();
    });

    test('applies green border for favorable offer', () => {
      const props = {
        interactionNeeded: { type: 'offer_double' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            offer_double: 0.7,
            expected_value: 3.0,
            risk_level: 'low'
          }
        },
        onDecision: jest.fn()
      };

      const { container } = renderWithTheme(<DecisionButtons {...props} />);

      // Should have green border style indicating favorable odds
      const button = container.querySelector('[data-decision-type="offer-double"]');
      expect(button).toHaveStyle({ borderColor: expect.stringMatching(/#2e7d32|rgb\(46, 125, 50\)/) });
    });

    test('applies red border for unfavorable offer', () => {
      const props = {
        interactionNeeded: { type: 'offer_double' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            offer_double: 0.25,
            expected_value: -2.0,
            risk_level: 'high'
          }
        },
        onDecision: jest.fn()
      };

      const { container } = renderWithTheme(<DecisionButtons {...props} />);

      const button = container.querySelector('[data-decision-type="offer-double"]');
      expect(button).toHaveStyle({ borderColor: expect.stringMatching(/#d32f2f|rgb\(211, 47, 47\)/) });
    });

    test('does not show odds hints when betting_analysis missing', () => {
      const props = {
        interactionNeeded: { type: 'offer_double' },
        gameState: mockGameState,
        shotProbabilities: {},
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      // Buttons should still render without odds hints
      expect(screen.getByText(/Offer Double/i)).toBeInTheDocument();
      expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    });

    test('does not show odds hints when shotProbabilities missing', () => {
      const props = {
        interactionNeeded: { type: 'offer_double' },
        gameState: mockGameState,
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      expect(screen.getByText(/Offer Double/i)).toBeInTheDocument();
      expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    });
  });

  describe('double_offer decision (accept/decline) with odds', () => {
    test('shows probability badge for accept double button', () => {
      const props = {
        interactionNeeded: { type: 'double_offer' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            accept_double: 0.45,
            expected_value: 0.8,
            risk_level: 'medium'
          }
        },
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      expect(screen.getByText(/45%/i)).toBeInTheDocument();
    });

    test('shows expected value hint for accept double', () => {
      const props = {
        interactionNeeded: { type: 'double_offer' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            accept_double: 0.55,
            expected_value: 1.2,
            risk_level: 'medium'
          }
        },
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      expect(screen.getByText(/\+1.2/i)).toBeInTheDocument();
    });
  });

  describe('non-betting decisions', () => {
    test('does not show odds for partnership decisions', () => {
      const props = {
        interactionNeeded: {
          type: 'captain_chooses_partner',
          available_partners: ['p2', 'p3']
        },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            offer_double: 0.65,
            expected_value: 2.0
          }
        },
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      // Should not show odds hints on partnership buttons
      expect(screen.queryByText(/%/)).not.toBeInTheDocument();
      expect(screen.queryByText(/EV/i)).not.toBeInTheDocument();
    });

    test('does not show odds for partnership response', () => {
      const props = {
        interactionNeeded: { type: 'partnership_request' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            offer_double: 0.65,
            expected_value: 2.0
          }
        },
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    });
  });

  describe('odds display formats', () => {
    test('shows two decimal places for EV', () => {
      const props = {
        interactionNeeded: { type: 'offer_double' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            offer_double: 0.65,
            expected_value: 2.456,
            risk_level: 'low'
          }
        },
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      // Should show formatted EV
      expect(screen.getByText(/2\.5/i)).toBeInTheDocument();
    });

    test('shows rounded percentage', () => {
      const props = {
        interactionNeeded: { type: 'offer_double' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            offer_double: 0.678,
            expected_value: 1.5,
            risk_level: 'low'
          }
        },
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      expect(screen.getByText(/68%/i)).toBeInTheDocument();
    });
  });

  describe('existing functionality preserved', () => {
    test('buttons still clickable with odds displayed', () => {
      const mockOnDecision = jest.fn();
      const props = {
        interactionNeeded: { type: 'offer_double' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            offer_double: 0.65,
            expected_value: 2.0,
            risk_level: 'low'
          }
        },
        onDecision: mockOnDecision
      };

      renderWithTheme(<DecisionButtons {...props} />);

      const offerButton = screen.getByText(/Offer Double/i).closest('button');
      offerButton.click();

      expect(mockOnDecision).toHaveBeenCalledWith({ offer_double: true });
    });

    test('loading state disables buttons with odds', () => {
      const props = {
        interactionNeeded: { type: 'offer_double' },
        gameState: mockGameState,
        shotProbabilities: {
          betting_analysis: {
            offer_double: 0.65,
            expected_value: 2.0,
            risk_level: 'low'
          }
        },
        loading: true,
        onDecision: jest.fn()
      };

      renderWithTheme(<DecisionButtons {...props} />);

      const offerButton = screen.getByText(/Offer Double/i).closest('button');
      expect(offerButton).toBeDisabled();
    });
  });
});
