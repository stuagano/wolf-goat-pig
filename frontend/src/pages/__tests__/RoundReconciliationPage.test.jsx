import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import RoundReconciliationPage from '../RoundReconciliationPage';
import { IssueReview } from '../../components/game/RoundConflictReview';
const request = vi.fn();
vi.mock('../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => request }));
vi.mock('@auth0/auth0-react', () => ({ useAuth0: () => ({ isAuthenticated: true }) }));
const issue = { id: 'i1', kind: 'value', field: 'quarters', status: 'open', game_id: 'g1', revision: 2, game_revision: 7, current_head_revision: 3, accepted_present: true, accepted_value: null, proposed_present: true, proposed_value: 2.5, source: { kind: 'sheet' }, observation: {}, audit: [] };
const response = (data, status = 200) => ({ ok: status < 400, status, json: async () => data });
beforeEach(() => request.mockReset());
it('shows accepted/proposed provenance and prevents stale 409 resubmission until reload', async () => {
  request.mockImplementation(async (url, options) => options?.method ? response({ detail: 'Stale' }, 409) : response(issue));
  render(<MemoryRouter><IssueReview issueId="i1" /></MemoryRouter>);
  expect(await screen.findByText('2.5')).toBeVisible();
  expect(screen.getByText('null')).toBeVisible();
  expect(screen.getByText('Provenance')).toBeVisible();
  expect(screen.getByText('Resolution audit (0)')).toBeVisible();
  fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Checked evidence' } });
  fireEvent.click(screen.getByRole('button', { name: 'Record reviewed decision' }));
  expect(await screen.findByRole('alert')).toHaveTextContent(/Reload current evidence/);
  const button = screen.getByRole('button', { name: 'Record reviewed decision' });
  expect(button).toBeDisabled();
  fireEvent.click(button);
  expect(request.mock.calls.filter(([, o]) => o?.method === 'POST')).toHaveLength(1);
  const sent = JSON.parse(request.mock.calls.find(([, o]) => o?.method === 'POST')[1].body);
  expect(sent).toMatchObject({ expected_game_revision: 7, expected_issue_revision: 2, expected_head_revision: 3, reason: 'Checked evidence' });
  fireEvent.click(screen.getByRole('button', { name: 'Reload current evidence' }));
  await waitFor(() => expect(screen.getByLabelText('Reason')).toHaveValue(''));
});
it('offers reviewed rebinding for a bound continuity issue and hides unsupported value actions', async () => {
  const continuity = { ...issue, kind: 'continuity', field: '', accepted_value: 'old-token', proposed_value: 'new-token' };
  request.mockImplementation(async (url, options) => options?.method ? response({ status: 'accepted' }) : response(continuity));
  render(<MemoryRouter><IssueReview issueId="i1" /></MemoryRouter>);
  const menu = await screen.findByLabelText('Decision');
  expect([...menu.options].map(o => o.value)).toEqual(['keep', 'bind_existing', 'retract']);
  expect(screen.getByRole('link', { name: 'Open shared game' })).toBeVisible();
  fireEvent.change(menu, { target: { value: 'bind_existing' } });
  fireEvent.change(screen.getByLabelText('Target game UUID'), { target: { value: 'other-uuid' } });
  fireEvent.change(screen.getByLabelText('Target accepted revision'), { target: { value: '4' } });
  fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Source belongs to the other round' } });
  fireEvent.click(screen.getByRole('button', { name: 'Record reviewed decision' }));
  await waitFor(() => expect(request.mock.calls.filter(([, o]) => o?.method === 'POST')).toHaveLength(1));
  expect(JSON.parse(request.mock.calls.find(([, o]) => o?.method === 'POST')[1].body)).toEqual({
    action: 'bind_existing', reason: 'Source belongs to the other round', target_game_id: 'other-uuid',
    expected_target_game_revision: 4, expected_game_revision: 7, expected_issue_revision: 2, expected_head_revision: 3,
  });
});
it('offers only keep for an unbound parse hold and never autosubmits a stale decision', async () => {
  const parse = { ...issue, kind: 'parse', field: '', game_id: null, game_revision: null, proposed_present: false, proposed_value: undefined };
  request.mockImplementation(async (url, options) => options?.method ? response({ detail: 'Stale reconciliation decision' }, 409) : response(parse));
  render(<MemoryRouter><IssueReview issueId="i1" /></MemoryRouter>);
  const menu = await screen.findByLabelText('Decision');
  expect([...menu.options].map(o => o.value)).toEqual(['keep']);
  expect(screen.getAllByText('Not supplied').length).toBeGreaterThan(0);
  fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Unparsed evidence held' } });
  fireEvent.click(screen.getByRole('button', { name: 'Record reviewed decision' }));
  expect(await screen.findByRole('alert')).toHaveTextContent(/Reload current evidence/);
  expect(request.mock.calls.filter(([, o]) => o?.method === 'POST')).toHaveLength(1);
  expect(JSON.parse(request.mock.calls.find(([, o]) => o?.method === 'POST')[1].body).expected_game_revision).toBeNull();
  expect(screen.queryByText(/no game has been assigned/)).toBeVisible();
});
it('keeps an unbound issue UUID-free', async () => {
  request.mockResolvedValue(response({ ...issue, game_id: null }));
  render(<MemoryRouter><IssueReview issueId="i1" /></MemoryRouter>);
  expect(await screen.findByText(/no game has been assigned/)).toBeVisible();
  expect(screen.queryByRole('link', { name: 'Open shared game' })).toBeNull();
});
it('does not expose a review form when the backend refuses access', async () => {
  request.mockResolvedValue(response({ detail: 'Review access required' }, 403));
  render(<MemoryRouter><RoundReconciliationPage /></MemoryRouter>);
  expect(await screen.findByRole('alert')).toHaveTextContent('Review access required');
  expect(screen.queryByText('Administrator recipient selection')).toBeNull();
  expect(screen.queryByRole('button', { name: 'Record reviewed decision' })).toBeNull();
});
it('uses the real separate consent and administrator selection API contracts', async () => {
  request.mockImplementation(async (url, options) => response(String(url).endsWith('/health') ? { routing: { confirmed: false } }
    : String(url).endsWith('/recipient/attest') ? { attestation_id: 'proof-local', expires_at: 'tomorrow' }
    : options?.method === 'PUT' ? { profile_id: 8 }
    : { items: [], total: 0, limit: 50 }));
  render(<MemoryRouter><RoundReconciliationPage /></MemoryRouter>);
  expect(await screen.findByText('Open review inbox (0)')).toBeVisible();
  expect(screen.getByRole('button', { name: 'Record my self-attestation' })).toBeDisabled();
  fireEvent.click(screen.getByLabelText(/I confirm my own account/));
  fireEvent.click(screen.getByRole('button', { name: 'Record my self-attestation' }));
  expect(await screen.findByText(/Proof ID: proof-local/)).toBeVisible();
  fireEvent.change(screen.getByLabelText('Recipient profile ID'), { target: { value: '8' } });
  fireEvent.change(screen.getByLabelText('Selection reason'), { target: { value: 'Reviewed matching proof' } });
  fireEvent.click(screen.getByLabelText(/I explicitly confirm/));
  fireEvent.click(screen.getByRole('button', { name: 'Confirm recipient selection' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Server confirmed recipient profile 8');
  const writes = request.mock.calls.filter(([, options]) => options?.method);
  expect(writes.map(([url, o]) => [String(url).split('/round-reconciliation')[1], o.method, JSON.parse(o.body)])).toEqual([
    ['/recipient/attest', 'POST', { confirmed: true }],
    ['/recipient', 'PUT', { profile_id: 8, attestation_id: 'proof-local', confirmed: true, reason: 'Reviewed matching proof' }],
  ]);
});
