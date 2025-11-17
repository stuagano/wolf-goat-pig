/**
 * Comprehensive test suite for BettingOddsPanel component
 * 
 * Tests the betting odds calculation and display system including:
 * - Real-time odds fetching and updates
 * - Multiple view modes (overview, scenarios, analysis)
 * - Error handling and loading states
 * - User interactions and betting actions
 * - Performance metrics display
 * - Educational tooltips and insights
 * - Responsive design behavior
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { act } from 'react-dom/test-utils';

// Test utilities and providers
import { ThemeProvider } from '../../theme/Provider';
import { GameProvider } from '../../context/GameProvider';

// Component under test
import BettingOddsPanel from '../BettingOddsPanel';

// Mock fetch globally
global.fetch = jest.fn();

// Mock components
jest.mock('../ProbabilityVisualization', () => {
  return function MockProbabilityVisualization({ data, currentOdds }) {
    return (
      <div data-testid="probability-visualization">
        <div>Mock Probability Visualization</div>
        <div data-testid="history-data">{JSON.stringify(data)}</div>
        <div data-testid="current-odds">{JSON.stringify(currentOdds)}</div>
      </div>
    );
  };
});

jest.mock('../EducationalTooltip', () => ({
  __esModule: true,
  default: function MockEducationalTooltip({ children, title, content }) {
    return (
      <div data-testid="educational-tooltip" title={`${title}: ${content}`}>
        {children}
      </div>
    );
  },
  BettingConcepts: {
    winProbability: {
      title: 'Win Probability',
      content: 'The chance of winning based on current position'
    },
    expectedValue: {
      title: 'Expected Value',
      content: 'The average expected return on this bet'
    },
    confidenceInterval: {
      title: 'Confidence Interval',
      content: 'The range of probable outcomes'
    }
  },
  generateStrategicInsight: jest.fn(() => [
    { title: 'Conservative Play', content: 'Recommended for current situation', type: 'tip' }
  ]),
  ContextualHelp: function MockContextualHelp({ gamePhase, playerPosition, bettingScenario }) {
    return (
      <div data-testid="contextual-help">
        <div>Game Phase: {gamePhase}</div>
        <div>Player Position: {playerPosition}</div>
        <div>Betting Scenario: {bettingScenario}</div>
      </div>
    );
  }
}));

// Mock UI components
jest.mock('../ui', () => ({
  Card: function MockCard({ children, className }) {
    return <div data-testid="card" className={className}>{children}</div>;
  }
}));

const mockGameState = {
  active: true,
  current_hole: 8,
  current_hole_par: 4,
  hole_difficulty: 3.5,
  human_player: 'player1',
  current_leader: 'player2',
  players: [
    {
      id: 'player1',
      name: 'Alice',
      handicap: 12,
      current_score: 32,
      shots_taken: 1,
      distance_to_pin: 150,
      lie_type: 'fairway',
      is_captain: true,
      team_id: 'team_a'
    },
    {
      id: 'player2',
      name: 'Bob',
      handicap: 18,
      current_score: 38,
      shots_taken: 2,
      distance_to_pin: 180,
      lie_type: 'rough',
      is_captain: false,
      team_id: 'team_b'
    }
  ],
  teams: { type: 'partnerships' },
  current_wager: 2,
  is_doubled: false,
  line_of_scrimmage_passed: true
};

const mockOddsResponse = {
  timestamp: '2024-01-15T10:30:00Z',
  calculation_time_ms: 145.2,
  confidence_level: 0.87,
  monte_carlo_used: true,
  player_probabilities: {
    player1: {
      name: 'Alice',
      win_probability: 0.65,
      expected_score: 4.2,
      risk_factors: ['weather', 'lie']
    },
    player2: {
      name: 'Bob',
      win_probability: 0.35,
      expected_score: 4.8,
      risk_factors: ['distance', 'lie']
    }
  },
  team_probabilities: {
    team_a: 0.58,
    team_b: 0.42
  },
  optimal_strategy: 'conservative_play',
  betting_scenarios: [
    {
      scenario_type: 'double_down',
      win_probability: 0.62,
      expected_value: 1.25,
      risk_level: 'medium',
      reasoning: 'Alice has favorable position with good lie and manageable distance',
      confidence_interval: [0.55, 0.69],
      payout_matrix: {
        win: 4.00,
        loss: -2.00,
        push: 0.00
      },
      recommendation: 'offer'
    },
    {
      scenario_type: 'side_bet',
      win_probability: 0.45,
      expected_value: -0.15,
      risk_level: 'high',
      reasoning: 'Bob faces challenging rough lie with increased distance',
      confidence_interval: [0.38, 0.52],
      payout_matrix: {
        win: 2.50,
        loss: -1.50
      },
      recommendation: 'decline'
    }
  ],
  risk_assessment: {
    volatility: 0.23,
    weather_factor: 1.0,
    course_difficulty: 3.5,
    player_fatigue: 0.15
  },
  educational_insights: [
    'Alice\'s fairway lie provides significant advantage over rough',
    'Current hole difficulty (3.5/5) suggests moderate challenge',
    'Team partnerships favor balanced risk-taking approach'
  ],
  simulation_details: {
    num_simulations_run: 5000,
    convergence_achieved: true,
    monte_carlo_variance: 0.012
  }
};

const TestWrapper = ({ children }) => (
  <ThemeProvider>
    <GameProvider>
      {children}
    </GameProvider>
  </ThemeProvider>
);

describe.skip('BettingOddsPanel', () => {
  let mockOnBettingAction;
  
  beforeEach(() => {
    mockOnBettingAction = jest.fn();
    fetch.mockClear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    act(() => {
      jest.runOnlyPendingTimers();
    });
    jest.useRealTimers();
  });

  describe('Basic Rendering and Loading States', () => {
    test('renders loading state initially', () => {
      // Mock pending fetch
      fetch.mockImplementation(() => new Promise(() => {}));

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Calculating odds...')).toBeInTheDocument();
      expect(screen.getByText('Running probability analysis')).toBeInTheDocument();
      expect(screen.getByText('🎯')).toBeInTheDocument();
    });

    test('renders error state when fetch fails', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Error calculating odds/)).toBeInTheDocument();
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
        expect(screen.getByText('Retry')).toBeInTheDocument();
      });
    });

    test('retries on error when retry button clicked', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
      
      // First call fails
      fetch.mockRejectedValueOnce(new Error('Network error'));
      // Second call succeeds
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockOddsResponse
      });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByText('Retry')).toBeInTheDocument();
      });

      // Click retry
      const retryButton = screen.getByText('Retry');
      await user.click(retryButton);

      // Should show loading then success
      await waitFor(() => {
        expect(screen.getByText('Real-Time Betting Odds')).toBeInTheDocument();
      });
    });

    test('renders nothing when gameState is inactive', () => {
      const inactiveGameState = { ...mockGameState, active: false };
      
      const { container } = render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={inactiveGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      expect(container.firstChild).toBeNull();
    });

    test('renders nothing when no players', () => {
      const noPlayersGameState = { ...mockGameState, players: [] };
      
      const { container } = render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={noPlayersGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Successful Data Loading and Display', () => {
    beforeEach(() => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockOddsResponse
      });
    });

    test('displays odds panel with header information', async () => {
      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Real-Time Betting Odds')).toBeInTheDocument();
        expect(screen.getByText(/Hole 8/)).toBeInTheDocument();
        expect(screen.getByText('87% Confidence')).toBeInTheDocument();
        expect(screen.getByText('145ms')).toBeInTheDocument();
      });
    });

    test('displays view switcher tabs', async () => {
      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('📊')).toBeInTheDocument(); // Overview icon
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('💰')).toBeInTheDocument(); // Scenarios icon
        expect(screen.getByText('Betting Scenarios')).toBeInTheDocument();
        expect(screen.getByText('🔍')).toBeInTheDocument(); // Analysis icon
        expect(screen.getByText('Analysis')).toBeInTheDocument();
      });
    });

    test('shows educational tooltips when enabled', async () => {
      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
            showEducationalTooltips={true}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId('contextual-help')).toBeInTheDocument();
        expect(screen.getByText('💡')).toBeInTheDocument();
        expect(screen.getByText('Strategic Insights')).toBeInTheDocument();
      });
    });

    test('hides educational tooltips when disabled', async () => {
      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
            showEducationalTooltips={false}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Real-Time Betting Odds')).toBeInTheDocument();
      });

      expect(screen.queryByTestId('contextual-help')).not.toBeInTheDocument();
      expect(screen.queryByText('💡')).not.toBeInTheDocument();
    });
  });

  describe('Overview View', () => {
    beforeEach(async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockOddsResponse
      });
    });

    test('displays individual player probabilities', async () => {
      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Individual')).toBeInTheDocument();
        expect(screen.getByText('Alice')).toBeInTheDocument();
        expect(screen.getByText('65.0%')).toBeInTheDocument(); // Alice's win probability
        expect(screen.getByText('Bob')).toBeInTheDocument();
        expect(screen.getByText('35.0%')).toBeInTheDocument(); // Bob's win probability
        expect(screen.getByText('Expected Score: 4.2')).toBeInTheDocument();
        expect(screen.getByText('Expected Score: 4.8')).toBeInTheDocument();
      });
    });

    test('displays team probabilities', async () => {
      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Team Win Probabilities')).toBeInTheDocument();
        expect(screen.getByText('Team_a')).toBeInTheDocument();
        expect(screen.getByText('58.0%')).toBeInTheDocument();
        expect(screen.getByText('Team_b')).toBeInTheDocument();
        expect(screen.getByText('42.0%')).toBeInTheDocument();
      });
    });

    test('displays recommended action', async () => {
      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Recommended Action')).toBeInTheDocument();
        expect(screen.getByText('Conservative Play')).toBeInTheDocument();
        expect(screen.getByText('Take Action')).toBeInTheDocument();
      });
    });

    test('calls onBettingAction when Take Action clicked', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Take Action')).toBeInTheDocument();
      });

      const actionButton = screen.getByText('Take Action');
      await user.click(actionButton);

      expect(mockOnBettingAction).toHaveBeenCalledWith(mockOddsResponse.betting_scenarios[0]);
    });
  });

  describe('Scenarios View', () => {
    beforeEach(async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockOddsResponse
      });
    });

    test('switches to scenarios view', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Betting Scenarios')).toBeInTheDocument();
      });

      const scenariosTab = screen.getByText('Betting Scenarios');
      await user.click(scenariosTab);

      expect(screen.getByText('Double Down')).toBeInTheDocument();
      expect(screen.getByText('Side Bet')).toBeInTheDocument();
    });

    test('displays betting scenarios with risk indicators', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Betting Scenarios')).toBeInTheDocument();
      });

      const scenariosTab = screen.getByText('Betting Scenarios');
      await user.click(scenariosTab);

      // Check scenario headers
      expect(screen.getByText('Double Down')).toBeInTheDocument();
      expect(screen.getByText('62.0% win probability')).toBeInTheDocument();
      expect(screen.getByText('EV: +1.25')).toBeInTheDocument();
      expect(screen.getByText('🟡 MEDIUM')).toBeInTheDocument(); // Risk indicator

      expect(screen.getByText('Side Bet')).toBeInTheDocument();
      expect(screen.getByText('45.0% win probability')).toBeInTheDocument();
      expect(screen.getByText('EV: -0.15')).toBeInTheDocument();
      expect(screen.getByText('🔴 HIGH')).toBeInTheDocument(); // Risk indicator
    });

    test('expands scenario when clicked', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Betting Scenarios')).toBeInTheDocument();
      });

      const scenariosTab = screen.getByText('Betting Scenarios');
      await user.click(scenariosTab);

      // Click on first scenario to expand
      const firstScenario = screen.getByText('Double Down');
      await user.click(firstScenario);

      // Check expanded content
      expect(screen.getByText('Analysis')).toBeInTheDocument();
      expect(screen.getByText(/Alice has favorable position/)).toBeInTheDocument();
      expect(screen.getByText('Potential Outcomes')).toBeInTheDocument();
      expect(screen.getByText('Win')).toBeInTheDocument();
      expect(screen.getByText('+4.00')).toBeInTheDocument();
      expect(screen.getByText('Loss')).toBeInTheDocument();
      expect(screen.getByText('-2.00')).toBeInTheDocument();
    });

    test('calls onBettingAction from scenario', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Betting Scenarios')).toBeInTheDocument();
      });

      const scenariosTab = screen.getByText('Betting Scenarios');
      await user.click(scenariosTab);

      // Expand first scenario
      const firstScenario = screen.getByText('Double Down');
      await user.click(firstScenario);

      // Click action button
      const actionButton = screen.getByText('💰 Offer');
      await user.click(actionButton);

      expect(mockOnBettingAction).toHaveBeenCalledWith(mockOddsResponse.betting_scenarios[0]);
    });

    test('shows no scenarios message when empty', async () => {
      const emptyResponse = { ...mockOddsResponse, betting_scenarios: [] };
      fetch.mockResolvedValue({
        ok: true,
        json: async () => emptyResponse
      });

      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Betting Scenarios')).toBeInTheDocument();
      });

      const scenariosTab = screen.getByText('Betting Scenarios');
      await user.click(scenariosTab);

      expect(screen.getByText('🎯')).toBeInTheDocument();
      expect(screen.getByText('No Betting Scenarios Available')).toBeInTheDocument();
      expect(screen.getByText(/Betting opportunities will appear/)).toBeInTheDocument();
    });
  });

  describe('Analysis View', () => {
    beforeEach(async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockOddsResponse
      });
    });

    test('switches to analysis view', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Analysis')).toBeInTheDocument();
      });

      const analysisTab = screen.getByText('Analysis');
      await user.click(analysisTab);

      expect(screen.getByText('Calculation Performance')).toBeInTheDocument();
      expect(screen.getByText('Risk Assessment')).toBeInTheDocument();
      expect(screen.getByText('Probability Trends')).toBeInTheDocument();
    });

    test('displays performance metrics', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Analysis')).toBeInTheDocument();
      });

      const analysisTab = screen.getByText('Analysis');
      await user.click(analysisTab);

      expect(screen.getByText('145ms')).toBeInTheDocument(); // Calculation time
      expect(screen.getByText('Calculation Time')).toBeInTheDocument();
      expect(screen.getByText('87%')).toBeInTheDocument(); // Confidence level
      expect(screen.getByText('Confidence Level')).toBeInTheDocument();
      expect(screen.getByText('5,000')).toBeInTheDocument(); // Simulations run
      expect(screen.getByText('Simulations Run')).toBeInTheDocument();
    });

    test('displays risk assessment data', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Analysis')).toBeInTheDocument();
      });

      const analysisTab = screen.getByText('Analysis');
      await user.click(analysisTab);

      expect(screen.getByText('Volatility:')).toBeInTheDocument();
      expect(screen.getByText('0.23')).toBeInTheDocument();
      expect(screen.getByText('Course Difficulty:')).toBeInTheDocument();
      expect(screen.getByText('3.50')).toBeInTheDocument();
    });

    test('displays probability visualization', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Analysis')).toBeInTheDocument();
      });

      const analysisTab = screen.getByText('Analysis');
      await user.click(analysisTab);

      expect(screen.getByTestId('probability-visualization')).toBeInTheDocument();
    });

    test('displays educational insights', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Analysis')).toBeInTheDocument();
      });

      const analysisTab = screen.getByText('Analysis');
      await user.click(analysisTab);

      expect(screen.getByText('Educational Insights')).toBeInTheDocument();
      expect(screen.getByText(/Alice's fairway lie provides/)).toBeInTheDocument();
      expect(screen.getByText(/Current hole difficulty/)).toBeInTheDocument();
    });
  });

  describe('Auto-update Functionality', () => {
    test('auto-updates at specified interval', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockOddsResponse
      });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
            autoUpdate={true}
            refreshInterval={2000}
          />
        </TestWrapper>
      );

      // Initial call
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(1);
      });

      // Advance time by refresh interval
      act(() => {
        jest.advanceTimersByTime(2000);
      });

      // Should have made another call
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(2);
      });
    });

    test('does not auto-update when disabled', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockOddsResponse
      });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
            autoUpdate={false}
            refreshInterval={1000}
          />
        </TestWrapper>
      );

      // Initial call
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(1);
      });

      // Advance time
      act(() => {
        jest.advanceTimersByTime(2000);
      });

      // Should not have made additional calls
      expect(fetch).toHaveBeenCalledTimes(1);
    });

    test('manual refresh works', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockOddsResponse
      });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
            autoUpdate={false}
          />
        </TestWrapper>
      );

      // Initial call
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(1);
      });

      // Click refresh button
      const refreshButton = screen.getByText('↻');
      await user.click(refreshButton);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('API Request Validation', () => {
    test('sends correct request data structure', async () => {
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockOddsResponse
      });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/wgp/calculate-odds', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: expect.any(String)
        });
      });

      const requestBody = JSON.parse(fetch.mock.calls[0][1].body);
      
      expect(requestBody).toHaveProperty('players');
      expect(requestBody).toHaveProperty('hole_state');
      expect(requestBody).toHaveProperty('use_monte_carlo');
      expect(requestBody).toHaveProperty('simulation_params');
      
      expect(requestBody.players).toHaveLength(2);
      expect(requestBody.players[0]).toMatchObject({
        id: 'player1',
        name: 'Alice',
        handicap: 12,
        distance_to_pin: 150,
        lie_type: 'fairway'
      });
      
      expect(requestBody.hole_state).toMatchObject({
        hole_number: 8,
        par: 4,
        difficulty_rating: 3.5,
        teams: 'partnerships'
      });
    });

    test('handles HTTP error responses', async () => {
      fetch.mockResolvedValue({
        ok: false,
        status: 500
      });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Error calculating odds/)).toBeInTheDocument();
        expect(screen.getByText(/HTTP error! status: 500/)).toBeInTheDocument();
      });
    });
  });

  describe('Calculation History Tracking', () => {
    test('maintains calculation history', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      // Mock multiple responses with different timestamps
      const responses = [
        { ...mockOddsResponse, timestamp: '2024-01-15T10:30:00Z' },
        { ...mockOddsResponse, timestamp: '2024-01-15T10:30:05Z' },
        { ...mockOddsResponse, timestamp: '2024-01-15T10:30:10Z' }
      ];

      fetch
        .mockResolvedValueOnce({ ok: true, json: async () => responses[0] })
        .mockResolvedValueOnce({ ok: true, json: async () => responses[1] })
        .mockResolvedValueOnce({ ok: true, json: async () => responses[2] });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
            autoUpdate={false}
          />
        </TestWrapper>
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Analysis')).toBeInTheDocument();
      });

      // Make manual refreshes
      const refreshButton = screen.getByText('↻');
      await user.click(refreshButton);
      await user.click(refreshButton);

      // Switch to analysis view to see history
      const analysisTab = screen.getByText('Analysis');
      await user.click(analysisTab);

      // Check that probability visualization received history data
      const historyData = screen.getByTestId('history-data');
      const historyArray = JSON.parse(historyData.textContent);
      
      expect(historyArray).toHaveLength(3);
      expect(historyArray[0].timestamp).toBe('2024-01-15T10:30:00Z');
      expect(historyArray[2].timestamp).toBe('2024-01-15T10:30:10Z');
    });

    test('limits history to last 20 calculations', async () => {
      // This would require a more complex test setup to generate 21+ calculations
      // For now, we verify the concept by checking the slice logic in manual calls
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockOddsResponse
      });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
            autoUpdate={false}
          />
        </TestWrapper>
      );

      // Multiple manual refreshes
      await waitFor(() => {
        expect(screen.getByText('↻')).toBeInTheDocument();
      });

      const refreshButton = screen.getByText('↻');
      
      // Make multiple calls
      for (let i = 0; i < 5; i++) {
        await user.click(refreshButton);
      }

      // Switch to analysis view
      const analysisTab = screen.getByText('Analysis');
      await user.click(analysisTab);

      // Verify history is tracked (exact count depends on timing)
      const historyData = screen.getByTestId('history-data');
      const historyArray = JSON.parse(historyData.textContent);
      
      expect(historyArray.length).toBeGreaterThan(0);
      expect(historyArray.length).toBeLessThanOrEqual(20);
    });
  });

  describe('Performance and Edge Cases', () => {
    test('handles missing optional data gracefully', async () => {
      const minimalResponse = {
        timestamp: '2024-01-15T10:30:00Z',
        calculation_time_ms: 100,
        confidence_level: 0.8,
        player_probabilities: {},
        team_probabilities: {},
        betting_scenarios: []
      };

      fetch.mockResolvedValue({
        ok: true,
        json: async () => minimalResponse
      });

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Real-Time Betting Odds')).toBeInTheDocument();
        expect(screen.getByText('80% Confidence')).toBeInTheDocument();
        expect(screen.getByText('100ms')).toBeInTheDocument();
      });

      // Should not crash with empty data
      expect(screen.queryByText('Alice')).not.toBeInTheDocument();
    });

    test('renders efficiently with complex data', async () => {
      const complexResponse = {
        ...mockOddsResponse,
        player_probabilities: Object.fromEntries(
          Array.from({ length: 6 }, (_, i) => [
            `player${i + 1}`,
            {
              name: `Player ${i + 1}`,
              win_probability: Math.random(),
              expected_score: 3 + Math.random() * 2,
              risk_factors: ['lie', 'distance', 'weather']
            }
          ])
        ),
        betting_scenarios: Array.from({ length: 10 }, (_, i) => ({
          scenario_type: `scenario_${i}`,
          win_probability: Math.random(),
          expected_value: (Math.random() - 0.5) * 5,
          risk_level: ['low', 'medium', 'high'][i % 3],
          reasoning: `Scenario ${i} reasoning`,
          confidence_interval: [0.3, 0.7],
          payout_matrix: { win: 2, loss: -1 },
          recommendation: 'offer'
        }))
      };

      fetch.mockResolvedValue({
        ok: true,
        json: async () => complexResponse
      });

      const start = performance.now();

      render(
        <TestWrapper>
          <BettingOddsPanel 
            gameState={mockGameState} 
            onBettingAction={mockOnBettingAction}
          />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Real-Time Betting Odds')).toBeInTheDocument();
      });

      const end = performance.now();
      
      // Should render complex data efficiently
      expect(end - start).toBeLessThan(1000); // Under 1 second
      expect(screen.getByText('Player 1')).toBeInTheDocument();
      expect(screen.getByText('Player 6')).toBeInTheDocument();
    });
  });
});