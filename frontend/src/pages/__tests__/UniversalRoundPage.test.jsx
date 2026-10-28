import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes, Link } from 'react-router-dom';
import SimpleScorekeeperPage from '../SimpleScorekeeperPage';
import RoundStoryPage from '../RoundStoryPage';
import syncManager from '../../services/syncManager';

const authFetch = vi.fn((...args) => fetch(...args));
vi.mock('../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => authFetch }));
vi.mock('@auth0/auth0-react', () => ({ useAuth0: () => ({ isAuthenticated: false }) }));
vi.mock('../../services/syncManager', () => ({ default: { queueSync: vi.fn(), reconcileOnLoad: vi.fn(), loadLocalGameState: vi.fn() } }));
vi.mock('../../components/game', () => ({ SimpleScorekeeper: () => <div>Live editor</div> }));
vi.mock('../../theme/Provider', () => ({ useTheme: () => ({ colors: {} }) }));
vi.mock('../../components/ui', () => ({ Card: ({ children }) => <div>{children}</div> }));

const summary = { game_id: 'fixture-round', revision: 7, detail_coverage: 'totals_only', players: [{ participant_id: 'p1', name: 'Avery', quarters: null }], hole_history: [], capabilities: {}, conflict_count: 0 };
function renderRound(path = '/game/fixture-round') {
  return render(<MemoryRouter initialEntries={[path]}><Link to="/game/second">Other UUID</Link><Routes>
    <Route path="/game/:gameId" element={<SimpleScorekeeperPage />} />
    <Route path="/rounds/:date/:group" element={<RoundStoryPage />} />
  </Routes></MemoryRouter>);
}
function network(overrides = {}) {
  global.fetch.mockImplementation(async (url) => {
    const path = String(url);
    if (path.includes('/state')) return { ok: true, json: async () => ({ game_status: 'completed' }) };
    if (path.includes('/round-summary')) return { ok: true, json: async () => ({ ...summary, ...overrides }) };
    if (path.includes('/discussion')) return { ok: true, json: async () => ({ comments: [], reactions: [] }) };
    return { ok: false, status: 404, json: async () => ({}) };
  });
}
beforeEach(() => { vi.clearAllMocks(); network(); });
it('resets accepted scores, discussion and photo controls when navigating to another UUID', async () => {
  fetch.mockImplementation(async url => {
    const path = String(url);
    const second = path.includes('/second/');
    const data = path.endsWith('/state') ? { game_status: 'completed' }
      : path.endsWith('/round-summary') ? { ...summary, players: [{ participant_id: 'slot', name: second ? 'Blair' : 'Avery', quarters: second ? 2.5 : null }] }
      : path.endsWith('/discussion') ? { comments: [{ id: second ? 2 : 1, author_name: 'Author', body: second ? 'Second discussion' : 'First discussion', reactions: [] }], reactions: [] } : null;
    return { ok: !!data, status: data ? 200 : 404, json: async () => data };
  });
  renderRound();
  expect(await screen.findByText('Avery')).toBeVisible();
  expect(await screen.findByText('First discussion')).toBeVisible();
  expect(screen.getByLabelText('Photo panel height')).toBeVisible();
  fireEvent.click(screen.getByRole('link', { name: 'Other UUID' }));
  expect(await screen.findByText('Blair')).toBeVisible();
  expect(await screen.findByText('Second discussion')).toBeVisible();
  expect(screen.queryByText('Avery')).toBeNull();
  expect(screen.queryByText('First discussion')).toBeNull();
  expect(screen.getByText(/\+2.5/)).toBeVisible();
  expect(syncManager.reconcileOnLoad).not.toHaveBeenCalled();
});
it('shows a completed totals-only game without live sync or fabricated holes', async () => {
  renderRound();
  expect(await screen.findByText('Avery')).toBeVisible();
  expect(screen.getAllByText(/Not recorded/).length).toBeGreaterThan(0);
  expect(screen.queryByRole('button', { name: /mark complete/i })).toBeNull();
  expect(screen.queryByText('Live editor')).toBeNull();
  expect(syncManager.queueSync).not.toHaveBeenCalled();
  expect(syncManager.reconcileOnLoad).not.toHaveBeenCalled();
  expect(fetch.mock.calls.every(([url, options]) => !options?.method || options.method === 'GET')).toBe(true);
  expect(fetch.mock.calls.some(([url]) => /courses/.test(String(url)))).toBe(false);
});
it('does not mistake cached completed data for server state', async () => {
  fetch.mockRejectedValue(new Error('Server unavailable'));
  syncManager.loadLocalGameState.mockReturnValue({ players: [{ name: 'Cached' }], gameStatus: 'completed' });
  renderRound();
  expect(await screen.findByRole('alert')).toHaveTextContent(/Server unavailable/);
  expect(screen.queryByText('Cached')).toBeNull();
});
it('retains the active editor only after the lifecycle read', async () => {
  fetch.mockResolvedValue({ ok: true, json: async () => ({ game_status: 'in_progress', players: [] }) });
  renderRound();
  expect(await screen.findByText('Live editor')).toBeVisible();
});
it('resolves ambiguous old aliases without rendering sheet scores or guessing a UUID', async () => {
  fetch.mockResolvedValue({ ok: true, json: async () => ({ status: 'ambiguous', game_ids: ['first', 'second'] }) });
  renderRound('/rounds/06-Oct/A?location=Old');
  expect(await screen.findByText(/ambiguous/i)).toBeVisible();
  expect(screen.getByRole('link', { name: /first/ })).toHaveAttribute('href', '/game/first');
  expect(screen.getByRole('link', { name: /second/ })).toHaveAttribute('href', '/game/second');
});
it('resolves an old URL into the shared UUID page without a second score reader', async () => {
  const requests = [];
  const fallback = fetch.getMockImplementation();
  fetch.mockImplementation(async (url, options) => {
    requests.push(String(url));
    if (String(url).includes('/aliases?')) return { ok: true, json: async () => ({ status: 'resolved', game_ids: ['fixture-round'] }) };
    return fallback(url, options);
  });
  renderRound('/rounds/06-Oct/B?location=Old');
  expect(await screen.findByText('Avery')).toBeVisible();
  expect(requests.some(path => path.includes('/fixture-round/round-summary'))).toBe(true);
  expect(requests.some(path => path.includes('/data/rounds/06-Oct'))).toBe(false);
  expect(syncManager.queueSync).not.toHaveBeenCalled();
});
it('renders partial coverage and a conflict without fabricating a complete scorecard', async () => {
  network({ detail_coverage: 'partial', conflict_count: 1, hole_history: [{ hole: 1, points_delta: { p1: 2.5 } }] });
  renderRound();
  expect((await screen.findAllByText('Avery'))[0]).toBeVisible();
  expect(screen.queryByText('Live editor')).toBeNull();
  expect(screen.getAllByText(/partial|review|conflict/i).length).toBeGreaterThan(0);
  expect(syncManager.reconcileOnLoad).not.toHaveBeenCalled();
});
it('shows loading and then the actual summary error', async () => {
  fetch.mockImplementation(async (url) => String(url).includes('/state')
    ? { ok: true, json: async () => ({ game_status: 'completed' }) }
    : { ok: false, status: 503, json: async () => ({ detail: 'Summary unavailable' }) });
  renderRound();
  expect(screen.getByText(/Loading/)).toBeVisible();
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Summary unavailable'));
});
