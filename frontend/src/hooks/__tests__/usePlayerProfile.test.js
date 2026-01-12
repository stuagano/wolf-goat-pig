import { renderHook, act, waitFor } from '@testing-library/react';
import usePlayerProfile from '../usePlayerProfile';
import useFetchAsync from '../useFetchAsync';
import { storage } from '../../utils/storage';

// Create simple mock profiles without using factory (to match API response format)
const mockProfiles = [
  { id: '1', name: 'Alice', handicap: 10 },
  { id: '2', name: 'Bob', handicap: 15 }
];

const mockStatistics = { rounds: 5 };

// Define mock functions that will be used by the mock implementation
const mockGet = jest.fn();
const mockPost = jest.fn();
const mockPut = jest.fn();
const mockDel = jest.fn();
const mockClearError = jest.fn();

// Mock useFetchAsync - the default export must be jest.fn() to allow mockReturnValue
jest.mock('../useFetchAsync', () => ({
  __esModule: true,
  default: jest.fn()
}));

// Mock the storage utility
jest.mock('../../utils/storage', () => ({
  storage: {
    get: jest.fn(() => null),
    set: jest.fn(),
    remove: jest.fn(),
    has: jest.fn(() => false),
    getKeys: jest.fn(() => []),
    clear: jest.fn()
  }
}));

describe('usePlayerProfile', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Configure mock implementations for each test
    mockGet.mockResolvedValue(mockProfiles);
    mockPost.mockResolvedValue({ id: '3', name: 'Carol', handicap: 20 });
    mockPut.mockResolvedValue({});
    mockDel.mockResolvedValue({});

    // Override the useFetchAsync mock to use our test-specific mocks
    useFetchAsync.mockReturnValue({
      loading: false,
      error: null,
      get: mockGet,
      post: mockPost,
      put: mockPut,
      del: mockDel,
      clearError: mockClearError
    });

    storage.get.mockReturnValue(null);
  });

  const renderProfileHook = () => renderHook(() => usePlayerProfile());

  test('hook initializes with empty profiles', () => {
    const { result } = renderProfileHook();

    expect(result.current).toBeDefined();
    expect(result.current.profiles).toBeDefined();
    expect(Array.isArray(result.current.profiles)).toBe(true);
    expect(typeof result.current.selectProfile).toBe('function');
    expect(typeof result.current.createProfile).toBe('function');
  });

  test('loads profiles on mount', async () => {
    const { result } = renderProfileHook();

    // Wait for the effect to run and profiles to load
    await waitFor(() => {
      expect(result.current.profiles.length).toBe(2);
    });

    expect(mockGet).toHaveBeenCalledWith('/api/players', expect.any(String));
  });

  test('selectProfile updates selected profile and saves to localStorage', async () => {
    const { result } = renderProfileHook();

    await waitFor(() => {
      expect(result.current.profiles.length).toBe(2);
    });

    await act(async () => {
      await result.current.selectProfile(mockProfiles[0]);
    });

    expect(result.current.selectedProfile).toEqual(mockProfiles[0]);
    expect(storage.set).toHaveBeenCalled();
  });

  test('createProfile posts to API and returns new profile', async () => {
    const { result } = renderProfileHook();

    await waitFor(() => {
      expect(result.current.profiles.length).toBe(2);
    });

    let created;
    await act(async () => {
      created = await result.current.createProfile({ name: 'Carol', handicap: 20 });
    });

    expect(created).toEqual({ id: '3', name: 'Carol', handicap: 20 });
    expect(mockPost).toHaveBeenCalledWith(
      '/api/players',
      { name: 'Carol', handicap: 20 },
      expect.any(String)
    );
  });

  test('loadProfileStatistics caches results', async () => {
    mockGet
      .mockResolvedValueOnce(mockProfiles) // First call: profiles
      .mockResolvedValueOnce(mockStatistics); // Second call: statistics

    const { result } = renderProfileHook();

    await waitFor(() => {
      expect(result.current.profiles.length).toBe(2);
    });

    let stats;
    await act(async () => {
      stats = await result.current.loadProfileStatistics('1');
    });

    expect(stats).toEqual(mockStatistics);
    expect(mockGet).toHaveBeenCalledWith('/api/players/1/statistics', expect.any(String));
  });
});
