import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeProvider } from '../../theme/Provider';
import EnhancedBettingWidget from '../EnhancedBettingWidget';
import EnhancedScoringWidget from '../EnhancedScoringWidget';
import InteractivePlayerCard from '../InteractivePlayerCard';

// Mock data for testing
const mockGameState = {
  players: [
    { id: '1', name: 'Player 1', handicap: 10, points: 5 },
    { id: '2', name: 'Player 2', handicap: 15, points: -2 }
  ],
  current_hole: 1,
  base_wager: 1,
  holeState: {
    hole_par: 4,
    stroke_index: 3,
    ball_positions: {
      '1': { distance_to_pin: 150, shot_count: 2, final_score: null },
      '2': { distance_to_pin: 200, shot_count: 1, final_score: null }
    },
    stroke_advantages: {
      '1': { strokes_received: 0 },
      '2': { strokes_received: 1 }
    },
    teams: { type: 'pending' }
  }
};

const mockBettingOpportunity = {
  message: "Test betting opportunity",
  options: ['offer_double', 'pass'],
  risk_assessment: 'medium',
  recommended_action: 'pass',
  probability_analysis: {
    win_probability: 0.65,
    expected_value: 0.8
  },
  reasoning: "Test reasoning"
};

const mockHoleState = {
  hole_par: 4,
  stroke_index: 3,
  ball_positions: {
    '1': { distance_to_pin: 150, shot_count: 2, final_score: null }
  },
  stroke_advantages: {
    '1': { strokes_received: 0 }
  },
  teams: { type: 'pending' }
};

const mockPlayer = {
  id: '1',
  name: 'Test Player',
  handicap: 12,
  points: 3
};

// Wrapper component with theme provider
const TestWrapper = ({ children }) => (
  <ThemeProvider>
    {children}
  </ThemeProvider>
);

describe('New Enhanced Components', () => {
  describe('EnhancedBettingWidget', () => {
    it('renders without crashing when no betting opportunity', () => {
      render(
        <TestWrapper>
          <EnhancedBettingWidget 
            gameState={mockGameState}
            bettingOpportunity={null}
            onBettingAction={jest.fn()}
          />
        </TestWrapper>
      );
      
      expect(screen.getByText('Waiting for Betting Opportunity')).toBeInTheDocument();
    });

    it('renders betting opportunity correctly', () => {
      render(
        <TestWrapper>
          <EnhancedBettingWidget 
            gameState={mockGameState}
            bettingOpportunity={mockBettingOpportunity}
            onBettingAction={jest.fn()}
          />
        </TestWrapper>
      );
      
      expect(screen.getByText('Betting Decision')).toBeInTheDocument();
      expect(screen.getByText('Test betting opportunity')).toBeInTheDocument();
    });

    it('displays risk assessment', () => {
      render(
        <TestWrapper>
          <EnhancedBettingWidget 
            gameState={mockGameState}
            bettingOpportunity={mockBettingOpportunity}
            onBettingAction={jest.fn()}
          />
        </TestWrapper>
      );
      
      expect(screen.getByText(/medium/i)).toBeInTheDocument();
    });
  });

  describe('EnhancedScoringWidget', () => {
    it('renders without crashing', () => {
      render(
        <TestWrapper>
          <EnhancedScoringWidget 
            gameState={mockGameState}
            holeState={mockHoleState}
            onScoreUpdate={jest.fn()}
            onAction={jest.fn()}
          />
        </TestWrapper>
      );
      
      expect(screen.getByText(/Hole 1 Scoring/)).toBeInTheDocument();
    });

    it('displays hole information', () => {
      render(
        <TestWrapper>
          <EnhancedScoringWidget 
            gameState={mockGameState}
            holeState={mockHoleState}
            onScoreUpdate={jest.fn()}
            onAction={jest.fn()}
          />
        </TestWrapper>
      );
      
      expect(screen.getByText(/Par 4/)).toBeInTheDocument();
    });

    it('displays players', () => {
      render(
        <TestWrapper>
          <EnhancedScoringWidget 
            gameState={mockGameState}
            holeState={mockHoleState}
            onScoreUpdate={jest.fn()}
            onAction={jest.fn()}
          />
        </TestWrapper>
      );
      
      expect(screen.getByText('Player 1')).toBeInTheDocument();
      expect(screen.getByText('Player 2')).toBeInTheDocument();
    });
  });

  describe('InteractivePlayerCard', () => {
    it('renders without crashing', () => {
      render(
        <TestWrapper>
          <InteractivePlayerCard 
            player={mockPlayer}
            gameState={mockGameState}
            holeState={mockHoleState}
          />
        </TestWrapper>
      );
      
      expect(screen.getByText('Test Player')).toBeInTheDocument();
    });

    it('displays player handicap and points', () => {
      render(
        <TestWrapper>
          <InteractivePlayerCard 
            player={mockPlayer}
            gameState={mockGameState}
            holeState={mockHoleState}
          />
        </TestWrapper>
      );
      
      expect(screen.getByText('Handicap 12')).toBeInTheDocument();
      expect(screen.getByText('+3 pts')).toBeInTheDocument();
    });

    it('shows click indicator when not expanded', () => {
      render(
        <TestWrapper>
          <InteractivePlayerCard 
            player={mockPlayer}
            gameState={mockGameState}
            holeState={mockHoleState}
            expanded={false}
          />
        </TestWrapper>
      );
      
      expect(screen.getByText('Click for details')).toBeInTheDocument();
    });
  });
});