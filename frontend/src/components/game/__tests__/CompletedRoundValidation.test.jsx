import React from 'react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import CompletedRoundView from '../CompletedRoundView';

vi.mock('../../../config/api.config', () => ({ apiConfig: { baseUrl: 'http://test-api' } }));
vi.mock('../../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => authFetch }));
vi.mock('../../ui/SyncStatusIndicator', () => ({ SyncStatusBanner: () => <div>Sync status</div> }));
// Keep the completion controls wired, but exercise the real review, photo,
// extraction, comparison and permission hook rather than mocking those seams.
vi.mock('../GameCompletionView', () => ({
  default: ({ onMarkComplete, onEditScores }) => (
    <div>
      <p>Saved round standings</p>
      <button onClick={onMarkComplete}>Mark complete</button>
      {onEditScores && <button onClick={onEditScores}>Legacy edit scores</button>}
    </div>
  ),
}));

const authFetch = vi.fn();
const publicFetch = vi.fn();
const response = (data) => ({ ok: true, json: async () => data });
const extraction = {
  players: [{ name: 'Alice', confidence: 1 }],
  running_totals: [
    { player_index: 0, hole: 1, value: 2, confidence: 1 },
    { player_index: 0, hole: 2, value: 9, confidence: 1 },
  ],
};
const photoResponse = () => ({
  ok: true,
  blob: async () => new Blob(['saved photo bytes'], { type: 'image/jpeg' }),
});
const deferred = () => {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
};
const scanCalls = () => publicFetch.mock.calls.filter(([url]) => url.endsWith('/scorecard/scan'));
const mutations = (mock) => mock.mock.calls.filter(([, options]) =>
  !['GET', 'HEAD'].includes(options?.method || 'GET'));
const scanButton = () => screen.getByRole('button', { name: 'Extract & compare card' });

function propsForRound() {
  return {
    gameId: 'g1',
    players: [{ id: 'p1', name: 'Alice' }, { id: 'p2', name: 'Bob' }],
    playerStandings: {},
    holeHistory: [
      { hole: 1, gross_scores: { p1: 4, p2: 5 }, points_delta: { p1: 2, p2: -2 } },
      { hole: 2, gross_scores: { p1: 5, p2: 4 }, points_delta: { p1: -1, p2: 1 } },
    ],
    courseHoles: [],
    strokeAllocation: {},
    isMarkedComplete: true,
    onMarkedComplete: vi.fn(),
    onSaveHole: vi.fn(),
    onEditScores: vi.fn(),
  };
}

async function loadPhoto() {
  const photo = await screen.findByAltText('scorecard');
  fireEvent.load(photo);
  expect(scanButton()).toBeEnabled();
  return photo;
}

function expectNoScoreWrites(props) {
  expect(props.onMarkedComplete).not.toHaveBeenCalled();
  expect(props.onSaveHole).not.toHaveBeenCalled();
  expect(props.onEditScores).not.toHaveBeenCalled();
}

beforeEach(() => {
  vi.resetAllMocks();
  vi.stubGlobal('fetch', publicFetch);
  authFetch.mockImplementation((url, options) => {
    if (url.endsWith('/card') && !options?.method) {
      return Promise.resolve(response({ has_photo: true, can_edit: false }));
    }
    throw new Error(`Unexpected authenticated request: ${options?.method} ${url}`);
  });
  publicFetch.mockImplementation((url, options) => {
    if (url.endsWith('/scorecard/scan') && options?.method === 'POST') {
      return Promise.resolve(response(extraction));
    }
    if (url.includes('/scorecard-photo?') && !options?.method) {
      return Promise.resolve(photoResponse());
    }
    throw new Error(`Unexpected public request: ${options?.method} ${url}`);
  });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('completed-round extraction validation integration', () => {
  test('waits for the photo to load, compares saved running quarters, and POSTs only the file without saving', async () => {
    const props = propsForRound();
    const savedBefore = JSON.stringify(props.holeHistory);
    render(<CompletedRoundView {...props} />);
    expect(screen.queryByRole('button', { name: 'Extract & compare card' })).toBeNull();
    const photo = await screen.findByAltText('scorecard');
    expect(screen.queryByRole('button', { name: 'Extract & compare card' })).toBeNull();
    expect(scanCalls()).toHaveLength(0);
    fireEvent.load(photo);
    fireEvent.click(scanButton());

    const table = await screen.findByRole('table', { name: 'Alice running quarters' });
    const rows = within(table).getAllByRole('row');
    const cells = (row) => [...row.children].map((cell) => cell.textContent);
    expect(cells(rows[1])).toEqual(['1', '2', '2', 'Match']);
    expect(cells(rows[2])).toEqual(['2', '1', '9', 'Possible extraction error']);
    expect(screen.getByText('Saved round standings')).toBeVisible();
    expect(scanCalls()).toHaveLength(1);
    const [url, options] = scanCalls()[0];
    expect(url).toBe('http://test-api/scorecard/scan');
    expect(options.method).toBe('POST');
    expect(options.body).toBeInstanceOf(FormData);
    expect([...options.body.keys()]).toEqual(['file']);
    expect(options.body.get('file')).toBeInstanceOf(File);
    expect(options.body.get('file').size).toBe(new Blob(['saved photo bytes']).size);
    expect(options.body.get('file').type).toBe('image/jpeg');
    expect(options.headers).toBeUndefined();
    expect(publicFetch).toHaveBeenCalledWith(photo.getAttribute('src'), expect.objectContaining({ cache: 'no-store' }));
    expect(mutations(publicFetch)).toEqual(scanCalls());
    expect(mutations(authFetch)).toEqual([]);
    expect(JSON.stringify(props.holeHistory)).toBe(savedBefore);
    expectNoScoreWrites(props);
  });

  test.each([true, false])('read-only comparison and mapping never unlock edits (inline save callback: %s)', async (inline) => {
    const props = propsForRound();
    render(<CompletedRoundView {...props} onSaveHole={inline ? props.onSaveHole : undefined} />);
    await loadPhoto();
    fireEvent.click(scanButton());
    const mapping = await screen.findByLabelText('Map card row 1');
    fireEvent.change(mapping, { target: { value: '1' } });
    expect(screen.getByRole('table', { name: 'Bob running quarters' })).toBeVisible();
    fireEvent.click(screen.getByRole('button', { name: 'Retry extraction' }));
    expect(await screen.findByRole('table', { name: 'Alice running quarters' })).toBeVisible();
    expect(screen.queryByRole('button', { name: /edit scores|edit hole|done editing/i })).toBeNull();
    expect(screen.queryByLabelText(/replace card photo|add the card photo/i)).toBeNull();
    expect(screen.queryByRole('button', { name: /^save$|apply/i })).toBeNull();
    expect(scanCalls()).toHaveLength(2);
    expect(mutations(authFetch)).toEqual([]);
    expectNoScoreWrites(props);
  });

  test('replacement upload invalidates a pending scan at upload start, even when the upload fails', async () => {
    const pendingScan = deferred();
    const pendingUpload = deferred();
    const props = propsForRound();
    authFetch.mockImplementation((url, options) => options?.method === 'PUT'
      ? pendingUpload.promise
      : Promise.resolve(response({ has_photo: true, can_edit: true })));
    render(<CompletedRoundView {...props} />);
    await loadPhoto();
    publicFetch.mockImplementationOnce(() => Promise.resolve(photoResponse()))
      .mockImplementationOnce(() => pendingScan.promise);
    fireEvent.click(scanButton());
    await waitFor(() => expect(scanCalls()).toHaveLength(1));
    const signal = scanCalls()[0][1].signal;
    const replacement = new File(['replacement'], 'replacement.jpg', { type: 'image/jpeg' });
    fireEvent.change(screen.getByLabelText(/replace card photo/i), { target: { files: [replacement] } });

    expect(signal.aborted).toBe(true);
    expect(screen.queryByRole('region', { name: 'Extraction validation' })).toBeNull();
    expect(screen.getByLabelText('Uploading…')).toBeDisabled();
    await act(async () => { pendingScan.resolve(response(extraction)); });
    expect(screen.queryByRole('table')).toBeNull();
    await act(async () => { pendingUpload.resolve({ ok: false, status: 503 }); });
    expect(await screen.findByRole('alert')).toHaveTextContent('Upload failed (503)');
    expect(scanButton()).toBeEnabled();
    expect(screen.queryByRole('table')).toBeNull();
    expect(mutations(authFetch)).toHaveLength(1);
    expect(mutations(authFetch)[0][0]).toBe('http://test-api/games/g1/scorecard-photo');
    expect(mutations(authFetch)[0][1].method).toBe('PUT');
    expect(mutations(authFetch)[0][1].body.get('file')).toBe(replacement);
    expectNoScoreWrites(props);
  });

  test('a successful replacement loads a new photo and never revives the previous pending extraction', async () => {
    const pendingScan = deferred();
    const props = propsForRound();
    authFetch.mockImplementation((url, options) => Promise.resolve(options?.method === 'PUT'
      ? { ok: true }
      : response({ has_photo: true, can_edit: true })));
    render(<CompletedRoundView {...props} />);
    const oldPhoto = await loadPhoto();
    const oldSrc = oldPhoto.getAttribute('src');
    publicFetch.mockImplementationOnce(() => Promise.resolve(photoResponse()))
      .mockImplementationOnce(() => pendingScan.promise);
    fireEvent.click(scanButton());
    await waitFor(() => expect(scanCalls()).toHaveLength(1));
    fireEvent.change(screen.getByLabelText(/replace card photo/i), {
      target: { files: [new File(['replacement'], 'new.jpg', { type: 'image/jpeg' })] },
    });
    await waitFor(() => expect(screen.getByAltText('scorecard').getAttribute('src')).not.toBe(oldSrc));
    expect(screen.getByAltText('scorecard')).toHaveAttribute('src', 'http://test-api/games/g1/scorecard-photo?v=1&retry=0');
    expect(screen.queryByRole('button', { name: 'Extract & compare card' })).toBeNull();
    expect(scanCalls()[0][1].signal.aborted).toBe(true);
    fireEvent.load(screen.getByAltText('scorecard'));
    await act(async () => { pendingScan.resolve(response(extraction)); });
    expect(screen.queryByRole('table')).toBeNull();
    fireEvent.click(scanButton());
    expect(await screen.findByRole('table', { name: 'Alice running quarters' })).toBeVisible();
    expect(publicFetch).toHaveBeenCalledWith('http://test-api/games/g1/scorecard-photo?v=1&retry=0', expect.objectContaining({ cache: 'no-store' }));
    expect(mutations(authFetch).map(([, options]) => options.method)).toEqual(['PUT']);
    expectNoScoreWrites(props);
  });

  test('switching games aborts pending extraction and a late response cannot populate the new round', async () => {
    const pendingScan = deferred();
    const props = propsForRound();
    const { rerender } = render(<CompletedRoundView {...props} />);
    await loadPhoto();
    publicFetch.mockImplementationOnce(() => Promise.resolve(photoResponse()))
      .mockImplementationOnce(() => pendingScan.promise);
    fireEvent.click(scanButton());
    await waitFor(() => expect(scanCalls()).toHaveLength(1));
    rerender(<CompletedRoundView {...props} gameId="g2" />);
    expect(scanCalls()[0][1].signal.aborted).toBe(true);
    expect(screen.queryByRole('button', { name: 'Extract & compare card' })).toBeNull();
    const photo = await loadPhoto();
    expect(photo).toHaveAttribute('src', 'http://test-api/games/g2/scorecard-photo?v=0&retry=0');
    await act(async () => { pendingScan.resolve(response(extraction)); });
    expect(screen.queryByRole('table')).toBeNull();
    fireEvent.click(scanButton());
    expect(await screen.findByRole('table', { name: 'Alice running quarters' })).toBeVisible();
    expect(publicFetch).toHaveBeenCalledWith(photo.getAttribute('src'), expect.objectContaining({ cache: 'no-store' }));
    expect(mutations(authFetch)).toEqual([]);
    expectNoScoreWrites(props);
  });

  test('a missing photo offers no extraction action and preserves the recorded round', async () => {
    publicFetch.mockResolvedValue({ ok: false, status: 404 });
    authFetch.mockResolvedValue(response({ has_photo: false, can_edit: false }));
    const props = propsForRound();
    render(<CompletedRoundView {...props} />);
    expect(await screen.findByText('No card photo has been saved for this round.')).toBeVisible();
    expect(screen.getByText('Saved round standings')).toBeVisible();
    expect(screen.queryByRole('button', { name: /extract|scan/i })).toBeNull();
    expect(screen.queryByRole('region', { name: 'Extraction validation' })).toBeNull();
    expect(scanCalls()).toHaveLength(0);
    expect(mutations(publicFetch)).toEqual([]);
    expect(mutations(authFetch)).toEqual([]);
    expectNoScoreWrites(props);
  });
});
