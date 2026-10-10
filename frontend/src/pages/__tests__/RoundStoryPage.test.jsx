import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import RoundStoryPage from '../RoundStoryPage';
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
    </Routes>
  </MemoryRouter>,
);

beforeEach(() => {
  mockUseAuth0.mockReturnValue({
    isAuthenticated: false,
    loginWithRedirect: vi.fn(),
    getAccessTokenSilently: vi.fn(),
  });
  global.fetch = vi.fn(async () => ({ ok: true, json: async () => story }));
});

describe('RoundStoryPage', () => {
  test.each(['?location=Wing%20Point', ''])('saves a round reaction with the location query %s', async (query) => {
    mockUseAuth0.mockReturnValue({
      isAuthenticated: true,
      getAccessTokenSilently: vi.fn().mockResolvedValue('test-token'),
    });
    global.fetch = vi.fn(async (url, options) => {
      if (options?.method === 'POST') {
        const parsed = new URL(url, 'http://localhost');
        const valid = parsed.pathname === '/data/rounds/2026-10-06/A/reactions'
          && parsed.search === query;
        return { ok: valid, json: async () => valid
          ? [{ ...story.reactions[0], count: 3, mine: true }]
          : { detail: 'Method Not Allowed' } };
      }
      return { ok: true, json: async () => url.endsWith('/players/me') ? { id: 2 } : story };
    });
    renderStory(query);
    fireEvent.click(await screen.findByRole('button', { name: '😭 2' }));
    expect(await screen.findByRole('button', { name: '😭 3' })).toHaveAttribute('aria-pressed', 'true');
  });

  test.each(['?location=Wing%20Point', ''])('posts a comment with the location query %s', async (query) => {
    mockUseAuth0.mockReturnValue({
      isAuthenticated: true,
      getAccessTokenSilently: vi.fn().mockResolvedValue('test-token'),
    });
    global.fetch = vi.fn(async (url, options) => {
      if (options?.method === 'POST') {
        const parsed = new URL(url, 'http://localhost');
        const valid = parsed.pathname === '/data/rounds/2026-10-06/A/comments'
          && parsed.search === query;
        return { ok: valid, json: async () => valid
          ? { ...story.comments[0], id: 10, body: 'Great round!' }
          : { detail: 'Method Not Allowed' } };
      }
      return { ok: true, json: async () => url.endsWith('/players/me') ? { id: 2 } : story };
    });
    renderStory(query);
    fireEvent.change(await screen.findByLabelText('Add a comment'), { target: { value: 'Great round!' } });
    fireEvent.click(screen.getByRole('button', { name: 'Post comment' }));
    expect(await screen.findByText('Great round!', { selector: 'p' })).toBeInTheDocument();
    expect(screen.getByLabelText('Add a comment')).toHaveValue('');
  });

  test('shows the foursome and Coulburn losing 400, with an empty comment thread', async () => {
    renderStory();
    expect(await screen.findByText('Coulburn')).toBeInTheDocument();
    expect(screen.getByText('-400')).toBeInTheDocument();
    expect(screen.getByText('+200')).toBeInTheDocument();
    expect(screen.getByText('Coulburn never recovered after the turn.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '😭 2' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '🔥 1' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Copy link' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Coulburn' })).toHaveAttribute('href', '/players/4');
    expect(screen.getByText('Stuart Gano').closest('a')).toBeNull();
    expect(screen.getByRole('button', { name: 'Sign in to comment' })).toBeInTheDocument();
  });
});
