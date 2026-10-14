import { describe, test, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import useRoundCard from '../useRoundCard';

vi.mock('../../config/api.config', () => ({ apiConfig: { baseUrl: 'http://test-api' } }));

const authFetch = vi.fn();
vi.mock('../useAuthenticatedFetch', () => ({ useAuthenticatedFetch: () => authFetch }));

const ok = (data) => Promise.resolve({ ok: true, json: async () => data });
const CARD = { has_photo: true, can_edit: true, edited_by: null, edited_at: null };

beforeEach(() => {
  authFetch.mockReset();
});

describe('useRoundCard', () => {
  test('returns the card JSON', async () => {
    authFetch.mockReturnValueOnce(ok(CARD));
    const { result } = renderHook(() => useRoundCard('g1'));
    await waitFor(() => expect(result.current.card).toEqual(CARD));
    expect(authFetch).toHaveBeenCalledWith('http://test-api/games/g1/card');
  });

  test('is null when the request rejects (signed out)', async () => {
    authFetch.mockReturnValueOnce(Promise.reject(new Error('Login required')));
    const { result } = renderHook(() => useRoundCard('g1'));
    await waitFor(() => expect(authFetch).toHaveBeenCalled());
    expect(result.current.card).toBeNull();
  });

  test('refresh re-fetches', async () => {
    authFetch.mockReturnValueOnce(ok({ ...CARD, has_photo: false })).mockReturnValueOnce(ok(CARD));
    const { result } = renderHook(() => useRoundCard('g1'));
    await waitFor(() => expect(result.current.card?.has_photo).toBe(false));

    act(() => result.current.refresh());

    await waitFor(() => expect(result.current.card?.has_photo).toBe(true));
    expect(authFetch).toHaveBeenCalledTimes(2);
  });
});
