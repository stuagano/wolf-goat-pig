import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '../../theme/Provider';
import { GameProvider } from '../../context';
import UnifiedGameInterface from '../game/UnifiedGameInterface';

// Mock the API module
jest.mock('../../utils/api', () => ({
  apiPost: jest.fn(),
  useApiCall: () => ({
    makeApiCall: jest.fn().mockResolvedValue({
      analysis: {
        recommended_shot: {
          type: 'conservative_approach',
          success_rate: '85%',
          risk_level: '25'
        }
      }
    }),
    loading: false,
    error: null,
    isColdStart: false
  })
}));

// Mock window.innerWidth
Object.defineProperty(window, 'innerWidth', {
  writable: true,
  configurable: true,
  value: 1024,
});

const mockGameState = {
  current_hole: 10,
  game_phase: 'regular',
  base_wager: 1,
  players: [
    { id: 'p1', name: 'John Doe', handicap: 10, points: 0 },
    { id: 'p2', name: 'Jane Smith', handicap: 15, points: 2 }
  ],
  hole_state: {
    hole_par: 4,
    hole_distance: 400,
    stroke_index: 5,
    teams: { type: 'solo' },
    betting: {
      current_wager: 1,
      base_wager: 1,
      doubled: false,
      redoubled: false
    },
    ball_positions: {
      'p1': {
        distance_to_pin: 150,
        lie_type: 'fairway',
        shot_count: 1
      }
    },
    current_shot_number: 1,
    next_player_to_hit: 'p1',
    line_of_scrimmage: 'p1',
    hole_complete: false,
    stroke_advantages: {
      'p1': { strokes_received: 0 },
      'p2': { strokes_received: 1 }
    }
  }
};

// Mock context values
const mockContextValue = {
  gameState: mockGameState,
  loading: false,
  error: null,
  setError: jest.fn(),
  fetchGameState: jest.fn(),
  makeGameAction: jest.fn(),
  isGameActive: true,
  startGame: jest.fn(),
  endGame: jest.fn()
};

// Mock the useGame hook
jest.mock('../../context', () => ({
  ...jest.requireActual('../../context'),
  useGame: () => mockContextValue
}));

const TestWrapper = ({ children }) => (
  <ThemeProvider>
    <GameProvider>
      {children}
    </GameProvider>
  </ThemeProvider>
);

describe('UnifiedGameInterface Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Regular Mode', () => {
    test('renders game interface in regular mode', () => {
      render(
        <TestWrapper>
          <UnifiedGameInterface mode="regular" />
        </TestWrapper>
      );

      expect(screen.getByText('🎯 Wolf Goat Pig Game')).toBeInTheDocument();
      expect(screen.getByText('🎯 Shot Analysis')).toBeInTheDocument();
    });

    test('toggles shot analysis widget', () => {
      render(
        <TestWrapper>
          <UnifiedGameInterface mode="regular" />
        </TestWrapper>
      );

      const analysisToggle = screen.getByText('🎯 Shot Analysis');
      fireEvent.click(analysisToggle);

      expect(screen.getByText('🎯 Analysis ON')).toBeInTheDocument();
    });

    test('shot analysis widget receives correct props', () => {
      render(
        <TestWrapper>
          <UnifiedGameInterface mode="regular" />
        </TestWrapper>
      );

      // Toggle analysis on
      const analysisToggle = screen.getByText('🎯 Shot Analysis');
      fireEvent.click(analysisToggle);

      // Verify shot analysis widget is rendered with player data
      expect(screen.getByText('John Doe (HC: 10)')).toBeInTheDocument();
      expect(screen.getByText('150 yards')).toBeInTheDocument();
    });
  });

  describe('Enhanced Mode', () => {
    test('renders enhanced interface with view switcher', () => {
      render(
        <TestWrapper>
          <UnifiedGameInterface mode="enhanced" />
        </TestWrapper>
      );

      expect(screen.getByText('🚀 Enhanced Wolf Goat Pig')).toBeInTheDocument();
      expect(screen.getByDisplayValue('🎮 Game View')).toBeInTheDocument();
    });

    test('switches between different views', () => {
      render(
        <TestWrapper>
          <UnifiedGameInterface mode="enhanced" />
        </TestWrapper>
      );

      const viewSelect = screen.getByDisplayValue('🎮 Game View');
      
      // Switch to analytics view
      fireEvent.change(viewSelect, { target: { value: 'analytics' } });
      expect(viewSelect.value).toBe('analytics');
      
      // Switch to visualization view
      fireEvent.change(viewSelect, { target: { value: 'visualization' } });
      expect(viewSelect.value).toBe('visualization');
    });

    test('displays game status information', () => {
      render(
        <TestWrapper>
          <UnifiedGameInterface mode="enhanced" />
        </TestWrapper>
      );

      expect(screen.getByText('Current Hole')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('Game Phase')).toBeInTheDocument();
      expect(screen.getByText('Regular Play')).toBeInTheDocument();
      expect(screen.getByText('Base Wager')).toBeInTheDocument();
      expect(screen.getByText('$1')).toBeInTheDocument();
    });

    test('shot analysis toggle works in enhanced mode', () => {
      render(
        <TestWrapper>
          <UnifiedGameInterface mode="enhanced" />
        </TestWrapper>
      );

      const analysisToggle = screen.getByText('🎯 Shot Analysis');
      fireEvent.click(analysisToggle);

      expect(screen.getByText('🎯 Analysis ON')).toBeInTheDocument();
      // Should show shot analysis widget
      expect(screen.getByText('🎯 Shot Analysis')).toBeInTheDocument();
    });

    test('timeline view shows events', () => {
      render(
        <TestWrapper>
          <UnifiedGameInterface mode="enhanced" />
        </TestWrapper>
      );

      const viewSelect = screen.getByDisplayValue('🎮 Game View');
      fireEvent.change(viewSelect, { target: { value: 'timeline' } });

      expect(screen.getByText('📋 Game Timeline')).toBeInTheDocument();
    });

    test('visualization view includes shot overlay when analysis active', async () => {
      render(
        <TestWrapper>
          <UnifiedGameInterface mode="enhanced" />
        </TestWrapper>
      );

      // Enable shot analysis
      const analysisToggle = screen.getByText('🎯 Shot Analysis');
      fireEvent.click(analysisToggle);

      // Switch to visualization view
      const viewSelect = screen.getByDisplayValue('🎮 Game View');
      fireEvent.change(viewSelect, { target: { value: 'visualization' } });

      // Trigger analysis to get shot data
      const analyzeButton = screen.getByText('Analyze Shot');
      fireEvent.click(analyzeButton);

      await waitFor(() => {
        expect(screen.getByText('🎯 Shot Analysis Overlay')).toBeInTheDocument();
      });
    });
  });

  describe('Shot Analysis Integration', () => {
    test('shot recommendations trigger timeline events in enhanced mode', async () => {
      render(
        <TestWrapper>
          <UnifiedGameInterface mode="enhanced" />
        </TestWrapper>
      );

      // Enable shot analysis
      const analysisToggle = screen.getByText('🎯 Shot Analysis');
      fireEvent.click(analysisToggle);

      // Trigger analysis
      const analyzeButton = screen.getByText('Analyze Shot');
      fireEvent.click(analyzeButton);

      // Check timeline for analysis event
      const viewSelect = screen.getByDisplayValue('🎮 Game View');
      fireEvent.change(viewSelect, { target: { value: 'timeline' } });

      await waitFor(() => {
        expect(screen.getByText(/Shot recommendation/)).toBeInTheDocument();
      });
    });

    test('mobile layout adapts grid correctly', () => {
      // Mock mobile screen
      Object.defineProperty(window, 'innerWidth', {
        value: 600,
      });

      render(
        <TestWrapper>
          <UnifiedGameInterface mode="enhanced" />
        </TestWrapper>
      );

      // Should render without errors on mobile
      expect(screen.getByText('🚀 Enhanced Wolf Goat Pig')).toBeInTheDocument();
    });

    test('shot analysis updates when game state changes', () => {
      const { rerender } = render(
        <TestWrapper>
          <UnifiedGameInterface mode="regular" />
        </TestWrapper>
      );

      // Enable shot analysis
      const analysisToggle = screen.getByText('🎯 Shot Analysis');
      fireEvent.click(analysisToggle);

      expect(screen.getByText('John Doe (HC: 10)')).toBeInTheDocument();

      // Update the mock context to change current player
      const updatedContextValue = {
        ...mockContextValue,
        gameState: {
          ...mockGameState,
          next_player_to_hit: 'p2'
        }
      };

      // Mock updated context
      require('../../context').useGame.mockReturnValue(updatedContextValue);

      rerender(
        <TestWrapper>
          <UnifiedGameInterface mode="regular" />
        </TestWrapper>
      );

      // Should now show the updated player info
      expect(screen.getByText('Jane Smith (HC: 15)')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('displays error state when game loading fails', () => {
      const errorContextValue = {
        ...mockContextValue,
        error: 'Failed to load game state'
      };

      require('../../context').useGame.mockReturnValue(errorContextValue);

      render(
        <TestWrapper>
          <UnifiedGameInterface mode="regular" />
        </TestWrapper>
      );

      expect(screen.getByText('Game Error')).toBeInTheDocument();
      expect(screen.getByText('Failed to load game state')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    test('displays loading state', () => {
      const loadingContextValue = {
        ...mockContextValue,
        loading: true,
        gameState: null
      };

      require('../../context').useGame.mockReturnValue(loadingContextValue);

      render(
        <TestWrapper>
          <UnifiedGameInterface mode="regular" />
        </TestWrapper>
      );

      expect(screen.getByText('Loading Wolf Goat Pig...')).toBeInTheDocument();
    });

    test('displays no game state message', () => {
      const noGameContextValue = {
        ...mockContextValue,
        gameState: null,
        loading: false
      };

      require('../../context').useGame.mockReturnValue(noGameContextValue);

      render(
        <TestWrapper>
          <UnifiedGameInterface mode="regular" />
        </TestWrapper>
      );

      expect(screen.getByText('No Active Game')).toBeInTheDocument();
      expect(screen.getByText('Start New Game')).toBeInTheDocument();
    });
  });
});