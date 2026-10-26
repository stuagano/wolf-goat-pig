import React, { useState } from 'react';
import { afterEach, describe, expect, test, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import EditHoleModal from '../EditHoleModal';
import Scorecard from '../Scorecard';
import useHoleSubmission, { standingsFromHistory } from '../../../hooks/useHoleSubmission';
import syncManager from '../../../services/syncManager';

const players = [{ id: 'p1', name: 'Alice' }, { id: 'p2', name: 'Bob' }];
const originalHole = {
  hole: 1,
  gross_scores: { p1: 4, p2: 5 },
  points_delta: { p1: 1, p2: -1 },
};

// Keep the selected hole snapshot, history, and standings in React state just
// like the scorekeeper/completed-round view. Assertions observe rendered state.
function CorrectionHarness({ syncHole }) {
  const [holeHistory, setHoleHistory] = useState([originalHole]);
  const [playerStandings, setPlayerStandings] = useState(() => standingsFromHistory(players, [originalHole]));
  const [editingHole, setEditingHole] = useState(originalHole);
  const { handleEditModalSave } = useHoleSubmission({
    players, holeHistory, setHoleHistory, setPlayerStandings,
    syncHole, currentHole: 19,
  });
  return <>
    <div aria-label="History">Alice strokes: {holeHistory[0].gross_scores.p1}; quarters: {holeHistory[0].points_delta.p1}</div>
    <div aria-label="Standings">Alice: {playerStandings.p1.quarters}; Bob: {playerStandings.p2.quarters}</div>
    <button onClick={() => setEditingHole(holeHistory[0])}>Reopen correction</button>
    <EditHoleModal embedded isOpen={editingHole !== null} holeData={editingHole}
      players={players} onSave={handleEditModalSave} onClose={() => setEditingHole(null)} />
  </>;
}

function editAndSave() {
  fireEvent.change(screen.getByLabelText('Alice strokes'), { target: { value: '6' } });
  fireEvent.change(screen.getByLabelText('Alice quarters'), { target: { value: '2' } });
  fireEvent.change(screen.getByLabelText('Bob quarters'), { target: { value: '-2' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save' }));
}

function expectOriginalState() {
  expect(screen.getByLabelText('History')).toHaveTextContent('Alice strokes: 4; quarters: 1');
  expect(screen.getByLabelText('Standings')).toHaveTextContent('Alice: 1; Bob: -1');
}

function expectCorrectedState() {
  expect(screen.getByLabelText('History')).toHaveTextContent('Alice strokes: 6; quarters: 2');
  expect(screen.getByLabelText('Standings')).toHaveTextContent('Alice: 2; Bob: -2');
}

// Cell corrections from the scorecard go through the same handler.
function ScorecardCorrectionHarness({ syncHole }) {
  const [holeHistory, setHoleHistory] = useState([originalHole]);
  const [playerStandings, setPlayerStandings] = useState(() => standingsFromHistory(players, [originalHole]));
  const { handleEditHoleFromScorecard } = useHoleSubmission({
    players, holeHistory, setHoleHistory, setPlayerStandings,
    syncHole, currentHole: 19,
  });
  return <>
    <div aria-label="History">Alice strokes: {holeHistory[0].gross_scores.p1}; quarters: {holeHistory[0].points_delta.p1}</div>
    <div aria-label="Standings">Alice: {playerStandings.p1.quarters}; Bob: {playerStandings.p2.quarters}</div>
    <Scorecard players={players} holeHistory={holeHistory} currentHole={19}
      onEditHole={handleEditHoleFromScorecard} defaultExpanded />
  </>;
}

const storageSetItem = localStorage.setItem.getMockImplementation();
let cleanupSync;
afterEach(() => {
  cleanupSync?.();
  cleanupSync = undefined;
  vi.restoreAllMocks();
  // setupTests installs a vi.fn rather than native Storage; restore its
  // implementation explicitly after quota-failure injection.
  localStorage.setItem.mockImplementation(storageSetItem);
  act(() => syncManager.clearQueue());
  vi.unstubAllGlobals();
});

describe('correction save through the real handler and editor', () => {
  test('does not publish while waiting, then publishes an acknowledged correction and reopens it', async () => {
    let resolveSave;
    render(<CorrectionHarness syncHole={() => new Promise(resolve => { resolveSave = resolve; })} />);
    editAndSave();
    expectOriginalState();
    expect(screen.getByRole('button', { name: 'Saving...' })).toBeDisabled();
    expect(screen.getByLabelText('Alice strokes')).toBeDisabled();
    expect(screen.getByLabelText('Alice quarters')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled();
    fireEvent.keyDown(screen.getByRole('region'), { key: 'Escape' });
    expect(screen.getByLabelText('Alice strokes')).toBeVisible();
    await act(async () => resolveSave({ success: true, synced: true }));
    expectCorrectedState();
    expect(screen.queryByLabelText('Alice strokes')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Reopen correction' }));
    expect(screen.getByLabelText('Alice strokes')).toHaveValue('6');
    expect(screen.getByLabelText('Alice quarters')).toHaveValue('2');
  });

  test('an unexpected thrown network error keeps edits available for a successful retry', async () => {
    const syncHole = vi.fn().mockRejectedValueOnce(new TypeError('Failed to fetch'))
      .mockResolvedValueOnce({ success: true, synced: true });
    render(<CorrectionHarness syncHole={syncHole} />);
    editAndSave();
    expect(await screen.findByRole('alert')).toHaveTextContent('Failed to fetch');
    expect(screen.getByRole('alert')).toHaveTextContent(/retry/i);
    expectOriginalState();
    expect(screen.getByLabelText('Alice strokes')).toHaveValue('6');
    expect(screen.getByLabelText('Bob quarters')).toHaveValue('-2');
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(screen.queryByLabelText('Alice strokes')).toBeNull());
    expectCorrectedState();
  });

  test.each([undefined, { success: true }, { success: false, queued: true }])(
    'does not publish an unconfirmed result %j', async (result) => {
      render(<CorrectionHarness syncHole={async () => result} />);
      editAndSave();
      expect(await screen.findByRole('alert')).toHaveTextContent(/retry/i);
      expectOriginalState();
      expect(screen.getByLabelText('Alice strokes')).toHaveValue('6');
    },
  );

  test.each(['offline', 'network failure'])('real sync manager queues a correction on %s, and the editor explicitly reports pending sync', async (mode) => {
    vi.stubGlobal('navigator', { onLine: mode !== 'offline' });
    const fetchWithAuth = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));
    cleanupSync = syncManager.setupAutoSync(fetchWithAuth);
    render(<CorrectionHarness syncHole={(...args) => syncManager.syncHoleData('correction-game', ...args)} />);
    editAndSave();
    expect(await screen.findByRole('status')).toHaveTextContent(/pending sync/i);
    expect(screen.getByRole('status')).toHaveTextContent(/not saved to the server/i);
    expectCorrectedState();
    expect(screen.getByLabelText('Alice strokes')).toHaveValue('6');
    const queue = syncManager.getSyncQueue();
    expect(queue).toHaveLength(1);
    expect(queue[0].payload.hole_quarters['1']).toEqual({ p1: 2, p2: -2 });
    expect(queue[0].payload.optional_details['1'].gross_scores).toEqual({ p1: 6, p2: 5 });
    expect(queue[0].payload.current_hole).toBe(19);
    if (mode === 'offline') expect(fetchWithAuth).not.toHaveBeenCalled();
  });

  describe.each([
    ['hole editor', CorrectionHarness, () => editAndSave(), () => screen.getByLabelText('Alice strokes')],
    ['scorecard editor', ScorecardCorrectionHarness, () => {
      fireEvent.click(screen.getByText('Front 9'));
      fireEvent.click(screen.getAllByTitle('Click to edit')[0]);
      fireEvent.change(screen.getAllByRole('spinbutton')[0], { target: { value: '6' } });
      fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    }, () => screen.getAllByRole('spinbutton')[0]],
  ])('%s queued outcomes', (_name, Harness, submit, strokesInput) => {
    test.each([200, 422])('observes the exact queued save HTTP %s outcome without discarding edits', async (status) => {
      vi.stubGlobal('navigator', { onLine: false });
      cleanupSync = syncManager.setupAutoSync(async () => ({
        ok: status === 200, status, headers: new Headers({ 'X-Request-ID': 'queued-rejection-ref' }),
        json: async () => ({ detail: 'Correction rejected on retry' }),
      }));
      render(<Harness syncHole={(...args) => syncManager.syncHoleData('queued-outcome', ...args)} />);
      submit();
      expect(await screen.findByRole('status')).toHaveTextContent(/pending sync/i);
      vi.stubGlobal('navigator', { onLine: true });
      await act(async () => { await syncManager.processQueue(); });
      expect(syncManager.getSyncQueue()).toHaveLength(0);
      if (status === 200) {
        expect(screen.getByRole('status')).toHaveTextContent(/saved to the server/i);
        expect(screen.getByRole('status')).not.toHaveTextContent(/not saved|pending|retry automatically/i);
      } else {
        expect(screen.getByRole('alert')).toHaveTextContent('Correction rejected on retry');
        expect(screen.getByRole('alert')).toHaveTextContent('queued-rejection-ref');
        expect(screen.queryByText(/retry automatically/i)).toBeNull();
      }
      expect(String(strokesInput().value)).toBe('6');
      expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled();
    });

    test.each([200, 422])('changing the draft invalidates pending feedback even after the older HTTP %s outcome', async (status) => {
      vi.stubGlobal('navigator', { onLine: false });
      cleanupSync = syncManager.setupAutoSync(async () => ({
        ok: status === 200, status, json: async () => ({ detail: 'Older draft rejected' }),
      }));
      render(<Harness syncHole={(...args) => syncManager.syncHoleData('changed-draft', ...args)} />);
      submit();
      expect(await screen.findByRole('status')).toHaveTextContent(/pending sync/i);
      fireEvent.change(strokesInput(), { target: { value: '7' } });
      expect(screen.getByRole('status')).toHaveTextContent(/unsaved changes/i);
      expect(screen.getByRole('status')).not.toHaveTextContent(/pending sync/i);
      vi.stubGlobal('navigator', { onLine: true });
      await act(async () => { await syncManager.processQueue(); });
      expect(screen.getByRole('status')).toHaveTextContent(/unsaved changes/i);
      expect(String(strokesInput().value)).toBe('7');
      if (status === 422) expect(screen.getByRole('alert')).toHaveTextContent('Older draft rejected');
    });

    test('a later queue revision is not discarded or marked saved by an older in-flight success', async () => {
      vi.stubGlobal('navigator', { onLine: false });
      let resolveAttempt;
      const fetchWithAuth = vi.fn().mockImplementationOnce(() => new Promise(resolve => { resolveAttempt = resolve; }))
        .mockResolvedValue({ ok: true });
      cleanupSync = syncManager.setupAutoSync(fetchWithAuth);
      render(<Harness syncHole={(...args) => syncManager.syncHoleData('versioned-save', ...args)} />);
      submit();
      await screen.findByRole('status');
      vi.stubGlobal('navigator', { onLine: true });
      let drain;
      act(() => { drain = syncManager.processQueue(); });
      vi.stubGlobal('navigator', { onLine: false });
      fireEvent.change(strokesInput(), { target: { value: '7' } });
      fireEvent.click(screen.getByRole('button', { name: 'Save' }));
      await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent(/pending sync/i));
      await act(async () => { resolveAttempt({ ok: true }); await drain; });
      expect(screen.getByRole('status')).toHaveTextContent(/pending sync/i);
      expect(syncManager.getSyncQueue()[0].payload.optional_details['1'].gross_scores.p1).toBe(7);
      vi.stubGlobal('navigator', { onLine: true });
      await act(async () => { await syncManager.processQueue(); });
      expect(screen.getByRole('status')).toHaveTextContent('was saved to the server');
      expect(String(strokesInput().value)).toBe('7');
    });

    test('a superseded revision is unconfirmed, not marked saved by a different revision', async () => {
      vi.stubGlobal('navigator', { onLine: false });
      cleanupSync = syncManager.setupAutoSync(async () => ({ ok: true }));
      render(<Harness syncHole={(...args) => syncManager.syncHoleData('superseded-save', ...args)} />);
      submit();
      await screen.findByRole('status');
      await act(async () => {
        await syncManager.syncHoleData('superseded-save', { 1: { p1: 0, p2: 0 } }, { 1: { gross_scores: { p1: 8, p2: 5 } } }, 19);
      });
      expect(screen.getByRole('status')).toHaveTextContent(/not confirmed/i);
      vi.stubGlobal('navigator', { onLine: true });
      await act(async () => { await syncManager.processQueue(); });
      expect(screen.getByRole('status')).toHaveTextContent(/not confirmed/i);
      expect(String(strokesInput().value)).toBe('6');
    });

    test('clearing the queue without acknowledgement does not claim success', async () => {
      vi.stubGlobal('navigator', { onLine: false });
      render(<Harness syncHole={(...args) => syncManager.syncHoleData('cleared-queue', ...args)} />);
      submit();
      expect(await screen.findByRole('status')).toHaveTextContent(/pending sync/i);
      act(() => syncManager.clearQueue());
      expect(screen.getByRole('status')).toHaveTextContent(/not confirmed/i);
      expect(screen.queryByText(/retry automatically/i)).toBeNull();
      expect(String(strokesInput().value)).toBe('6');
    });
  });

  test.each(['offline', 'network failure'])('storage failure on %s does not publish or claim the correction is queued', async (mode) => {
    vi.stubGlobal('navigator', { onLine: mode !== 'offline' });
    cleanupSync = syncManager.setupAutoSync(async () => { throw new TypeError('Failed to fetch'); });
    vi.spyOn(localStorage, 'setItem').mockImplementation(() => { throw new Error('Quota exceeded'); });
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    render(<CorrectionHarness syncHole={(...args) => syncManager.syncHoleData('storage-failure', ...args)} />);
    editAndSave();
    expect(await screen.findByRole('alert')).toHaveTextContent(/unable to store/i);
    expectOriginalState();
    expect(screen.getByLabelText('Alice strokes')).toHaveValue('6');
    expect(screen.queryByRole('status')).toBeNull();
    expect(syncManager.getSyncQueue()).toHaveLength(0);
  });

  test('storage failure merging a second correction preserves the previously queued revision', async () => {
    vi.stubGlobal('navigator', { onLine: false });
    render(<CorrectionHarness syncHole={(...args) => syncManager.syncHoleData('merge-storage-failure', ...args)} />);
    editAndSave();
    await screen.findByRole('status');
    fireEvent.change(screen.getByLabelText('Alice strokes'), { target: { value: '7' } });
    vi.spyOn(localStorage, 'setItem').mockImplementation(() => { throw new Error('Quota exceeded'); });
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/unable to store/i);
    expectCorrectedState();
    expect(screen.getByLabelText('Alice strokes')).toHaveValue('7');
    expect(syncManager.getSyncQueue()[0].payload.optional_details['1'].gross_scores.p1).toBe(6);
  });

  test('scorecard locks the submitted edits while waiting for acknowledgement', async () => {
    let resolveSave;
    render(<ScorecardCorrectionHarness syncHole={() => new Promise(resolve => { resolveSave = resolve; })} />);
    fireEvent.click(screen.getByText('Front 9'));
    fireEvent.click(screen.getAllByTitle('Click to edit')[0]);
    fireEvent.change(screen.getAllByRole('spinbutton')[0], { target: { value: '6' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expectOriginalState();
    screen.getAllByRole('spinbutton').forEach(input => expect(input).toBeDisabled());
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled();
    await act(async () => resolveSave({ success: true, synced: true }));
    expect(screen.queryByRole('spinbutton')).toBeNull();
    expect(screen.getByLabelText('History')).toHaveTextContent('Alice strokes: 6; quarters: 1');
  });

  test('scorecard cell correction also preserves the editor and history on rejection', async () => {
    render(<ScorecardCorrectionHarness syncHole={async () => ({ success: false, error: 'Correction rejected' })} />);
    fireEvent.click(screen.getByText('Front 9'));
    fireEvent.click(screen.getAllByTitle('Click to edit')[0]);
    fireEvent.change(screen.getAllByRole('spinbutton')[0], { target: { value: '6' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Correction rejected');
    expectOriginalState();
    expect(screen.getAllByRole('spinbutton')[0]).toHaveValue(6);
  });

  test.each([
    [{ success: true, synced: true }, false],
    [{ success: true, queued: true }, true],
  ])('scorecard cell correction publishes only accepted results %j', async (result, queued) => {
    render(<ScorecardCorrectionHarness syncHole={async () => result} />);
    fireEvent.click(screen.getByText('Front 9'));
    fireEvent.click(screen.getAllByTitle('Click to edit')[0]);
    fireEvent.change(screen.getAllByRole('spinbutton')[0], { target: { value: '6' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(screen.getByLabelText('History')).toHaveTextContent('Alice strokes: 6; quarters: 1'));
    expect(screen.getByLabelText('Standings')).toHaveTextContent('Alice: 1; Bob: -1');
    if (queued) {
      // A legacy callback without a queue receipt cannot establish pending or success.
      expect(screen.getByRole('status')).toHaveTextContent(/not confirmed/i);
      expect(screen.getAllByRole('spinbutton')[0]).toHaveValue(6);
    } else {
      expect(screen.queryByRole('spinbutton')).toBeNull();
    }
  });

  test('real HTTP acknowledgement updates rendered state and closes the editor', async () => {
    vi.stubGlobal('navigator', { onLine: true });
    cleanupSync = syncManager.setupAutoSync(async () => ({ ok: true, headers: new Headers() }));
    render(<CorrectionHarness syncHole={(...args) => syncManager.syncHoleData('correction-game', ...args)} />);
    editAndSave();
    await waitFor(() => expect(screen.queryByLabelText('Alice strokes')).toBeNull());
    expectCorrectedState();
    expect(syncManager.getSyncQueue()).toHaveLength(0);
  });

  test('real HTTP rejection preserves rendered state and edits', async () => {
    vi.stubGlobal('navigator', { onLine: true });
    cleanupSync = syncManager.setupAutoSync(async () => ({
      ok: false, status: 422, headers: new Headers({ 'X-Request-ID': 'http-rejection-id' }),
      json: async () => ({ detail: 'Zero-sum validation failed' }),
    }));
    render(<CorrectionHarness syncHole={(...args) => syncManager.syncHoleData('correction-game', ...args)} />);
    editAndSave();
    expect(await screen.findByRole('alert')).toHaveTextContent('Zero-sum validation failed');
    expect(screen.getByRole('alert')).toHaveTextContent('http-rejection-id');
    expectOriginalState();
    expect(screen.getByLabelText('Alice strokes')).toHaveValue('6');
    expect(syncManager.getSyncQueue()).toHaveLength(0);
  });

  test('server rejection preserves history, standings, and editable corrections with an actionable request reference', async () => {
    render(<CorrectionHarness syncHole={async () => ({
      success: false, permanent: true, error: 'Quarters rejected', requestId: 'req-correction-422',
    })} />);
    editAndSave();
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Quarters rejected');
    expect(alert).toHaveTextContent('req-correction-422');
    expect(alert).toHaveTextContent(/retry/i);
    expectOriginalState();
    expect(screen.getByLabelText('Alice strokes')).toHaveValue('6');
    expect(screen.getByLabelText('Alice quarters')).toHaveValue('2');
    expect(screen.getByLabelText('Bob quarters')).toHaveValue('-2');
    expect(screen.getByRole('button', { name: 'Save' })).toBeEnabled();
  });
});
