import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '../../theme/Provider';
import ShotVisualizationOverlay from '../ShotVisualizationOverlay';

const mockAnalysis = {
  recommended_shot: {
    type: 'conservative_approach',
    success_rate: '85%',
    risk_level: '25',
    equity_vs_field: '+0.5'
  },
  all_ranges: [
    {
      type: 'conservative_approach',
      success_rate: '85%',
      risk: '25',
      ev: '+0.3',
      equity: '+0.5'
    },
    {
      type: 'aggressive_approach',
      success_rate: '70%',
      risk: '45',
      ev: '+0.1',
      equity: '+0.2'
    }
  ]
};

const mockHoleState = {
  hole_distance: 400,
  ball_positions: {
    'p1': {
      distance_to_pin: 150,
      lie_type: 'fairway'
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
    {children}
  </ThemeProvider>
);

describe('ShotVisualizationOverlay', () => {
  test('renders without crashing when all props provided', () => {
    render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
        />
      </TestWrapper>
    );

    // Should render the hole visualization container
    expect(document.querySelector('svg')).toBeInTheDocument();
  });

  test('returns null when analysis is missing', () => {
    const { container } = render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={null}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
        />
      </TestWrapper>
    );

    expect(container.firstChild).toBeNull();
  });

  test('returns null when holeState is missing', () => {
    const { container } = render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={null}
          currentPlayer={mockCurrentPlayer}
        />
      </TestWrapper>
    );

    expect(container.firstChild).toBeNull();
  });

  test('returns null when currentPlayer is missing', () => {
    const { container } = render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={mockHoleState}
          currentPlayer={null}
        />
      </TestWrapper>
    );

    expect(container.firstChild).toBeNull();
  });

  test('returns null when ball position not found', () => {
    const holeStateWithoutBallPosition = {
      ...mockHoleState,
      ball_positions: {}
    };

    const { container } = render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={holeStateWithoutBallPosition}
          currentPlayer={mockCurrentPlayer}
        />
      </TestWrapper>
    );

    expect(container.firstChild).toBeNull();
  });

  test('displays legend with correct elements', () => {
    render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
        />
      </TestWrapper>
    );

    expect(screen.getByText('Legend')).toBeInTheDocument();
    expect(screen.getByText('Low Risk')).toBeInTheDocument();
    expect(screen.getByText('Medium Risk')).toBeInTheDocument();
    expect(screen.getByText('High Risk')).toBeInTheDocument();
    expect(screen.getByText('Optimal Path')).toBeInTheDocument();
  });

  test('displays shot recommendation overlay', () => {
    render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
        />
      </TestWrapper>
    );

    expect(screen.getByText('🎯 Recommended')).toBeInTheDocument();
    expect(screen.getAllByText('CONSERVATIVE APPROACH').length).toBeGreaterThan(0);
    expect(screen.getByText('Success: 85%')).toBeInTheDocument();
    expect(screen.getByText('Risk: 25')).toBeInTheDocument();
  });

  test('creates target zones based on analysis ranges', () => {
    render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          showTargetZones={true}
        />
      </TestWrapper>
    );

    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
    
    // Check for target zone circles
    const circles = svg.querySelectorAll('circle');
    expect(circles.length).toBeGreaterThan(0);
  });

  test('shows risk areas when enabled', () => {
    render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          showRiskAreas={true}
        />
      </TestWrapper>
    );

    expect(screen.getByText('WATER')).toBeInTheDocument();
    expect(screen.getByText('SAND')).toBeInTheDocument();
  });

  test('shows optimal path when enabled', () => {
    render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          showOptimalPath={true}
        />
      </TestWrapper>
    );

    const svg = document.querySelector('svg');
    const paths = svg.querySelectorAll('path');
    expect(paths.length).toBeGreaterThan(0);
  });

  test('displays distance markers', () => {
    render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
        />
      </TestWrapper>
    );

    // Should show distance markers like "100y"
    expect(screen.getByText('100y')).toBeInTheDocument();
  });

  test('positions player and pin correctly', () => {
    render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
        />
      </TestWrapper>
    );

    expect(screen.getByText('YOU')).toBeInTheDocument();
    expect(screen.getByText('PIN')).toBeInTheDocument();
  });

  test('handles props for toggling different overlays', () => {
    const { rerender } = render(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          showTargetZones={false}
          showRiskAreas={false}
          showOptimalPath={false}
        />
      </TestWrapper>
    );

    // Verify legend still shows
    expect(screen.getByText('Legend')).toBeInTheDocument();

    rerender(
      <TestWrapper>
        <ShotVisualizationOverlay
          analysis={mockAnalysis}
          holeState={mockHoleState}
          currentPlayer={mockCurrentPlayer}
          showTargetZones={true}
          showRiskAreas={true}
          showOptimalPath={true}
        />
      </TestWrapper>
    );

    // All elements should be visible
    expect(screen.getByText('WATER')).toBeInTheDocument();
    expect(screen.getByText('SAND')).toBeInTheDocument();
  });
});
