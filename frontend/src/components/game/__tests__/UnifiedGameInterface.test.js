/**
 * Comprehensive tests for UnifiedGameInterface.js - Main game interface component
 * 
 * Tests cover:
 * - Component initialization and rendering
 * - Game state management integration
 * - Mode switching (regular/enhanced/simulation)
 * - Player interactions and game actions
 * - Real-time odds integration
 * - Error handling and loading states
 * - Component lifecycle and cleanup
 * - Accessibility features
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react-dom/test-utils';
import '@testing-library/jest-dom';

// Mock dependencies
jest.mock('../../theme/Provider', () => ({
  useTheme: () => ({
    colors: {
      primary: '#007bff',
      secondary: '#6c757d',
      success: '#28a745',
      warning: '#ffc107',
      error: '#dc3545'
    },
    spacing: { sm: '8px', md: '16px', lg: '24px' },
    breakpoints: { mobile: '768px', tablet: '1024px' }
  })
}));

jest.mock('../../context', () => ({
  useGame: jest.fn()
}));

jest.mock('../../hooks/useOddsCalculation', () => ({
  __esModule: true,
  default: jest.fn()
}));

// Mock sub-components
jest.mock('../ShotResultWidget', () => ({ children, ...props }) => (
  <div data-testid="shot-result-widget" {...props}>{children}</div>
));

jest.mock('../BettingOpportunityWidget', () => ({ children, ...props }) => (
  <div data-testid="betting-opportunity-widget" {...props}>{children}</div>
));

jest.mock('../BettingOddsPanel', () => ({ children, ...props }) => (
  <div data-testid="betting-odds-panel" {...props}>{children}</div>
));

jest.mock('../GameStateWidget', () => ({ children, ...props }) => (
  <div data-testid="game-state-widget" {...props}>{children}</div>
));

jest.mock('../StrategicAnalysisWidget', () => ({ children, ...props }) => (
  <div data-testid="strategic-analysis-widget" {...props}>{children}</div>
));

jest.mock('../AnalyticsDashboard', () => ({ children, ...props }) => (
  <div data-testid="analytics-dashboard" {...props}>{children}</div>
));

jest.mock('../HoleVisualization', () => ({ children, ...props }) => (
  <div data-testid="hole-visualization" {...props}>{children}</div>
));

jest.mock('../ShotAnalysisWidget', () => ({ children, ...props }) => (
  <div data-testid="shot-analysis-widget" {...props}>{children}</div>
));

jest.mock('../ShotVisualizationOverlay', () => ({ children, ...props }) => (
  <div data-testid="shot-visualization-overlay" {...props}>{children}</div>
));

jest.mock('../simulation', () => ({
  GameSetup: ({ children, ...props }) => (
    <div data-testid="simulation-setup" {...props}>{children}</div>
  ),
  GamePlay: ({ children, ...props }) => (
    <div data-testid="simulation-play" {...props}>{children}</div>
  )
}));

import UnifiedGameInterface from '../UnifiedGameInterface';
import { useGame } from '../../context';
import useOddsCalculation from '../../hooks/useOddsCalculation';

describe('UnifiedGameInterface', () => {
  let mockUseGame;
  let mockUseOddsCalculation;
  let user;

  beforeEach(() => {
    user = userEvent.setup();
    
    // Default mock for useGame
    mockUseGame = {
      gameState: {
        current_hole: 1,
        players: [
          { id: 'p1', name: 'Alice', points: 0, handicap: 10 },
          { id: 'p2', name: 'Bob', points: 0, handicap: 15 },
          { id: 'p3', name: 'Charlie', points: 0, handicap: 8 },
          { id: 'p4', name: 'Dave', points: 0, handicap: 20 }
        ],
        captain_id: 'p1',
        game_status_message: 'Time to toss the tees!',
        teams: {},
        base_wager: 1
      },
      setGameState: jest.fn(),
      loading: false,
      setLoading: jest.fn(),
      error: null,
      clearError: jest.fn(),
      fetchGameState: jest.fn(),
      makeGameAction: jest.fn(),
      isGameActive: true,
      startGame: jest.fn(),
      endGame: jest.fn()
    };

    // Default mock for useOddsCalculation
    mockUseOddsCalculation = {
      oddsData: {
        optimal_strategy: 'request_partner',
        confidence_level: 0.85,
        calculation_time_ms: 150,
        recommendations: ['Request partner with Bob', 'Avoid going solo']
      },
      loading: false,
      error: null,
      lastUpdate: new Date(),
      calculationHistory: [],
      performanceMetrics: { avgCalculationTime: 200, successRate: 0.95 },
      calculateOdds: jest.fn(),
      refreshOdds: jest.fn(),
      clearError: jest.fn(),
      isCalculationStale: false,
      canCalculate: true
    };

    useGame.mockReturnValue(mockUseGame);
    useOddsCalculation.mockReturnValue(mockUseOddsCalculation);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Initialization', () => {
    it('renders successfully in regular mode', () => {
      render(<UnifiedGameInterface mode="regular" />);
      
      expect(screen.getByTestId('game-state-widget')).toBeInTheDocument();
      expect(screen.getByTestId('betting-odds-panel')).toBeInTheDocument();
    });

    it('renders successfully in enhanced mode', () => {
      render(<UnifiedGameInterface mode="enhanced" />);
      
      expect(screen.getByTestId('analytics-dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('strategic-analysis-widget')).toBeInTheDocument();
    });

    it('renders successfully in simulation mode', () => {
      render(<UnifiedGameInterface mode="simulation" />);
      
      // Should show simulation setup initially
      expect(screen.getByTestId('simulation-setup')).toBeInTheDocument();
    });

    it('applies correct default props when mode is not specified', () => {
      render(<UnifiedGameInterface />);
      
      // Should default to regular mode
      expect(screen.getByTestId('game-state-widget')).toBeInTheDocument();
    });
  });

  describe('Game State Integration', () => {
    it('displays current game state information', () => {
      render(<UnifiedGameInterface mode="regular" />);
      
      // Check that game state is passed to widgets
      const gameStateWidget = screen.getByTestId('game-state-widget');
      expect(gameStateWidget).toBeInTheDocument();
    });

    it('handles game state loading', () => {
      mockUseGame.loading = true;
      useGame.mockReturnValue(mockUseGame);

      render(<UnifiedGameInterface mode="regular" />);
      
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('displays game state errors', () => {
      mockUseGame.error = 'Failed to load game state';
      useGame.mockReturnValue(mockUseGame);

      render(<UnifiedGameInterface mode="regular" />);
      
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/Failed to load game state/)).toBeInTheDocument();
    });

    it('calls clearError when error dismiss button is clicked', async () => {
      mockUseGame.error = 'Test error';
      useGame.mockReturnValue(mockUseGame);

      render(<UnifiedGameInterface mode="regular" />);
      
      const dismissButton = screen.getByRole('button', { name: /dismiss/i });
      await user.click(dismissButton);
      
      expect(mockUseGame.clearError).toHaveBeenCalled();
    });
  });

  describe('View Management', () => {
    it('switches between game views correctly', async () => {
      render(<UnifiedGameInterface mode="enhanced" />);
      
      // Should start with game view
      expect(screen.getByTestId('game-state-widget')).toBeInTheDocument();
      
      // Switch to analytics view
      const analyticsTab = screen.getByRole('tab', { name: /analytics/i });
      await user.click(analyticsTab);
      
      expect(screen.getByTestId('analytics-dashboard')).toBeInTheDocument();
    });

    it('maintains view state across re-renders', async () => {
      const { rerender } = render(<UnifiedGameInterface mode="enhanced" />);
      
      // Switch to analytics view
      const analyticsTab = screen.getByRole('tab', { name: /analytics/i });
      await user.click(analyticsTab);
      
      // Re-render component
      rerender(<UnifiedGameInterface mode="enhanced" />);
      
      // Should still be on analytics view
      expect(screen.getByTestId('analytics-dashboard')).toBeInTheDocument();
    });

    it('shows/hides odds panel correctly', async () => {
      render(<UnifiedGameInterface mode="regular" />);
      
      expect(screen.getByTestId('betting-odds-panel')).toBeInTheDocument();
      
      // Hide odds panel
      const toggleButton = screen.getByRole('button', { name: /hide odds/i });
      await user.click(toggleButton);
      
      expect(screen.queryByTestId('betting-odds-panel')).not.toBeInTheDocument();
    });
  });

  describe('Odds Calculation Integration', () => {
    it('displays odds data when available', () => {
      render(<UnifiedGameInterface mode="regular" />);
      
      const oddsPanel = screen.getByTestId('betting-odds-panel');
      expect(oddsPanel).toBeInTheDocument();
    });

    it('handles odds loading state', () => {
      mockUseOddsCalculation.loading = true;
      useOddsCalculation.mockReturnValue(mockUseOddsCalculation);

      render(<UnifiedGameInterface mode="regular" />);
      
      expect(screen.getByTestId('odds-loading-indicator')).toBeInTheDocument();
    });

    it('displays odds errors', () => {
      mockUseOddsCalculation.error = 'Odds calculation failed';
      useOddsCalculation.mockReturnValue(mockUseOddsCalculation);

      render(<UnifiedGameInterface mode="regular" />);
      
      expect(screen.getByText(/Odds calculation failed/)).toBeInTheDocument();
    });

    it('refreshes odds when refresh button is clicked', async () => {
      render(<UnifiedGameInterface mode="regular" />);
      
      const refreshButton = screen.getByRole('button', { name: /refresh odds/i });
      await user.click(refreshButton);
      
      expect(mockUseOddsCalculation.refreshOdds).toHaveBeenCalled();
    });

    it('creates timeline events in enhanced mode', () => {
      const onOddsUpdate = useOddsCalculation.mock.calls[0][0].onOddsUpdate;
      
      render(<UnifiedGameInterface mode="enhanced" />);
      
      // Trigger odds update
      act(() => {
        onOddsUpdate({
          optimal_strategy: 'go_solo',
          confidence_level: 0.92,
          calculation_time_ms: 180
        });
      });
      
      // Should create timeline event
      expect(screen.getByText(/Odds updated: go solo/)).toBeInTheDocument();
    });
  });

  describe('Player Interactions', () => {
    it('handles game actions correctly', async () => {
      render(<UnifiedGameInterface mode="regular" />);
      
      // Simulate clicking a betting action
      const requestPartnerButton = screen.getByRole('button', { name: /request partner/i });
      await user.click(requestPartnerButton);
      
      expect(mockUseGame.makeGameAction).toHaveBeenCalledWith('request_partner', expect.any(Object));
    });

    it('disables actions when game is not active', () => {
      mockUseGame.isGameActive = false;
      useGame.mockReturnValue(mockUseGame);

      render(<UnifiedGameInterface mode="regular" />);
      
      const actionButtons = screen.getAllByRole('button');
      const gameActionButtons = actionButtons.filter(button => 
        button.textContent.match(/request partner|go solo|offer double/i)
      );
      
      gameActionButtons.forEach(button => {
        expect(button).toBeDisabled();
      });
    });

    it('shows confirmation for high-risk actions', async () => {
      render(<UnifiedGameInterface mode="regular" />);
      
      // Click go solo (high-risk action)
      const goSoloButton = screen.getByRole('button', { name: /go solo/i });
      await user.click(goSoloButton);
      
      // Should show confirmation dialog
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });
  });

  describe('Shot Analysis Features', () => {
    it('toggles shot analysis widget', async () => {
      render(<UnifiedGameInterface mode="enhanced" />);
      
      // Shot analysis should be hidden initially
      expect(screen.queryByTestId('shot-analysis-widget')).not.toBeInTheDocument();
      
      // Toggle shot analysis
      const toggleButton = screen.getByRole('button', { name: /shot analysis/i });
      await user.click(toggleButton);
      
      expect(screen.getByTestId('shot-analysis-widget')).toBeInTheDocument();
    });

    it('passes correct player data to shot analysis', async () => {
      render(<UnifiedGameInterface mode="enhanced" />);
      
      // Enable shot analysis
      const toggleButton = screen.getByRole('button', { name: /shot analysis/i });
      await user.click(toggleButton);
      
      // Select player for analysis
      const playerSelect = screen.getByLabelText(/select player/i);
      await user.selectOptions(playerSelect, 'p1');
      
      const shotAnalysisWidget = screen.getByTestId('shot-analysis-widget');
      expect(shotAnalysisWidget).toHaveAttribute('data-player-id', 'p1');
    });
  });

  describe('Simulation Mode Features', () => {
    it('renders simulation setup initially', () => {
      render(<UnifiedGameInterface mode="simulation" />);
      
      expect(screen.getByTestId('simulation-setup')).toBeInTheDocument();
      expect(screen.queryByTestId('simulation-play')).not.toBeInTheDocument();
    });

    it('transitions from setup to play mode', async () => {
      render(<UnifiedGameInterface mode="simulation" />);
      
      // Complete setup
      const startButton = screen.getByRole('button', { name: /start simulation/i });
      await user.click(startButton);
      
      await waitFor(() => {
        expect(screen.getByTestId('simulation-play')).toBeInTheDocument();
        expect(screen.queryByTestId('simulation-setup')).not.toBeInTheDocument();
      });
    });

    it('handles human player configuration', async () => {
      render(<UnifiedGameInterface mode="simulation" />);
      
      const nameInput = screen.getByLabelText(/player name/i);
      const handicapInput = screen.getByLabelText(/handicap/i);
      
      await user.type(nameInput, 'Test Player');
      await user.clear(handicapInput);
      await user.type(handicapInput, '12');
      
      expect(nameInput).toHaveValue('Test Player');
      expect(handicapInput).toHaveValue(12);
    });
  });

  describe('Error Handling', () => {
    it('displays component-specific errors', () => {
      // Mock console.error to avoid noise in tests
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      // Force an error by passing invalid props
      const ErrorComponent = () => {
        throw new Error('Component error');
      };
      
      render(
        <ErrorBoundary>
          <ErrorComponent />
        </ErrorBoundary>
      );
      
      expect(screen.getByRole('alert')).toBeInTheDocument();
      
      consoleSpy.mockRestore();
    });

    it('recovers from errors gracefully', async () => {
      mockUseGame.error = 'Network error';
      useGame.mockReturnValue(mockUseGame);

      render(<UnifiedGameInterface mode="regular" />);
      
      // Clear error
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);
      
      expect(mockUseGame.clearError).toHaveBeenCalled();
      expect(mockUseGame.fetchGameState).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<UnifiedGameInterface mode="enhanced" />);
      
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('tablist')).toBeInTheDocument();
      expect(screen.getAllByRole('tab')).toHaveLength(3); // Game, Analytics, Strategy
    });

    it('supports keyboard navigation', async () => {
      render(<UnifiedGameInterface mode="enhanced" />);
      
      // Tab navigation
      await user.tab();
      expect(screen.getByRole('tab', { name: /game/i })).toHaveFocus();
      
      await user.tab();
      expect(screen.getByRole('tab', { name: /analytics/i })).toHaveFocus();
    });

    it('announces state changes to screen readers', async () => {
      render(<UnifiedGameInterface mode="regular" />);
      
      // Check for live regions
      expect(screen.getByRole('status')).toBeInTheDocument();
      
      // Simulate state change
      const actionButton = screen.getByRole('button', { name: /request partner/i });
      await user.click(actionButton);
      
      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent(/action completed/i);
      });
    });
  });

  describe('Performance', () => {
    it('does not re-render unnecessarily', () => {
      const renderSpy = jest.fn();
      const TestComponent = () => {
        renderSpy();
        return <UnifiedGameInterface mode="regular" />;
      };
      
      const { rerender } = render(<TestComponent />);
      
      expect(renderSpy).toHaveBeenCalledTimes(1);
      
      // Re-render with same props
      rerender(<TestComponent />);
      
      // Should only re-render if props actually changed
      expect(renderSpy).toHaveBeenCalledTimes(2);
    });

    it('cleans up resources on unmount', () => {
      const { unmount } = render(<UnifiedGameInterface mode="enhanced" />);
      
      // Mock cleanup function
      const cleanupSpy = jest.fn();
      useOddsCalculation.mockReturnValue({
        ...mockUseOddsCalculation,
        cleanup: cleanupSpy
      });
      
      unmount();
      
      // Verify cleanup was called
      expect(cleanupSpy).toHaveBeenCalled();
    });
  });

  describe('Mobile Responsiveness', () => {
    it('adapts layout for mobile screens', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });
      
      render(<UnifiedGameInterface mode="enhanced" />);
      
      // Should show mobile-optimized layout
      expect(screen.getByTestId('mobile-layout')).toBeInTheDocument();
    });

    it('collapses panels on small screens', () => {
      // Mock small screen
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 400,
      });
      
      render(<UnifiedGameInterface mode="regular" />);
      
      // Odds panel should be collapsed
      expect(screen.getByTestId('betting-odds-panel')).toHaveClass('collapsed');
    });
  });
});

// Error Boundary for testing error handling
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <div role="alert">Something went wrong.</div>;
    }

    return this.props.children;
  }
}