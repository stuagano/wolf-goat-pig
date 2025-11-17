/**
 * WGPAnalyticsDashboard Component Tests
 * Tests the analytics dashboard functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import WGPAnalyticsDashboard from '../WGPAnalyticsDashboard';
import { ThemeProvider } from '../theme/Provider';
import { AuthProvider } from '../context/AuthContext';

// Mock API calls
global.fetch = jest.fn();

// Mock Auth0
jest.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    isAuthenticated: true,
    user: { name: 'Test User', email: 'test@example.com' },
    isLoading: false,
    getAccessTokenSilently: jest.fn(() => Promise.resolve('test-token')),
  }),
}));

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider>
      <AuthProvider>
        {children}
      </AuthProvider>
    </ThemeProvider>
  </BrowserRouter>
);

const mockAnalyticsData = {
  player_stats: {
    'Player 1': { games_played: 10, points: 45, win_rate: 0.6 },
    'Player 2': { games_played: 8, points: -12, win_rate: 0.4 }
  },
  game_stats: {
    total_games: 25,
    average_score: 2.1,
    most_common_outcome: 'Wolf wins'
  },
  trends: {
    monthly_games: [5, 8, 12, 15],
    popular_holes: [1, 9, 18]
  }
};

describe.skip('WGPAnalyticsDashboard', () => {
  beforeEach(() => {
    fetch.mockClear();
    fetch.mockResolvedValue({
      ok: true,
      json: async () => mockAnalyticsData,
    });
  });

  test('renders analytics dashboard with main heading', () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    expect(screen.getByRole('heading', { name: /analytics.*dashboard/i })).toBeInTheDocument();
  });

  test('displays player statistics section', async () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/player.*stats/i)).toBeInTheDocument();
    });
  });

  test('shows game statistics overview', async () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/total.*games/i)).toBeInTheDocument();
      expect(screen.getByText(/25/)).toBeInTheDocument();
    });
  });

  test('displays performance metrics', async () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/win.*rate/i)).toBeInTheDocument();
      expect(screen.getByText(/points/i)).toBeInTheDocument();
    });
  });

  test('shows trend analysis charts', async () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/trends/i) || screen.getByText(/chart/i)).toBeInTheDocument();
    });
  });

  test('displays player comparison tables', async () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Player 1')).toBeInTheDocument();
      expect(screen.getByText('Player 2')).toBeInTheDocument();
    });
  });

  test('shows filtering options', () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    // Should have date range or filter controls
    expect(screen.getByText(/filter/i) || screen.getByText(/date/i) || screen.getByRole('combobox')).toBeInTheDocument();
  });

  test('handles date range selection', () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    const dateInput = screen.getByLabelText(/date/i) || screen.getByRole('textbox');
    fireEvent.change(dateInput, { target: { value: '2024-01-01' } });

    expect(dateInput.value).toBe('2024-01-01');
  });

  test('displays export functionality', () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    // Should have export options
    expect(screen.getByText(/export/i) || screen.getByText(/download/i)).toBeInTheDocument();
  });

  test('shows performance breakdown by role', async () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/wolf/i) || screen.getByText(/goat/i) || screen.getByText(/pig/i)).toBeInTheDocument();
    });
  });

  test('displays hole-by-hole analysis', async () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/hole.*analysis/i) || screen.getByText(/popular.*holes/i)).toBeInTheDocument();
    });
  });

  test('shows betting pattern analysis', async () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/betting/i) || screen.getByText(/wager/i)).toBeInTheDocument();
    });
  });

  test('handles analytics API failures', async () => {
    fetch.mockRejectedValueOnce(new Error('Analytics API failed'));

    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/error/i) || screen.getByText(/failed.*load/i)).toBeInTheDocument();
    });
  });

  test('displays loading state while fetching data', () => {
    fetch.mockImplementationOnce(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    expect(screen.getByText(/loading/i) || screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('shows refreshable data with refresh button', () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    expect(refreshButton).toBeInTheDocument();

    fireEvent.click(refreshButton);
    expect(fetch).toHaveBeenCalledTimes(2); // Initial load + refresh
  });

  test('displays time period selection', () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    // Should have period selection (last 30 days, 3 months, etc.)
    expect(screen.getByText(/30.*days/i) || screen.getByText(/month/i) || screen.getByText(/year/i)).toBeInTheDocument();
  });

  test('shows individual player drill-down', async () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      const playerName = screen.getByText('Player 1');
      fireEvent.click(playerName);
      
      // Should show detailed player stats
      expect(screen.getByText(/games.*played/i)).toBeInTheDocument();
    });
  });

  test('displays comparative analysis features', async () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/compare/i) || screen.getByText(/vs/i)).toBeInTheDocument();
    });
  });

  test('shows statistical significance indicators', async () => {
    render(
      <TestWrapper>
        <WGPAnalyticsDashboard />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/confidence/i) || screen.getByText(/significant/i) || screen.getByText(/±/)).toBeInTheDocument();
    });
  });

  test('renders without crashing', () => {
    expect(() => {
      render(
        <TestWrapper>
          <WGPAnalyticsDashboard />
        </TestWrapper>
      );
    }).not.toThrow();
  });
});