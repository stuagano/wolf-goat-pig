import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import PlayersRosterPage from '../PlayersRosterPage';

const PLAYERS = [
  { id: 21, name: 'Kevin Gent', handicap: 7.6, avatar_url: null, has_avatar_image: true, is_ai: false },
  { id: 3, name: 'Alice Park', handicap: 12, avatar_url: null, has_avatar_image: false, is_ai: false },
  { id: 99, name: 'Bot Bobby', handicap: 18, avatar_url: null, has_avatar_image: false, is_ai: true },
];

beforeEach(() => {
  global.fetch = vi.fn(async () => ({ ok: true, json: async () => PLAYERS }));
});

describe('PlayersRosterPage', () => {
  test('lists human players sorted by name, excluding AI players', async () => {
    render(
      <MemoryRouter>
        <PlayersRosterPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText('Alice Park')).toBeInTheDocument();
    expect(screen.getByText('Kevin Gent')).toBeInTheDocument();
    expect(screen.queryByText('Bot Bobby')).toBeNull();
    expect(screen.getByText('2 players')).toBeInTheDocument();

    const names = screen.getAllByText(/Alice Park|Kevin Gent/).map(el => el.textContent);
    expect(names).toEqual(['Alice Park', 'Kevin Gent']);
  });

  test('shows "Handicap Pending" for default/unknown source and the value for a real one (issue #320)', async () => {
    global.fetch = vi.fn(async () => ({
      ok: true,
      json: async () => [
        { id: 1, name: 'Pending Pete', handicap: 18, handicap_source: 'default', is_ai: false },
        { id: 2, name: 'Ghin Gary', handicap: 9.3, handicap_source: 'ghin', is_ai: false },
        { id: 3, name: 'Nosource Nancy', handicap: 18, is_ai: false },
      ],
    }));

    render(
      <MemoryRouter>
        <PlayersRosterPage />
      </MemoryRouter>,
    );

    await screen.findByText('Ghin Gary');
    // Real GHIN handicap shows the value.
    expect(screen.getByText('Handicap 9.3')).toBeInTheDocument();
    // Default and missing sources show "Pending", never the 18 placeholder.
    expect(screen.getAllByText('Handicap Pending')).toHaveLength(2);
    expect(screen.queryByText('Handicap 18')).toBeNull();
  });

  test('clicking a player navigates to their profile', async () => {
    render(
      <MemoryRouter initialEntries={['/players']}>
        <Routes>
          <Route path="/players" element={<PlayersRosterPage />} />
          <Route path="/players/:playerId" element={<div>Profile page</div>} />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByText('Kevin Gent'));
    expect(await screen.findByText('Profile page')).toBeInTheDocument();
  });
});
