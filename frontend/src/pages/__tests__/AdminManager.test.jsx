import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import AdminManager from '../admin/AdminManager';

const request = vi.fn();
vi.mock('../../hooks/useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => request }));
vi.mock('../../hooks/usePlayerProfile', () => ({ usePlayerProfile: () => ({ profile: { id: 9 }, isSuperAdmin: true }) }));
vi.mock('../../components/ui', () => ({ Card: ({ children }) => <div>{children}</div> }));

const ok = data => ({ ok: true, json: async () => data });
const jeff = { id: 2, name: 'Jeff Green', legacy_name: 'Jeff Green', email: 'j@example.com', auth0_id: 'auth0|j', is_admin: true, admin_granted_by: 'env@example.com', admin_granted_at: '2026-10-08T10:00:00' };

beforeEach(() => { request.mockReset(); vi.spyOn(window, 'confirm').mockReturnValue(true); });

test('shows env admins as locked and flagged profiles with who granted them', async () => {
  request.mockResolvedValueOnce(ok({ env_admins: ['env@example.com'], profile_admins: [jeff] }));
  render(<AdminManager />);
  expect(await screen.findByText('env@example.com')).toBeInTheDocument();
  expect(screen.getByText(/Set in deployment config/)).toBeInTheDocument();
  expect(screen.getByText(/granted by env@example.com/)).toBeInTheDocument();
});

test('remove calls DELETE for that profile', async () => {
  request.mockResolvedValueOnce(ok({ env_admins: [], profile_admins: [jeff] }));
  render(<AdminManager />);
  request.mockResolvedValueOnce(ok({ ...jeff, is_admin: false }));
  fireEvent.click(await screen.findByRole('button', { name: 'Remove admin Jeff Green' }));
  await screen.findByText(/Removed admin/);
  expect(request.mock.calls[1][0]).toMatch(/\/players\/admin\/admins\/2$/);
  expect(request.mock.calls[1][1]).toEqual({ method: 'DELETE' });
});

test('search offers Make admin only for linked profiles', async () => {
  request.mockResolvedValueOnce(ok({ env_admins: [], profile_admins: [] }));
  render(<AdminManager />);
  request.mockResolvedValueOnce(ok({ players: [
    { id: 5, name: 'Linked Player', email: 'l@example.com', auth0_id: 'auth0|l' },
    { id: 6, name: 'Never Signed In', email: null, auth0_id: null },
  ] }));
  fireEvent.change(await screen.findByLabelText('Find a player'), { target: { value: 'pla' } });
  fireEvent.click(screen.getByRole('button', { name: 'Search' }));
  expect(await screen.findByRole('button', { name: 'Make admin Linked Player' })).toBeInTheDocument();
  expect(screen.getByText('Needs to sign in first')).toBeInTheDocument();
  request.mockResolvedValueOnce(ok({ id: 5, name: 'Linked Player', is_admin: true, admin_granted_by: 'me@example.com', admin_granted_at: 'now' }));
  fireEvent.click(screen.getByRole('button', { name: 'Make admin Linked Player' }));
  await screen.findByText(/Linked Player is now an admin/);
  expect(request.mock.calls[2][1]).toEqual({ method: 'POST' });
});
