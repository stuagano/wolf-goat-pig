import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import Leaderboard from '../../components/game/Leaderboard';
import PlayerProfilePage from '../PlayerProfilePage';
import AccountPage from '../AccountPage';
import CompletedGamesPage from '../CompletedGamesPage';
import { api } from '../../api/client';

const user = { name: 'Alex', email: 'alex@example.test' };
const getToken = vi.fn().mockResolvedValue('test-token');
vi.mock('@auth0/auth0-react', () => ({ useAuth0: () => ({ user, isAuthenticated: true }) }));
vi.mock('../../hooks/useAccessToken', () => ({ useAccessToken: () => ({ getToken }) }));
vi.mock('../../hooks/usePlayerProfile', () => ({ usePlayerProfile: () => ({ profile: { id: 1 }, isAdmin: false }) }));
vi.mock('../../hooks/useFeatureFlags', () => ({ useFeatureFlags: () => ({ livsow: false }) }));
vi.mock('../../theme/Provider', () => ({ useTheme: () => ({ colors: {} }) }));
vi.mock('../../components/ui', () => ({ Card: ({ children }) => <div>{children}</div> }));
vi.mock('../../components/auth/ClubPlayerSection', () => ({ default: () => null }));
vi.mock('../../components/signup/PlayerAvailability', () => ({ default: () => null }));
vi.mock('../../components/signup/EmailPreferences', () => ({ default: () => null }));
vi.mock('../../components/signup/MyMatches', () => ({ default: () => null }));
vi.mock('../../components/game/CommissionerChat', () => ({ default: () => null }));
vi.mock('../../context', () => ({
  useSheetSync: () => ({ syncData: [], syncStatus: 'idle', performLiveSync: vi.fn() }),
}));
vi.mock('../../api/client', () => ({ api: { GET: vi.fn() } }));

const GAME_ID = '11111111-2222-4333-8444-555555555555';
const round = {
  game_id: GAME_ID,
  date: '25-Oct', date_sortable: '2026-10-25', group: 'A', location: 'Example Golf & Country Club',
  players: ['Alex', 'Blair', 'Casey', 'Drew', 'Evan', 'Frankie'].map((member, i) => ({
    member, quarters: [147, 82, -8, -16, -66, -139][i],
  })),
};
const storyPath = '/rounds/2026-10-25/A?location=Example+Golf+%26+Country+Club';
const historyRound = { ...round, date: round.date_sortable, score: -16, holes: [{ hole: 1, quarters: -16 }] };

function Destination() {
  const location = useLocation();
  return <div data-testid="destination">{location.pathname}{location.search}</div>;
}

function renderPage(page, path = '/start') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path={path.startsWith('/players/') ? '/players/:playerId' : '/start'} element={page} />
        <Route path="/game/:gameId" element={<Destination />} />
        <Route path="/rounds/:date/:group" element={<Destination />} />
      </Routes>
    </MemoryRouter>,
  );
}

function mockHistory(rounds) {
  global.fetch.mockImplementation(async (url) => ({
    ok: true,
    json: async () => String(url).includes('/public-profile')
      ? { name: 'Alex', badges: [], available_days: [], game_history: rounds }
      : String(url).includes('/players/me/history')
        ? { found: true, rounds_played: rounds.length, recent_rounds: rounds }
        : { name: 'Alex', description: '' },
  }));
}

beforeEach(() => localStorage.clear());

describe('leaderboard scorecard navigation', () => {
  function mockRounds(gameId = GAME_ID) {
    api.GET.mockImplementation(async (path) => ({ data: path === '/data/leaderboard/rounds'
      ? [{ ...round, game_id: gameId }]
      : path === '/data/leaderboard/scores'
        ? [{ ...round, ...round.players[0], game_id: gameId }]
        : {} }));
  }

  test.each(['Rounds', 'Best scores', 'Worst scores'])('%s opens the saved scorecard and preserves the story link', async (tab) => {
    mockRounds();
    renderPage(<Leaderboard />);
    fireEvent.click(screen.getByRole('tab', { name: tab }));
    const card = await screen.findByRole('link', { name: /Scorecard/ });
    expect(screen.getByRole('link', { name: '25-Oct' })).toHaveAttribute('href', storyPath);
    fireEvent.click(card);
    expect(await screen.findByTestId('destination')).toHaveTextContent(`/game/${GAME_ID}`);
  });

  test('same-date rounds open their own saved cards, never the first matching date', async () => {
    const secondId = 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee';
    api.GET.mockImplementation(async (path) => ({ data: path === '/data/leaderboard/rounds'
      ? [round, { ...round, game_id: secondId }]
      : path === '/data/leaderboard/scores' ? [] : {} }));
    renderPage(<Leaderboard />);
    fireEvent.click(screen.getByRole('tab', { name: 'Rounds' }));
    const cards = await screen.findAllByRole('link', { name: /Scorecard/ });
    expect(cards.map(card => card.getAttribute('href'))).toEqual([`/game/${GAME_ID}`, `/game/${secondId}`]);
    fireEvent.click(cards[1]);
    expect(await screen.findByTestId('destination')).toHaveTextContent(`/game/${secondId}`);
  });

  test.each(['Rounds', 'Best scores', 'Worst scores'])('%s keeps story navigation with no associated card', async (tab) => {
    mockRounds(null);
    renderPage(<Leaderboard />);
    fireEvent.click(screen.getByRole('tab', { name: tab }));
    const story = await screen.findByRole('link', { name: '25-Oct' });
    expect(screen.queryByRole('link', { name: /Scorecard/ })).toBeNull();
    fireEvent.click(story);
    expect(await screen.findByTestId('destination')).toHaveTextContent(storyPath);
  });
});

describe('history scorecard navigation', () => {
  test.each(['public profile', 'account'])('%s navigates the server-linked round to its scorecard', async (page) => {
    mockHistory([historyRound, { ...historyRound, game_id: null, date: '2026-10-24' },
      { date: '2026-10-23', score: 0 }]);
    renderPage(page === 'account' ? <AccountPage /> : <PlayerProfilePage />, page === 'account' ? '/start' : '/players/1');
    const card = await screen.findByRole('link', { name: /Scorecard/ });
    // Only one of the three history rows has a card: null and legacy omissions
    // must not become /game/null, /game/undefined, or guessed date-based URLs.
    expect(screen.getAllByRole('link', { name: /Scorecard/ })).toHaveLength(1);
    if (page === 'public profile') {
      expect(screen.getByRole('link', { name: 'Oct 25, 2026' })).toHaveAttribute('href', storyPath);
    }
    fireEvent.click(card);
    expect(await screen.findByTestId('destination')).toHaveTextContent(`/game/${GAME_ID}`);
  });

  test('public profile still opens the round story and expands local hole detail', async () => {
    mockHistory([historyRound]);
    renderPage(<PlayerProfilePage />, '/players/1');
    fireEvent.click(await screen.findByText('▾ hole-by-hole'));
    expect(document.querySelector('.wgp-profile__hole-quarters')).toHaveTextContent('-16');
    fireEvent.click(screen.getByRole('link', { name: 'Oct 25, 2026' }));
    expect(await screen.findByTestId('destination')).toHaveTextContent(storyPath);
  });
});

describe('completed games', () => {
  const game = { game_id: GAME_ID, player_count: 6, created_at: '2026-10-26T12:00:00', updated_at: '2026-10-27T12:00:00' };
  function mockGame(overrides = {}) {
    api.GET.mockResolvedValue({ data: { games: [{ ...game, ...overrides }], total_count: 1 }, response: { ok: true } });
  }

  test('uses played_at rather than scan/upload/update date and opens the same card', async () => {
    mockGame({ played_at: '2026-10-25' });
    renderPage(<CompletedGamesPage />);
    expect(await screen.findByText('Oct 25, 2026')).toBeInTheDocument();
    expect(screen.queryByText(/Oct 2[67], 2026/)).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: /View Results/ }));
    expect(await screen.findByTestId('destination')).toHaveTextContent(`/game/${GAME_ID}`);
  });

  test.each([
    [{}, 'Oct 27, 2026'],
    [{ played_at: null, updated_at: null }, 'Oct 26, 2026'],
  ])('falls back to existing timestamps for old responses: %j', async (overrides, date) => {
    mockGame(overrides);
    renderPage(<CompletedGamesPage />);
    expect(await screen.findByText(new RegExp(date))).toBeInTheDocument();
  });
});
