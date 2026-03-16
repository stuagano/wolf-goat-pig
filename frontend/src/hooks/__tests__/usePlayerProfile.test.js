import { renderHook, act, waitFor } from '@testing-library/react';
import usePlayerProfile from '../usePlayerProfile';

// Mock Auth0
const mockGetAccessTokenSilently = jest.fn();
jest.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    isAuthenticated: true,
    getAccessTokenSilently: mockGetAccessTokenSilently
  })
}));

const mockProfile = {
  id: '1',
  name: 'Alice',
  legacy_name: null
};

describe('usePlayerProfile', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetAccessTokenSilently.mockResolvedValue('mock-token');
  });

  test('hook initializes with null profile and loading state', () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockProfile)
    });

    const { result } = renderHook(() => usePlayerProfile());

    expect(result.current.profile).toBeNull();
    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.updateLegacyName).toBe('function');
    expect(typeof result.current.skipLegacyName).toBe('function');
    expect(typeof result.current.refetch).toBe('function');
  });

  test('fetches profile on mount', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockProfile)
    });

    const { result } = renderHook(() => usePlayerProfile());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.profile).toEqual(mockProfile);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/players/me'),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer mock-token'
        })
      })
    );
  });

  test('sets needsLegacyName when profile has no legacy_name', async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ ...mockProfile, legacy_name: null })
    });

    const { result } = renderHook(() => usePlayerProfile());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.needsLegacyName).toBe(true);
  });

  test('skipLegacyName sets flag in localStorage', async () => {
    const setItemSpy = jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {});

    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockProfile)
    });

    const { result } = renderHook(() => usePlayerProfile());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      result.current.skipLegacyName();
    });

    expect(result.current.needsLegacyName).toBe(false);
    expect(setItemSpy).toHaveBeenCalledWith('legacy_name_skipped', 'true');
    setItemSpy.mockRestore();
  });

  test('handles fetch error gracefully', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 500
    });

    const { result } = renderHook(() => usePlayerProfile());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.profile).toBeNull();
  });
});
