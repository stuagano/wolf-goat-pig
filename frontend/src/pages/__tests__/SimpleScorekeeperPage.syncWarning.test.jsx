import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import syncManager from '../../services/syncManager';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import SimpleScorekeeperPage from '../SimpleScorekeeperPage';
import useGameData from '../../hooks/useGameData';

vi.mock('../../hooks/useGameData', () => ({ default: vi.fn() }));
vi.mock('../../hooks/useRoundCard', () => ({ default: () => ({ card: { can_edit: true } }) }));
vi.mock('../../components/game', () => ({
  SimpleScorekeeper: ({ players, initialHoleHistory, initialCurrentHole }) => {
    const [draft, setDraft] = React.useState('');
    return (
      <section aria-label="Playable round">
        {players[0].name}: hole {initialCurrentHole}; saved strokes {initialHoleHistory[0].gross_scores.p1}
        <button type="button">Edit scores</button>
        <input aria-label="Unsaved strokes" value={draft} onChange={event => setDraft(event.target.value)} />
      </section>
    );
  },
}));
vi.mock('../../components/game/ScorecardBackfill', () => ({
  default: ({ players, holeHistory }) => (
    <section aria-label="Backfill editor">
      {players[0].name}: saved strokes {holeHistory[0].gross_scores.p1}
      <button type="button">Edit missing holes</button>
    </section>
  ),
}));

const realUseGameData = (await vi.importActual('../../hooks/useGameData')).default;
const reload = vi.fn();
const retrySync = vi.fn();
const syncError = 'Could not queue cached scores for sync: Unable to store the correction on this device.';
const game = {
  players: [{ id: 'p1', name: 'Alice' }],
  holeHistory: [{ hole: 1, gross_scores: { p1: 5 } }],
  currentHole: 2,
  standings: { p1: 2 },
  courseName: 'Cached GC',
  baseWager: 1,
  isComplete: false,
};

function Page() {
  return (
    <MemoryRouter initialEntries={['/game/g1']}>
      <Routes><Route path="/game/:gameId" element={<SimpleScorekeeperPage />} /></Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  reload.mockReset();
  retrySync.mockReset();
  useGameData.mockReset();
  useGameData.mockReturnValue({ loading: false, error: null, syncError, game, reload, retrySync });
});

test('shows an accessible sync warning alongside the usable cached round and retries without reload', () => {
  render(<Page />);
  expect(screen.getByRole('alert')).toHaveTextContent(syncError);
  expect(screen.getByRole('region', { name: 'Playable round' })).toHaveTextContent('Alice: hole 2; saved strokes 5');
  expect(screen.getByRole('button', { name: 'Edit scores' })).toBeEnabled();
  expect(screen.queryByText(/Error Loading Game|Invalid Game Data/)).toBeNull();
  expect(screen.getByRole('alert')).not.toHaveTextContent(/will retry|pending sync/i);
  fireEvent.click(screen.getByRole('button', { name: 'Retry sync' }));
  expect(retrySync).toHaveBeenCalledTimes(1);
  expect(reload).not.toHaveBeenCalled();
});

test('keeps the warning and retry available in the completed-round backfill editor', () => {
  useGameData.mockReturnValue({ loading: false, error: null, syncError, game: { ...game, isComplete: true }, reload, retrySync });
  render(<Page />);
  fireEvent.click(screen.getByRole('button', { name: /Fill in holes/ }));
  expect(screen.getByRole('alert')).toHaveTextContent(syncError);
  expect(screen.getByRole('region', { name: 'Backfill editor' })).toHaveTextContent('Alice: saved strokes 5');
  expect(screen.getByRole('button', { name: 'Edit missing holes' })).toBeEnabled();
  expect(screen.queryByText(/Error Loading Game|Invalid Game Data/)).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Retry sync' }));
  expect(retrySync).toHaveBeenCalledTimes(1);
  expect(reload).not.toHaveBeenCalled();
});

test('removes stale warning after reload clears the sync error without losing the round', () => {
  const { rerender } = render(<Page />);
  expect(screen.getByRole('alert')).toBeInTheDocument();
  useGameData.mockReturnValue({ loading: false, error: null, syncError: null, game, reload, retrySync });
  rerender(<Page />);
  expect(screen.queryByRole('alert')).toBeNull();
  expect(screen.queryByRole('button', { name: 'Retry sync' })).toBeNull();
  expect(screen.getByRole('region', { name: 'Playable round' })).toHaveTextContent('saved strokes 5');
});

test.each([true, false])('real hook preserves an unsaved editor draft when retry storage succeeds=%s', async (succeeds) => {
  const setItem = localStorage.setItem.getMockImplementation();
  let storageFails = true;
  localStorage.clear();
  syncManager.saveLocalGameState('g1', { ...game, playerStandings: game.standings });
  localStorage.setItem.mockImplementation((key, value) => {
    if (key === 'wgp-sync_sync-queue' && storageFails) throw new Error('Queue storage full');
    return setItem(key, value);
  });
  vi.stubGlobal('navigator', { onLine: false });
  vi.spyOn(console, 'warn').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});
  global.fetch.mockRejectedValue(new Error('offline'));
  useGameData.mockImplementation(realUseGameData);
  try {
    render(<Page />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/could not queue/i);
    const input = screen.getByRole('textbox', { name: 'Unsaved strokes' });
    fireEvent.change(input, { target: { value: '7' } });
    storageFails = !succeeds;
    fireEvent.click(screen.getByRole('button', { name: 'Retry sync' }));
    await waitFor(() => {
      if (succeeds) expect(screen.queryByRole('alert')).toBeNull();
      else expect(screen.getByRole('alert')).toHaveTextContent(/unable to store/i);
      expect(screen.getByRole('textbox', { name: 'Unsaved strokes' })).toHaveValue('7');
    });
    expect(screen.getByRole('textbox', { name: 'Unsaved strokes' })).toBe(input);
    expect(screen.queryByText('Loading Game...')).toBeNull();
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(syncManager.getSyncQueue()).toHaveLength(succeeds ? 1 : 0);
    if (succeeds) {
      // Retry queues the saved cache, not the still-unsubmitted editor draft.
      expect(syncManager.getSyncQueue()[0].payload.optional_details['1'].gross_scores.p1).toBe(5);
    }
    expect(screen.queryByText(/saved to the server/i)).toBeNull();
  } finally {
    vi.restoreAllMocks();
    localStorage.setItem.mockImplementation(setItem);
    localStorage.clear();
    vi.unstubAllGlobals();
  }
});

test('still shows the fatal load error when there is no usable round', () => {
  useGameData.mockReturnValue({ loading: false, error: 'Failed to load game', syncError: null, game: null, reload });
  render(<Page />);
  expect(screen.getByText(/Error Loading Game/)).toBeInTheDocument();
  expect(screen.queryByRole('region', { name: 'Playable round' })).toBeNull();
  expect(screen.queryByRole('button', { name: 'Retry sync' })).toBeNull();
});
