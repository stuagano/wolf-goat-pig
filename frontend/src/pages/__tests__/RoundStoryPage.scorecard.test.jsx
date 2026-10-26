/**
 * The round story is the page the user reaches from a shared /rounds link.
 * When the backend matched that round to a saved game it must offer a real
 * route to the card; when it did not, it must offer nothing — and the story's
 * own discussion features keep working either way.
 */
import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import RoundStoryPage from '../RoundStoryPage';
import { useAuth0 as mockUseAuth0 } from '@auth0/auth0-react';

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: vi.fn(),
}));

const GAME_ID = '4a7f1c20-5d9e-4a1b-8c33-0f9c2d6b7e81';

const story = (overrides = {}) => ({
  date: '25-Oct',
  date_sortable: '2026-10-25',
  location: 'Wing Point Golf & Country Club',
  group: 'A',
  players: [
    { member: 'Brett Saks', player_id: 7, quarters: 147 },
    { member: 'Aaron Foster', player_id: null, quarters: -139 },
  ],
  comments: [],
  reactions: [],
  ...overrides,
});

const renderStory = (round) => {
  global.fetch = vi.fn(async (url) => ({
    ok: true,
    json: async () => (String(url).endsWith('/players/me') ? { id: 2 } : round),
  }));
  return render(
    <MemoryRouter initialEntries={['/rounds/2026-10-25/A?location=Wing%20Point%20Golf%20%26%20Country%20Club']}>
      <Routes>
        <Route path="/rounds/:date/:group" element={<RoundStoryPage />} />
        <Route path="/game/:gameId" element={<div>scorecard for {GAME_ID}</div>} />
      </Routes>
    </MemoryRouter>,
  );
};

beforeEach(() => {
  mockUseAuth0.mockReturnValue({
    isAuthenticated: false,
    loginWithRedirect: vi.fn(),
    getAccessTokenSilently: vi.fn(),
  });
});

describe('RoundStoryPage scorecard navigation', () => {
  test('clicking Scorecard actually navigates to the saved game route', async () => {
    renderStory(story({ game_id: GAME_ID }));

    const link = await screen.findByRole('link', { name: /Scorecard/ });
    expect(link).toHaveAttribute('href', `/game/${GAME_ID}`);

    fireEvent.click(link);
    expect(await screen.findByText(`scorecard for ${GAME_ID}`)).toBeInTheDocument();
  });

  test.each([
    ['sheet-only round (no game_id key)', {}],
    ['explicitly unmatched round', { game_id: null }],
  ])('offers no scorecard link for a %s, and keeps the story usable', async (_label, overrides) => {
    renderStory(story(overrides));

    expect(await screen.findByText('Brett Saks')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Scorecard/ })).toBeNull();
    expect(document.querySelector('a[href^="/game/"]')).toBeNull();
    // Story-native features are untouched by the missing card.
    expect(screen.getByRole('button', { name: 'Copy link' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in to comment' })).toBeInTheDocument();
  });
});
