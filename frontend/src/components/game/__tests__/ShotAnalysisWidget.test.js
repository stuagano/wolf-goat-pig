import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ShotAnalysisWidget from '../ShotAnalysisWidget';

// Mock the useTheme hook
jest.mock('../../../theme/Provider', () => ({
  useTheme: () => ({
    colors: {
      primary: '#2196F3',
      success: '#4CAF50',
      error: '#f44336',
      textPrimary: '#333',
      textSecondary: '#666',
      border: '#e0e0e0',
      paper: '#ffffff',
      background: '#fafafa'
    },
    spacing: {
      1: '4px',
      2: '8px',
      4: '16px',
      6: '24px'
    },
    typography: {
      bold: '700',
      '3xl': '1.875rem'
    }
  })
}));

// Mock the useShotAnalysis hook
const mockAnalyzeShot = jest.fn();
jest.mock('../../../hooks', () => ({
  useShotAnalysis: () => ({
    analysis: null,
    loading: false,
    error: null,
    analyzeShot: mockAnalyzeShot
  })
}));

// Mock UI components
jest.mock('../../ui', () => ({
  Button: ({ children, onClick, disabled }) => (
    <button onClick={onClick} disabled={disabled}>{children}</button>
  ),
  Card: ({ children }) => <div>{children}</div>,
  Input: ({ label, value, onChange, name, type }) => (
    <div>
      <label htmlFor={name}>{label}</label>
      <input id={name} type={type} name={name} value={value} onChange={onChange} />
    </div>
  ),
  Select: ({ label, value, onChange, name, options }) => (
    <div>
      <label htmlFor={name}>{label}</label>
      <select id={name} name={name} value={value} onChange={onChange}>
        {options.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
      </select>
    </div>
  )
}));

describe('ShotAnalysisWidget', () => {
  const defaultProps = {
    holeNumber: 1,
    players: [
      { id: 'p1', name: 'Player 1', handicap: 10 },
      { id: 'p2', name: 'Player 2', handicap: 15 }
    ],
    captainId: 'p1',
    teamMode: 'solo',
    playerStandings: {
      'p1': { quarters: 5 },
      'p2': { quarters: -5 }
    }
  };

  beforeEach(() => {
    mockAnalyzeShot.mockClear();
  });

  it('renders correctly', () => {
    render(<ShotAnalysisWidget {...defaultProps} />);
    expect(screen.getByText('🎯 Strategic Shot Analysis')).toBeInTheDocument();
    expect(screen.getByText('Analyze')).toBeInTheDocument();
  });

  it('calls analyzeShot with correct data when Analyze is clicked', () => {
    render(<ShotAnalysisWidget {...defaultProps} />);
    
    fireEvent.click(screen.getByText('Analyze'));
    
    expect(mockAnalyzeShot).toHaveBeenCalledWith(expect.objectContaining({
      hole_number: 1,
      player_handicap: 10,
      team_situation: 'solo',
      score_differential: 5
    }));
  });

  it('updates form data when inputs change', () => {
    render(<ShotAnalysisWidget {...defaultProps} />);
    
    const distanceInput = screen.getByLabelText('Distance');
    fireEvent.change(distanceInput, { target: { value: '200' } });
    
    fireEvent.click(screen.getByText('Analyze'));
    
    expect(mockAnalyzeShot).toHaveBeenCalledWith(expect.objectContaining({
      distance_to_pin: 200
    }));
  });

  it('displays analysis results when available', () => {
    const mockAnalysis = {
      recommended_shot: {
        type: 'standard_approach',
        success_rate: '65.0%',
        risk_level: '40%',
        expected_value: 0.2
      },
      player_style: {
        profile: 'tag',
        description: 'Tight aggressive'
      },
      gto_recommendation: {
        type: 'safe_approach'
      },
      strategic_advice: ['Play it safe']
    };

    // Re-mock hook for this test
    require('../../../hooks').useShotAnalysis = () => ({
      analysis: mockAnalysis,
      loading: false,
      error: null,
      analyzeShot: mockAnalyzeShot
    });

    render(<ShotAnalysisWidget {...defaultProps} />);
    
    expect(screen.getByText('STANDARD APPROACH')).toBeInTheDocument();
    expect(screen.getByText(/Risk: 40%/)).toBeInTheDocument();
    expect(screen.getByText(/Success Rate: 65.0%/)).toBeInTheDocument();
    expect(screen.getByText(/Play it safe/)).toBeInTheDocument();
  });
});
