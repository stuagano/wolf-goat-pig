import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import RoundStoryPage from '../RoundStoryPage';
import RoundDiscussion from '../../components/game/RoundDiscussion';
vi.mock('../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => fetch }));
import { useAuth0 as mockUseAuth0 } from '@auth0/auth0-react';

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: vi.fn(),
}));

const story = {
  date: '6-Oct',
  date_sortable: '2026-10-06',
  location: 'Wing Point',
  group: 'A',
  players: [
    { member: 'Coulburn', player_id: 4, quarters: -400 },
    { member: 'Stuart Gano', player_id: null, quarters: 200 },
  ],
  comments: [
    {
      id: 9,
      author_name: 'Jeff',
      author_profile_id: 2,
      body: 'Coulburn never recovered after the turn.',
      created_at: '2026-10-06T18:00:00',
      can_delete: false,
      reactions: [{ emoji: '🔥', count: 1, reactor_names: ['Stuart'], mine: false }],
    },
  ],
  reactions: [{ emoji: '😭', count: 2, reactor_names: ['Jeff', 'Stuart'], mine: false }],
};

const renderStory = (query = '?location=Wing%20Point') => render(
  <MemoryRouter initialEntries={[`/rounds/2026-10-06/A${query}`]}>
    <Routes>
      <Route path="/rounds/:date/:group" element={<RoundStoryPage />} />
      <Route path="/game/:gameId" element={<RoundDiscussion gameId="shared-uuid" />} />
    </Routes>
  </MemoryRouter>,
);

beforeEach(() => {
  mockUseAuth0.mockReturnValue({
    isAuthenticated: false,
    loginWithRedirect: vi.fn(),
    getAccessTokenSilently: vi.fn(),
  });
  global.fetch = vi.fn(async url => ({ ok: true, json: async () => String(url).includes('/aliases?') ? { status: 'resolved', game_ids: ['shared-uuid'] } : story }));
});

// Old /rounds links now resolve to the same UUID records rather than rendering
// their own sheet-derived scores and a separate discussion.
describe('old round links reaching the shared UUID discussion', () => {
  test.each(['?location=Wing%20Point', ''])('toggles the same round reaction on the resolved UUID %s', async (query) => {
    mockUseAuth0.mockReturnValue({ isAuthenticated: true, getAccessTokenSilently: vi.fn().mockResolvedValue('test-token') });
    global.fetch = vi.fn(async (url, options) => {
      const path = String(url);
      if (options?.method === 'POST') {
        const valid = new URL(url, 'http://localhost').pathname === '/data/rounds/uuid/shared-uuid/reactions';
        return { ok: valid, status: valid ? 200 : 405, json: async () => valid ? [{ ...story.reactions[0], count: 3, mine: true }] : { detail: 'Method Not Allowed' } };
      }
      return { ok: true, json: async () => path.includes('/aliases?') ? { status: 'resolved', game_ids: ['shared-uuid'] }
        : path.endsWith('/players/me') ? { id: 2 } : story };
    });
    renderStory(query);
    fireEvent.click(await screen.findByRole('button', { name: '😭 2' }));
    expect(await screen.findByRole('button', { name: '😭 3' })).toHaveAttribute('aria-pressed', 'true');
  });

  test.each(['?location=Wing%20Point', ''])('posts onto the same UUID comment records %s', async (query) => {
    mockUseAuth0.mockReturnValue({ isAuthenticated: true, getAccessTokenSilently: vi.fn().mockResolvedValue('test-token') });
    global.fetch = vi.fn(async (url, options) => {
      const path = String(url);
      if (options?.method === 'POST') {
        const valid = new URL(url, 'http://localhost').pathname === '/data/rounds/uuid/shared-uuid/comments';
        return { ok: valid, status: valid ? 200 : 405, json: async () => valid ? { ...story.comments[0], id: 10, body: 'Great round!' } : { detail: 'Method Not Allowed' } };
      }
      return { ok: true, json: async () => path.includes('/aliases?') ? { status: 'resolved', game_ids: ['shared-uuid'] }
        : path.endsWith('/players/me') ? { id: 2 } : story };
    });
    renderStory(query);
    fireEvent.change(await screen.findByLabelText('Add a comment'), { target: { value: 'Great round!' } });
    fireEvent.click(screen.getByRole('button', { name: 'Post comment' }));
    expect(await screen.findByText('Great round!', { selector: 'p' })).toBeInTheDocument();
    expect(screen.getByLabelText('Add a comment')).toHaveValue('');
  });

  test('keeps the existing comment IDs, authors and reaction counts, with no sheet scores', async () => {
    renderStory();
    expect(await screen.findByText('Coulburn never recovered after the turn.')).toBeInTheDocument();
    expect(screen.getByText('Jeff')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '😭 2' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '🔥 1' })).toBeInTheDocument();
    expect(screen.queryByText('-400')).toBeNull();
    expect(screen.queryByText('+200')).toBeNull();
    expect(screen.getByRole('button', { name: 'Sign in to comment' })).toBeInTheDocument();
  });
});
