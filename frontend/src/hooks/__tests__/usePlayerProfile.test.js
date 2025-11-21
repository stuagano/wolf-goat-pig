import { renderHook, act, waitFor } from '@testing-library/react';
import usePlayerProfile from '../usePlayerProfile';

const mockProfiles = [
  { id: '1', name: 'Alice', handicap: 10 },
  { id: '2', name: 'Bob', handicap: 15 }
];

const mockStatistics = { rounds: 5 };

global.fetch = jest.fn();

const createMockStorage = () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn()
});

const localStorageMock = createMockStorage();
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true
});

global.URL = {
  createObjectURL: jest.fn(() => 'mock-url'),
  revokeObjectURL: jest.fn()
};

describe('usePlayerProfile', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: async () => mockProfiles
      })
    );
  });

  const renderProfileHook = () => renderHook(() => usePlayerProfile());

  test('loads profiles on mount', async () => {
    const { result } = renderProfileHook();

    await waitFor(() => expect(result.current.profiles.length).toBe(2));
    expect(fetch).toHaveBeenCalledWith('http://test-api.com/api/players');
  });

  test('selectProfile updates selected profile and saves to localStorage', async () => {
    const { result } = renderProfileHook();

    await waitFor(() => expect(result.current.profiles.length).toBe(2));

    act(() => {
      result.current.selectProfile(mockProfiles[0]);
    });

    expect(result.current.selectedProfile).toEqual(mockProfiles[0]);
    expect(localStorageMock.setItem).toHaveBeenCalled();
  });

  test('createProfile posts to API and returns new profile', async () => {
    fetch
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: async () => mockProfiles
        })
      )
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: async () => ({ id: '3', name: 'Carol', handicap: 20 })
        })
      );

    const { result } = renderProfileHook();
    await waitFor(() => expect(result.current.profiles.length).toBe(2));

    let created;
    await act(async () => {
      created = await result.current.createProfile({ name: 'Carol', handicap: 20 });
    });

    expect(created).toEqual({ id: '3', name: 'Carol', handicap: 20 });
    expect(fetch).toHaveBeenCalledWith('http://test-api.com/api/players', expect.any(Object));
  });

  test('loadProfileStatistics caches results', async () => {
    fetch
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: async () => mockProfiles
        })
      )
      .mockImplementationOnce(() =>
        Promise.resolve({
          ok: true,
          json: async () => mockStatistics
        })
      );

    const { result } = renderProfileHook();
    await waitFor(() => expect(result.current.profiles.length).toBe(2));

    let stats;
    await act(async () => {
      stats = await result.current.loadProfileStatistics('1');
    });

    expect(stats).toEqual(mockStatistics);
    expect(fetch).toHaveBeenCalledWith('http://test-api.com/api/players/1/statistics');
  });
});
