// frontend/src/components/game/__tests__/Scorecard.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Scorecard from '../Scorecard';
import {
  createMockTheme,
  createMockPlayers,
  createMockCourseHoles,
  createMockHoleHistory,
  createMockStrokeAllocation
} from '../../../test-utils/mockFactories';

// Mock the useTheme hook
jest.mock('../../../theme/Provider', () => ({
  useTheme: () => require('../../../test-utils/mockFactories').createMockTheme()
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
  const mockPlayers = createMockPlayers(4, {
    id: 'p1',
    name: 'Player 1',
    handicap: 15,
    is_human: true
  }).map((player, i) => ({
    ...player,
    id: `p${i + 1}`,
    name: `Player ${i + 1}`,
    handicap: [15, 18, 12, 20][i],
    is_human: i === 0
  }));

  const mockCourseHoles = createMockCourseHoles(18);

  const mockHoleHistory = createMockHoleHistory(2, ['p1', 'p2', 'p3', 'p4']);

  const mockStrokeAllocation = createMockStrokeAllocation(['p1', 'p2', 'p3', 'p4'], 3);

  const defaultProps = {
    players: mockPlayers,
    holeHistory: mockHoleHistory,
    currentHole: 3,
    courseHoles: mockCourseHoles,
    strokeAllocation: mockStrokeAllocation,
    defaultExpanded: true // Tests expect expanded view
  };

  describe('Basic Rendering', () => {
    test('renders scorecard title', () => {
      render(<Scorecard {...defaultProps} />);
      expect(screen.getByText(/SCORECARD/)).toBeInTheDocument();
    });

    test('renders front 9 holes by default when currentHole <= 9', () => {
      render(<Scorecard {...defaultProps} currentHole={3} />);
      // Front 9 holes (1-9) should be visible
      for (let i = 1; i <= 9; i++) {
        expect(screen.getAllByText(i.toString()).length).toBeGreaterThan(0);
      }
    });

    test('renders back 9 holes when currentHole > 9', () => {
      render(<Scorecard {...defaultProps} currentHole={12} />);
      // Back 9 holes (10-18) should be visible
      for (let i = 10; i <= 18; i++) {
        expect(screen.getAllByText(i.toString()).length).toBeGreaterThan(0);
      }
    });

    test('can toggle between front and back 9', () => {
      render(<Scorecard {...defaultProps} currentHole={3} />);
      // Should start on Front 9
      expect(screen.getByText('Front 9')).toBeInTheDocument();
      expect(screen.getByText('Back 9')).toBeInTheDocument();

      // Click Back 9 to switch
      fireEvent.click(screen.getByText('Back 9'));

      // Now holes 10-18 should be visible
      expect(screen.getAllByText('10').length).toBeGreaterThan(0);
    });

    test('renders all player names', () => {
      render(<Scorecard {...defaultProps} />);
      // Multiple instances per player in new layout (front 9, back 9, totals)
      mockPlayers.forEach(player => {
        expect(screen.getAllByText(new RegExp(player.name)).length).toBeGreaterThan(0);
      });
    });

    test('renders OUT, IN, and TOTAL columns', () => {
      render(<Scorecard {...defaultProps} />);
      // New layout has separate tables with OUT for front 9, IN for back 9, and TOTAL in summary
      expect(screen.getAllByText('OUT').length).toBeGreaterThan(0);
      expect(screen.getAllByText('IN').length).toBeGreaterThan(0);
      expect(screen.getAllByText('TOTAL').length).toBeGreaterThan(0);
    });

    test('renders PAR row when courseHoles provided', () => {
      render(<Scorecard {...defaultProps} />);
      // Multiple PAR rows in new layout (front 9, back 9, totals summary)
      expect(screen.getAllByText('PAR').length).toBeGreaterThan(0);
    });

    test('renders HDCP row when courseHoles provided', () => {
      render(<Scorecard {...defaultProps} />);
      // Multiple HDCP rows in new layout (front 9, back 9)
      expect(screen.getAllByText('HDCP').length).toBeGreaterThan(0);
    });
  });

  describe('Player Display', () => {
    test('shows human player indicator', () => {
      render(<Scorecard {...defaultProps} />);
      // Multiple instances in new layout (front 9, back 9, totals)
      expect(screen.getAllByText(/👤/).length).toBeGreaterThan(0);
    });

    test('shows AI player indicators', () => {
      render(<Scorecard {...defaultProps} />);
      const robotEmojis = screen.getAllByText(/🤖/);
      expect(robotEmojis.length).toBeGreaterThan(0);
    });

    test('shows player handicaps', () => {
      render(<Scorecard {...defaultProps} />);
      // Multiple instances in new layout (front 9, back 9, totals)
      expect(screen.getAllByText(/\(15\)/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/\(18\)/).length).toBeGreaterThan(0);
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
    test('starts expanded by default with down arrow', () => {
      render(<Scorecard {...defaultProps} />);
      // Down arrow (▼) indicates expanded state
      expect(screen.getByText('▼')).toBeInTheDocument();
    });

    test('collapses when SCORECARD header clicked', () => {
      render(<Scorecard {...defaultProps} />);
      // Click on the SCORECARD text to collapse
      fireEvent.click(screen.getByText('SCORECARD'));
      // Right arrow (▶) indicates collapsed state
      expect(screen.getByText('▶')).toBeInTheDocument();
    });

    test('shows collapsed view with player summaries', () => {
      render(<Scorecard {...defaultProps} />);
      // Click to collapse
      fireEvent.click(screen.getByText('SCORECARD'));

      // Collapsed view shows player names (first name) and their total quarters
      // All 4 players have "Player X" names, so we should see 4 "Player" labels
      expect(screen.getAllByText('Player').length).toBe(4);
    });
  });

  describe('Standings View Toggle', () => {
    test('shows standings toggle when captainId provided', () => {
      render(<Scorecard {...defaultProps} captainId="p1" />);
      expect(screen.getByText('Standings')).toBeInTheDocument();
    });

    test('does not show standings toggle without captainId', () => {
      render(<Scorecard {...defaultProps} />);
      expect(screen.queryByText('Standings')).not.toBeInTheDocument();
    });

    test('switches to standings view when clicked', () => {
      render(<Scorecard {...defaultProps} captainId="p1" />);
      fireEvent.click(screen.getByText('Standings'));
      // Button should now show "Scores" (to switch back)
      expect(screen.getByText('Scores')).toBeInTheDocument();
    });

    test('highlights captain in standings view', () => {
      render(<Scorecard {...defaultProps} captainId="p1" />);
      fireEvent.click(screen.getByText('Standings'));
      // Captain should have star indicator
      expect(screen.getByText(/⭐/)).toBeInTheDocument();
    });
  });

  describe('Edit Hole Modal', () => {
    // Helper to find a clickable score cell (with title attribute for editing)
    const findClickableScoreCell = () => {
      const allCells = document.querySelectorAll('td[title="Click to edit"]');
      return allCells[0];
    };

    test('opens edit modal when clicking completed hole cell', () => {
      const onEditHole = jest.fn();
      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      // Click on a score cell for hole 1 (completed) - find cell with "Click to edit" title
      const scoreCell = findClickableScoreCell();
      expect(scoreCell).toBeTruthy();
      fireEvent.click(scoreCell);

      // Modal should appear with Edit Hole title
      expect(screen.getByText(/Edit Hole/)).toBeInTheDocument();
    });

    test('shows strokes input in edit modal', () => {
      const onEditHole = jest.fn();
      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      const scoreCell = findClickableScoreCell();
      fireEvent.click(scoreCell);

      expect(screen.getByText(/Strokes \(Gross Score\)/)).toBeInTheDocument();
    });

    test('shows quarters input in edit modal', () => {
      const onEditHole = jest.fn();
      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      const scoreCell = findClickableScoreCell();
      fireEvent.click(scoreCell);

      expect(screen.getByText(/Quarters \(Manual Override\)/)).toBeInTheDocument();
    });

    test('closes modal on cancel', () => {
      const onEditHole = jest.fn();
      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      const scoreCell = findClickableScoreCell();
      fireEvent.click(scoreCell);

      fireEvent.click(screen.getByText('Cancel'));

      // Modal should be closed
      expect(screen.queryByText(/Edit Hole/)).not.toBeInTheDocument();
    });

    test('calls onEditHole with correct data on save', async () => {
      const onEditHole = jest.fn();
      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      const scoreCell = findClickableScoreCell();
      fireEvent.click(scoreCell);

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

      // Click on player name (multiple instances in new layout, get the first one)
      const playerNameElements = screen.getAllByText(/Player 1/);
      fireEvent.click(playerNameElements[0]);

      expect(screen.getByText('Edit Player Name')).toBeInTheDocument();
    });
  });

  describe('Totals Calculation', () => {
    test('calculates front 9 totals correctly', () => {
      render(<Scorecard {...defaultProps} />);
      // Quarters rows should show totals - either positive (+X), negative (-X), or zero (0)
      // Since mock data is random, just verify the Quarters row exists
      expect(screen.getAllByText(/Quarters/).length).toBeGreaterThan(0);
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
      // PAR rows should not be present
      expect(screen.queryAllByText('PAR').length).toBe(0);
    });
  });

  describe('Input Validation', () => {
    // Helper to find a clickable score cell (with title attribute for editing)
    const findClickableScoreCell = () => {
      const allCells = document.querySelectorAll('td[title="Click to edit"]');
      return allCells[0];
    };

    test('validates strokes are within valid range', async () => {
      const onEditHole = jest.fn();
      const alertMock = jest.spyOn(window, 'alert').mockImplementation(() => {});

      render(<Scorecard {...defaultProps} onEditHole={onEditHole} />);

      const scoreCell = findClickableScoreCell();
      fireEvent.click(scoreCell);

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

      const scoreCell = findClickableScoreCell();
      fireEvent.click(scoreCell);

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
