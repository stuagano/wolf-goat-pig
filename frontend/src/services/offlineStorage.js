/**
 * Offline Storage Service for Wolf Goat Pig
 *
 * Provides localStorage-based persistence for game state during offline play.
 * Automatically syncs with the server when connection is restored.
 */

import { storage, createNamespacedStorage } from '../utils/storage';

// Create namespaced storage for offline functionality
const offlineStore = createNamespacedStorage('wgp-offline');

const STORAGE_KEYS = {
  GAME_STATE: 'wgp-game-state',
  PENDING_SYNC: 'pending-sync',
  LAST_SYNC: 'last-sync',
};

/**
 * Save game state to localStorage for offline persistence
 * @param {string} gameId - The game ID
 * @param {object} state - The game state to save
 */
export function saveGameState(gameId, state) {
  const storageKey = `${STORAGE_KEYS.GAME_STATE}-${gameId}`;
  const data = {
    gameId,
    state,
    savedAt: new Date().toISOString(),
  };
  return storage.set(storageKey, data);
}

/**
 * Load game state from localStorage
 * @param {string} gameId - The game ID
 * @returns {object|null} The saved game state or null
 */
export function loadGameState(gameId) {
  const storageKey = `${STORAGE_KEYS.GAME_STATE}-${gameId}`;
  const data = storage.get(storageKey);
  return data ? data.state : null;
}

/**
 * Clear saved game state for a specific game
 * @param {string} gameId - The game ID
 */
export function clearGameState(gameId) {
  const storageKey = `${STORAGE_KEYS.GAME_STATE}-${gameId}`;
  return storage.remove(storageKey);
}

/**
 * Queue an API call for later sync when offline
 * @param {string} gameId - The game ID
 * @param {object} request - The request to queue {method, url, body}
 */
export function queueForSync(gameId, request) {
  const pending = getPendingSync();
  pending.push({
    gameId,
    request,
    queuedAt: new Date().toISOString(),
  });
  return offlineStore.set(STORAGE_KEYS.PENDING_SYNC, pending);
}

/**
 * Get all pending sync requests
 * @returns {Array} Array of pending sync requests
 */
export function getPendingSync() {
  return offlineStore.get(STORAGE_KEYS.PENDING_SYNC, []);
}

/**
 * Clear all pending sync requests
 */
export function clearPendingSync() {
  return offlineStore.remove(STORAGE_KEYS.PENDING_SYNC);
}

/**
 * Process pending sync requests when back online
 * @param {function} fetchFn - Optional custom fetch function
 * @returns {Promise<object>} Results of sync attempts
 */
export async function processPendingSync(fetchFn = fetch) {
  const pending = getPendingSync();
  if (pending.length === 0) {
    return { synced: 0, failed: 0, errors: [] };
  }

  console.log(`[OfflineStorage] Processing ${pending.length} pending sync requests...`);

  const results = {
    synced: 0,
    failed: 0,
    errors: [],
  };

  const remaining = [];

  for (const item of pending) {
    try {
      const response = await fetchFn(item.request.url, {
        method: item.request.method || 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...item.request.headers,
        },
        body: item.request.body ? JSON.stringify(item.request.body) : undefined,
      });

      if (response.ok) {
        results.synced++;
        console.log(`[OfflineStorage] Synced request for game ${item.gameId}`);
      } else {
        // Don't retry client errors (4xx)
        if (response.status >= 400 && response.status < 500) {
          results.failed++;
          results.errors.push({
            gameId: item.gameId,
            error: `HTTP ${response.status}`,
          });
        } else {
          // Retry server errors
          remaining.push(item);
        }
      }
    } catch (error) {
      // Network error - keep for retry
      remaining.push(item);
      results.errors.push({
        gameId: item.gameId,
        error: error.message,
      });
    }
  }

  // Update remaining items
  if (remaining.length > 0) {
    offlineStore.set(STORAGE_KEYS.PENDING_SYNC, remaining);
  } else {
    clearPendingSync();
  }

  // Update last sync time
  offlineStore.set(STORAGE_KEYS.LAST_SYNC, new Date().toISOString());

  console.log(`[OfflineStorage] Sync complete: ${results.synced} synced, ${results.failed} failed, ${remaining.length} remaining`);

  return results;
}

/**
 * Get the timestamp of the last successful sync
 * @returns {string|null} ISO timestamp or null
 */
export function getLastSyncTime() {
  return offlineStore.get(STORAGE_KEYS.LAST_SYNC);
}

/**
 * Check if there are pending sync requests
 * @returns {boolean}
 */
export function hasPendingSync() {
  return getPendingSync().length > 0;
}

/**
 * Get count of pending sync requests
 * @returns {number}
 */
export function getPendingSyncCount() {
  return getPendingSync().length;
}

/**
 * Set up automatic sync when connection is restored
 * @param {function} onSyncComplete - Callback when sync completes
 * @returns {function} Cleanup function
 */
export function setupAutoSync(onSyncComplete) {
  const handleOnline = async () => {
    if (!navigator.onLine) return;

    const pending = getPendingSync();
    if (pending.length === 0) return;

    console.log('[OfflineStorage] Connection restored, syncing pending requests...');

    try {
      const results = await processPendingSync();
      if (onSyncComplete) {
        onSyncComplete(results);
      }
    } catch (error) {
      console.error('[OfflineStorage] Auto-sync failed:', error);
    }
  };

  window.addEventListener('online', handleOnline);

  // Check immediately in case we're already online with pending items
  if (navigator.onLine) {
    handleOnline();
  }

  return () => {
    window.removeEventListener('online', handleOnline);
  };
}

/**
 * Export all saved game data (for backup/debugging)
 * @returns {object} All stored game data
 */
export function exportAllData() {
  const data = {
    exportedAt: new Date().toISOString(),
    games: {},
    pendingSync: getPendingSync(),
    lastSync: getLastSyncTime(),
  };

  // Find all game state entries
  const gameKeys = storage.getKeys(STORAGE_KEYS.GAME_STATE);
  gameKeys.forEach(key => {
    data.games[key] = storage.get(key);
  });

  return data;
}

const offlineStorage = {
  saveGameState,
  loadGameState,
  clearGameState,
  queueForSync,
  getPendingSync,
  clearPendingSync,
  processPendingSync,
  getLastSyncTime,
  hasPendingSync,
  getPendingSyncCount,
  setupAutoSync,
  exportAllData,
};

export default offlineStorage;
