// frontend/src/components/simulation/visual/__tests__/BettingCard.odds.test.js
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import BettingCard from '../BettingCard';
import ThemeProvider from '../../../../theme/Provider';

const renderWithTheme = (component) => {
  return render(<ThemeProvider>{component}</ThemeProvider>);
};

describe('BettingCard with Betting Odds', () => {
  const mockBetting = { current_wager: 20, doubled: false };
  const mockBaseWager = 10;

  test('renders odds section when betting_analysis present', () => {
    const props = {
      betting: mockBetting,
      baseWager: mockBaseWager,
      shotProbabilities: {
        betting_analysis: {
          offer_double: 0.65,
          expected_value: 2.3,
          risk_level: 'medium',
          reasoning: 'You are ahead'
        }
      }
    };

    renderWithTheme(<BettingCard {...props} />);

    expect(screen.getByText(/Betting Odds/i)).toBeInTheDocument();
    expect(screen.getByText(/Double Likely/i)).toBeInTheDocument();
    expect(screen.getByText(/65%/i)).toBeInTheDocument();
    expect(screen.getByText(/\+2.3 pts/i)).toBeInTheDocument();
  });

  test('shows expected value with correct sign', () => {
    const props = {
      betting: mockBetting,
      baseWager: mockBaseWager,
      shotProbabilities: {
        betting_analysis: {
          offer_double: 0.5,
          expected_value: -1.8,
          risk_level: 'high'
        }
      }
    };

    renderWithTheme(<BettingCard {...props} />);

    expect(screen.getByText(/-1.8 pts/i)).toBeInTheDocument();
  });

  test('shows risk level with appropriate styling', () => {
    const props = {
      betting: mockBetting,
      baseWager: mockBaseWager,
      shotProbabilities: {
        betting_analysis: {
          offer_double: 0.3,
          expected_value: -0.5,
          risk_level: 'high'
        }
      }
    };

    renderWithTheme(<BettingCard {...props} />);

    expect(screen.getByText(/Risk:/i)).toBeInTheDocument();
    expect(screen.getByText(/High/i)).toBeInTheDocument();
  });

  test('shows reasoning text when provided', () => {
    const props = {
      betting: mockBetting,
      baseWager: mockBaseWager,
      shotProbabilities: {
        betting_analysis: {
          offer_double: 0.7,
          expected_value: 3.5,
          risk_level: 'low',
          reasoning: 'Opponent is under pressure'
        }
      }
    };

    renderWithTheme(<BettingCard {...props} />);

    expect(screen.getByText(/Opponent is under pressure/i)).toBeInTheDocument();
  });

  test('renders error state when odds unavailable', () => {
    const props = {
      betting: mockBetting,
      baseWager: mockBaseWager,
      shotProbabilities: {
        betting_analysis: { error: 'unavailable' }
      }
    };

    renderWithTheme(<BettingCard {...props} />);

    expect(screen.getByText(/Odds temporarily unavailable/i)).toBeInTheDocument();
  });

  test('does not render odds section when betting_analysis missing', () => {
    const props = {
      betting: mockBetting,
      baseWager: mockBaseWager,
      shotProbabilities: {}
    };

    renderWithTheme(<BettingCard {...props} />);

    expect(screen.queryByText(/Betting Odds/i)).not.toBeInTheDocument();
  });

  test('does not render odds section when shotProbabilities missing', () => {
    const props = {
      betting: mockBetting,
      baseWager: mockBaseWager
    };

    renderWithTheme(<BettingCard {...props} />);

    expect(screen.queryByText(/Betting Odds/i)).not.toBeInTheDocument();
  });

  test('renders educational tooltip', () => {
    const props = {
      betting: mockBetting,
      baseWager: mockBaseWager,
      shotProbabilities: {
        betting_analysis: {
          offer_double: 0.65,
          expected_value: 2.3,
          risk_level: 'medium'
        }
      }
    };

    renderWithTheme(<BettingCard {...props} />);

    // Tooltip button should be present
    const tooltipButton = screen.getByRole('button', { name: /betting odds/i });
    expect(tooltipButton).toBeInTheDocument();
  });

  test('shows correct probability label for high probability', () => {
    const props = {
      betting: mockBetting,
      baseWager: mockBaseWager,
      shotProbabilities: {
        betting_analysis: {
          offer_double: 0.75,
          expected_value: 2.0,
          risk_level: 'low'
        }
      }
    };

    renderWithTheme(<BettingCard {...props} />);

    expect(screen.getByText(/Double Likely/i)).toBeInTheDocument();
  });

  test('shows correct probability label for medium probability', () => {
    const props = {
      betting: mockBetting,
      baseWager: mockBaseWager,
      shotProbabilities: {
        betting_analysis: {
          offer_double: 0.5,
          expected_value: 0.5,
          risk_level: 'medium'
        }
      }
    };

    renderWithTheme(<BettingCard {...props} />);

    expect(screen.getByText(/Double Possible/i)).toBeInTheDocument();
  });

  test('shows correct probability label for low probability', () => {
    const props = {
      betting: mockBetting,
      baseWager: mockBaseWager,
      shotProbabilities: {
        betting_analysis: {
          offer_double: 0.2,
          expected_value: -1.0,
          risk_level: 'high'
        }
      }
    };

    renderWithTheme(<BettingCard {...props} />);

    expect(screen.getByText(/Double Unlikely/i)).toBeInTheDocument();
  });

  test('existing betting information still displays correctly', () => {
    const props = {
      betting: { current_wager: 30, doubled: true },
      baseWager: 15,
      pokerState: { pot_size: 120, betting_phase: 'Post-tee' },
      shotProbabilities: {
        betting_analysis: {
          offer_double: 0.65,
          expected_value: 2.3,
          risk_level: 'medium'
        }
      }
    };

    renderWithTheme(<BettingCard {...props} />);

    // Existing info should still be there
    expect(screen.getByText('$30')).toBeInTheDocument();
    expect(screen.getByText('2x')).toBeInTheDocument();
    expect(screen.getByText(/Base: \$15/i)).toBeInTheDocument();
    expect(screen.getByText(/Pot:/i)).toBeInTheDocument();
    expect(screen.getByText('$120')).toBeInTheDocument();
    expect(screen.getByText(/Post-tee/i)).toBeInTheDocument();

    // New odds info should also be there
    expect(screen.getByText(/Betting Odds/i)).toBeInTheDocument();
  });
});
