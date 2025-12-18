import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import TeeTossModal from '../TeeTossModal';

describe('TeeTossModal', () => {
    const mockPlayers = [
        { id: 'p1', name: 'Player 1' },
        { id: 'p2', name: 'Player 2' },
        { id: 'p3', name: 'Player 3' },
        { id: 'p4', name: 'Player 4' },
    ];
    const mockOnClose = jest.fn();
    const mockOnOrderComplete = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    test('renders correctly with initial state', () => {
        render(
            <TeeTossModal
                players={mockPlayers}
                onClose={mockOnClose}
                onOrderComplete={mockOnOrderComplete}
            />
        );

        expect(screen.getByText('Toss Tees for Order')).toBeInTheDocument();
        expect(screen.getByText("Tap 'Spin' to toss the tee!")).toBeInTheDocument();
        expect(screen.getByText('Spin Tee')).toBeInTheDocument();

        // Check if all players are rendered in the circle
        mockPlayers.forEach(player => {
            expect(screen.getByText(player.name)).toBeInTheDocument();
        });
    });

    test('switches to manual mode', () => {
        render(
            <TeeTossModal
                players={mockPlayers}
                onClose={mockOnClose}
                onOrderComplete={mockOnOrderComplete}
            />
        );

        fireEvent.click(screen.getByText('✋ Set Order'));

        expect(screen.getByText('Use the arrows to move players up or down in the order.')).toBeInTheDocument();
        expect(screen.getByText('✓ Confirm Order')).toBeInTheDocument();
        expect(screen.queryByText('Spin Tee')).not.toBeInTheDocument();
    });

    test('move buttons reorder players in manual mode', () => {
        render(
            <TeeTossModal
                players={mockPlayers}
                onClose={mockOnClose}
                onOrderComplete={mockOnOrderComplete}
            />
        );

        // Switch to manual mode
        fireEvent.click(screen.getByText('✋ Set Order'));

        // Get all move down buttons (first player can only move down)
        const moveDownButtons = screen.getAllByLabelText('Move down');
        expect(moveDownButtons.length).toBe(mockPlayers.length);

        // Click move down on first player
        fireEvent.click(moveDownButtons[0]);

        // Verify order changed - Player 2 should now be first
        const playerRows = screen.getAllByText(/Player \d/);
        expect(playerRows[0]).toHaveTextContent('Player 2');
    });

    test('calls onClose when close button is clicked', () => {
        render(
            <TeeTossModal
                players={mockPlayers}
                onClose={mockOnClose}
                onOrderComplete={mockOnOrderComplete}
            />
        );

        fireEvent.click(screen.getByText('×'));
        expect(mockOnClose).toHaveBeenCalled();
    });
});
