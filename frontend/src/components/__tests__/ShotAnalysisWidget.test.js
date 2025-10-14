import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '../../theme/Provider';
import { GameProvider } from '../../context';
import ShotAnalysisWidget from '../ShotAnalysisWidget';

// Mock the API module
jest.mock('../../utils/api', () => {
  const mockUseApiCall = jest.fn(() => ({
    makeApiCall: jest.fn(),
    loading: false,
    error: null,
    isColdStart: false
  }));

  return {
    apiPost: jest.fn(),
    useApiCall: mockUseApiCall,
  };
});

const { useApiCall } = require('../../utils/api');

// Mock window.innerWidth for mobile testing
Object.defineProperty(window, 'innerWidth', {
  writable: true,
  configurable: true,
  value: 1024,
});

const mockGameState = {
  current_hole: 10,
  players: [
    { id: 'p1', name: 'John Doe', handicap: 10, points: 0 },
    { id: 'p2', name: 'Jane Smith', handicap: 15, points: 2 }
  ]
};

const mockHoleState = {
  hole_par: 4,
  hole_distance: 400,
  teams: { type: 'solo' },
  ball_positions: {
    'p1': {
      distance_to_pin: 150,
      lie_type: 'fairway',
      shot_count: 1
    }
  }
};

const mockCurrentPlayer = {
  id: 'p1',
  name: 'John Doe',
  handicap: 10
};

const TestWrapper = ({ children }) => (
  <ThemeProvider>
    <GameProvider>
      {children}
    </GameProvider>
  </ThemeProvider>
);

describe('ShotAnalysisWidget', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useApiCall.mockReturnValue({
      makeApiCall: jest.fn(),
      loading: false,
      error: null,
      isColdStart: false
    });
  });

  test('renders without crashing', () => {
    render(
      <TestWrapper>
        <ShotAnalysisWidget
          gameState={mockGameState}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          visible={true}
        />
      </TestWrapper>
    );

    expect(screen.getByText('🎯 Shot Analysis')).toBeInTheDocument();
  });

  test('does not render when not visible', () => {
    const { container } = render(
      <TestWrapper>
        <ShotAnalysisWidget
          gameState={mockGameState}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          visible={false}
        />
      </TestWrapper>
    );

    expect(container.firstChild).toBeNull();
  });

  test('displays current player information', () => {
    render(
      <TestWrapper>
        <ShotAnalysisWidget
          gameState={mockGameState}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          visible={true}
        />
      </TestWrapper>
    );

    expect(screen.getByText('John Doe (HC: 10)')).toBeInTheDocument();
    expect(screen.getByText('150 yards')).toBeInTheDocument();
    expect(screen.getByText('Fairway')).toBeInTheDocument();
  });

  test('toggles advanced view', () => {
    render(
      <TestWrapper>
        <ShotAnalysisWidget
          gameState={mockGameState}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          visible={true}
        />
      </TestWrapper>
    );

    const advancedButton = screen.getByText('Advanced View');
    fireEvent.click(advancedButton);

    expect(screen.getByText('Basic View')).toBeInTheDocument();
  });

  test('toggles auto-analyze option', () => {
    render(
      <TestWrapper>
        <ShotAnalysisWidget
          gameState={mockGameState}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          visible={true}
        />
      </TestWrapper>
    );

    const autoAnalyzeCheckbox = screen.getByRole('checkbox');
    expect(autoAnalyzeCheckbox).toBeChecked();

    fireEvent.click(autoAnalyzeCheckbox);
    expect(autoAnalyzeCheckbox).not.toBeChecked();
  });

  test('calls analysis function when button clicked', async () => {
    const { useApiCall } = require('../../utils/api');
    const mockMakeApiCall = jest.fn().mockResolvedValue({
      analysis: {
        recommended_shot: {
          type: 'conservative_approach',
          success_rate: '85%',
          risk_level: '25',
          equity_vs_field: '+0.5'
        },
        player_style: {
          profile: 'balanced',
          description: 'Plays safe when needed'
        }
      }
    });

    useApiCall.mockReturnValue({
      makeApiCall: mockMakeApiCall,
      loading: false,
      error: null,
      isColdStart: false
    });

    render(
      <TestWrapper>
        <ShotAnalysisWidget
          gameState={mockGameState}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          visible={true}
        />
      </TestWrapper>
    );

    const analyzeButton = screen.getByText('Analyze Shot');
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(mockMakeApiCall).toHaveBeenCalled();
    });
  });

  test('displays loading state', () => {
    const { useApiCall } = require('../../utils/api');
    useApiCall.mockReturnValue({
      makeApiCall: jest.fn(),
      loading: true,
      error: null,
      isColdStart: false
    });

    render(
      <TestWrapper>
        <ShotAnalysisWidget
          gameState={mockGameState}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          visible={true}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Analyzing shot options...')).toBeInTheDocument();
  });

  test('displays cold start state', () => {
    const { useApiCall } = require('../../utils/api');
    useApiCall.mockReturnValue({
      makeApiCall: jest.fn(),
      loading: true,
      error: null,
      isColdStart: true
    });

    render(
      <TestWrapper>
        <ShotAnalysisWidget
          gameState={mockGameState}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          visible={true}
        />
      </TestWrapper>
    );

    expect(screen.getByText(/Starting analysis service/)).toBeInTheDocument();
  });

  test('displays error state with retry button', () => {
    const { useApiCall } = require('../../utils/api');
    const mockMakeApiCall = jest.fn();
    useApiCall.mockReturnValue({
      makeApiCall: mockMakeApiCall,
      loading: false,
      error: 'Analysis failed',
      isColdStart: false
    });

    render(
      <TestWrapper>
        <ShotAnalysisWidget
          gameState={mockGameState}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          visible={true}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Analysis failed')).toBeInTheDocument();
    expect(screen.getByText('Retry Analysis')).toBeInTheDocument();

    const retryButton = screen.getByText('Retry Analysis');
    fireEvent.click(retryButton);

    expect(mockMakeApiCall).toHaveBeenCalled();
  });

  test('adapts to mobile screen size', () => {
    // Mock mobile screen size
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 600,
    });

    render(
      <TestWrapper>
        <ShotAnalysisWidget
          gameState={mockGameState}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          visible={true}
        />
      </TestWrapper>
    );

    // The component should still render on mobile
    expect(screen.getByText('🎯 Shot Analysis')).toBeInTheDocument();
  });

  test('calls onShotRecommendation callback when analysis completes', async () => {
    const { useApiCall } = require('../../utils/api');
    const mockOnShotRecommendation = jest.fn();
    const mockAnalysis = {
      analysis: {
        recommended_shot: {
          type: 'aggressive_approach',
          success_rate: '70%',
          risk_level: '45'
        }
      }
    };

    const mockMakeApiCall = jest.fn().mockResolvedValue(mockAnalysis);
    useApiCall.mockReturnValue({
      makeApiCall: mockMakeApiCall,
      loading: false,
      error: null,
      isColdStart: false
    });

    render(
      <TestWrapper>
        <ShotAnalysisWidget
          gameState={mockGameState}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          visible={true}
          onShotRecommendation={mockOnShotRecommendation}
        />
      </TestWrapper>
    );

    const analyzeButton = screen.getByText('Analyze Shot');
    fireEvent.click(analyzeButton);

    await waitFor(() => {
      expect(mockOnShotRecommendation).toHaveBeenCalledWith(
        mockAnalysis.analysis.recommended_shot
      );
    });
  });
});
