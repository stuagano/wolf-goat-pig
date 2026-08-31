import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom';
import PlayerName from '../PlayerName';

function ProfileDestination() {
  return <h1>Profile: {useParams().playerName}</h1>;
}

test('sheet-only players link to their name-based profile', async () => {
  render(
    <MemoryRouter initialEntries={['/leaderboard']}>
      <Routes>
        <Route path="/leaderboard" element={<PlayerName name="Anne / Lee & Co" />} />
        <Route path="/players/name/:playerName" element={<ProfileDestination />} />
      </Routes>
    </MemoryRouter>,
  );
  const link = screen.getByRole('link', { name: 'Anne / Lee & Co' });
  expect(link).toHaveAttribute('href', '/players/name/Anne%20%2F%20Lee%20%26%20Co');
  fireEvent.click(link);
  expect(await screen.findByRole('heading', { name: 'Profile: Anne / Lee & Co' })).toBeInTheDocument();
});

test('players with an id link to the id route; nameless players stay plain text', () => {
  render(
    <MemoryRouter>
      <PlayerName name="Bob" playerId={7} />
      <PlayerName />
    </MemoryRouter>,
  );
  expect(screen.getByRole('link', { name: 'Bob' })).toHaveAttribute('href', '/players/7');
  expect(screen.getByText('Unknown Player').tagName).toBe('SPAN');
});
