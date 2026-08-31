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
  game_history: [
    { date: '2026-06-13', location: 'Wingpoint', score: 4, duration: '02:15:00', source: 'primary_sheet' },
    { date: '2026-06-06', location: 'Wingpoint', score: -2, duration: null, source: 'member' },
  ],
  badges: [],
  total_badges: 33,
  stats: { games_played: 2, games_won: 1, total_earnings: 200, solo_wins: 0 },
};

const renderPage = (playerId = '21') =>
  render(
    <MemoryRouter initialEntries={[`/players/${playerId}`]}>
      <Routes>
        <Route path="/players/name/:playerName" element={<PlayerProfilePage />} />
        <Route path="/players/:playerId" element={<PlayerProfilePage />} />
      </Routes>
    </MemoryRouter>,
  );

beforeEach(() => {
  mockUseAuth0.mockReturnValue({
    getAccessTokenSilently: vi.fn().mockResolvedValue('mock-token'),
    loginWithRedirect: vi.fn(),
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

describe('PlayerProfilePage leaderboard name links', () => {
  test('resolves a roster name to its existing profile and preserves owner controls', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 21 } });
    global.fetch = vi.fn(async (url) => ({
      ok: true,
      json: async () => String(url).includes('/players/name/') ? { id: 21 } : baseProfile,
    }));
    renderPage('name/Kevin%20Gent');

    expect(await screen.findByRole('heading', { name: 'Kevin Gent' })).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/players/name/Kevin%20Gent'));
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/players/21/public-profile'));
    expect(screen.getByTitle('Change photo')).toBeInTheDocument();
  });

  test('sheet-only players show recorded history without creating a profile', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 21 } });
    global.fetch = vi.fn(async (url) => {
      if (String(url).includes('/players/name/')) return { ok: false, status: 404 };
      if (String(url).includes('/data/player/')) return {
        ok: true,
        json: async () => [{ date_sortable: '2026-08-23', member: 'Dave Holt', score: 102, location: 'Wing Point' }],
      };
      return { ok: true, json: async () => ({}) };
    });
    renderPage('name/Dave%20Holt');

    expect(await screen.findByRole('heading', { name: 'Dave Holt' })).toBeInTheDocument();
    expect(screen.getByText('Wing Point')).toBeInTheDocument();
    expect(screen.getAllByText('+102').length).toBeGreaterThan(0);
    expect(screen.queryByTitle('Change photo')).toBeNull();
    expect(global.fetch.mock.calls.every(([, options]) => !options?.method || options.method === 'GET')).toBe(true);
  });

  test.each([404, 500])('a failed name lookup (%s) does not invent a player', async (status) => {
    mockUsePlayerProfile.mockReturnValue({ profile: null });
    global.fetch = vi.fn(async (url) => String(url).includes('/players/name/')
      ? { ok: false, status }
      : { ok: true, json: async () => [] });
    renderPage('name/Unknown');

    expect(await screen.findByRole('button', { name: 'Go back' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Unknown' })).toBeNull();
    if (status === 500) expect(global.fetch).toHaveBeenCalledTimes(1);
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

  test('scoreboard totals quarters from the full round history, not in-app wins', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 999 } });
    renderPage();

    expect(await screen.findByText('Quarters')).toBeInTheDocument();
    expect(screen.getByText('Avg Quarters')).toBeInTheDocument();
    expect(screen.queryByText('Wins')).toBeNull();

    const scoreboard = [...document.querySelectorAll('.wgp-profile__stat')].map(el => el.textContent);
    expect(scoreboard).toEqual(['2Rounds', '+2Quarters', '+1Avg Quarters']);
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

  test('a round with hole-by-hole data expands to show it on click; the nudge appears for the rest', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 999 } });
    global.fetch = vi.fn(async (url) => {
      if (String(url).includes('/public-profile')) {
        return {
          ok: true,
          json: async () => ({
            ...baseProfile,
            game_history: [
              {
                date: '2026-06-13', location: 'Wingpoint', score: 4, source: 'database',
                holes: [{ hole: 1, quarters: 2, gross_score: 4 }, { hole: 2, quarters: -1, gross_score: 6 }],
              },
              { date: '2026-06-06', location: 'Wingpoint', score: -2, source: 'primary_sheet', holes: null },
            ],
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });
    renderPage();

    expect(await screen.findByText('▾ hole-by-hole')).toBeInTheDocument();
    const holeQuarters = () =>
      [...document.querySelectorAll('.wgp-profile__hole-quarters')].map(el => el.textContent);
    expect(holeQuarters()).toEqual([]); // collapsed by default

    fireEvent.click(screen.getByText('▾ hole-by-hole'));
    expect(holeQuarters()).toEqual(['+2', '-1']);

    expect(screen.getByText(/Score live in the app or scan your scorecard/)).toBeInTheDocument();
    expect(screen.getByText(/1 of 2 rounds already have it/)).toBeInTheDocument();
  });
});

describe('PlayerProfilePage badges', () => {
  test('renders earned badges with name and rarity', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 999 } });
    global.fetch = vi.fn(async (url) => {
      if (String(url).includes('/public-profile')) {
        return {
          ok: true,
          json: async () => ({
            ...baseProfile,
            badges: [
              { name: 'First Win', description: 'Won your first game', rarity: 'common', category: 'wins', emoji: '🎉' },
              { name: 'Legend', description: 'Legendary feat', rarity: 'legendary', emoji: '👑' },
            ],
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });
    renderPage();

    expect(await screen.findByText('First Win')).toBeInTheDocument();
    expect(screen.getByText('Legend')).toBeInTheDocument();
    expect(screen.queryByText(/No badges earned yet/)).toBeNull();
  });

  test('still shows the Badges section with a locked empty-state when a player has none', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 999 } });
    renderPage(); // baseProfile has badges: []

    expect(await screen.findByText(/Badges/)).toBeInTheDocument();
    expect(screen.getByText(/No badges earned yet/)).toBeInTheDocument();
    expect(screen.getAllByText('Locked').length).toBeGreaterThan(0);
  });

  test('clicking a badge on your own profile equips it and does nothing on someone else\'s', async () => {
    const badgeProfile = {
      ...baseProfile,
      badges: [{ id: 42, name: 'First Win', description: 'Won your first game', rarity: 'common', emoji: '🎉', showcased: false }],
    };
    global.fetch = vi.fn(async (url) => {
      if (String(url).includes('/api/badges/me/42/showcase')) {
        return { ok: true, json: async () => ({ showcased: true, position: 1 }) };
      }
      if (String(url).includes('/public-profile')) {
        return { ok: true, json: async () => badgeProfile };
      }
      return { ok: true, json: async () => ({}) };
    });

    // Someone else's profile: clicking the badge must not call the showcase endpoint.
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 999 } });
    const { unmount } = renderPage();
    fireEvent.click(await screen.findByText('First Win'));
    await new Promise(r => setTimeout(r, 0));
    expect(global.fetch.mock.calls.some(([url]) => String(url).includes('/showcase'))).toBe(false);
    unmount();

    // Own profile: clicking equips it.
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 21 } });
    renderPage();
    fireEvent.click(await screen.findByText('First Win'));
    await waitFor(() => {
      expect(global.fetch.mock.calls.some(([url]) => String(url).includes('/api/badges/me/42/showcase'))).toBe(true);
    });
  });
});

describe('PlayerProfilePage handicap display (issue #320)', () => {
  test('shows "Pending" with a GHIN hint when handicap_source is "default"', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 999 } });
    global.fetch = vi.fn(async (url) => {
      if (String(url).includes('/public-profile')) {
        return { ok: true, json: async () => ({ ...baseProfile, handicap: 18.0, handicap_source: 'default' }) };
      }
      return { ok: true, json: async () => ({}) };
    });
    renderPage();

    expect(await screen.findByText('Pending')).toBeInTheDocument();
    expect(screen.getByText(/GHIN sync pending/)).toBeInTheDocument();
    // The 18.0 placeholder must NOT be shown as a real handicap.
    expect(screen.queryByText('18')).toBeNull();
    expect(screen.queryByText('18.0')).toBeNull();
  });

  test('shows "Pending" when handicap_source is missing', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 999 } });
    // baseProfile has no handicap_source at all.
    renderPage();

    expect(await screen.findByText('Pending')).toBeInTheDocument();
    expect(screen.getByText(/GHIN sync pending/)).toBeInTheDocument();
  });

  test('shows the GHIN handicap value with a freshness note when source is "ghin"', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: { id: 999 } });
    global.fetch = vi.fn(async (url) => {
      if (String(url).includes('/public-profile')) {
        return {
          ok: true,
          json: async () => ({
            ...baseProfile,
            handicap: 7.6,
            handicap_source: 'ghin',
            ghin_last_updated: '2026-07-01T12:00:00Z',
          }),
        };
      }
      return { ok: true, json: async () => ({}) };
    });
    renderPage();

    expect(await screen.findByText('7.6')).toBeInTheDocument();
    expect(screen.getByText(/GHIN ·/)).toBeInTheDocument();
    expect(screen.queryByText('Pending')).toBeNull();
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
