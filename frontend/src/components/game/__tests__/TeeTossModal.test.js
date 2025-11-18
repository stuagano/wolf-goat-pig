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

        fireEvent.click(screen.getByText('Manual List'));

        expect(screen.getByText('Drag and drop to reorder players.')).toBeInTheDocument();
        expect(screen.getByText('Confirm Order')).toBeInTheDocument();
        expect(screen.queryByText('Spin Tee')).not.toBeInTheDocument();
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
