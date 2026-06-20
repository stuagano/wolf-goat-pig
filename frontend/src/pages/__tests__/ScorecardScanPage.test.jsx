import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ScorecardScanPage from '../ScorecardScanPage';

// Mock the heavy photo flow — we only assert the landing routes into it.
vi.mock('../../components/game/ScorecardPhoto', () => ({
  default: ({ mode, pickedPlayers }) => (
    <div data-testid="scorecard-photo">
      mode:{mode}
      {pickedPlayers && pickedPlayers.length > 0 && (
        <span data-testid="picked-count">{pickedPlayers.length}</span>
      )}
    </div>
  ),
}));

const ROSTER = ['Alice', 'Bob', 'Carol', 'Dave', 'Eve', 'Frank'];

beforeEach(() => {
  global.fetch = vi.fn(async (url) => ({
    ok: true,
    json: async () => (String(url).includes('/legacy-players') ? { players: ROSTER } : []),
  }));
});

describe('ScorecardScanPage landing', () => {
  test("'Scan a finished round' shows player picker then photo flow after selecting 4 players", async () => {
    render(
      <MemoryRouter>
        <ScorecardScanPage />
      </MemoryRouter>,
    );
    // Enter new-round mode — should show player picker, not photo yet
    fireEvent.click(await screen.findByText(/Scan a finished round/i));
    expect(screen.queryByTestId('scorecard-photo')).toBeNull();
    expect(await screen.findByText(/Who played/i)).toBeInTheDocument();

    // Select 4 players
    for (const name of ROSTER.slice(0, 4)) {
      fireEvent.click(screen.getByLabelText(name));
    }

    // Continue should now be enabled
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    expect(screen.getByTestId('scorecard-photo')).toHaveTextContent('mode:new-round');
    expect(screen.getByTestId('picked-count')).toHaveTextContent('4');
  });

  test("'Add to an active game' does NOT immediately enter the photo flow (shows game picker)", async () => {
    render(
      <MemoryRouter>
        <ScorecardScanPage />
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByText(/Add to an active game/i));
    expect(screen.queryByTestId('scorecard-photo')).toBeNull();
  });
});
