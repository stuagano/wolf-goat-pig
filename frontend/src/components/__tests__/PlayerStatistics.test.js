// frontend/src/components/__tests__/PlayerStatistics.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PlayerStatistics from '../PlayerStatistics';

// Mock the Card component
jest.mock('../ui', () => ({
  Card: ({ children, className }) => (
    <div className={className} data-testid="card">{children}</div>
  )
}));

// Mock fetch
global.fetch = jest.fn();

describe('PlayerStatistics', () => {
  const mockStatistics = {
    games_played: 25,
    games_won: 10,
    total_earnings: 250.50,
    avg_earnings_per_hole: 2.78,
    holes_played: 450,
    holes_won: 120,
    betting_success_rate: 0.65,
    successful_bets: 130,
    total_bets: 200,
    partnership_success_rate: 0.60,
    partnerships_won: 15,
    partnerships_formed: 25,
    solo_attempts: 10,
    solo_wins: 3,
    current_win_streak: 2,
    best_win_streak: 5,
    current_loss_streak: 0,
    worst_loss_streak: 3,
    times_as_wolf: 50,
    times_as_goat: 40,
    times_as_pig: 35,
    times_as_aardvark: 25,
    eagles: 5,
    birdies: 45,
    pars: 180,
    bogeys: 150,
    double_bogeys: 50,
    worse_than_double: 20,
    ping_pong_count: 8,
    ping_pong_wins: 5,
    invisible_aardvark_appearances: 3,
    invisible_aardvark_wins: 2,
    duncan_attempts: 4,
    duncan_wins: 2,
    tunkarri_attempts: 2,
    tunkarri_wins: 1,
    big_dick_attempts: 3,
    big_dick_wins: 1
  };

  const mockAnalytics = {
    performance_summary: {
      win_rate: 40,
      avg_earnings: 10.02,
      avg_position: 2.1,
      recent_form: 'Good'
    },
    strength_analysis: {
      betting: 'Strong',
      partnership: 'Average',
      solo_play: 'Weak'
    },
    comparative_analysis: {
      ranking_summary: 'Top 30%',
      earnings_percentile: 72,
      win_rate_percentile: 68
    },
    improvement_recommendations: [
      'Focus on improving solo play success rate',
      'Consider more conservative betting on difficult holes',
      'Partnerships are strong - leverage this advantage'
    ],
    trend_analysis: {
      status: 'sufficient_data',
      earnings_trend: 'improving',
      position_trend: 'stable',
      games_analyzed: 10,
      volatility: 'Medium'
    }
  };

  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockImplementation((url) => {
      if (url.includes('/statistics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockStatistics)
        });
      }
      if (url.includes('/analytics')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockAnalytics)
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });
  });

  describe('Loading State', () => {
    test('shows loading spinner when loading', () => {
      render(<PlayerStatistics playerId={1} />);
      expect(screen.getByText('Loading player statistics...')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    test('shows error message when API fails', async () => {
      fetch.mockRejectedValue(new Error('Network error'));

      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Error Loading Statistics')).toBeInTheDocument();
      });
    });

    test('shows retry button on error', async () => {
      fetch.mockRejectedValue(new Error('Network error'));

      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Retry')).toBeInTheDocument();
      });
    });

    test('retries loading when retry button clicked', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Retry')).toBeInTheDocument();
      });

      fetch.mockImplementation((url) => {
        if (url.includes('/statistics')) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(mockStatistics) });
        }
        if (url.includes('/analytics')) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAnalytics) });
        }
        return Promise.reject(new Error('Unknown'));
      });

      fireEvent.click(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('Player Statistics')).toBeInTheDocument();
      });
    });
  });

  describe('No Data State', () => {
    test('shows no statistics message when data is null', async () => {
      fetch.mockImplementation((url) => {
        if (url.includes('/statistics')) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(null) });
        }
        if (url.includes('/analytics')) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(null) });
        }
        return Promise.reject(new Error('Unknown'));
      });

      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('No statistics available for this player.')).toBeInTheDocument();
      });
    });
  });

  describe('Overview Tab', () => {
    test('shows player name in header when provided', async () => {
      render(<PlayerStatistics playerId={1} playerName="John Doe" />);

      await waitFor(() => {
        expect(screen.getByText("John Doe's Statistics")).toBeInTheDocument();
      });
    });

    test('shows generic header when no player name', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Player Statistics')).toBeInTheDocument();
      });
    });

    test('displays games played stat', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Games Played')).toBeInTheDocument();
        expect(screen.getByText('25')).toBeInTheDocument();
      });
    });

    test('displays win rate', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Win Rate')).toBeInTheDocument();
        expect(screen.getByText('40.0%')).toBeInTheDocument();
      });
    });

    test('displays total earnings', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Total Earnings')).toBeInTheDocument();
        expect(screen.getByText('+$250.50')).toBeInTheDocument();
      });
    });

    test('displays holes won', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Holes Won')).toBeInTheDocument();
        expect(screen.getByText('120/450')).toBeInTheDocument();
      });
    });

    test('displays betting performance section', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Betting Performance')).toBeInTheDocument();
        expect(screen.getByText('Betting Success Rate')).toBeInTheDocument();
        expect(screen.getByText('65.0%')).toBeInTheDocument();
      });
    });

    test('displays partnership performance section', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Partnership Performance')).toBeInTheDocument();
        expect(screen.getByText('Partnership Success Rate')).toBeInTheDocument();
        expect(screen.getByText('60.0%')).toBeInTheDocument();
      });
    });

    test('displays solo play performance section', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Solo Play Performance')).toBeInTheDocument();
        expect(screen.getByText('Solo Attempts')).toBeInTheDocument();
        expect(screen.getByText('10')).toBeInTheDocument();
        expect(screen.getByText('Solo Wins')).toBeInTheDocument();
        expect(screen.getByText('3')).toBeInTheDocument();
      });
    });

    test('displays streak tracking', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Streaks & Form')).toBeInTheDocument();
        expect(screen.getByText('Current Win Streak')).toBeInTheDocument();
        expect(screen.getByText('2')).toBeInTheDocument();
        expect(screen.getByText('Best Win Streak')).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
      });
    });

    test('displays role distribution', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Role Distribution')).toBeInTheDocument();
        expect(screen.getByText('Wolf')).toBeInTheDocument();
        expect(screen.getByText('Goat')).toBeInTheDocument();
        expect(screen.getByText('Pig')).toBeInTheDocument();
        expect(screen.getByText('Aardvark')).toBeInTheDocument();
      });
    });

    test('displays score performance', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Score Performance')).toBeInTheDocument();
        expect(screen.getByText('Eagles')).toBeInTheDocument();
        expect(screen.getByText('Birdies')).toBeInTheDocument();
        expect(screen.getByText('Pars')).toBeInTheDocument();
        expect(screen.getByText('Bogeys')).toBeInTheDocument();
      });
    });

    test('displays special events', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Special Events')).toBeInTheDocument();
        expect(screen.getByText('Ping Pong')).toBeInTheDocument();
        expect(screen.getByText('Invisible Aardvark')).toBeInTheDocument();
        expect(screen.getByText('The Duncan')).toBeInTheDocument();
        expect(screen.getByText('The Tunkarri')).toBeInTheDocument();
        expect(screen.getByText('Big Dick')).toBeInTheDocument();
      });
    });
  });

  describe('Tab Navigation', () => {
    test('shows three tab buttons', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('Performance')).toBeInTheDocument();
        expect(screen.getByText('Insights')).toBeInTheDocument();
      });
    });

    test('overview tab is active by default', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        const overviewButton = screen.getByText('Overview');
        expect(overviewButton).toHaveClass('bg-blue-600');
      });
    });

    test('switches to performance tab when clicked', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Performance'));

      expect(screen.getByText('Performance Summary')).toBeInTheDocument();
    });

    test('switches to insights tab when clicked', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Insights'));

      expect(screen.getByText('Improvement Recommendations')).toBeInTheDocument();
    });
  });

  describe('Performance Tab', () => {
    test('displays performance summary', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Performance'));
      });

      expect(screen.getByText('Performance Summary')).toBeInTheDocument();
      expect(screen.getByText('40%')).toBeInTheDocument(); // Win Rate
      expect(screen.getByText('$10.02')).toBeInTheDocument(); // Avg. Earnings
    });

    test('displays strength analysis', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Performance'));
      });

      expect(screen.getByText('Strength Analysis')).toBeInTheDocument();
      expect(screen.getByText('Strong')).toBeInTheDocument();
      expect(screen.getByText('Average')).toBeInTheDocument();
      expect(screen.getByText('Weak')).toBeInTheDocument();
    });

    test('displays comparative ranking', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Performance'));
      });

      expect(screen.getByText('Comparative Ranking')).toBeInTheDocument();
      expect(screen.getByText('Top 30%')).toBeInTheDocument();
    });
  });

  describe('Insights Tab', () => {
    test('displays improvement recommendations', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Insights'));
      });

      expect(screen.getByText('Improvement Recommendations')).toBeInTheDocument();
      expect(screen.getByText('Focus on improving solo play success rate')).toBeInTheDocument();
    });

    test('displays trend analysis', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Insights'));
      });

      expect(screen.getByText('Recent Trends')).toBeInTheDocument();
      expect(screen.getByText('Earnings Trend')).toBeInTheDocument();
      expect(screen.getByText('improving')).toBeInTheDocument();
    });

    test('displays achievements placeholder', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        fireEvent.click(screen.getByText('Insights'));
      });

      expect(screen.getByText('Recent Achievements')).toBeInTheDocument();
      expect(screen.getByText('Achievement system coming soon!')).toBeInTheDocument();
    });
  });

  describe('Data Formatting', () => {
    test('formats positive earnings correctly', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('+$250.50')).toBeInTheDocument();
      });
    });

    test('formats negative earnings correctly', async () => {
      fetch.mockImplementation((url) => {
        if (url.includes('/statistics')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ ...mockStatistics, total_earnings: -100.25 })
          });
        }
        if (url.includes('/analytics')) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAnalytics) });
        }
        return Promise.reject(new Error('Unknown'));
      });

      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('-$100.25')).toBeInTheDocument();
      });
    });

    test('formats percentages correctly', async () => {
      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        // Win rate: 10/25 = 40%
        expect(screen.getByText('40.0%')).toBeInTheDocument();
        // Betting: 65%
        expect(screen.getByText('65.0%')).toBeInTheDocument();
      });
    });
  });

  describe('Player ID Changes', () => {
    test('refetches data when playerId changes', async () => {
      const { rerender } = render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('Player Statistics')).toBeInTheDocument();
      });

      expect(fetch).toHaveBeenCalledTimes(2);

      rerender(<PlayerStatistics playerId={2} />);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(4);
      });
    });
  });

  describe('Empty/Zero Values', () => {
    test('handles zero games gracefully', async () => {
      fetch.mockImplementation((url) => {
        if (url.includes('/statistics')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              ...mockStatistics,
              games_played: 0,
              games_won: 0,
              holes_played: 0,
              holes_won: 0
            })
          });
        }
        if (url.includes('/analytics')) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAnalytics) });
        }
        return Promise.reject(new Error('Unknown'));
      });

      render(<PlayerStatistics playerId={1} />);

      await waitFor(() => {
        expect(screen.getByText('0')).toBeInTheDocument(); // games_played
        expect(screen.getByText('0.0%')).toBeInTheDocument(); // win rate
      });
    });
  });
});
