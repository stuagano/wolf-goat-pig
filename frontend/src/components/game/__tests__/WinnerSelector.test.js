// frontend/src/components/game/__tests__/WinnerSelector.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import WinnerSelector from '../WinnerSelector';

// Mock the useTheme hook
jest.mock('../../../theme/Provider', () => ({
  useTheme: () => ({
    colors: {
      textSecondary: '#666',
      border: '#e0e0e0',
      paper: '#ffffff'
    }
  })
}));

describe('WinnerSelector', () => {
  const mockOnWinnerChange = jest.fn();

  beforeEach(() => {
    mockOnWinnerChange.mockClear();
  });

  describe('Partners Mode', () => {
    const partnersProps = {
      teamMode: 'partners',
      winner: null,
      onWinnerChange: mockOnWinnerChange
    };

    test('renders Winner title', () => {
      render(<WinnerSelector {...partnersProps} />);
      expect(screen.getByText('Winner')).toBeInTheDocument();
    });

    test('shows all partners mode options', () => {
      render(<WinnerSelector {...partnersProps} />);
      expect(screen.getByText('Team 1')).toBeInTheDocument();
      expect(screen.getByText('Team 2')).toBeInTheDocument();
      expect(screen.getByText('Push')).toBeInTheDocument();
      expect(screen.getByText('Team 1 Flush')).toBeInTheDocument();
      expect(screen.getByText('Team 2 Flush')).toBeInTheDocument();
    });

    test('calls onWinnerChange when Team 1 clicked', () => {
      render(<WinnerSelector {...partnersProps} />);
      fireEvent.click(screen.getByText('Team 1'));
      expect(mockOnWinnerChange).toHaveBeenCalledWith('team1');
    });

    test('calls onWinnerChange when Team 2 clicked', () => {
      render(<WinnerSelector {...partnersProps} />);
      fireEvent.click(screen.getByText('Team 2'));
      expect(mockOnWinnerChange).toHaveBeenCalledWith('team2');
    });

    test('calls onWinnerChange when Push clicked', () => {
      render(<WinnerSelector {...partnersProps} />);
      fireEvent.click(screen.getByText('Push'));
      expect(mockOnWinnerChange).toHaveBeenCalledWith('push');
    });

    test('calls onWinnerChange when Team 1 Flush clicked', () => {
      render(<WinnerSelector {...partnersProps} />);
      fireEvent.click(screen.getByText('Team 1 Flush'));
      expect(mockOnWinnerChange).toHaveBeenCalledWith('team1_flush');
    });

    test('calls onWinnerChange when Team 2 Flush clicked', () => {
      render(<WinnerSelector {...partnersProps} />);
      fireEvent.click(screen.getByText('Team 2 Flush'));
      expect(mockOnWinnerChange).toHaveBeenCalledWith('team2_flush');
    });

    test('highlights selected winner', () => {
      render(<WinnerSelector {...partnersProps} winner="team1" />);
      const team1Button = screen.getByText('Team 1');
      // Selected button should have border style indicating selection
      expect(team1Button).toHaveStyle('font-weight: bold');
    });
  });

  describe('Solo Mode', () => {
    const soloProps = {
      teamMode: 'solo',
      winner: null,
      onWinnerChange: mockOnWinnerChange
    };

    test('shows all solo mode options', () => {
      render(<WinnerSelector {...soloProps} />);
      expect(screen.getByText('Captain')).toBeInTheDocument();
      expect(screen.getByText('Opponents')).toBeInTheDocument();
      expect(screen.getByText('Push')).toBeInTheDocument();
      expect(screen.getByText('Captain Flush')).toBeInTheDocument();
      expect(screen.getByText('Opponents Flush')).toBeInTheDocument();
    });

    test('does not show team options in solo mode', () => {
      render(<WinnerSelector {...soloProps} />);
      expect(screen.queryByText('Team 1')).not.toBeInTheDocument();
      expect(screen.queryByText('Team 2')).not.toBeInTheDocument();
    });

    test('calls onWinnerChange when Captain clicked', () => {
      render(<WinnerSelector {...soloProps} />);
      fireEvent.click(screen.getByText('Captain'));
      expect(mockOnWinnerChange).toHaveBeenCalledWith('captain');
    });

    test('calls onWinnerChange when Opponents clicked', () => {
      render(<WinnerSelector {...soloProps} />);
      fireEvent.click(screen.getByText('Opponents'));
      expect(mockOnWinnerChange).toHaveBeenCalledWith('opponents');
    });

    test('calls onWinnerChange when Captain Flush clicked', () => {
      render(<WinnerSelector {...soloProps} />);
      fireEvent.click(screen.getByText('Captain Flush'));
      expect(mockOnWinnerChange).toHaveBeenCalledWith('captain_flush');
    });

    test('calls onWinnerChange when Opponents Flush clicked', () => {
      render(<WinnerSelector {...soloProps} />);
      fireEvent.click(screen.getByText('Opponents Flush'));
      expect(mockOnWinnerChange).toHaveBeenCalledWith('opponents_flush');
    });
  });

  describe('Disabled State', () => {
    const disabledProps = {
      teamMode: 'partners',
      winner: null,
      onWinnerChange: mockOnWinnerChange,
      disabled: true
    };

    test('does not call onWinnerChange when disabled', () => {
      render(<WinnerSelector {...disabledProps} />);
      fireEvent.click(screen.getByText('Team 1'));
      expect(mockOnWinnerChange).not.toHaveBeenCalled();
    });

    test('buttons are disabled', () => {
      render(<WinnerSelector {...disabledProps} />);
      const team1Button = screen.getByText('Team 1');
      expect(team1Button).toBeDisabled();
    });

    test('buttons have reduced opacity when disabled', () => {
      render(<WinnerSelector {...disabledProps} />);
      const team1Button = screen.getByText('Team 1');
      expect(team1Button).toHaveStyle('opacity: 0.5');
    });

    test('cursor shows not-allowed when disabled', () => {
      render(<WinnerSelector {...disabledProps} />);
      const team1Button = screen.getByText('Team 1');
      expect(team1Button).toHaveStyle('cursor: not-allowed');
    });
  });

  describe('Selection Styles', () => {
    test('unselected buttons have default border', () => {
      render(
        <WinnerSelector
          teamMode="partners"
          winner="team2"
          onWinnerChange={mockOnWinnerChange}
        />
      );
      const team1Button = screen.getByText('Team 1');
      // Unselected should have border color from theme
      expect(team1Button).not.toHaveStyle('border: 3px solid #00bcd4');
    });

    test('flush buttons have smaller font size', () => {
      render(
        <WinnerSelector
          teamMode="partners"
          winner={null}
          onWinnerChange={mockOnWinnerChange}
        />
      );
      const flushButton = screen.getByText('Team 1 Flush');
      expect(flushButton).toHaveStyle('font-size: 14px');
    });

    test('regular buttons have larger font size', () => {
      render(
        <WinnerSelector
          teamMode="partners"
          winner={null}
          onWinnerChange={mockOnWinnerChange}
        />
      );
      const regularButton = screen.getByText('Team 1');
      expect(regularButton).toHaveStyle('font-size: 16px');
    });
  });

  describe('Mode Switching', () => {
    test('updates options when mode changes from partners to solo', () => {
      const { rerender } = render(
        <WinnerSelector
          teamMode="partners"
          winner={null}
          onWinnerChange={mockOnWinnerChange}
        />
      );

      expect(screen.getByText('Team 1')).toBeInTheDocument();

      rerender(
        <WinnerSelector
          teamMode="solo"
          winner={null}
          onWinnerChange={mockOnWinnerChange}
        />
      );

      expect(screen.queryByText('Team 1')).not.toBeInTheDocument();
      expect(screen.getByText('Captain')).toBeInTheDocument();
    });
  });
});
