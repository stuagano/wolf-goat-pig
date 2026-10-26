import React from 'react';
import { test, expect, vi, afterEach } from 'vitest';
import { act, render, screen, fireEvent, within } from '@testing-library/react';
import CardExtractionValidation from '../CardExtractionValidation';

vi.mock('../../../config/api.config', () => ({ apiConfig: { baseUrl: 'http://test-api' } }));
const players = [{ id: 'p1', name: 'Alice' }];
const holeHistory = [{ hole: 1, points_delta: { p1: 2 }, gross_scores: { p1: 7 } }, { hole: 2, points_delta: { p1: -1 } }];
const extraction = {
  players: [{ name: 'Alice', confidence: 1 }],
  running_totals: [{ player_index: 0, hole: 1, value: 2, confidence: 1 }, { player_index: 0, hole: 2, value: 5, confidence: 1 }],
  per_hole_quarters: [{ player_index: 0, hole: 3, quarters: 0 }],
};
const props = { photoSrc: 'http://test-api/games/g1/scorecard-photo?v=0', players, holeHistory };
afterEach(() => vi.unstubAllGlobals());
const response = (data) => ({ ok: true, json: async () => data });
function mockScan(data = extraction) {
  const fetch = vi.fn().mockResolvedValueOnce({ ok: true, blob: async () => new Blob(['synthetic photo'], { type: 'image/jpeg' }) }).mockResolvedValueOnce(response(data));
  vi.stubGlobal('fetch', fetch);
  return fetch;
}
const scan = () => fireEvent.click(screen.getByRole('button', { name: 'Extract & compare card' }));
const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };

test('malformed nested scanner names remain unmapped and readable', async () => {
  mockScan({ players: [{ name: { unexpected: 'object' }, confidence: 1 }, null], running_totals: [null] });
  render(<CardExtractionValidation {...props} />);
  scan();
  expect(await screen.findByLabelText('Map card row 1')).toHaveValue('');
  expect(screen.getByLabelText('Map card row 2')).toHaveValue('');
  expect(screen.getAllByText(/Unreadable name/)).toHaveLength(2);
  expect(screen.queryByRole('table')).toBeNull();
});

test('cancel permits retry and ignores a late response from the cancelled scan', async () => {
  const pending = deferred();
  const fetch = mockScan();
  fetch.mockReset().mockResolvedValueOnce({ ok: true, blob: async () => new Blob(['old']) }).mockReturnValueOnce(pending.promise);
  render(<CardExtractionValidation {...props} />);
  scan();
  await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  fireEvent.click(screen.getByRole('button', { name: 'Cancel extraction' }));
  expect(fetch.mock.calls[1][1].signal.aborted).toBe(true);
  expect(screen.getByRole('button', { name: 'Extract & compare card' })).toBeEnabled();
  const retry = deferred();
  fetch.mockResolvedValueOnce({ ok: true, blob: async () => new Blob(['new']) }).mockReturnValueOnce(retry.promise);
  scan();
  await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(4));
  await act(async () => { pending.resolve(response({ players: [], running_totals: [] })); });
  expect(screen.getByRole('button', { name: 'Extracting card…' })).toBeDisabled();
  expect(screen.queryByRole('table')).toBeNull();
  await act(async () => { retry.resolve(response(extraction)); });
  expect(screen.getByRole('table')).toBeVisible();
});

test('discards pending responses on photo change and allows a fresh scan', async () => {
  const old = deferred();
  const fetch = mockScan();
  fetch.mockReset().mockResolvedValueOnce({ ok: true, blob: async () => new Blob(['old'], { type: 'image/jpeg' }) }).mockReturnValueOnce(old.promise);
  const { rerender } = render(<CardExtractionValidation {...props} />);
  scan();
  await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  rerender(<CardExtractionValidation {...props} photoSrc="new-photo" />);
  expect(screen.getByRole('button', { name: 'Extract & compare card' })).toBeEnabled();
  expect(fetch.mock.calls[1][1].signal.aborted).toBe(true);
  old.resolve(response(extraction));
  await vi.waitFor(() => expect(screen.queryByRole('table')).toBeNull());
  fetch.mockResolvedValueOnce({ ok: true, blob: async () => new Blob(['new'], { type: 'image/jpeg' }) }).mockResolvedValueOnce(response(extraction));
  scan();
  expect(await screen.findByRole('table')).toBeVisible();
  expect(fetch.mock.calls[2][0]).toBe('new-photo');
});

test('treats possible totals-only history conservatively and compares only explicit hole 18', async () => {
  mockScan({ ...extraction, running_totals: [...extraction.running_totals, { player_index: 0, hole: 18, value: 4, confidence: 1 }] });
  const totalsOnly = Array.from({ length: 18 }, (_, i) => ({ hole: i + 1, points_delta: { p1: i === 17 ? 4 : 0 } }));
  render(<CardExtractionValidation {...props} holeHistory={totalsOnly} />);
  scan();
  const table = await screen.findByRole('table');
  expect(within(table).getAllByRole('row')).toHaveLength(2);
  expect(screen.getByText(/may contain only a final total/i)).toBeVisible();
});

test('duplicate saved holes invalidate cumulative quarters rather than choosing a winner', async () => {
  mockScan();
  render(<CardExtractionValidation {...props} holeHistory={[...holeHistory, holeHistory[0]]} />);
  scan();
  const table = await screen.findByRole('table');
  expect(within(table).getAllByText('Saved quarters unavailable')).toHaveLength(2);
  expect(within(table).queryByText('Match')).toBeNull();
});

test('requires explicit mapping for uncertain or duplicate names and blocks duplicate assignments', async () => {
  mockScan({ ...extraction, players: [{ name: 'Alice', confidence: 0.4 }, { name: 'Alice', confidence: 1 }] });
  render(<CardExtractionValidation {...props} />);
  scan();
  const first = await screen.findByLabelText('Map card row 1');
  expect(first).toHaveValue('');
  expect(screen.queryByRole('table')).toBeNull();
  fireEvent.change(first, { target: { value: '0' } });
  expect(screen.getByRole('table')).toBeVisible();
  fireEvent.change(screen.getByLabelText('Map card row 2'), { target: { value: '0' } });
  expect(screen.queryByRole('table')).toBeNull();
  expect(screen.getAllByRole('alert')[0]).toHaveTextContent('Ambiguous mapping');
});

test('marks malformed, duplicate, absent and uncertain cells without assuming zero', async () => {
  mockScan({ ...extraction, running_totals: [
    { player_index: 0, hole: 1, value: 2, confidence: null },
    { player_index: 0, hole: 2, value: 1, confidence: 1 },
    { player_index: 0, hole: 2, value: 1, confidence: 1 },
    { player_index: 0, hole: 3, value: '0', confidence: 1 },
    { player_index: 0, hole: 4, value: 0, confidence: 1 },
  ] });
  render(<CardExtractionValidation {...props} />);
  scan();
  const table = await screen.findByRole('table');
  expect(within(table).getByText('Equal · uncertain extraction')).toBeVisible();
  expect(within(table).getByText('Ambiguous extraction')).toBeVisible();
  expect(within(table).getByText('Saved quarters unavailable')).toBeVisible();
  expect(within(table).getAllByText('Missing extraction')).toHaveLength(15);
});

test.each([503, 422])('errors can be retried without changing scores (%s)', async status => {
  const fetch = mockScan();
  fetch.mockReset().mockResolvedValueOnce({ ok: true, blob: async () => new Blob(['x']) }).mockResolvedValueOnce({ ok: false, status });
  render(<CardExtractionValidation {...props} />);
  scan();
  expect(await screen.findByRole('alert')).toHaveTextContent(`Extraction failed (${status})`);
  fetch.mockResolvedValueOnce({ ok: true, blob: async () => new Blob(['x']) }).mockResolvedValueOnce(response(extraction));
  fireEvent.click(screen.getByRole('button', { name: 'Retry extraction' }));
  expect(await screen.findByRole('table')).toBeVisible();
  expect(fetch.mock.calls.filter(([, o]) => o.method === 'POST').every(([url]) => url.endsWith('/scorecard/scan'))).toBe(true);
});

test('compares running quarters, not strokes/deltas; extraction sends only the photo and never mutates scores', async () => {
  const fetch = mockScan();
  const before = JSON.stringify(holeHistory);
  render(<CardExtractionValidation {...props} />);
  scan();
  const table = await screen.findByRole('table', { name: /Alice.*running quarters/i });
  const rows = within(table).getAllByRole('row');
  const cells = row => [...row.children].map(cell => cell.textContent);
  expect(cells(rows[1])).toEqual(['1', '2', '2', 'Match']);
  expect(cells(rows[2])).toEqual(['2', '1', '5', 'Possible extraction error']);
  expect(cells(rows[3])).toEqual(['3', '—', '—', 'Missing extraction']);
  expect(JSON.stringify(holeHistory)).toBe(before);
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(fetch.mock.calls[0][0]).toBe(props.photoSrc);
  const [url, options] = fetch.mock.calls[1];
  expect(url).toBe('http://test-api/scorecard/scan');
  expect(options.method).toBe('POST');
  expect([...options.body.keys()]).toEqual(['file']);
  expect(options.body.get('file')).toBeInstanceOf(File);
  expect(screen.queryByRole('button', { name: /apply|replace|save/i })).toBeNull();
  expect(screen.getByText(/saved scores are the ground truth/i)).toBeVisible();
});
