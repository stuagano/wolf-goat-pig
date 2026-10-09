import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Leaderboard from '../Leaderboard';
import { api } from '../../../api/client';
import { FeaturesProvider } from '../../../hooks/useFeatureFlags';

const standings = [
  { rank: 1, member: 'Alice', quarters: 40, rounds: 8, average: 5 },
  { rank: 2, member: 'Jeff', quarters: 10, rounds: 22, average: 0.5 },
  { rank: 3, member: 'Bob', quarters: -4, rounds: 21, average: -0.2 },
];

vi.mock('../../../context', () => ({
  useSheetSync: () => ({
    syncData: standings,
    syncStatus: 'idle',
    error: null,
    performLiveSync: vi.fn(),
  }),
}));
vi.mock('../../../api/client', () => ({ api: { GET: vi.fn() } }));

const best = [
  { date: '2-Aug', date_sortable: '2026-08-02', member: 'Jeff', quarters: 30, group: 'A' },
  { date: '1-Aug', date_sortable: '2026-08-01', member: 'Alice', quarters: 12, group: 'A' },
];
const worst = [
  { date: '3-Aug', date_sortable: '2026-08-03', member: 'Bob', quarters: -40, group: 'B' },
  { date: '4-Aug', date_sortable: '2026-08-04', member: 'Alice', quarters: -5, group: 'A' },
];
const games = [
  {
    date: '4-Aug',
    date_sortable: '2026-08-04',
    location: 'Wing Point',
    group: 'A',
    players: [{ member: 'Alice', quarters: -5 }, { member: 'Jeff', quarters: 5 }],
  },
  {
    date: '1-Aug',
    date_sortable: '2026-08-01',
    location: 'Gold Mountain',
    group: 'B',
    players: [{ member: 'Bob', quarters: 12 }],
  },
];

function mockApi() {
  api.GET.mockImplementation((path, options) => {
    if (path === '/data/leaderboard-config') return Promise.resolve({ data: {} });
    if (path === '/data/leaderboard/scores' && options?.params?.query?.kind === 'best') {
      return Promise.resolve({ data: best });
    }
    if (path === '/data/leaderboard/scores' && options?.params?.query?.kind === 'worst') {
      return Promise.resolve({ data: worst });
    }
    if (path === '/data/leaderboard/rounds') return Promise.resolve({ data: games });
    return Promise.resolve({ data: {} });
  });
}

function renderBoard() {
  global.fetch.mockResolvedValue({ json: async () => ({ features: { livsow: false } }) });
  return render(
    <MemoryRouter>
      <FeaturesProvider>
        <Leaderboard />
      </FeaturesProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  api.GET.mockReset();
  mockApi();
});

test.each([false, true])('LivSow team lookup respects the runtime flag: %s', async (enabled) => {
  global.fetch.mockResolvedValue({ json: async () => ({ features: { livsow: enabled } }) });
  render(
    <MemoryRouter>
      <FeaturesProvider>
        <Leaderboard />
      </FeaturesProvider>
    </MemoryRouter>,
  );
  await screen.findByText('Alice');
  await waitFor(() => expect(global.fetch).toHaveBeenCalled());
  if (enabled) {
    await waitFor(() => expect(api.GET).toHaveBeenCalledWith('/data/livsow/team-map'));
  } else {
    expect(api.GET).not.toHaveBeenCalledWith('/data/livsow/team-map');
  }
});

test('standings default to rank ascending and each header re-sorts', async () => {
  renderBoard();
  const names = () => screen.getAllByRole('row').slice(1).map((row) => row.textContent);
  await screen.findByText('Alice');
  expect(names()[0]).toContain('Alice');
  expect(names()[2]).toContain('Bob');

  fireEvent.click(screen.getByRole('button', { name: 'Sort by Quarters' }));
  expect(names()[0]).toContain('Alice');
  fireEvent.click(screen.getByRole('button', { name: 'Sort by Quarters' }));
  expect(names()[0]).toContain('Bob');

  fireEvent.click(screen.getByRole('button', { name: 'Sort by Player' }));
  expect(names()[0]).toContain('Alice');
  expect(names()[1]).toContain('Bob');
});

test('banquet filter keeps players with 20 or more rounds', async () => {
  renderBoard();
  await screen.findByText('Alice');
  fireEvent.click(screen.getByRole('button', { name: 'Banquet eligible' }));
  expect(screen.queryByText('Alice')).not.toBeInTheDocument();
  expect(screen.getByText('Jeff')).toBeInTheDocument();
  expect(screen.getByText('Bob')).toBeInTheDocument();
});

test('best and worst tabs show single-game date, player, and quarters', async () => {
  renderBoard();
  fireEvent.click(screen.getByRole('tab', { name: 'Best scores' }));
  expect(await screen.findByText('30')).toBeInTheDocument();
  const bestRows = screen.getAllByRole('row').slice(1).map((row) => row.textContent);
  expect(bestRows[0]).toContain('2-Aug');
  expect(bestRows[0]).toContain('Jeff');
  expect(bestRows[1]).toContain('Alice');

  fireEvent.click(screen.getByRole('tab', { name: 'Worst scores' }));
  const worstRows = screen.getAllByRole('row').slice(1).map((row) => row.textContent);
  expect(worstRows[0]).toContain('-40');
  expect(worstRows[0]).toContain('Bob');
  expect(worstRows[1]).toContain('Alice');
});

test('rounds tab is newest first and filters by player, date, score, and location', async () => {
  renderBoard();
  fireEvent.click(screen.getByRole('tab', { name: 'Rounds' }));
  expect(await screen.findByText('Wing Point')).toBeInTheDocument();
  const items = () => screen.getAllByRole('listitem').map((item) => item.textContent);
  expect(items()[0]).toContain('4-Aug');
  expect(items()[0]).toContain('Jeff');
  expect(items()[1]).toContain('Gold Mountain');

  fireEvent.change(screen.getByLabelText('Filter by player'), { target: { value: 'bob' } });
  expect(screen.queryByText('Wing Point')).not.toBeInTheDocument();
  expect(screen.getByText('Gold Mountain')).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText('Filter by player'), { target: { value: '' } });
  fireEvent.change(screen.getByLabelText('Filter by location'), { target: { value: 'wing' } });
  expect(screen.getByText('Wing Point')).toBeInTheDocument();
  expect(screen.queryByText('Gold Mountain')).not.toBeInTheDocument();

  fireEvent.change(screen.getByLabelText('Filter by location'), { target: { value: '' } });
  fireEvent.change(screen.getByLabelText('Filter by date'), { target: { value: '2026-08-01' } });
  expect(screen.getByText('Gold Mountain')).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText('Filter by date'), { target: { value: '' } });
  fireEvent.change(screen.getByLabelText('Filter by score'), { target: { value: '-5' } });
  expect(screen.getByText('Wing Point')).toBeInTheDocument();
  expect(screen.queryByText('Gold Mountain')).not.toBeInTheDocument();
});
