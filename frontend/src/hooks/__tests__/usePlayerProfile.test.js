/**
 * Comprehensive test suite for usePlayerProfile hook
 * 
 * Tests the player profile management hook including:
 * - Profile selection and persistence
 * - Local storage integration
 * - Profile CRUD operations
 * - Statistics caching
 * - Server synchronization
 * - Error handling and loading states
 * - Export/import functionality
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import usePlayerProfile from '../usePlayerProfile';

// Mock fetch globally
global.fetch = jest.fn();

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

// Mock URL and createElement for export functionality
global.URL = {
  createObjectURL: jest.fn(() => 'mock-object-url'),
  revokeObjectURL: jest.fn()
};

// Mock DOM manipulation for file download
const mockLink = {
  href: '',
  download: '',
  click: jest.fn()
};

global.document = {
  createElement: jest.fn(() => mockLink),
  body: {
    appendChild: jest.fn(),
    removeChild: jest.fn()
  }
};

const mockProfiles = [
  {
    id: '1',
    name: 'Alice Johnson',
    handicap: 8.5,
    avatar_url: 'https://example.com/alice.jpg',
    last_played: '2024-01-15T10:30:00Z',
    preferences: {
      ai_difficulty: 'medium',
      preferred_game_modes: ['wolf_goat_pig'],
      preferred_player_count: 4,
      betting_style: 'conservative',
      display_hints: true
    }
  },
  {
    id: '2',
    name: 'Bob Smith',
    handicap: 18.0,
    avatar_url: '',
    last_played: null,
    preferences: {
      ai_difficulty: 'easy',
      preferred_game_modes: ['wolf_goat_pig'],
      preferred_player_count: 4,
      betting_style: 'aggressive',
      display_hints: false
    }
  }
];

const mockStatistics = {
  games_played: 15,
  total_earnings: 125.50,
  win_rate: 0.67,
  average_score: 82.3,
  best_score: 74,
  holes_won: 42,
  favorite_bet_type: 'conservative'
};

describe('usePlayerProfile', () => {
  beforeEach(() => {
    fetch.mockClear();
    mockLocalStorage.getItem.mockClear();
    mockLocalStorage.setItem.mockClear();
    mockLocalStorage.removeItem.mockClear();
    mockLocalStorage.clear.mockClear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Initialization and Loading', () => {
    test('initializes with empty state', () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => []
      });

      const { result } = renderHook(() => usePlayerProfile());

      expect(result.current.selectedProfile).toBeNull();
      expect(result.current.profiles).toEqual([]);
      expect(result.current.profileStatistics).toBeNull();
      expect(result.current.loading).toBe(true);
      expect(result.current.error).toBeNull();
      expect(result.current.syncStatus).toBe('idle');
      expect(result.current.hasProfiles).toBe(false);
      expect(result.current.hasSelectedProfile).toBe(false);
    });

    test('loads data from localStorage on initialization', async () => {
      const cachedProfile = JSON.stringify(mockProfiles[0]);
      const cachedProfiles = JSON.stringify(mockProfiles);
      const cachedStats = JSON.stringify({ '1': { data: mockStatistics, loadedAt: Date.now() } });

      mockLocalStorage.getItem
        .mockImplementationOnce((key) => {
          if (key === 'wgp_selected_profile') return cachedProfile;
          if (key === 'wgp_profiles_cache') return cachedProfiles;
          if (key === 'wgp_statistics_cache') return cachedStats;
          return null;
        });

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.selectedProfile).toEqual(mockProfiles[0]);
      expect(result.current.profiles).toEqual(mockProfiles);
      expect(result.current.hasProfiles).toBe(true);
      expect(result.current.hasSelectedProfile).toBe(true);
    });

    test('handles corrupted localStorage data gracefully', async () => {
      mockLocalStorage.getItem
        .mockReturnValue('invalid json');

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should clear corrupted data and proceed normally
      expect(mockLocalStorage.removeItem).toHaveBeenCalled();
      expect(result.current.profiles).toEqual(mockProfiles);
    });

    test('syncs with server on initialization', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/players');
      });

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'wgp_profiles_cache',
        JSON.stringify(mockProfiles)
      );
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'wgp_last_sync',
        expect.any(String)
      );
    });

    test('handles server sync errors gracefully', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Failed to load player profiles');
      expect(result.current.syncStatus).toBe('error');
    });
  });

  describe('Profile Selection', () => {
    test('selects profile and saves to localStorage', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Mock statistics fetch
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatistics
      });

      // Mock last played update
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      await act(async () => {
        await result.current.selectProfile(mockProfiles[0]);
      });

      expect(result.current.selectedProfile).toEqual(mockProfiles[0]);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'wgp_selected_profile',
        JSON.stringify(mockProfiles[0])
      );
    });

    test('loads statistics when profile is selected', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Mock statistics fetch
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatistics
      });

      // Mock last played update
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      await act(async () => {
        await result.current.selectProfile(mockProfiles[0]);
      });

      expect(fetch).toHaveBeenCalledWith('/api/players/1/statistics');
      expect(result.current.profileStatistics).toEqual(mockStatistics);
    });

    test('updates last played when profile is selected', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Mock statistics and last played calls
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatistics
      });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      await act(async () => {
        await result.current.selectProfile(mockProfiles[0]);
      });

      expect(fetch).toHaveBeenCalledWith('/api/players/1', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          last_played: expect.any(String)
        })
      });
    });
  });

  describe('Profile CRUD Operations', () => {
    test('creates new profile successfully', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const newProfileData = {
        name: 'Charlie Brown',
        handicap: 12.0,
        preferences: {
          ai_difficulty: 'medium',
          betting_style: 'moderate'
        }
      };

      const createdProfile = { id: '3', ...newProfileData };

      // Mock create profile API call
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => createdProfile
      });

      // Mock statistics and last played calls for auto-selection
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      let createdProfileResult;
      await act(async () => {
        createdProfileResult = await result.current.createProfile(newProfileData);
      });

      expect(fetch).toHaveBeenCalledWith('/api/players', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProfileData)
      });

      expect(createdProfileResult).toEqual(createdProfile);
      expect(result.current.profiles).toContainEqual(createdProfile);
      expect(result.current.selectedProfile).toEqual(createdProfile);
    });

    test('updates existing profile successfully', async () => {
      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(mockProfiles[0]));
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const updateData = {
        name: 'Alice Johnson-Smith',
        handicap: 7.5
      };

      const updatedProfile = { ...mockProfiles[0], ...updateData };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => updatedProfile
      });

      let updateResult;
      await act(async () => {
        updateResult = await result.current.updateProfile('1', updateData);
      });

      expect(fetch).toHaveBeenCalledWith('/api/players/1', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
      });

      expect(updateResult).toEqual(updatedProfile);
      expect(result.current.profiles.find(p => p.id === '1')).toEqual(updatedProfile);
      expect(result.current.selectedProfile).toEqual(updatedProfile);
    });

    test('deletes profile successfully', async () => {
      const profilesWithSelected = JSON.stringify(mockProfiles);
      const selectedProfile = JSON.stringify(mockProfiles[0]);

      mockLocalStorage.getItem
        .mockImplementation((key) => {
          if (key === 'wgp_selected_profile') return selectedProfile;
          if (key === 'wgp_profiles_cache') return profilesWithSelected;
          return null;
        });

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.selectedProfile).toEqual(mockProfiles[0]);
      });

      fetch.mockResolvedValueOnce({ ok: true });

      await act(async () => {
        await result.current.deleteProfile('1');
      });

      expect(fetch).toHaveBeenCalledWith('/api/players/1', {
        method: 'DELETE'
      });

      expect(result.current.profiles.find(p => p.id === '1')).toBeUndefined();
      expect(result.current.selectedProfile).toBeNull();
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('wgp_selected_profile');
    });

    test('handles API errors in CRUD operations', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Test create error
      fetch.mockRejectedValueOnce(new Error('Creation failed'));

      await act(async () => {
        try {
          await result.current.createProfile({ name: 'Test' });
        } catch (error) {
          expect(error.message).toBe('Creation failed');
        }
      });

      expect(result.current.error).toBe('Creation failed');

      // Clear error and test update error
      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();

      fetch.mockRejectedValueOnce(new Error('Update failed'));

      await act(async () => {
        try {
          await result.current.updateProfile('1', { name: 'Updated' });
        } catch (error) {
          expect(error.message).toBe('Update failed');
        }
      });

      expect(result.current.error).toBe('Update failed');
    });
  });

  describe('Statistics Management', () => {
    test('loads and caches profile statistics', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatistics
      });

      let stats;
      await act(async () => {
        stats = await result.current.loadProfileStatistics('1');
      });

      expect(fetch).toHaveBeenCalledWith('/api/players/1/statistics');
      expect(stats).toEqual(mockStatistics);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'wgp_statistics_cache',
        expect.stringContaining('"1"')
      );
    });

    test('returns cached statistics when available and recent', async () => {
      const recentCache = {
        '1': {
          data: mockStatistics,
          loadedAt: Date.now() - 60000 // 1 minute ago
        }
      };

      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'wgp_statistics_cache') return JSON.stringify(recentCache);
        return null;
      });

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      let stats;
      await act(async () => {
        stats = await result.current.loadProfileStatistics('1');
      });

      // Should return cached data without making API call
      expect(stats).toEqual(mockStatistics);
      expect(fetch).not.toHaveBeenCalledWith('/api/players/1/statistics');
    });

    test('fetches fresh statistics when cache is stale', async () => {
      const staleCache = {
        '1': {
          data: mockStatistics,
          loadedAt: Date.now() - 600000 // 10 minutes ago
        }
      };

      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'wgp_statistics_cache') return JSON.stringify(staleCache);
        return null;
      });

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const freshStats = { ...mockStatistics, games_played: 20 };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => freshStats
      });

      let stats;
      await act(async () => {
        stats = await result.current.loadProfileStatistics('1');
      });

      expect(fetch).toHaveBeenCalledWith('/api/players/1/statistics');
      expect(stats).toEqual(freshStats);
    });

    test('records game result and invalidates statistics cache', async () => {
      const cachedStats = {
        '1': {
          data: mockStatistics,
          loadedAt: Date.now()
        }
      };

      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'wgp_statistics_cache') return JSON.stringify(cachedStats);
        return null;
      });

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const gameResult = {
        player_profile_id: '1',
        total_score: 78,
        earnings: 25.00,
        holes_won: 8
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 'game_123', ...gameResult })
      });

      let recordResult;
      await act(async () => {
        recordResult = await result.current.recordGameResult(gameResult);
      });

      expect(fetch).toHaveBeenCalledWith('/api/game-results', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(gameResult)
      });

      expect(recordResult.id).toBe('game_123');

      // Statistics cache should be invalidated
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'wgp_statistics_cache',
        JSON.stringify({})
      );
    });
  });

  describe('Server Synchronization', () => {
    test('syncs with server periodically', async () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'wgp_last_sync') return String(Date.now() - 400000); // 6+ minutes ago
        return null;
      });

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      renderHook(() => usePlayerProfile());

      // Initial sync
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/players');
      });

      // Clear previous calls
      fetch.mockClear();
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      // Advance time to trigger periodic sync
      act(() => {
        jest.advanceTimersByTime(60000); // 1 minute
      });

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/players');
      });
    });

    test('updates selected profile during sync', async () => {
      const originalProfile = mockProfiles[0];
      const updatedProfileFromServer = {
        ...originalProfile,
        handicap: 7.0, // Changed on server
        last_played: '2024-01-16T10:00:00Z'
      };

      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'wgp_selected_profile') return JSON.stringify(originalProfile);
        return null;
      });

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => [updatedProfileFromServer, mockProfiles[1]]
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.selectedProfile).toEqual(updatedProfileFromServer);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'wgp_selected_profile',
        JSON.stringify(updatedProfileFromServer)
      );
    });

    test('handles sync errors gracefully', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      
      // First call succeeds for initial load
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
        expect(result.current.syncStatus).toBe('success');
      });

      // Next sync fails
      fetch.mockRejectedValueOnce(new Error('Sync failed'));

      await act(async () => {
        await result.current.syncWithServer();
      });

      expect(result.current.syncStatus).toBe('error');

      // Status should clear after timeout
      act(() => {
        jest.advanceTimersByTime(6000);
      });

      expect(result.current.syncStatus).toBe('idle');
    });
  });

  describe('Utility Functions', () => {
    test('getProfileById returns correct profile', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.getProfileById('1')).toEqual(mockProfiles[0]);
      expect(result.current.getProfileById('2')).toEqual(mockProfiles[1]);
      expect(result.current.getProfileById('999')).toBeUndefined();
    });

    test('getProfileByName returns correct profile (case insensitive)', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.getProfileByName('Alice Johnson')).toEqual(mockProfiles[0]);
      expect(result.current.getProfileByName('alice johnson')).toEqual(mockProfiles[0]);
      expect(result.current.getProfileByName('ALICE JOHNSON')).toEqual(mockProfiles[0]);
      expect(result.current.getProfileByName('Bob Smith')).toEqual(mockProfiles[1]);
      expect(result.current.getProfileByName('Nonexistent')).toBeUndefined();
    });

    test('refreshProfiles triggers server sync', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Clear previous calls
      fetch.mockClear();
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      await act(async () => {
        await result.current.refreshProfiles();
      });

      expect(fetch).toHaveBeenCalledWith('/api/players');
    });

    test('clearError resets error state', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockRejectedValue(new Error('Initial error'));

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.error).toBe('Failed to load player profiles');
      });

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Export Functionality', () => {
    test('exports profile data with statistics', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Mock statistics fetch
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatistics
      });

      await act(async () => {
        await result.current.exportProfileData('1');
      });

      expect(fetch).toHaveBeenCalledWith('/api/players/1/statistics');
      expect(URL.createObjectURL).toHaveBeenCalled();
      expect(mockLink.click).toHaveBeenCalled();
      expect(document.body.appendChild).toHaveBeenCalledWith(mockLink);
      expect(document.body.removeChild).toHaveBeenCalledWith(mockLink);
      expect(URL.revokeObjectURL).toHaveBeenCalledWith('mock-object-url');

      // Check download filename format
      expect(mockLink.download).toMatch(/^wgp-profile-Alice Johnson-\d{4}-\d{2}-\d{2}\.json$/);
    });

    test('handles export errors gracefully', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Mock statistics fetch failure
      fetch.mockRejectedValueOnce(new Error('Stats failed'));

      await act(async () => {
        await result.current.exportProfileData('1');
      });

      expect(result.current.error).toBe('Failed to export profile data');
    });
  });

  describe('Performance and Edge Cases', () => {
    test('handles rapid profile selection changes', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Mock rapid API calls
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockStatistics
      });

      // Rapid selections
      await act(async () => {
        result.current.selectProfile(mockProfiles[0]);
        result.current.selectProfile(mockProfiles[1]);
        result.current.selectProfile(mockProfiles[0]);
      });

      // Should handle gracefully without errors
      expect(result.current.error).toBeNull();
    });

    test('handles localStorage quota exceeded', async () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('QuotaExceededError');
      });

      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Should not crash when localStorage fails
      expect(result.current.profiles).toEqual(mockProfiles);
    });

    test('maintains state consistency during concurrent operations', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockProfiles
      });

      const { result } = renderHook(() => usePlayerProfile());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Mock concurrent operations
      const createPromise = act(async () => {
        fetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({ id: '3', name: 'New Player' })
        });
        fetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
        fetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
        
        return result.current.createProfile({ name: 'New Player' });
      });

      const updatePromise = act(async () => {
        fetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({ ...mockProfiles[0], name: 'Updated Alice' })
        });
        
        return result.current.updateProfile('1', { name: 'Updated Alice' });
      });

      await Promise.all([createPromise, updatePromise]);

      // State should remain consistent
      expect(result.current.profiles.length).toBeGreaterThanOrEqual(2);
      expect(result.current.error).toBeNull();
    });
  });
});