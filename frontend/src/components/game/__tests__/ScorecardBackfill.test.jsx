import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ScorecardBackfill from '../ScorecardBackfill';

// Mock api config
vi.mock('../../../config/api.config', () => ({
  apiConfig: { baseUrl: 'http://test-api' },
}));

// Mock ScorecardPhotoZoom so we can test without real CSS/scroll
vi.mock('../ScorecardPhotoZoom', () => ({
  default: ({ src, onClose }) => (
    <div data-testid="photo-zoom">
      <img alt="scorecard-zoom" src={src} />
      <button onClick={onClose}>close zoom</button>
    </div>
  ),
}));

const players = [
  { id: 'p1', name: 'Alice' },
  { id: 'p2', name: 'Bob' },
];
const standings = { p1: 6, p2: -6 };
// hole_history with no per-hole detail (totals-only, everything on hole 18)
const holeHistory = [
  { hole: 18, points_delta: { p1: 6, p2: -6 } },
];

beforeEach(() => {
  vi.resetAllMocks();
});

describe('ScorecardBackfill — money path', () => {
  test('PATCH body per_hole_quarters sums to locked totals per player and calls onSaved', async () => {
    const onSaved = vi.fn();
    const onCancel = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ game_id: 'g1', standings }),
    });

    render(
      <ScorecardBackfill
        gameId="g1"
        players={players}
        holeHistory={holeHistory}
        standings={standings}
        photoUrl="http://test-api/games/g1/scorecard-photo"
        onSaved={onSaved}
        onCancel={onCancel}
      />,
    );

    // Verify the locked totals are shown (uses "Locked: 6" and "Locked: -6" text)
    expect(screen.getAllByText(/Locked: 6/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Locked: -6/).length).toBeGreaterThan(0);

    // Enter running totals for hole 18 only (simplest path: 1 nonzero delta each)
    // p1 (row 0, Alice): running total at hole 18 = 6
    // p2 (row 1, Bob): running total at hole 18 = -6
    const aliceHole18 = screen.getByRole('spinbutton', {
      name: /running total alice hole 18/i,
    });
    const bobHole18 = screen.getByRole('spinbutton', {
      name: /running total bob hole 18/i,
    });
    fireEvent.change(aliceHole18, { target: { value: '6' } });
    fireEvent.change(bobHole18, { target: { value: '-6' } });

    // Save
    fireEvent.click(screen.getByRole('button', { name: /save/i }));

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

    const [url, opts] = global.fetch.mock.calls[0];
    expect(url).toBe('http://test-api/games/g1/scorecard');
    expect(opts.method).toBe('PATCH');

    const body = JSON.parse(opts.body);
    expect(body).toHaveProperty('per_hole_quarters');

    // p1 (player_index=0) quarters sum = 6
    const p1Sum = body.per_hole_quarters
      .filter((q) => q.player_index === 0)
      .reduce((acc, q) => acc + q.quarters, 0);
    expect(p1Sum).toBe(6);

    // p2 (player_index=1) quarters sum = -6
    const p2Sum = body.per_hole_quarters
      .filter((q) => q.player_index === 1)
      .reduce((acc, q) => acc + q.quarters, 0);
    expect(p2Sum).toBe(-6);

    expect(onSaved).toHaveBeenCalledTimes(1);
  });
});

describe('ScorecardBackfill — mismatch warning', () => {
  test('shows amber warning when running totals do not reach locked total, but Save still works', async () => {
    const onSaved = vi.fn();

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ game_id: 'g1', standings }),
    });

    render(
      <ScorecardBackfill
        gameId="g1"
        players={players}
        holeHistory={holeHistory}
        standings={standings}
        photoUrl={null}
        onSaved={onSaved}
        onCancel={() => {}}
      />,
    );

    // Enter a wrong total for Alice (4 instead of 6) → mismatch
    const aliceHole18 = screen.getByRole('spinbutton', {
      name: /running total alice hole 18/i,
    });
    fireEvent.change(aliceHole18, { target: { value: '4' } });

    // Warning should be visible (text is split across elements so query by test id via container)
    const container = document.body;
    expect(container.textContent).toMatch(/don't reach locked total|doesn't reach locked total/i);

    // Save still fires (non-blocking)
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    expect(onSaved).toHaveBeenCalledTimes(1);
  });
});

describe('ScorecardBackfill — photo button', () => {
  test('Photo button opens the zoom overlay when photoUrl is provided', () => {
    render(
      <ScorecardBackfill
        gameId="g1"
        players={players}
        holeHistory={holeHistory}
        standings={standings}
        photoUrl="http://test-api/games/g1/scorecard-photo"
        onSaved={() => {}}
        onCancel={() => {}}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /photo/i }));
    expect(screen.getByTestId('photo-zoom')).toBeTruthy();
    expect(screen.getByAltText('scorecard-zoom').getAttribute('src')).toBe(
      'http://test-api/games/g1/scorecard-photo',
    );
  });

  test('No photo button when photoUrl is null', () => {
    render(
      <ScorecardBackfill
        gameId="g1"
        players={players}
        holeHistory={holeHistory}
        standings={standings}
        photoUrl={null}
        onSaved={() => {}}
        onCancel={() => {}}
      />,
    );
    expect(screen.queryByRole('button', { name: /photo/i })).toBeNull();
  });
});
