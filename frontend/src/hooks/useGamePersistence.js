import { useEffect, useCallback } from 'react';
import { storage } from '../utils';

/**
 * Hook for persisting game state to localStorage
 * Allows the game to work offline or when the backend is unavailable
 */
export const useGamePersistence = (gameState, isActive) => {
  const STORAGE_KEY = 'wolf-goat-pig-game-state';
  const BACKUP_KEY = 'wolf-goat-pig-game-backup';

  // Save game state to localStorage
  const saveToLocal = useCallback((state) => {
    if (!state) return;

    const dataToSave = {
      ...state,
      savedAt: new Date().toISOString(),
      version: '1.0'
    };

    // Keep a backup of the previous state before overwriting
    const existing = storage.get(STORAGE_KEY);
    if (existing) {
      storage.set(BACKUP_KEY, existing);
    }

    // Save current state
    const success = storage.set(STORAGE_KEY, dataToSave);
    if (success) {
      console.log('[Persistence] Game state saved to localStorage');
    }
  }, [STORAGE_KEY, BACKUP_KEY]);

  // Load game state from localStorage
  const loadFromLocal = useCallback(() => {
    // Try to load main state
    const stored = storage.get(STORAGE_KEY);
    if (stored) {
      console.log('[Persistence] Game state loaded from localStorage');
      return stored;
    }

    // Try backup if main state failed
    const backup = storage.get(BACKUP_KEY);
    if (backup) {
      console.log('[Persistence] Loaded from backup');
      return backup;
    }

    return null;
  }, [STORAGE_KEY, BACKUP_KEY]);

  // Clear saved game state
  const clearLocal = useCallback(() => {
    const removed = storage.remove(STORAGE_KEY) && storage.remove(BACKUP_KEY);
    if (removed) {
      console.log('[Persistence] Game state cleared from localStorage');
    }
  }, [STORAGE_KEY, BACKUP_KEY]);

  // Auto-save when game state changes
  useEffect(() => {
    if (isActive && gameState) {
      const timeoutId = setTimeout(() => {
        saveToLocal(gameState);
      }, 1000); // Debounce saves by 1 second

      return () => clearTimeout(timeoutId);
    }
  }, [gameState, isActive, saveToLocal]);

  // Check for abandoned games on mount
  const getAbandonedGame = useCallback(() => {
    const stored = loadFromLocal();
    if (!stored) return null;

    // Check if the game was saved recently (within 24 hours)
    const savedAt = new Date(stored.savedAt);
    const now = new Date();
    const hoursSince = (now - savedAt) / (1000 * 60 * 60);

    if (hoursSince > 24) {
      // Game is too old, clear it
      clearLocal();
      return null;
    }

    return stored;
  }, [loadFromLocal, clearLocal]);

  return {
    saveToLocal,
    loadFromLocal,
    clearLocal,
    getAbandonedGame
  };
};

export default useGamePersistence;
