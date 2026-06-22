import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ScorecardPhotoButton from '../ScorecardPhotoButton';

// Mock the api config so the component does not need a live server
vi.mock('../../../config/api.config', () => ({
  apiConfig: { baseUrl: 'http://test-api' },
}));

// Mock the zoom overlay so we can assert it renders without needing CSS/scroll
vi.mock('../ScorecardPhotoZoom', () => ({
  default: ({ src, onClose }) => (
    <div>
      <img alt="scorecard" src={src} />
      <button onClick={onClose}>close</button>
    </div>
  ),
}));

beforeEach(() => {
  vi.resetAllMocks();
});

describe('ScorecardPhotoButton', () => {
  test('shows Photo button and opens overlay when fetch returns ok', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true });

    render(<ScorecardPhotoButton gameId="game-123" />);

    // Button should appear after fetch resolves
    const btn = await screen.findByRole('button', { name: /photo/i });
    expect(btn).toBeTruthy();

    // Clicking the button opens the zoom overlay
    fireEvent.click(btn);
    expect(screen.getByAltText('scorecard')).toBeTruthy();

    // The overlay src points at the scorecard-photo endpoint
    expect(screen.getByAltText('scorecard').getAttribute('src')).toBe(
      'http://test-api/games/game-123/scorecard-photo',
    );
  });

  test('renders nothing when fetch returns 404 (not ok)', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false });

    render(<ScorecardPhotoButton gameId="game-404" />);

    // Wait for the fetch promise to settle
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    expect(screen.queryByRole('button', { name: /photo/i })).toBeNull();
  });

  test('renders nothing when fetch rejects (network error)', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'));

    render(<ScorecardPhotoButton gameId="game-err" />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    expect(screen.queryByRole('button', { name: /photo/i })).toBeNull();
  });
});
