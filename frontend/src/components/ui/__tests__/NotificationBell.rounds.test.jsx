import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import NotificationBell from '../NotificationBell';

const { navigate, getToken } = vi.hoisted(() => ({
  navigate: vi.fn(), getToken: vi.fn().mockResolvedValue('fixture'),
}));
vi.mock('react-router-dom', () => ({ useNavigate: () => navigate }));
vi.mock('@auth0/auth0-react', () => ({ useAuth0: () => ({ isAuthenticated: true }) }));
vi.mock('../../../hooks/useAccessToken', () => ({ useAccessToken: () => ({ getToken }) }));

describe('round conflict bell', () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.unstubAllGlobals());

  const show = async (path) => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (_url, options) => ({
      ok: true,
      json: async () => options?.method ? {} : [{
        id: 12, notification_type: 'round_conflict', message: 'Round needs review',
        data: { path }, created_at: new Date().toISOString(),
      }],
    })));
    render(<NotificationBell />);
    fireEvent.click(await screen.findByRole('button', { name: '1 unread notification' }));
    fireEvent.click(screen.getByText('Round needs review'));
    await waitFor(() => expect(navigate).toHaveBeenCalled());
  };

  it('requests supported types before server limit and opens the shared round', async () => {
    await show('/game/fixture');
    expect(fetch.mock.calls[0][0]).toContain('types=');
    expect(fetch.mock.calls[0][0]).toContain('round_conflict');
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/notifications/12/read'), expect.objectContaining({ method: 'POST' }));
    expect(navigate).toHaveBeenCalledWith('/game/fixture');
  });

  it('opens the reconciliation inbox for an unbound issue', async () => {
    await show('/rounds/reconciliation?issue=fixture');
    expect(navigate).toHaveBeenCalledWith('/rounds/reconciliation?issue=fixture');
  });

  it.each(['//evil.invalid', 'https://evil.invalid', '/\\evil.invalid', '/%2f%2fevil.invalid', 'javascript:alert(1)'])(
    'rejects unsafe stored path %s', async (path) => {
      await show(path);
      expect(navigate).toHaveBeenCalledWith('/account');
    },
  );
});
