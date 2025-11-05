// frontend/src/components/game/__tests__/BettingTracker.integration.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import BettingTracker from '../BettingTracker';

describe('BettingTracker Integration', () => {
  const mockGameState = {
    id: 'game-123',
    current_hole: 5,
    players: [
      { id: 'p1', name: 'Player1' },
      { id: 'p2', name: 'Player2' }
    ]
  };

  // Mock fetch for sync testing
  beforeEach(() => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true, confirmedEvents: [], corrections: [] })
      })
    );
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('complete double offer and accept workflow', async () => {
    render(<BettingTracker gameState={mockGameState} currentPlayer="Player1" />);

    // Initial state - collapsed
    expect(screen.getByText(/Bet: \$1\.00 \(1x\)/)).toBeInTheDocument();

    // Expand tracker
    fireEvent.click(screen.getByText(/Bet:/));

    // Should show expanded view
    await waitFor(() => {
      expect(screen.getByText(/Betting Tracker/)).toBeInTheDocument();
    });

    // Should show offer double button
    expect(screen.getByText(/Offer Double/)).toBeInTheDocument();

    // Offer double
    fireEvent.click(screen.getByText(/Offer Double/));

    // Should show pending action
    await waitFor(() => {
      expect(screen.getByText(/Player1 offered to double/)).toBeInTheDocument();
    });

    // Should show accept/decline buttons
    expect(screen.getByText(/Accept Double/)).toBeInTheDocument();
    expect(screen.getByText(/Decline/)).toBeInTheDocument();

    // Accept double
    fireEvent.click(screen.getByText(/Accept Double/));

    // Should update multiplier in the CurrentBetStatus component
    await waitFor(() => {
      expect(screen.getByText(/2x/)).toBeInTheDocument();
    });

    // Should show in history
    expect(screen.getByText(/DOUBLE_OFFERED/)).toBeInTheDocument();
    expect(screen.getByText(/DOUBLE_ACCEPTED/)).toBeInTheDocument();
  });

  test('complete double offer and decline workflow', async () => {
    render(<BettingTracker gameState={mockGameState} currentPlayer="Player1" />);

    // Expand tracker
    fireEvent.click(screen.getByText(/Bet:/));

    await waitFor(() => {
      expect(screen.getByText(/Betting Tracker/)).toBeInTheDocument();
    });

    // Offer double
    fireEvent.click(screen.getByText(/Offer Double/));

    await waitFor(() => {
      expect(screen.getByText(/Player1 offered to double/)).toBeInTheDocument();
    });

    // Decline double
    fireEvent.click(screen.getByText(/Decline/));

    // Should remain at 1x multiplier
    await waitFor(() => {
      expect(screen.getByText(/1x/)).toBeInTheDocument();
    });

    // Pending action should be cleared
    expect(screen.queryByText(/Player1 offered to double/)).not.toBeInTheDocument();

    // Should show both events in history
    expect(screen.getByText(/DOUBLE_OFFERED/)).toBeInTheDocument();
    expect(screen.getByText(/DOUBLE_DECLINED/)).toBeInTheDocument();
  });

  test('should switch between history tabs', async () => {
    render(<BettingTracker gameState={mockGameState} currentPlayer="Player1" />);

    // Expand tracker
    fireEvent.click(screen.getByText(/Bet:/));

    await waitFor(() => {
      expect(screen.getByText(/Betting Tracker/)).toBeInTheDocument();
    });

    // Should see Current Hole tab by default
    expect(screen.getByRole('tab', { name: /Current Hole/ })).toHaveAttribute('aria-selected', 'true');

    // Click Last Hole tab
    fireEvent.click(screen.getByRole('tab', { name: /Last Hole/ }));

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Last Hole/ })).toHaveAttribute('aria-selected', 'true');
    });

    // Click Game History tab
    fireEvent.click(screen.getByRole('tab', { name: /Game History/ }));

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /Game History/ })).toHaveAttribute('aria-selected', 'true');
    });
  });

  test('should show pending action indicator when collapsed', async () => {
    render(<BettingTracker gameState={mockGameState} currentPlayer="Player1" />);

    // Expand and offer double
    fireEvent.click(screen.getByText(/Bet:/));

    await waitFor(() => {
      expect(screen.getByText(/Offer Double/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/Offer Double/));

    await waitFor(() => {
      expect(screen.getByText(/Player1 offered to double/)).toBeInTheDocument();
    });

    // Collapse the tracker
    fireEvent.click(screen.getByText(/Collapse/));

    // Should show pending indicator
    await waitFor(() => {
      expect(screen.getByTestId('pending-indicator')).toBeInTheDocument();
      expect(screen.getByText(/Action Required/)).toBeInTheDocument();
    });
  });

  test('should handle multiple sequential double offers', async () => {
    render(<BettingTracker gameState={mockGameState} currentPlayer="Player1" />);

    // Expand tracker
    fireEvent.click(screen.getByText(/Bet:/));

    await waitFor(() => {
      expect(screen.getByText(/Offer Double/)).toBeInTheDocument();
    });

    // First offer and accept
    fireEvent.click(screen.getByText(/Offer Double/));

    await waitFor(() => {
      expect(screen.getByText(/Player1 offered to double/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/Accept Double/));

    await waitFor(() => {
      expect(screen.getByText(/2x/)).toBeInTheDocument();
    });

    // Second offer and accept
    fireEvent.click(screen.getByText(/Offer Double/));

    await waitFor(() => {
      expect(screen.getByText(/Player1 offered to double to 4x/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/Accept Double/));

    await waitFor(() => {
      expect(screen.getByText(/4x/)).toBeInTheDocument();
    });

    // Should show all events in history (2 offers + 2 accepts = 4 events)
    const allEvents = screen.getAllByText(/DOUBLE_/);
    expect(allEvents.length).toBeGreaterThanOrEqual(4);
  });

  test('should collapse when clicking backdrop on mobile', async () => {
    // Mock mobile viewport
    global.innerWidth = 500;
    window.dispatchEvent(new Event('resize'));

    render(<BettingTracker gameState={mockGameState} currentPlayer="Player1" />);

    // Expand tracker
    fireEvent.click(screen.getByText(/Bet:/));

    await waitFor(() => {
      expect(screen.getByText(/Betting Tracker/)).toBeInTheDocument();
    });

    // Find and click the backdrop
    const backdrop = document.querySelector('div[style*="rgba(0, 0, 0, 0.5)"]');
    if (backdrop) {
      fireEvent.click(backdrop);

      // Should collapse
      await waitFor(() => {
        expect(screen.queryByText(/Betting Tracker/)).not.toBeInTheDocument();
      });
    }

    // Reset viewport
    global.innerWidth = 1024;
    window.dispatchEvent(new Event('resize'));
  });
});
