import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import '@testing-library/jest-dom';
import LivSowTeamPage from '../LivSowTeamPage';

const TEAM = {
  slug: 'high-beta',
  name: 'High Beta',
  rank: 1,
  total: 44,
  weeks: ['6/1', '6/8'],
  sheet_url: 'https://example.com/sheet',
  players: [
    { name: 'Gregg Colburn', role: 'Captain', total: 3, count: 3, weeks: { '6/1': 7, '6/8': -4 }, best_scores: [7, -4], team_contribution: 3 },
    { name: 'Chip Halpert', role: 'Alternate', total: 14, count: 1, weeks: { '6/1': 14 }, best_scores: [14], team_contribution: 14 },
  ],
  transactions: [
    {
      id: 1, detected_at: '2026-06-12T15:00:00', season: '2026', week: '6/8',
      snapshot_id: 9, type: 'signed', player: 'Dom Lacie',
      from_team: null, to_team: 'High Beta', from_role: 'Free Agent', to_role: 'Alternate',
      details: null, description: 'Dom Lacie signed by High Beta as Alternate',
    },
  ],
};

const renderAt = (slug) =>
  render(
    <MemoryRouter initialEntries={[`/livsow/teams/${slug}`]}>
      <Routes>
        <Route path="/livsow/teams/:teamSlug" element={<LivSowTeamPage />} />
      </Routes>
    </MemoryRouter>,
  );

describe('LivSowTeamPage', () => {
  test('renders hero, roster, and transactions', async () => {
    global.fetch.mockResolvedValue({ ok: true, status: 200, json: async () => TEAM });
    renderAt('high-beta');
    await waitFor(() => expect(screen.getByText('High Beta')).toBeInTheDocument());
    // Hero stats
    expect(screen.getByText('#1')).toBeInTheDocument();
    expect(screen.getByText('+44')).toBeInTheDocument();
    // Roster
    expect(screen.getByText('Gregg Colburn')).toBeInTheDocument();
    expect(screen.getByText('Captain')).toBeInTheDocument();
    // Transaction with badge + description
    expect(screen.getByText('SIGNED')).toBeInTheDocument();
    expect(screen.getByText(/Dom Lacie signed by High Beta/)).toBeInTheDocument();
  });

  test('unknown slug shows not-found with a way back', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 404, json: async () => ({}) });
    renderAt('no-such-team');
    await waitFor(() => expect(screen.getByText('Team not found')).toBeInTheDocument());
    expect(screen.getByText(/Back to LivSow standings/)).toBeInTheDocument();
  });
});
