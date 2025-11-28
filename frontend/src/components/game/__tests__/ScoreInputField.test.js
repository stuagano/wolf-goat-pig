// frontend/src/components/game/__tests__/ScoreInputField.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ScoreInputField from '../ScoreInputField';

// Mock the useTheme hook
jest.mock('../../../theme/Provider', () => ({
  useTheme: () => ({
    colors: {
      primary: '#2196F3',
      success: '#4CAF50',
      error: '#f44336',
      textSecondary: '#666',
      border: '#e0e0e0',
      paper: '#ffffff',
      background: '#fafafa'
    }
  })
}));

// Mock the Input component
jest.mock('../../ui', () => ({
  Input: ({ type, value, onChange, disabled, min, max, placeholder, variant, inputStyle }) => (
    <input
      type={type}
      value={value}
      onChange={onChange}
      disabled={disabled}
      min={min}
      max={max}
      placeholder={placeholder}
      data-variant={variant}
      style={inputStyle}
      data-testid="score-input"
    />
  )
}));

// Mock the SCORE_CONSTRAINTS
jest.mock('../../../hooks/useScoreValidation', () => ({
  SCORE_CONSTRAINTS: {
    MIN_STROKES: 1,
    MAX_STROKES: 15
  }
}));

describe('ScoreInputField', () => {
  const mockPlayer = {
    id: 'player1',
    name: 'Test Player',
    handicap: 15
  };

  const mockOnChange = jest.fn();
  const mockOnClear = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
    mockOnClear.mockClear();
  });

  describe('Compact Mode', () => {
    const compactProps = {
      player: mockPlayer,
      value: 5,
      onChange: mockOnChange,
      compact: true
    };

    test('renders player name in compact mode', () => {
      render(<ScoreInputField {...compactProps} />);
      expect(screen.getByText('Test Player:')).toBeInTheDocument();
    });

    test('renders input with current value', () => {
      render(<ScoreInputField {...compactProps} />);
      const input = screen.getByTestId('score-input');
      expect(input).toHaveValue(5);
    });

    test('calls onChange when input changes', () => {
      render(<ScoreInputField {...compactProps} />);
      const input = screen.getByTestId('score-input');
      fireEvent.change(input, { target: { value: '6' } });
      expect(mockOnChange).toHaveBeenCalledWith('player1', 6);
    });

    test('shows error message when error prop provided', () => {
      render(<ScoreInputField {...compactProps} error="Invalid score" />);
      expect(screen.getByText('Invalid score')).toBeInTheDocument();
    });
  });

  describe('Full Mode (Default)', () => {
    const fullModeProps = {
      player: mockPlayer,
      value: '',
      onChange: mockOnChange
    };

    test('renders player name prominently', () => {
      render(<ScoreInputField {...fullModeProps} />);
      expect(screen.getByText('Test Player')).toBeInTheDocument();
    });

    test('shows player handicap', () => {
      render(<ScoreInputField {...fullModeProps} />);
      expect(screen.getByText(/Hdcp 15/)).toBeInTheDocument();
    });

    test('renders input field', () => {
      render(<ScoreInputField {...fullModeProps} />);
      const input = screen.getByTestId('score-input');
      expect(input).toBeInTheDocument();
    });

    test('does not show Clear button when no value', () => {
      render(<ScoreInputField {...fullModeProps} />);
      expect(screen.queryByText('Clear')).not.toBeInTheDocument();
    });

    test('shows Clear button when value is present', () => {
      render(<ScoreInputField {...fullModeProps} value={5} />);
      expect(screen.getByText('Clear')).toBeInTheDocument();
    });

    test('calls onClear when Clear button clicked', () => {
      render(<ScoreInputField {...fullModeProps} value={5} onClear={mockOnClear} />);
      fireEvent.click(screen.getByText('Clear'));
      expect(mockOnClear).toHaveBeenCalledWith('player1');
    });

    test('calls onChange with empty string when Clear clicked without onClear', () => {
      render(<ScoreInputField {...fullModeProps} value={5} />);
      fireEvent.click(screen.getByText('Clear'));
      expect(mockOnChange).toHaveBeenCalledWith('player1', '');
    });
  });

  describe('Quick Score Buttons', () => {
    const quickButtonProps = {
      player: mockPlayer,
      value: '',
      onChange: mockOnChange,
      holePar: 4,
      showQuickButtons: true
    };

    test('renders 5 quick score buttons when showQuickButtons is true', () => {
      render(<ScoreInputField {...quickButtonProps} />);
      // Par 4 hole: buttons for 2, 3, 4, 5, 6
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('6')).toBeInTheDocument();
    });

    test('shows score labels for quick buttons', () => {
      render(<ScoreInputField {...quickButtonProps} />);
      expect(screen.getByText('Eagle')).toBeInTheDocument(); // -2 from par
      expect(screen.getByText('Birdie')).toBeInTheDocument(); // -1 from par
      expect(screen.getByText('Par')).toBeInTheDocument(); // 0 from par
      expect(screen.getByText('Bogey')).toBeInTheDocument(); // +1 from par
      expect(screen.getByText('Double')).toBeInTheDocument(); // +2 from par
    });

    test('calls onChange when quick button clicked', () => {
      render(<ScoreInputField {...quickButtonProps} />);
      fireEvent.click(screen.getByText('4')); // Par
      expect(mockOnChange).toHaveBeenCalledWith('player1', 4);
    });

    test('highlights selected quick button', () => {
      render(<ScoreInputField {...quickButtonProps} value={4} />);
      const parButton = screen.getByText('4').closest('button');
      expect(parButton).toHaveStyle('font-weight: bold');
    });

    test('does not show quick buttons when showQuickButtons is false', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value=""
          onChange={mockOnChange}
          holePar={4}
          showQuickButtons={false}
        />
      );
      expect(screen.queryByText('Eagle')).not.toBeInTheDocument();
    });
  });

  describe('Score Confirmation Badge', () => {
    test('shows score badge when value is present', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value={4}
          onChange={mockOnChange}
          holePar={4}
        />
      );
      expect(screen.getByText(/Score: 4/)).toBeInTheDocument();
    });

    test('shows score label in badge when par is known', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value={3}
          onChange={mockOnChange}
          holePar={4}
        />
      );
      expect(screen.getByText(/Score: 3 \(Birdie\)/)).toBeInTheDocument();
    });

    test('does not show badge when no value', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value=""
          onChange={mockOnChange}
        />
      );
      expect(screen.queryByText(/Score:/)).not.toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    test('disables input when disabled prop is true', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value={5}
          onChange={mockOnChange}
          disabled={true}
        />
      );
      const input = screen.getByTestId('score-input');
      expect(input).toBeDisabled();
    });

    test('disables Clear button when disabled', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value={5}
          onChange={mockOnChange}
          disabled={true}
        />
      );
      const clearButton = screen.getByText('Clear');
      expect(clearButton).toBeDisabled();
    });

    test('disables quick buttons when disabled', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value=""
          onChange={mockOnChange}
          holePar={4}
          showQuickButtons={true}
          disabled={true}
        />
      );
      const parButton = screen.getByText('4').closest('button');
      expect(parButton).toBeDisabled();
    });
  });

  describe('Input Validation', () => {
    test('clears value when empty string entered', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value={5}
          onChange={mockOnChange}
        />
      );
      const input = screen.getByTestId('score-input');
      fireEvent.change(input, { target: { value: '' } });
      expect(mockOnChange).toHaveBeenCalledWith('player1', '');
    });

    test('accepts valid score value', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value=""
          onChange={mockOnChange}
        />
      );
      const input = screen.getByTestId('score-input');
      fireEvent.change(input, { target: { value: '5' } });
      expect(mockOnChange).toHaveBeenCalledWith('player1', 5);
    });

    test('does not accept score below minimum', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value=""
          onChange={mockOnChange}
        />
      );
      const input = screen.getByTestId('score-input');
      fireEvent.change(input, { target: { value: '0' } });
      // 0 is below MIN_STROKES (1), should not call onChange
      expect(mockOnChange).not.toHaveBeenCalled();
    });

    test('does not accept score above maximum', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value=""
          onChange={mockOnChange}
        />
      );
      const input = screen.getByTestId('score-input');
      fireEvent.change(input, { target: { value: '20' } });
      // 20 is above MAX_STROKES (15), should not call onChange
      expect(mockOnChange).not.toHaveBeenCalled();
    });
  });

  describe('Error Display', () => {
    test('shows error message in full mode', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value={5}
          onChange={mockOnChange}
          error="Score is required"
        />
      );
      expect(screen.getByText('Score is required')).toBeInTheDocument();
    });
  });

  describe('Score Style Calculations', () => {
    test('shows Albatross for -3 from par', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value={2}
          onChange={mockOnChange}
          holePar={5}
        />
      );
      expect(screen.getByText(/Albatross/)).toBeInTheDocument();
    });

    test('shows +3 label for triple bogey', () => {
      render(
        <ScoreInputField
          player={mockPlayer}
          value={7}
          onChange={mockOnChange}
          holePar={4}
        />
      );
      expect(screen.getByText(/\+3/)).toBeInTheDocument();
    });
  });

  describe('Player Without Handicap', () => {
    test('does not show handicap when not provided', () => {
      const playerWithoutHandicap = { id: 'p2', name: 'Player 2' };
      render(
        <ScoreInputField
          player={playerWithoutHandicap}
          value=""
          onChange={mockOnChange}
        />
      );
      expect(screen.queryByText(/Hdcp/)).not.toBeInTheDocument();
    });
  });
});
