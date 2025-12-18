// frontend/src/hooks/__tests__/useGamePersistence.test.js
import { renderHook, act, waitFor } from '@testing-library/react';
import { useGamePersistence } from '../useGamePersistence';
import { mockLocalStorage } from '../../test-utils/testHelpers';
import { createMockGameState } from '../../test-utils/mockFactories';

describe('useGamePersistence', () => {
  const STORAGE_KEY = 'wolf-goat-pig-game-state';
  const BACKUP_KEY = 'wolf-goat-pig-game-backup';

  let localStorageMock;

  beforeEach(() => {
    // Use mock factory from testHelpers
    localStorageMock = mockLocalStorage();

    // Suppress console.log/error during tests
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
    jest.useRealTimers();
  });

  describe('saveToLocal', () => {
    test('should save game state to localStorage', () => {
      const { result } = renderHook(() => useGamePersistence(null, false));

      const gameState = createMockGameState('mid_game', {
        game_id: 'test-123',
        current_hole: 5,
      });

      act(() => {
        result.current.saveToLocal(gameState);
      });

      expect(localStorageMock.setItem).toHaveBeenCalled();
      const savedData = JSON.parse(localStorageMock.setItem.mock.calls[0][1]);
      expect(savedData.game_id).toBe('test-123');
      expect(savedData.current_hole).toBe(5);
      expect(savedData.savedAt).toBeDefined();
      expect(savedData.version).toBe('1.0');
    });

    test('should not save when state is null', () => {
      const { result } = renderHook(() => useGamePersistence(null, false));

      act(() => {
        result.current.saveToLocal(null);
      });

      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });

    test('should not save when state is undefined', () => {
      const { result } = renderHook(() => useGamePersistence(null, false));

      act(() => {
        result.current.saveToLocal(undefined);
      });

      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });

    test('should handle localStorage errors gracefully', () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error('Storage full');
      });

      const { result } = renderHook(() => useGamePersistence(null, false));

      // Should not throw
      expect(() => {
        act(() => {
          result.current.saveToLocal({ game_id: 'test' });
        });
      }).not.toThrow();
    });
  });

  describe('loadFromLocal', () => {
    test('should load game state from localStorage', () => {
      const savedState = {
        game_id: 'test-123',
        current_hole: 5,
        savedAt: new Date().toISOString(),
      };
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === STORAGE_KEY) return JSON.stringify(savedState);
        return null;
      });

      const { result } = renderHook(() => useGamePersistence(null, false));

      let loaded;
      act(() => {
        loaded = result.current.loadFromLocal();
      });

      expect(loaded).toEqual(savedState);
    });

    test('should return null when no data exists', () => {
      const { result } = renderHook(() => useGamePersistence(null, false));

      let loaded;
      act(() => {
        loaded = result.current.loadFromLocal();
      });

      expect(loaded).toBeNull();
    });

    test('should load from backup when primary fails', () => {
      const backupState = {
        game_id: 'backup-123',
        current_hole: 3,
      };

      localStorageMock.getItem.mockImplementation((key) => {
        if (key === STORAGE_KEY) return 'invalid json{';
        if (key === BACKUP_KEY) return JSON.stringify(backupState);
        return null;
      });

      const { result } = renderHook(() => useGamePersistence(null, false));

      let loaded;
      act(() => {
        loaded = result.current.loadFromLocal();
      });

      expect(loaded).toEqual(backupState);
    });

    test('should return null when both primary and backup fail', () => {
      localStorageMock.getItem.mockImplementation(() => 'invalid json{');

      const { result } = renderHook(() => useGamePersistence(null, false));

      let loaded;
      act(() => {
        loaded = result.current.loadFromLocal();
      });

      expect(loaded).toBeNull();
    });
  });

  describe('clearLocal', () => {
    test('should remove both primary and backup keys', () => {
      const { result } = renderHook(() => useGamePersistence(null, false));

      act(() => {
        result.current.clearLocal();
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith(STORAGE_KEY);
      expect(localStorageMock.removeItem).toHaveBeenCalledWith(BACKUP_KEY);
    });

    test('should handle errors gracefully', () => {
      localStorageMock.removeItem.mockImplementation(() => {
        throw new Error('Cannot remove');
      });

      const { result } = renderHook(() => useGamePersistence(null, false));

      // Should not throw
      expect(() => {
        act(() => {
          result.current.clearLocal();
        });
      }).not.toThrow();
    });
  });

  describe('getAbandonedGame', () => {
    test('should return game if saved within 24 hours', () => {
      const recentState = {
        game_id: 'recent-123',
        savedAt: new Date().toISOString(),
      };
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === STORAGE_KEY) return JSON.stringify(recentState);
        return null;
      });

      const { result } = renderHook(() => useGamePersistence(null, false));

      let abandoned;
      act(() => {
        abandoned = result.current.getAbandonedGame();
      });

      expect(abandoned).toEqual(recentState);
    });

    test('should return null and clear if game is older than 24 hours', () => {
      const oldDate = new Date();
      oldDate.setHours(oldDate.getHours() - 25); // 25 hours ago

      const oldState = {
        game_id: 'old-123',
        savedAt: oldDate.toISOString(),
      };
      localStorageMock.getItem.mockImplementation((key) => {
        if (key === STORAGE_KEY) return JSON.stringify(oldState);
        return null;
      });

      const { result } = renderHook(() => useGamePersistence(null, false));

      let abandoned;
      act(() => {
        abandoned = result.current.getAbandonedGame();
      });

      expect(abandoned).toBeNull();
      expect(localStorageMock.removeItem).toHaveBeenCalled();
    });

    test('should return null when no stored data exists', () => {
      const { result } = renderHook(() => useGamePersistence(null, false));

      let abandoned;
      act(() => {
        abandoned = result.current.getAbandonedGame();
      });

      expect(abandoned).toBeNull();
    });
  });

  describe('auto-save behavior', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    test('should auto-save when isActive is true and gameState changes', async () => {
      const gameState = createMockGameState('initial', { game_id: 'auto-123', current_hole: 1 });
      const { rerender } = renderHook(
        ({ state, active }) => useGamePersistence(state, active),
        { initialProps: { state: gameState, active: true } }
      );

      // Wait for debounce
      act(() => {
        jest.advanceTimersByTime(1100);
      });

      expect(localStorageMock.setItem).toHaveBeenCalled();

      // Update game state
      const updatedState = createMockGameState('initial', { game_id: 'auto-123', current_hole: 2 });
      rerender({ state: updatedState, active: true });

      act(() => {
        jest.advanceTimersByTime(1100);
      });

      // Should have saved again
      expect(localStorageMock.setItem.mock.calls.length).toBeGreaterThanOrEqual(2);
    });

    test('should not auto-save when isActive is false', async () => {
      const gameState = createMockGameState('initial', { game_id: 'inactive-123', current_hole: 1 });
      renderHook(
        ({ state, active }) => useGamePersistence(state, active),
        { initialProps: { state: gameState, active: false } }
      );

      act(() => {
        jest.advanceTimersByTime(1100);
      });

      // setItem should not be called for auto-save
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });

    test('should debounce saves by 1 second', async () => {
      const gameState = createMockGameState('initial', { game_id: 'debounce-123', current_hole: 1 });
      const { rerender } = renderHook(
        ({ state, active }) => useGamePersistence(state, active),
        { initialProps: { state: gameState, active: true } }
      );

      // Rapidly change state
      for (let i = 2; i <= 5; i++) {
        rerender({ state: { ...gameState, current_hole: i }, active: true });
        act(() => {
          jest.advanceTimersByTime(100); // Less than 1 second
        });
      }

      // Should not have saved yet due to debouncing
      expect(localStorageMock.setItem).not.toHaveBeenCalled();

      // Wait for full debounce period
      act(() => {
        jest.advanceTimersByTime(1000);
      });

      // Now it should have saved
      expect(localStorageMock.setItem).toHaveBeenCalled();
    });
  });

  describe('hook return values', () => {
    test('should return all expected functions', () => {
      const { result } = renderHook(() => useGamePersistence(null, false));

      expect(typeof result.current.saveToLocal).toBe('function');
      expect(typeof result.current.loadFromLocal).toBe('function');
      expect(typeof result.current.clearLocal).toBe('function');
      expect(typeof result.current.getAbandonedGame).toBe('function');
    });
  });
});
