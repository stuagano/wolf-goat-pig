import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import AccountLinkingManager from '../admin/AccountLinkingManager';

const request = vi.fn();
vi.mock('../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => request }));
vi.mock('../../hooks/useLegacyPlayers', () => ({
  useLegacyPlayers: () => ({ players: ['Kevin Gent', 'Casey McFarland'], loading: false }),
}));
vi.mock('../../components/ui', () => ({ Card: ({ children }) => <div>{children}</div> }));

const kevin = { id: 1, name: 'kevin@example.com', email: 'kevin@example.com', auth0_id: 'auth0|test-kevin', legacy_name: null, updated_at: null };
const response = data => ({ ok: true, json: async () => data });

beforeEach(() => request.mockReset());

test('search, explicitly select, review, then save an existing account link', async () => {
  request.mockResolvedValueOnce(response({ players: [kevin] }));
  render(<AccountLinkingManager />);
  fireEvent.change(screen.getByLabelText('Search name or email'), { target: { value: 'kevin@' } });
  fireEvent.click(screen.getByRole('button', { name: 'Search profiles' }));
  fireEvent.click(await screen.findByRole('button', { name: /Select profile 1/ }));
  fireEvent.change(screen.getByLabelText('Roster player'), { target: { value: 'Kevin Gent' } });
  expect(screen.getByLabelText('Player email')).toHaveValue('kevin@example.com');
  expect(screen.getByLabelText('Auth0 user ID')).toHaveValue('auth0|test-kevin');
  fireEvent.click(screen.getByRole('button', { name: 'Review link' }));
  expect(request).toHaveBeenCalledTimes(1);
  expect(screen.getByText(/Profile #1 will display as Kevin Gent/)).toBeInTheDocument();
  request.mockResolvedValueOnce(response({ ...kevin, name: 'Kevin Gent', legacy_name: 'Kevin Gent', updated_at: '2026-10-04T15:00:00' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save account link' }));
  await screen.findByText(/Account linked to Kevin Gent/);
  const options = request.mock.calls[1][1];
  expect(JSON.parse(options.body)).toEqual({ player_id: 1, legacy_name: 'Kevin Gent', email: 'kevin@example.com', auth0_id: 'auth0|test-kevin', expected_updated_at: null });
});

test('shows conflict and preserves edits without silently moving another account', async () => {
  request.mockResolvedValueOnce(response({ players: [kevin] }));
  render(<AccountLinkingManager />);
  fireEvent.change(screen.getByLabelText('Search name or email'), { target: { value: 'Kevin' } });
  fireEvent.click(screen.getByRole('button', { name: 'Search profiles' }));
  fireEvent.click(await screen.findByRole('button', { name: /Select profile 1/ }));
  fireEvent.change(screen.getByLabelText('Roster player'), { target: { value: 'Casey McFarland' } });
  fireEvent.click(screen.getByRole('button', { name: 'Review link' }));
  request.mockResolvedValueOnce({ ok: false, json: async () => ({ detail: 'Casey McFarland is linked to profile #2.' }) });
  fireEvent.click(screen.getByRole('button', { name: 'Save account link' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('linked to profile #2');
  expect(screen.getByLabelText('Roster player')).toHaveValue('Casey McFarland');
  await waitFor(() => expect(request).toHaveBeenCalledTimes(2));
});
