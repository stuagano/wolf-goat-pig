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
