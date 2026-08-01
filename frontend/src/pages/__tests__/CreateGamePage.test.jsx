import React from 'react';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import CreateGamePage from '../CreateGamePage';

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({ user: null, isAuthenticated: false }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => vi.fn() };
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
  { name: 'Mark Richardson', handicap: 9.1, player_profile_id: 47 },
  { name: 'Stuart Gano', handicap: 12.9, player_profile_id: 20 },
  { name: 'Hart Williams', handicap: 7.4, player_profile_id: 39 },
  // Shares the "Stu" prefix with Stuart Gano, so that prefix must stay ambiguous.
  { name: 'Stu Sutorius', handicap: 1.5, player_profile_id: 55 },
];

beforeEach(() => {
  global.fetch = vi.fn(async (url) => {
    if (String(url).includes('/games/roster-suggestions')) {
      return { ok: true, json: async () => ({ players: SUGGESTIONS }) };
    }
    if (String(url).includes('/courses')) {
      return { ok: true, json: async () => ({ 'Wing Point Golf & Country Club': {} }) };
    }
    return { ok: true, json: async () => ({ game_id: 'g1', has_ghosts: false }) };
  });
});

const renderPage = async () => {
  render(<MemoryRouter><CreateGamePage /></MemoryRouter>);
  // Wait for the roster fetch so name matching has data to work with.
  await screen.findByText(/Not on the roster|Players \(4\)/);
};

const nameField = (i) => screen.getByLabelText(`Player ${i} name`);
const handicapField = (i) => screen.getByLabelText(`Player ${i} handicap`);

const fillRoster = async () => {
  fireEvent.change(nameField(1), { target: { value: 'Rainer Richardson' } });
  fireEvent.change(nameField(2), { target: { value: 'Mark Richardson' } });
  fireEvent.change(nameField(3), { target: { value: 'Stuart Gano' } });
  fireEvent.change(nameField(4), { target: { value: 'Hart Williams' } });
};

const submittedPlayers = () => {
  const call = global.fetch.mock.calls.find(([url]) => String(url).includes('/games/create-custom'));
  return JSON.parse(call[1].body).players;
};

describe('CreateGamePage handicaps', () => {
  test('a rostered name pulls its real handicap instead of the 18 default', async () => {
    await renderPage();
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/games/roster-suggestions')));

    fireEvent.change(nameField(1), { target: { value: 'Rainer Richardson' } });

    expect(handicapField(1)).toHaveValue(0.2);
    expect(screen.getByText('Roster handicap 0.2')).toBeInTheDocument();
  });

  test('an unambiguous partial name still resolves, and blur completes it', async () => {
    await renderPage();
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/games/roster-suggestions')));

    fireEvent.change(nameField(1), { target: { value: 'Rainer' } });
    expect(handicapField(1)).toHaveValue(0.2);

    fireEvent.blur(nameField(1));
    expect(nameField(1)).toHaveValue('Rainer Richardson');
  });

  test('an ambiguous prefix does not guess a handicap', async () => {
    await renderPage();
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/games/roster-suggestions')));

    // "Stu" prefixes both Stuart Gano and Stu Sutorius — picking either would be a guess.
    fireEvent.change(nameField(1), { target: { value: 'Stu' } });

    expect(handicapField(1)).toHaveValue(18);
    expect(screen.getByText('Not on the roster — will play off 18')).toBeInTheDocument();
  });

  test('a name that matches nothing is flagged instead of silently playing off 18', async () => {
    await renderPage();
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/games/roster-suggestions')));

    fireEvent.change(nameField(1), { target: { value: 'Unknown Guest' } });

    expect(screen.getByText('Not on the roster — will play off 18')).toBeInTheDocument();
  });

  test('omits the handicap so the server uses the roster value', async () => {
    await renderPage();
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/games/roster-suggestions')));

    await fillRoster();
    fireEvent.click(screen.getByText(/Start Game/));

    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/games/create-custom'),
      expect.anything(),
    ));

    const players = submittedPlayers();
    expect(players.map((p) => p.handicap)).toEqual([null, null, null, null]);
    expect(players.map((p) => p.player_profile_id)).toEqual([40, 47, 20, 39]);
  });

  test('a hand-typed handicap is sent as an explicit override', async () => {
    await renderPage();
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/games/roster-suggestions')));

    await fillRoster();
    fireEvent.change(handicapField(1), { target: { value: '4' } });
    expect(screen.getByText('Handicap set by hand for this round')).toBeInTheDocument();

    fireEvent.click(screen.getByText(/Start Game/));
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/games/create-custom'),
      expect.anything(),
    ));

    expect(submittedPlayers()[0].handicap).toBe(4);
  });

  test('typing a name after editing the handicap keeps the typed number', async () => {
    await renderPage();
    await waitFor(() => expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/games/roster-suggestions')));

    fireEvent.change(handicapField(1), { target: { value: '4' } });
    fireEvent.change(nameField(1), { target: { value: 'Rainer Richardson' } });

    expect(handicapField(1)).toHaveValue(4);
  });
});
