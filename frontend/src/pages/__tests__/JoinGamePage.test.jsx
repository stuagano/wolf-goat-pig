import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import JoinGamePage from '../JoinGamePage';

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({ user: null, isAuthenticated: false }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => vi.fn(), useParams: () => ({ code: 'ABC123' }) };
});

vi.mock('../../theme/Provider', async () => {
  const factories = await import('../../test-utils/mockFactories');
  return {
    ThemeProvider: ({ children }) => <div>{children}</div>,
    useTheme: () => factories.createMockTheme(),
  };
});

const SUGGESTIONS = [
  { name: 'Rainer Richardson', handicap: 0.2, player_profile_id: 40 },
  { name: 'Stuart Gano', handicap: 12.9, player_profile_id: 20 },
];

beforeEach(() => {
  global.fetch = vi.fn(async (url) => {
    if (String(url).includes('/games/roster-suggestions')) {
      return { ok: true, json: async () => ({ players: SUGGESTIONS }) };
    }
    if (String(url).includes('/games/join/')) {
      return {
        ok: true,
        json: async () => ({
          status: 'joined',
          game_id: 'g1',
          handicap: 0.2,
          handicap_source: 'profile',
        }),
      };
    }
    return { ok: true, json: async () => ({}) };
  });
});

describe('JoinGamePage handicaps', () => {
  test('rostered name pulls real handicap and omits it on submit', async () => {
    render(<MemoryRouter><JoinGamePage /></MemoryRouter>);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/games/roster-suggestions'),
    ));

    fireEvent.change(screen.getByPlaceholderText('Enter your name'), {
      target: { value: 'Rainer Richardson' },
    });
    expect(screen.getByDisplayValue('0.2')).toBeInTheDocument();
    expect(screen.getByText('Roster handicap 0.2')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Join Game'));
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/games/join/ABC123'),
      expect.anything(),
    ));

    const call = global.fetch.mock.calls.find(([url]) => String(url).includes('/games/join/'));
    const body = JSON.parse(call[1].body);
    expect(body.handicap).toBeNull();
    expect(body.player_profile_id).toBe(40);
  });

  test('hand-typed handicap is sent as an override', async () => {
    render(<MemoryRouter><JoinGamePage /></MemoryRouter>);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/games/roster-suggestions'),
    ));

    fireEvent.change(screen.getByPlaceholderText('Enter your name'), {
      target: { value: 'Rainer Richardson' },
    });
    fireEvent.change(screen.getByDisplayValue('0.2'), { target: { value: '4' } });
    expect(screen.getByText('Handicap set by hand for this round')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Join Game'));
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/games/join/ABC123'),
      expect.anything(),
    ));

    const call = global.fetch.mock.calls.find(([url]) => String(url).includes('/games/join/'));
    expect(JSON.parse(call[1].body).handicap).toBe(4);
  });
});
