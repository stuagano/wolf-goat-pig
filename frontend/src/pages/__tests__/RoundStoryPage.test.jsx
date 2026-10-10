import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
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

const renderStory = () => render(
  <MemoryRouter initialEntries={['/rounds/2026-10-06/A?location=Wing%20Point']}>
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
