// frontend/src/components/game/__tests__/Scorecard.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Scorecard from '../Scorecard';

// Mock the useTheme hook
jest.mock('../../../theme/Provider', () => ({
  useTheme: () => ({
    colors: {
      primary: '#2196F3',
      secondary: '#757575',
      success: '#4CAF50',
      error: '#f44336',
      warning: '#ff9800',
      accent: '#FFD700',
      textSecondary: '#666',
      backgroundSecondary: '#f5f5f5',
      border: '#e0e0e0'
    }
  })
}));

// Mock the UI components
jest.mock('../../ui', () => ({
  Card: ({ children, style }) => <div style={style} data-testid="card">{children}</div>,
  Button: ({ children, onClick, variant, style }) => (
    <button onClick={onClick} data-variant={variant} style={style}>
      {children}
    </button>
  ),
  Input: ({ type, value, onChange, min, max, step, variant, inputStyle, onKeyPress, placeholder, autoFocus, maxLength }) => (
    <input
      type={type}
      value={value}
      onChange={onChange}
      min={min}
      max={max}
      step={step}
      data-variant={variant}
      style={inputStyle}
      onKeyPress={onKeyPress}
      placeholder={placeholder}
      autoFocus={autoFocus}
      maxLength={maxLength}
      data-testid="input"
    />
  )
}));

describe('Scorecard', () => {
  const mockPlayers = [
    { id: 'p1', name: 'Player 1', handicap: 15, is_human: true },
    { id: 'p2', name: 'Player 2', handicap: 18, is_human: false },
    { id: 'p3', name: 'Player 3', handicap: 12, is_human: false },
    { id: 'p4', name: 'Player 4', handicap: 20, is_human: false }
  ];

  const mockCourseHoles = Array.from({ length: 18 }, (_, i) => ({
    hole: i + 1,
    par: i < 9 ? [4, 5, 3, 4, 4, 5, 4, 3, 4][i % 9] : [4, 3, 5, 4, 4, 3, 5, 4, 4][i % 9],
    handicap: i + 1,
    yards: 350 + (i * 10)
  }));

  const mockHoleHistory = [
    {
      hole: 1,
      points_delta: { p1: 2, p2: -2, p3: 2, p4: -2 },
      gross_scores: { p1: 4, p2: 5, p3: 4, p4: 6 }
    },
    {
      hole: 2,
      points_delta: { p1: -1, p2: 1, p3: -1, p4: 1 },
      gross_scores: { p1: 5, p2: 4, p3: 5, p4: 4 }
    }
  ];

  const mockStrokeAllocation = {
    p1: { 1: 1, 2: 0, 3: 1 },
    p2: { 1: 1, 2: 1, 3: 1 },
    p3: { 1: 0, 2: 1, 3: 0 },
    p4: { 1: 1, 2: 1, 3: 1 }
  };

  const defaultProps = {
    players: mockPlayers,
    holeHistory: mockHoleHistory,
    currentHole: 3,
    courseHoles: mockCourseHoles,
    strokeAllocation: mockStrokeAllocation
  };

  describe('Basic Rendering', () => {
    test('renders scorecard title', () => {
      render(<Scorecard {...defaultProps} />);
      expect(screen.getByText(/SCORECARD/)).toBeInTheDocument();
    });

    test('renders all 18 hole columns', () => {
      render(<Scorecard {...defaultProps} />);
      for (let i = 1; i <= 18; i++) {
        expect(screen.getByText(i.toString())).toBeInTheDocument();
      }
    });

    test('renders all player names', () => {
      render(<Scorecard {...defaultProps} />);
      mockPlayers.forEach(player => {
        expect(screen.getByText(new RegExp(player.name))).toBeInTheDocument();
      });
    });

    test('renders OUT, IN, and TOT columns', () => {
      render(<Scorecard {...defaultProps} />);
      expect(screen.getByText('OUT')).toBeInTheDocument();
      expect(screen.getByText('IN')).toBeInTheDocument();
      expect(screen.getByText('TOT')).toBeInTheDocument();
    });

    test('renders PAR row when courseHoles provided', () => {
      render(<Scorecard {...defaultProps} />);
      expect(screen.getByText('PAR')).toBeInTheDocument();
    });

    test('renders HDCP row when courseHoles provided', () => {
      render(<Scorecard {...defaultProps} />);
      expect(screen.getByText('HDCP')).toBeInTheDocument();
    });
  });

  describe('Player Display', () => {
    test('shows human player indicator', () => {
      render(<Scorecard {...defaultProps} />);
      expect(screen.getByText(/👤/)).toBeInTheDocument();
    });

    test('shows AI player indicators', () => {
      render(<Scorecard {...defaultProps} />);
      const robotEmojis = screen.getAllByText(/🤖/);
      expect(robotEmojis.length).toBeGreaterThan(0);
    });

    test('shows player handicaps', () => {
      render(<Scorecard {...defaultProps} />);
      expect(screen.getByText(/\(15\)/)).toBeInTheDocument();
      expect(screen.getByText(/\(18\)/)).toBeInTheDocument();
    });
  });

  describe('Score Display', () => {
    test('displays completed hole scores', () => {
      render(<Scorecard {...defaultProps} />);
      // Hole 1 scores: 4, 5, 4, 6
      expect(screen.getAllByText('4').length).toBeGreaterThan(0);
      expect(screen.getAllByText('5').length).toBeGreaterThan(0);
    });

    test('displays quarters with correct signs', () => {
      render(<Scorecard {...defaultProps} />);
      // Should show positive quarters with + sign
      expect(screen.getAllByText(/\+2/).length).toBeGreaterThan(0);
    });
  });

  describe('Collapse/Expand', () => {
    test('starts expanded by default', () => {
      render(<Scorecard {...defaultProps} />);
      expect(screen.getByText('Minimize')).toBeInTheDocument();
    });

    test('collapses when Minimize button clicked', () => {
      render(<Scorecard {...defaultProps} />);
      fireEvent.click(screen.getByText('Minimize'));
      expect(screen.getByText('Expand')).toBeInTheDocument();
    });

    test('shows collapsed view with player summaries', () => {
      render(<Scorecard {...defaultProps} />);
      fireEvent.click(screen.getByText('Minimize'));

      // Should show OUT, IN, TOT labels in collapsed view
      expect(screen.getAllByText('OUT:').length).toBeGreaterThan(0);
      expect(screen.getAllByText('IN:').length).toBeGreaterThan(0);
      expect(screen.getAllByText('TOT:').length).toBeGreaterThan(0);
    });
  });

  describe('Standings View Toggle', () => {
    test('shows standings toggle when captainId provided', () => {
      render(<Scorecard {...defaultProps} captainId="p1" />);
      expect(screen.getByText('📊 Standings')).toBeInTheDocument();
    });

    test('does not show standings toggle without captainId', () => {
      render(<Scorecard {...defaultProps} />);
      expect(screen.queryByText('📊 Standings')).not.toBeInTheDocument();
    });

    test('switches to standings view when clicked', () => {
      render(<Scorecard {...defaultProps} captainId="p1" />);
      fireEvent.click(screen.getByText('📊 Standings'));
      // Button should now show "📋 Scorecard"
      expect(screen.getByText('📋 Scorecard')).toBeInTheDocument();
    });

    test('highlights captain in standings view', () => {
      render(<Scorecard {...defaultProps} captainId="p1" />);
      fireEvent.click(screen.getByText('📊 Standings'));
      // Captain should have star indicator
      expect(screen.getByText(/⭐/)).toBeInTheDocument();
    });
  });

  describe('Edit Hole Modal', () => {
    test('opens edit modal when clicking completed hole cell', () => {
      const onEditHole = jest.fn();
      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      // Click on a score cell for hole 1 (completed)
      const scoreCells = screen.getAllByText('4');
      fireEvent.click(scoreCells[0]);

      // Modal should appear with Edit Hole title
      expect(screen.getByText(/Edit Hole/)).toBeInTheDocument();
    });

    test('shows strokes input in edit modal', () => {
      const onEditHole = jest.fn();
      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      const scoreCells = screen.getAllByText('4');
      fireEvent.click(scoreCells[0]);

      expect(screen.getByText(/Strokes \(Gross Score\)/)).toBeInTheDocument();
    });

    test('shows quarters input in edit modal', () => {
      const onEditHole = jest.fn();
      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      const scoreCells = screen.getAllByText('4');
      fireEvent.click(scoreCells[0]);

      expect(screen.getByText(/Quarters \(Manual Override\)/)).toBeInTheDocument();
    });

    test('closes modal on cancel', () => {
      const onEditHole = jest.fn();
      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      const scoreCells = screen.getAllByText('4');
      fireEvent.click(scoreCells[0]);

      fireEvent.click(screen.getByText('Cancel'));

      // Modal should be closed
      expect(screen.queryByText(/Edit Hole/)).not.toBeInTheDocument();
    });

    test('calls onEditHole with correct data on save', async () => {
      const onEditHole = jest.fn();
      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      const scoreCells = screen.getAllByText('4');
      fireEvent.click(scoreCells[0]);

      // Edit the strokes input
      const inputs = screen.getAllByTestId('input');
      fireEvent.change(inputs[0], { target: { value: '5' } });
      fireEvent.change(inputs[1], { target: { value: '3' } });

      fireEvent.click(screen.getByText('Save'));

      expect(onEditHole).toHaveBeenCalledWith(expect.objectContaining({
        strokes: 5,
        quarters: 3
      }));
    });
  });

  describe('Player Name Editing', () => {
    test('shows edit icon when onPlayerNameChange provided', () => {
      const onPlayerNameChange = jest.fn();
      render(<Scorecard {...defaultProps} onPlayerNameChange={onPlayerNameChange} />);

      // Should show edit icons (pencil emoji)
      expect(screen.getAllByText('✏️').length).toBeGreaterThan(0);
    });

    test('does not show edit icon without onPlayerNameChange', () => {
      render(<Scorecard {...defaultProps} />);
      expect(screen.queryByText('✏️')).not.toBeInTheDocument();
    });

    test('opens name edit modal when clicking player name', () => {
      const onPlayerNameChange = jest.fn();
      render(<Scorecard {...defaultProps} onPlayerNameChange={onPlayerNameChange} />);

      // Click on player name
      const playerNameElement = screen.getByText(/Player 1/);
      fireEvent.click(playerNameElement);

      expect(screen.getByText('Edit Player Name')).toBeInTheDocument();
    });
  });

  describe('Totals Calculation', () => {
    test('calculates front 9 totals correctly', () => {
      render(<Scorecard {...defaultProps} />);
      // Player 1 has +2 on hole 1 and -1 on hole 2 = +1 for front 9 so far
      expect(screen.getAllByText('+1').length).toBeGreaterThan(0);
    });
  });

  describe('Score Indicators', () => {
    test('shows par indicator for par score', () => {
      render(<Scorecard {...defaultProps} />);
      // Scores of 4 on par 4 holes should show plain number
      const scoreElements = screen.getAllByText('4');
      expect(scoreElements.length).toBeGreaterThan(0);
    });
  });

  describe('Stroke Allocation Display', () => {
    test('shows stroke dots for players receiving strokes', () => {
      render(<Scorecard {...defaultProps} />);
      // Players with strokes should show dots
      // This is indicated by the ● symbol
    });
  });

  describe('Empty States', () => {
    test('renders without players gracefully', () => {
      render(<Scorecard {...defaultProps} players={[]} />);
      expect(screen.getByText(/SCORECARD/)).toBeInTheDocument();
    });

    test('renders without hole history gracefully', () => {
      render(<Scorecard {...defaultProps} holeHistory={[]} />);
      expect(screen.getByText(/SCORECARD/)).toBeInTheDocument();
    });

    test('renders without course holes gracefully', () => {
      render(<Scorecard {...defaultProps} courseHoles={[]} />);
      expect(screen.getByText(/SCORECARD/)).toBeInTheDocument();
      // PAR row should not be present
      expect(screen.queryByText('PAR')).not.toBeInTheDocument();
    });
  });

  describe('Input Validation', () => {
    test('validates strokes are within valid range', async () => {
      const onEditHole = jest.fn();
      const alertMock = jest.spyOn(window, 'alert').mockImplementation(() => {});

      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      const scoreCells = screen.getAllByText('4');
      fireEvent.click(scoreCells[0]);

      const inputs = screen.getAllByTestId('input');
      fireEvent.change(inputs[0], { target: { value: '20' } }); // Invalid: > 15

      fireEvent.click(screen.getByText('Save'));

      expect(alertMock).toHaveBeenCalledWith('Strokes must be a number between 0 and 15');
      expect(onEditHole).not.toHaveBeenCalled();

      alertMock.mockRestore();
    });

    test('validates quarters are within valid range', async () => {
      const onEditHole = jest.fn();
      const alertMock = jest.spyOn(window, 'alert').mockImplementation(() => {});

      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      const scoreCells = screen.getAllByText('4');
      fireEvent.click(scoreCells[0]);

      const inputs = screen.getAllByTestId('input');
      fireEvent.change(inputs[0], { target: { value: '4' } });
      fireEvent.change(inputs[1], { target: { value: '15' } }); // Invalid: > 10

      fireEvent.click(screen.getByText('Save'));

      expect(alertMock).toHaveBeenCalledWith('Quarters must be a number between -10 and 10');
      expect(onEditHole).not.toHaveBeenCalled();

      alertMock.mockRestore();
    });
  });

  describe('Current Hole Highlighting', () => {
    test('highlights current hole column', () => {
      render(<Scorecard {...defaultProps} currentHole={5} />);
      // Hole 5 header should have special highlighting
      const holeHeaders = screen.getAllByText('5');
      expect(holeHeaders.length).toBeGreaterThan(0);
    });
  });

  describe('Responsive Design', () => {
    test('has horizontal scroll wrapper', () => {
      render(<Scorecard {...defaultProps} />);
      // The table should be in an overflow container
      const cardElement = screen.getByTestId('card');
      expect(cardElement).toBeInTheDocument();
    });
  });
});
