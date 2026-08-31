import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom';
import Leaderboard from '../Leaderboard';

vi.mock('../../../context', () => {
  const syncData = [{ member: 'Anne / Lee & Co', quarters: 12, rounds: 2, average: 6 }];
  return {
    useSheetSync: () => ({ syncData, syncStatus: 'idle', error: null, performLiveSync: vi.fn() }),
  };
});
vi.mock('../../../api/client', () => ({
  api: { GET: vi.fn(async () => ({ data: {} })) },
}));

function ProfileDestination() {
  return <h1>Profile: {useParams().playerName}</h1>;
}

test.each(['Overall Ranking', 'Most Rounds Played', 'Bottom 5 Scores'])(
  'player names navigate to their profile in %s', async (metric) => {
    render(
      <MemoryRouter initialEntries={['/leaderboard']}>
        <Routes>
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/players/name/:playerName" element={<ProfileDestination />} />
        </Routes>
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('button', { name: metric }));
    const link = await screen.findByRole('link', { name: 'Anne / Lee & Co' });
    expect(link).toHaveAttribute('href', '/players/name/Anne%20%2F%20Lee%20%26%20Co');
    fireEvent.click(link);
    expect(await screen.findByRole('heading', { name: 'Profile: Anne / Lee & Co' })).toBeInTheDocument();
  },
);
