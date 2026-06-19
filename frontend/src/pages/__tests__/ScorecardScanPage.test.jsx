import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ScorecardScanPage from '../ScorecardScanPage';

// Mock the heavy photo flow — we only assert the landing routes into it.
vi.mock('../../components/game/ScorecardPhoto', () => ({
  default: ({ mode }) => <div data-testid="scorecard-photo">mode:{mode}</div>,
}));

beforeEach(() => {
  global.fetch = vi.fn(async (url) => ({
    ok: true,
    json: async () => (String(url).includes('/legacy-players') ? { players: [] } : []),
  }));
});

describe('ScorecardScanPage landing', () => {
  test("'Scan a finished round' enters new-round mode without selecting a game", async () => {
    render(
      <MemoryRouter>
        <ScorecardScanPage />
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByText(/Scan a finished round/i));
    expect(screen.getByTestId('scorecard-photo')).toHaveTextContent('mode:new-round');
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
