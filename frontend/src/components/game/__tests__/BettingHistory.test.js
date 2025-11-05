// frontend/src/components/game/__tests__/BettingHistory.test.js
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import BettingHistory from '../BettingHistory';
import { BettingEventTypes } from '../../../constants/bettingEvents';

describe('BettingHistory', () => {
  const mockEventHistory = {
    currentHole: [
      {
        eventId: '1',
        eventType: BettingEventTypes.DOUBLE_OFFERED,
        actor: 'Player1',
        timestamp: '2025-11-04T10:00:00Z',
        data: { proposedMultiplier: 2 }
      },
      {
        eventId: '2',
        eventType: BettingEventTypes.DOUBLE_ACCEPTED,
        actor: 'Player2',
        timestamp: '2025-11-04T10:01:00Z',
        data: { newMultiplier: 2 }
      }
    ],
    lastHole: [],
    gameHistory: []
  };

  test('should show current hole tab by default', () => {
    render(<BettingHistory eventHistory={mockEventHistory} />);
    expect(screen.getByRole('tab', { name: /Current Hole/ })).toHaveAttribute('aria-selected', 'true');
  });

  test('should display events from current hole', () => {
    render(<BettingHistory eventHistory={mockEventHistory} />);
    expect(screen.getByText(/Player1/)).toBeInTheDocument();
    expect(screen.getByText(/DOUBLE_OFFERED/)).toBeInTheDocument();
  });

  test('should switch to last hole tab when clicked', () => {
    render(<BettingHistory eventHistory={mockEventHistory} />);

    fireEvent.click(screen.getByRole('tab', { name: /Last Hole/ }));
    expect(screen.getByRole('tab', { name: /Last Hole/ })).toHaveAttribute('aria-selected', 'true');
  });
});
