import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import PlayerProfilePage from '../PlayerProfilePage';
import { useAuth0 as mockUseAuth0 } from '@auth0/auth0-react';

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: vi.fn(),
}));

const mockUsePlayerProfile = vi.fn();
vi.mock('../../hooks/usePlayerProfile', () => ({
  usePlayerProfile: () => mockUsePlayerProfile(),
}));

const baseProfile = {
  id: 21,
  name: 'Kevin Gent',
  handicap: 7.6,
  description: null,
  avatar_url: null,
  has_avatar_image: false,
  last_played: null,
  created_at: '2025-10-14T17:52:37.182507',
  available_days: [],
  match_history: [],
  game_history: [
    { date: '2026-06-13', location: 'Wingpoint', score: 4, duration: '02:15:00', source: 'primary_sheet' },
    { date: '2026-06-06', location: 'Wingpoint', score: -2, duration: null, source: 'member' },
  ],
  badges: [],
  stats: { games_played: 2, games_won: 1, total_earnings: 200, solo_wins: 0 },
};

const renderPage = (playerId = '21') =>
  render(
    <MemoryRouter initialEntries={[`/players/${playerId}`]}>
      <Routes>
        <Route path="/players/:playerId" element={<PlayerProfilePage />} />
      </Routes>
    </MemoryRouter>,
  );

beforeEach(() => {
  mockUseAuth0.mockReturnValue({
    getAccessTokenSilently: vi.fn().mockResolvedValue('mock-token'),
  });
  global.fetch = vi.fn(async (url) => {
    if (String(url).includes('/public-profile')) {
      return { ok: true, json: async () => baseProfile };
    }
    if (String(url).includes('/livsow/team-map')) {
      return { ok: true, json: async () => ({}) };
    }
    if (String(url).includes('/players/me/avatar')) {
      return { ok: true, json: async () => ({ has_avatar_image: true }) };
    }
    return { ok: true, json: async () => ({}) };
  });
});

describe('PlayerProfilePage game history', () => {
  test('renders recorded rounds with date, location, and signed score', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 999 } }); // viewing someone else
    renderPage();

    expect(await screen.findByText(/Game History/)).toBeInTheDocument();
    expect(screen.getAllByText(/Wingpoint/)).toHaveLength(2);
    expect(screen.getByText('+4')).toBeInTheDocument();
    expect(screen.getByText('-2')).toBeInTheDocument();
  });

  test('shows empty state when no rounds recorded', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 999 } });
    global.fetch = vi.fn(async (url) => {
      if (String(url).includes('/public-profile')) {
        return { ok: true, json: async () => ({ ...baseProfile, game_history: [] }) };
      }
      return { ok: true, json: async () => ({}) };
    });
    renderPage();

    expect(await screen.findByText(/No recorded rounds yet/)).toBeInTheDocument();
  });
});

describe('PlayerProfilePage avatar upload', () => {
  test('does not show an upload control on someone else\'s profile', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 999 } });
    renderPage();

    await screen.findByText('Kevin Gent');
    expect(screen.queryByTitle('Change photo')).toBeNull();
  });

  test('shows upload control on own profile and posts the selected file', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 21 } }); // viewing own profile
    renderPage();

    await screen.findByText('Kevin Gent');
    const trigger = screen.getByTitle('Change photo');
    expect(trigger).toBeInTheDocument();

    const file = new File(['fake-bytes'], 'photo.jpg', { type: 'image/jpeg' });
    const input = document.querySelector('input[type="file"]');
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      const avatarCall = global.fetch.mock.calls.find(([url]) => String(url).includes('/players/me/avatar'));
      expect(avatarCall).toBeTruthy();
      expect(avatarCall[1].method).toBe('POST');
      expect(avatarCall[1].body).toBeInstanceOf(FormData);
    });
  });
});
