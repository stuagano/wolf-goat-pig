import { useEffect, useCallback } from 'react';

/**
 * Hook for persisting game state to localStorage
 * Allows the game to work offline or when the backend is unavailable
 */
export const useGamePersistence = (gameState, isActive) => {
  const STORAGE_KEY = 'wolf-goat-pig-game-state';
  const BACKUP_KEY = 'wolf-goat-pig-game-backup';

  // Save game state to localStorage
  const saveToLocal = useCallback((state) => {
    try {
      if (!state) return;

      const dataToSave = {
        ...state,
        savedAt: new Date().toISOString(),
        version: '1.0'
      };

      // Save current state
      localStorage.setItem(STORAGE_KEY, JSON.stringify(dataToSave));

      // Keep a backup of the previous state
      const existing = localStorage.getItem(STORAGE_KEY);
      if (existing) {
        localStorage.setItem(BACKUP_KEY, existing);
      }

      console.log('[Persistence] Game state saved to localStorage');
    } catch (error) {
      console.error('[Persistence] Failed to save game state:', error);
      // Storage might be full or disabled - fail silently
    }
  }, [STORAGE_KEY, BACKUP_KEY]);

  // Load game state from localStorage
  const loadFromLocal = useCallback(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return null;

      const parsed = JSON.parse(stored);
      console.log('[Persistence] Game state loaded from localStorage');
      return parsed;
    } catch (error) {
      console.error('[Persistence] Failed to load game state:', error);

      // Try backup
      try {
        const backup = localStorage.getItem(BACKUP_KEY);
        if (backup) {
          console.log('[Persistence] Loaded from backup');
          return JSON.parse(backup);
        }
      } catch (backupError) {
        console.error('[Persistence] Backup also failed:', backupError);
      }

      return null;
    }
  }, [STORAGE_KEY, BACKUP_KEY]);

  // Clear saved game state
  const clearLocal = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(BACKUP_KEY);
      console.log('[Persistence] Game state cleared from localStorage');
    } catch (error) {
      console.error('[Persistence] Failed to clear game state:', error);
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
