import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
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

  it('polls later email failure after read and keeps it visible after dismissing again', async () => {
    let isRead = false;
    let failed = false;
    let poll;
    const originalInterval = globalThis.setInterval;
    vi.spyOn(globalThis, 'setInterval').mockImplementation((callback, delay, ...args) => {
      if (delay === 60_000) { poll = callback; return 123; }
      return originalInterval(callback, delay, ...args);
    });
    vi.stubGlobal('fetch', vi.fn().mockImplementation(async (url, options) => {
      if (options?.method) {
        isRead = true;
        return { ok: true, json: async () => ({ ok: true }) };
      }
      const requestedHealth = url.includes('include_delivery_health=true');
      return { ok: true, json: async () => (!isRead || (requestedHealth && failed)) ? [{
        id: 12, notification_type: 'round_conflict', message: 'Round needs review', is_read: isRead,
        data: { path: '/game/fixture', delivery_health: failed ? { email: 'failed' } : {} },
      }] : [] };
    }));
    try {
      render(<NotificationBell />);
      fireEvent.click(await screen.findByRole('button', { name: '1 unread notification' }));
      fireEvent.click(screen.getByText('Round needs review'));
      await waitFor(() => expect(navigate).toHaveBeenCalledWith('/game/fixture'));
      expect(screen.queryByText('🔔')).not.toBeInTheDocument();
      failed = true;
      await act(async () => { await poll(); });
      fireEvent.click(await screen.findByRole('button', { name: '1 unread notification' }));
      expect(screen.getByText('· Email delivery needs attention')).toBeInTheDocument();
      fireEvent.click(screen.getByText('Mark all read'));
      await act(async () => {});
      expect(screen.getByText('· Email delivery needs attention')).toBeInTheDocument();
      fireEvent.click(screen.getByText('Round needs review'));
      await act(async () => {});
      expect(screen.getByRole('button', { name: '1 unread notification' })).toBeInTheDocument();
    } finally {
      vi.restoreAllMocks();
    }
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
