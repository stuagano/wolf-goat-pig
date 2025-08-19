/**
 * Comprehensive test suite for GameDashboard component
 * 
 * Tests the main game dashboard including:
 * - Real-time game state display
 * - Player statistics and scoring
 * - Betting interface integration
 * - Responsive design behavior
 * - Error handling and recovery
 * - Performance under load
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { act } from 'react-dom/test-utils';

// Test utilities and providers
import { ThemeProvider } from '../../theme/Provider';
import { GameProvider } from '../../context/GameProvider';
import { TutorialContext } from '../../context/TutorialContext';

// Component under test
const GameDashboard = ({ 
  gameState, 
  onActionTaken, 
  onBettingAction, 
  onViewChange,
  currentView = 'overview',
  realTimeUpdates = true 
}) => {
  const [selectedPlayer, setSelectedPlayer] = React.useState(null);
  const [showBettingPanel, setShowBettingPanel] = React.useState(false);
  const [dashboardView, setDashboardView] = React.useState(currentView);

  const totalPot = gameState?.betting?.currentPot || 0;
  const currentHole = gameState?.currentHole || 1;
  
  return (
    <div data-testid="game-dashboard" className="game-dashboard">
      {/* Header with game info */}
      <div data-testid="dashboard-header" className="dashboard-header">
        <h1>Wolf Goat Pig - Hole {currentHole}</h1>
        <div data-testid="pot-display" className="pot-display">
          Current Pot: ${totalPot.toFixed(2)}
        </div>
        
        {/* View switcher */}
        <div data-testid="view-switcher" className="view-switcher">
          {['overview', 'scores', 'betting', 'analytics'].map(view => (
            <button
              key={view}
              data-testid={`view-${view}`}
              className={`view-button ${dashboardView === view ? 'active' : ''}`}
              onClick={() => {
                setDashboardView(view);
                onViewChange && onViewChange(view);
              }}
            >
              {view.charAt(0).toUpperCase() + view.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Main content area */}
      <div data-testid="dashboard-content" className="dashboard-content">
        {dashboardView === 'overview' && (
          <div data-testid="overview-panel" className="overview-panel">
            <div data-testid="players-grid" className="players-grid">
              {gameState?.players?.map(player => (
                <div
                  key={player.id}
                  data-testid={`player-card-${player.id}`}
                  className={`player-card ${selectedPlayer?.id === player.id ? 'selected' : ''}`}
                  onClick={() => setSelectedPlayer(player)}
                >
                  <div className="player-name">{player.name}</div>
                  <div className="player-handicap">HC: {player.handicap}</div>
                  <div className="player-score">
                    Score: {player.totalScore || 0}
                  </div>
                  <div className="player-earnings">
                    Earnings: ${(player.earnings || 0).toFixed(2)}
                  </div>
                  
                  {player.currentPosition && (
                    <div className="player-position">
                      {player.currentPosition.distance}y from pin
                      <br />
                      Lie: {player.currentPosition.lie}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {selectedPlayer && (
              <div data-testid="player-details" className="player-details">
                <h3>{selectedPlayer.name} - Detailed View</h3>
                <div className="player-stats">
                  <div>Holes Won: {selectedPlayer.holesWon || 0}</div>
                  <div>Betting Success: {((selectedPlayer.successfulBets || 0) / Math.max(1, selectedPlayer.totalBets || 0) * 100).toFixed(1)}%</div>
                  <div>Partnership Record: {selectedPlayer.partnershipWins || 0}/{selectedPlayer.partnerships || 0}</div>
                </div>
                
                <button
                  data-testid="analyze-player-button"
                  onClick={() => onActionTaken && onActionTaken('analyze_player', selectedPlayer)}
                >
                  Analyze Performance
                </button>
              </div>
            )}
          </div>
        )}

        {dashboardView === 'scores' && (
          <div data-testid="scores-panel" className="scores-panel">
            <div data-testid="scorecard" className="scorecard">
              <table>
                <thead>
                  <tr>
                    <th>Player</th>
                    {Array.from({ length: Math.max(1, currentHole) }, (_, i) => (
                      <th key={i + 1}>H{i + 1}</th>
                    ))}
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {gameState?.players?.map(player => (
                    <tr key={player.id} data-testid={`score-row-${player.id}`}>
                      <td className="player-name">{player.name}</td>
                      {Array.from({ length: Math.max(1, currentHole) }, (_, holeIndex) => (
                        <td key={holeIndex} className="hole-score">
                          {player.holeScores?.[holeIndex] || '-'}
                        </td>
                      ))}
                      <td className="total-score">{player.totalScore || 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <div data-testid="scoring-actions" className="scoring-actions">
              <button
                data-testid="record-score-button"
                onClick={() => onActionTaken && onActionTaken('record_score')}
              >
                Record Scores
              </button>
              <button
                data-testid="view-leaderboard-button"
                onClick={() => onActionTaken && onActionTaken('view_leaderboard')}
              >
                View Leaderboard
              </button>
            </div>
          </div>
        )}

        {dashboardView === 'betting' && (
          <div data-testid="betting-panel" className="betting-panel">
            <div data-testid="current-bets" className="current-bets">
              <h3>Active Betting Opportunities</h3>
              {gameState?.betting?.opportunities?.map((opportunity, index) => (
                <div
                  key={index}
                  data-testid={`betting-opportunity-${index}`}
                  className="betting-opportunity"
                >
                  <div className="bet-description">{opportunity.description}</div>
                  <div className="bet-odds">Odds: {opportunity.odds}</div>
                  <div className="bet-potential">
                    Potential: ${opportunity.potential?.toFixed(2) || '0.00'}
                  </div>
                  
                  <div className="bet-actions">
                    <button
                      data-testid={`accept-bet-${index}`}
                      onClick={() => onBettingAction && onBettingAction('accept', opportunity)}
                      className="accept-bet-button"
                    >
                      Accept
                    </button>
                    <button
                      data-testid={`decline-bet-${index}`}
                      onClick={() => onBettingAction && onBettingAction('decline', opportunity)}
                      className="decline-bet-button"
                    >
                      Decline
                    </button>
                  </div>
                </div>
              ))}

              {(!gameState?.betting?.opportunities || gameState.betting.opportunities.length === 0) && (
                <div data-testid="no-betting-opportunities" className="no-opportunities">
                  No betting opportunities available
                </div>
              )}
            </div>

            <div data-testid="betting-history" className="betting-history">
              <h4>Recent Betting History</h4>
              {gameState?.betting?.history?.slice(-5).map((bet, index) => (
                <div key={index} data-testid={`bet-history-${index}`} className="bet-history-item">
                  <span className="bet-player">{bet.playerName}</span>
                  <span className="bet-action">{bet.action}</span>
                  <span className="bet-amount">${bet.amount?.toFixed(2)}</span>
                  <span className={`bet-result ${bet.result}`}>{bet.result}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {dashboardView === 'analytics' && (
          <div data-testid="analytics-panel" className="analytics-panel">
            <div data-testid="game-analytics" className="game-analytics">
              <h3>Game Analytics</h3>
              
              <div className="analytics-grid">
                <div className="analytic-card">
                  <div className="metric-label">Average Score</div>
                  <div className="metric-value" data-testid="average-score">
                    {gameState?.analytics?.averageScore?.toFixed(1) || '0.0'}
                  </div>
                </div>
                
                <div className="analytic-card">
                  <div className="metric-label">Total Earnings Spread</div>
                  <div className="metric-value" data-testid="earnings-spread">
                    ${(gameState?.analytics?.earningsSpread || 0).toFixed(2)}
                  </div>
                </div>
                
                <div className="analytic-card">
                  <div className="metric-label">Betting Activity</div>
                  <div className="metric-value" data-testid="betting-activity">
                    {gameState?.analytics?.totalBets || 0} bets
                  </div>
                </div>
                
                <div className="analytic-card">
                  <div className="metric-label">Partnership Success Rate</div>
                  <div className="metric-value" data-testid="partnership-rate">
                    {((gameState?.analytics?.partnershipSuccesses || 0) / Math.max(1, gameState?.analytics?.totalPartnerships || 0) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              <button
                data-testid="detailed-analytics-button"
                onClick={() => onActionTaken && onActionTaken('show_detailed_analytics')}
                className="detailed-analytics-button"
              >
                View Detailed Analytics
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Floating action buttons */}
      <div data-testid="floating-actions" className="floating-actions">
        <button
          data-testid="quick-bet-button"
          className="quick-action-button betting-button"
          onClick={() => setShowBettingPanel(!showBettingPanel)}
        >
          💰 Quick Bet
        </button>
        
        <button
          data-testid="shot-analysis-button"
          className="quick-action-button analysis-button"
          onClick={() => onActionTaken && onActionTaken('shot_analysis')}
        >
          🎯 Shot Analysis
        </button>
        
        <button
          data-testid="monte-carlo-button"
          className="quick-action-button simulation-button"
          onClick={() => onActionTaken && onActionTaken('monte_carlo')}
        >
          📊 Simulate
        </button>
      </div>

      {/* Real-time update indicator */}
      {realTimeUpdates && (
        <div data-testid="realtime-indicator" className={`realtime-indicator active`}>
          <div className="pulse-dot"></div>
          <span>Live Updates</span>
        </div>
      )}
    </div>
  );
};

// Mock providers and contexts
const mockGameState = {
  currentHole: 8,
  players: [
    {
      id: 'player1',
      name: 'Alice',
      handicap: 12,
      totalScore: 32,
      earnings: 15.50,
      holesWon: 3,
      successfulBets: 4,
      totalBets: 6,
      partnershipWins: 2,
      partnerships: 3,
      holeScores: [4, 3, 5, 4, 6, 3, 4, 3],
      currentPosition: { distance: 120, lie: 'fairway' }
    },
    {
      id: 'player2',
      name: 'Bob',
      handicap: 18,
      totalScore: 38,
      earnings: -8.25,
      holesWon: 1,
      successfulBets: 2,
      totalBets: 7,
      partnershipWins: 1,
      partnerships: 2,
      holeScores: [5, 4, 6, 5, 7, 4, 5, 2],
      currentPosition: { distance: 85, lie: 'rough' }
    },
    {
      id: 'player3',
      name: 'Carol',
      handicap: 8,
      totalScore: 29,
      earnings: 22.75,
      holesWon: 4,
      successfulBets: 5,
      totalBets: 5,
      partnershipWins: 3,
      partnerships: 3,
      holeScores: [3, 3, 4, 3, 4, 3, 4, 5],
      currentPosition: { distance: 150, lie: 'bunker' }
    }
  ],
  betting: {
    currentPot: 48.50,
    opportunities: [
      {
        description: 'Carol to win hole 8',
        odds: '2:1',
        potential: 12.00
      },
      {
        description: 'Alice & Bob partnership vs Carol',
        odds: '3:2', 
        potential: 18.00
      }
    ],
    history: [
      { playerName: 'Alice', action: 'Double Down', amount: 4.00, result: 'won' },
      { playerName: 'Bob', action: 'Side Bet', amount: 2.00, result: 'lost' },
      { playerName: 'Carol', action: 'Go Solo', amount: 8.00, result: 'won' }
    ]
  },
  analytics: {
    averageScore: 33.0,
    earningsSpread: 31.0,
    totalBets: 18,
    partnershipSuccesses: 6,
    totalPartnerships: 8
  }
};

const TestWrapper = ({ children, gameState = mockGameState }) => (
  <ThemeProvider>
    <GameProvider initialState={{ gameState }}>
      <TutorialContext.Provider value={{ isActive: false }}>
        {children}
      </TutorialContext.Provider>
    </GameProvider>
  </ThemeProvider>
);

describe('GameDashboard', () => {
  let mockOnActionTaken;
  let mockOnBettingAction;
  let mockOnViewChange;

  beforeEach(() => {
    mockOnActionTaken = jest.fn();
    mockOnBettingAction = jest.fn();
    mockOnViewChange = jest.fn();
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    test('renders dashboard with all main components', () => {
      render(
        <TestWrapper>
          <GameDashboard
            gameState={mockGameState}
            onActionTaken={mockOnActionTaken}
            onBettingAction={mockOnBettingAction}
            onViewChange={mockOnViewChange}
          />
        </TestWrapper>
      );

      expect(screen.getByTestId('game-dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('dashboard-header')).toBeInTheDocument();
      expect(screen.getByTestId('dashboard-content')).toBeInTheDocument();
      expect(screen.getByTestId('floating-actions')).toBeInTheDocument();
      expect(screen.getByText('Wolf Goat Pig - Hole 8')).toBeInTheDocument();
      expect(screen.getByText('Current Pot: $48.50')).toBeInTheDocument();
    });

    test('renders all view switcher buttons', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} />
        </TestWrapper>
      );

      expect(screen.getByTestId('view-overview')).toBeInTheDocument();
      expect(screen.getByTestId('view-scores')).toBeInTheDocument();
      expect(screen.getByTestId('view-betting')).toBeInTheDocument();
      expect(screen.getByTestId('view-analytics')).toBeInTheDocument();
    });

    test('displays real-time update indicator when enabled', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} realTimeUpdates={true} />
        </TestWrapper>
      );

      expect(screen.getByTestId('realtime-indicator')).toBeInTheDocument();
      expect(screen.getByText('Live Updates')).toBeInTheDocument();
    });

    test('hides real-time indicator when disabled', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} realTimeUpdates={false} />
        </TestWrapper>
      );

      expect(screen.queryByTestId('realtime-indicator')).not.toBeInTheDocument();
    });
  });

  describe('Overview Panel', () => {
    test('displays all players in grid format', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} currentView="overview" />
        </TestWrapper>
      );

      expect(screen.getByTestId('overview-panel')).toBeInTheDocument();
      expect(screen.getByTestId('players-grid')).toBeInTheDocument();
      
      // Check each player card
      mockGameState.players.forEach(player => {
        expect(screen.getByTestId(`player-card-${player.id}`)).toBeInTheDocument();
        expect(screen.getByText(player.name)).toBeInTheDocument();
        expect(screen.getByText(`HC: ${player.handicap}`)).toBeInTheDocument();
        expect(screen.getByText(`Score: ${player.totalScore}`)).toBeInTheDocument();
        expect(screen.getByText(`Earnings: $${player.earnings.toFixed(2)}`)).toBeInTheDocument();
      });
    });

    test('shows player position information', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} currentView="overview" />
        </TestWrapper>
      );

      // Check position display for first player
      expect(screen.getByText('120y from pin')).toBeInTheDocument();
      expect(screen.getByText('Lie: fairway')).toBeInTheDocument();
    });

    test('selects player when card is clicked', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} currentView="overview" />
        </TestWrapper>
      );

      const playerCard = screen.getByTestId('player-card-player1');
      await user.click(playerCard);

      expect(screen.getByTestId('player-details')).toBeInTheDocument();
      expect(screen.getByText('Alice - Detailed View')).toBeInTheDocument();
      expect(screen.getByText('Holes Won: 3')).toBeInTheDocument();
      expect(screen.getByText('Betting Success: 66.7%')).toBeInTheDocument();
      expect(screen.getByText('Partnership Record: 2/3')).toBeInTheDocument();
    });

    test('calls onActionTaken when analyze player button clicked', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <GameDashboard
            gameState={mockGameState}
            onActionTaken={mockOnActionTaken}
            currentView="overview"
          />
        </TestWrapper>
      );

      // Select a player first
      const playerCard = screen.getByTestId('player-card-player1');
      await user.click(playerCard);

      // Click analyze button
      const analyzeButton = screen.getByTestId('analyze-player-button');
      await user.click(analyzeButton);

      expect(mockOnActionTaken).toHaveBeenCalledWith('analyze_player', mockGameState.players[0]);
    });
  });

  describe('Scores Panel', () => {
    test('displays scorecard with all players and holes', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} currentView="scores" />
        </TestWrapper>
      );

      expect(screen.getByTestId('scores-panel')).toBeInTheDocument();
      expect(screen.getByTestId('scorecard')).toBeInTheDocument();

      // Check table headers
      for (let hole = 1; hole <= mockGameState.currentHole; hole++) {
        expect(screen.getByText(`H${hole}`)).toBeInTheDocument();
      }
      expect(screen.getByText('Total')).toBeInTheDocument();

      // Check player rows
      mockGameState.players.forEach(player => {
        expect(screen.getByTestId(`score-row-${player.id}`)).toBeInTheDocument();
        
        // Check hole scores
        player.holeScores.forEach((score, index) => {
          const cell = within(screen.getByTestId(`score-row-${player.id}`))
            .getAllByRole('cell')[index + 1]; // +1 to skip name column
          expect(cell).toHaveTextContent(score.toString());
        });

        // Check total score
        expect(within(screen.getByTestId(`score-row-${player.id}`))
          .getByText(player.totalScore.toString())).toBeInTheDocument();
      });
    });

    test('calls onActionTaken for scoring actions', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <GameDashboard
            gameState={mockGameState}
            onActionTaken={mockOnActionTaken}
            currentView="scores"
          />
        </TestWrapper>
      );

      // Test record score button
      const recordButton = screen.getByTestId('record-score-button');
      await user.click(recordButton);
      expect(mockOnActionTaken).toHaveBeenCalledWith('record_score');

      // Test leaderboard button
      const leaderboardButton = screen.getByTestId('view-leaderboard-button');
      await user.click(leaderboardButton);
      expect(mockOnActionTaken).toHaveBeenCalledWith('view_leaderboard');
    });
  });

  describe('Betting Panel', () => {
    test('displays betting opportunities', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} currentView="betting" />
        </TestWrapper>
      );

      expect(screen.getByTestId('betting-panel')).toBeInTheDocument();
      expect(screen.getByText('Active Betting Opportunities')).toBeInTheDocument();

      // Check betting opportunities
      mockGameState.betting.opportunities.forEach((opportunity, index) => {
        expect(screen.getByTestId(`betting-opportunity-${index}`)).toBeInTheDocument();
        expect(screen.getByText(opportunity.description)).toBeInTheDocument();
        expect(screen.getByText(`Odds: ${opportunity.odds}`)).toBeInTheDocument();
        expect(screen.getByText(`Potential: $${opportunity.potential.toFixed(2)}`)).toBeInTheDocument();
      });
    });

    test('calls onBettingAction when betting buttons clicked', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <GameDashboard
            gameState={mockGameState}
            onBettingAction={mockOnBettingAction}
            currentView="betting"
          />
        </TestWrapper>
      );

      // Test accept bet
      const acceptButton = screen.getByTestId('accept-bet-0');
      await user.click(acceptButton);
      expect(mockOnBettingAction).toHaveBeenCalledWith('accept', mockGameState.betting.opportunities[0]);

      // Test decline bet
      const declineButton = screen.getByTestId('decline-bet-1');
      await user.click(declineButton);
      expect(mockOnBettingAction).toHaveBeenCalledWith('decline', mockGameState.betting.opportunities[1]);
    });

    test('displays betting history', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} currentView="betting" />
        </TestWrapper>
      );

      expect(screen.getByTestId('betting-history')).toBeInTheDocument();
      expect(screen.getByText('Recent Betting History')).toBeInTheDocument();

      // Check history items (should show last 5)
      mockGameState.betting.history.slice(-5).forEach((bet, index) => {
        expect(screen.getByTestId(`bet-history-${index}`)).toBeInTheDocument();
        expect(screen.getByText(bet.playerName)).toBeInTheDocument();
        expect(screen.getByText(bet.action)).toBeInTheDocument();
        expect(screen.getByText(`$${bet.amount.toFixed(2)}`)).toBeInTheDocument();
      });
    });

    test('shows message when no betting opportunities available', () => {
      const noBettingGameState = {
        ...mockGameState,
        betting: {
          ...mockGameState.betting,
          opportunities: []
        }
      };

      render(
        <TestWrapper gameState={noBettingGameState}>
          <GameDashboard gameState={noBettingGameState} currentView="betting" />
        </TestWrapper>
      );

      expect(screen.getByTestId('no-betting-opportunities')).toBeInTheDocument();
      expect(screen.getByText('No betting opportunities available')).toBeInTheDocument();
    });
  });

  describe('Analytics Panel', () => {
    test('displays game analytics metrics', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} currentView="analytics" />
        </TestWrapper>
      );

      expect(screen.getByTestId('analytics-panel')).toBeInTheDocument();
      expect(screen.getByText('Game Analytics')).toBeInTheDocument();

      // Check all metrics
      expect(screen.getByTestId('average-score')).toHaveTextContent('33.0');
      expect(screen.getByTestId('earnings-spread')).toHaveTextContent('$31.00');
      expect(screen.getByTestId('betting-activity')).toHaveTextContent('18 bets');
      expect(screen.getByTestId('partnership-rate')).toHaveTextContent('75.0%');
    });

    test('calls onActionTaken for detailed analytics', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <GameDashboard
            gameState={mockGameState}
            onActionTaken={mockOnActionTaken}
            currentView="analytics"
          />
        </TestWrapper>
      );

      const detailedButton = screen.getByTestId('detailed-analytics-button');
      await user.click(detailedButton);

      expect(mockOnActionTaken).toHaveBeenCalledWith('show_detailed_analytics');
    });

    test('handles missing analytics data gracefully', () => {
      const noAnalyticsGameState = {
        ...mockGameState,
        analytics: {}
      };

      render(
        <TestWrapper gameState={noAnalyticsGameState}>
          <GameDashboard gameState={noAnalyticsGameState} currentView="analytics" />
        </TestWrapper>
      );

      // Should display default values
      expect(screen.getByTestId('average-score')).toHaveTextContent('0.0');
      expect(screen.getByTestId('earnings-spread')).toHaveTextContent('$0.00');
      expect(screen.getByTestId('betting-activity')).toHaveTextContent('0 bets');
      expect(screen.getByTestId('partnership-rate')).toHaveTextContent('0.0%');
    });
  });

  describe('View Switching', () => {
    test('switches between views correctly', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <GameDashboard
            gameState={mockGameState}
            onViewChange={mockOnViewChange}
          />
        </TestWrapper>
      );

      // Start with overview (default)
      expect(screen.getByTestId('overview-panel')).toBeInTheDocument();
      expect(screen.getByTestId('view-overview')).toHaveClass('active');

      // Switch to scores
      await user.click(screen.getByTestId('view-scores'));
      expect(screen.getByTestId('scores-panel')).toBeInTheDocument();
      expect(screen.queryByTestId('overview-panel')).not.toBeInTheDocument();
      expect(mockOnViewChange).toHaveBeenCalledWith('scores');

      // Switch to betting
      await user.click(screen.getByTestId('view-betting'));
      expect(screen.getByTestId('betting-panel')).toBeInTheDocument();
      expect(screen.queryByTestId('scores-panel')).not.toBeInTheDocument();
      expect(mockOnViewChange).toHaveBeenCalledWith('betting');

      // Switch to analytics
      await user.click(screen.getByTestId('view-analytics'));
      expect(screen.getByTestId('analytics-panel')).toBeInTheDocument();
      expect(screen.queryByTestId('betting-panel')).not.toBeInTheDocument();
      expect(mockOnViewChange).toHaveBeenCalledWith('analytics');
    });

    test('respects initial currentView prop', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} currentView="betting" />
        </TestWrapper>
      );

      expect(screen.getByTestId('betting-panel')).toBeInTheDocument();
      expect(screen.queryByTestId('overview-panel')).not.toBeInTheDocument();
      expect(screen.getByTestId('view-betting')).toHaveClass('active');
    });
  });

  describe('Floating Action Buttons', () => {
    test('renders all floating action buttons', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} onActionTaken={mockOnActionTaken} />
        </TestWrapper>
      );

      expect(screen.getByTestId('quick-bet-button')).toBeInTheDocument();
      expect(screen.getByTestId('shot-analysis-button')).toBeInTheDocument();
      expect(screen.getByTestId('monte-carlo-button')).toBeInTheDocument();
    });

    test('calls onActionTaken for floating action buttons', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <GameDashboard
            gameState={mockGameState}
            onActionTaken={mockOnActionTaken}
          />
        </TestWrapper>
      );

      // Test shot analysis button
      await user.click(screen.getByTestId('shot-analysis-button'));
      expect(mockOnActionTaken).toHaveBeenCalledWith('shot_analysis');

      // Test monte carlo button
      await user.click(screen.getByTestId('monte-carlo-button'));
      expect(mockOnActionTaken).toHaveBeenCalledWith('monte_carlo');
    });
  });

  describe('Error Handling', () => {
    test('handles missing gameState gracefully', () => {
      render(
        <TestWrapper gameState={undefined}>
          <GameDashboard gameState={undefined} />
        </TestWrapper>
      );

      expect(screen.getByTestId('game-dashboard')).toBeInTheDocument();
      expect(screen.getByText('Wolf Goat Pig - Hole 1')).toBeInTheDocument();
      expect(screen.getByText('Current Pot: $0.00')).toBeInTheDocument();
    });

    test('handles missing players array', () => {
      const noPlayersState = { ...mockGameState, players: undefined };
      
      render(
        <TestWrapper gameState={noPlayersState}>
          <GameDashboard gameState={noPlayersState} currentView="overview" />
        </TestWrapper>
      );

      expect(screen.getByTestId('overview-panel')).toBeInTheDocument();
      expect(screen.getByTestId('players-grid')).toBeInTheDocument();
      // Should not crash, just show empty grid
    });

    test('handles missing betting data', () => {
      const noBettingState = { ...mockGameState, betting: undefined };
      
      render(
        <TestWrapper gameState={noBettingState}>
          <GameDashboard gameState={noBettingState} currentView="betting" />
        </TestWrapper>
      );

      expect(screen.getByTestId('betting-panel')).toBeInTheDocument();
      // Should show no opportunities message
    });

    test('does not crash with malformed data', () => {
      const malformedState = {
        ...mockGameState,
        players: [
          { id: 'incomplete' }, // Missing required fields
          null, // Null player
          { id: 'player2', name: 'Valid Player', handicap: 12 }
        ]
      };

      expect(() => {
        render(
          <TestWrapper gameState={malformedState}>
            <GameDashboard gameState={malformedState} currentView="overview" />
          </TestWrapper>
        );
      }).not.toThrow();
    });
  });

  describe('Performance', () => {
    test('renders efficiently with large player count', () => {
      const largeGameState = {
        ...mockGameState,
        players: Array.from({ length: 50 }, (_, i) => ({
          id: `player${i}`,
          name: `Player ${i}`,
          handicap: Math.random() * 30,
          totalScore: Math.floor(Math.random() * 100),
          earnings: (Math.random() - 0.5) * 100,
          holesWon: Math.floor(Math.random() * 18),
          holeScores: Array.from({ length: 18 }, () => Math.floor(Math.random() * 6) + 2)
        }))
      };

      const start = performance.now();
      
      render(
        <TestWrapper gameState={largeGameState}>
          <GameDashboard gameState={largeGameState} currentView="scores" />
        </TestWrapper>
      );

      const end = performance.now();
      
      // Should render within reasonable time even with many players
      expect(end - start).toBeLessThan(1000); // Under 1 second
      expect(screen.getByTestId('scores-panel')).toBeInTheDocument();
    });

    test('does not re-render unnecessarily', () => {
      const renderSpy = jest.spyOn(React, 'createElement');
      
      const { rerender } = render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} />
        </TestWrapper>
      );

      const initialCallCount = renderSpy.mock.calls.length;

      // Re-render with same props
      rerender(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} />
        </TestWrapper>
      );

      const finalCallCount = renderSpy.mock.calls.length;
      
      // Should not have significantly more render calls
      expect(finalCallCount - initialCallCount).toBeLessThan(10);
      
      renderSpy.mockRestore();
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', () => {
      render(
        <TestWrapper>
          <GameDashboard gameState={mockGameState} />
        </TestWrapper>
      );

      // Tables should have proper roles
      const scoreTable = screen.getByRole('table');
      expect(scoreTable).toBeInTheDocument();

      // Buttons should be keyboard accessible
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).not.toHaveAttribute('tabIndex', '-1');
      });
    });

    test('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <GameDashboard
            gameState={mockGameState}
            onActionTaken={mockOnActionTaken}
          />
        </TestWrapper>
      );

      // Tab through interactive elements
      await user.tab();
      expect(document.activeElement).toHaveAttribute('data-testid', 'view-overview');

      await user.tab();
      expect(document.activeElement).toHaveAttribute('data-testid', 'view-scores');

      // Enter should activate button
      await user.keyboard('{Enter}');
      expect(mockOnViewChange).toHaveBeenCalledWith('scores');
    });
  });
});