/**
 * Sync Manager - Offline-First Data Synchronization
 * 
 * Handles unreliable network conditions (like on a golf course) by:
 * 1. Saving all data locally first (optimistic update)
 * 2. Queueing sync requests for background processing
 * 3. Automatically retrying when connectivity is restored
 * 4. Providing sync status for UI feedback
 */

import { createNamespacedStorage } from '../utils/storage';

const syncStore = createNamespacedStorage('wgp-sync');

const STORAGE_KEYS = {
  SYNC_QUEUE: 'sync-queue',
  LAST_SYNC: 'last-sync',
  SYNC_ERRORS: 'sync-errors',
  GAME_STATE: 'game-state', // Local game state backup
};

// Sync status for event listeners
let syncListeners = [];
let isProcessing = false;
let retryTimeoutId = null;

/**
 * Get current sync queue
 */
export function getSyncQueue() {
  return syncStore.get(STORAGE_KEYS.SYNC_QUEUE, []);
}

/**
 * Get pending sync count
 */
export function getPendingSyncCount() {
  return getSyncQueue().length;
}

/**
 * Check if there are pending syncs
 */
export function hasPendingSync() {
  return getPendingSyncCount() > 0;
}

/**
 * Get last successful sync time
 */
export function getLastSyncTime() {
  return syncStore.get(STORAGE_KEYS.LAST_SYNC, null);
}

/**
 * Get recent sync errors
 */
export function getSyncErrors() {
  return syncStore.get(STORAGE_KEYS.SYNC_ERRORS, []);
}

/**
 * Add a listener for sync status changes
 * @param {Function} listener - Callback function(status)
 * @returns {Function} Unsubscribe function
 */
export function addSyncListener(listener) {
  syncListeners.push(listener);
  return () => {
    syncListeners = syncListeners.filter(l => l !== listener);
  };
}

/**
 * Notify all listeners of status change
 */
function notifyListeners() {
  const status = {
    pendingCount: getPendingSyncCount(),
    isProcessing,
    lastSync: getLastSyncTime(),
    isOnline: navigator.onLine,
    errors: getSyncErrors(),
  };
  syncListeners.forEach(listener => {
    try {
      listener(status);
    } catch (err) {
      console.error('[SyncManager] Listener error:', err);
    }
  });
}

/**
 * Queue a sync request for background processing
 * 
 * @param {string} gameId - The game ID
 * @param {string} type - Request type (e.g., 'quarters-only', 'complete-hole')
 * @param {Object} payload - The data to sync
 * @param {Object} options - Additional options
 * @returns {string} Queue item ID
 */
export function queueSync(gameId, type, payload, options = {}) {
  const queue = getSyncQueue();
  
  const queueItem = {
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    gameId,
    type,
    payload,
    createdAt: new Date().toISOString(),
    attempts: 0,
    lastAttempt: null,
    priority: options.priority || 'normal', // 'high', 'normal', 'low'
    ...options,
  };

  // For hole syncs, we can merge with existing queue items for same game
  // This prevents duplicate syncs if user submits multiple holes while offline
  if (type === 'quarters-only') {
    const existingIndex = queue.findIndex(
      item => item.gameId === gameId && item.type === 'quarters-only'
    );
    
    if (existingIndex >= 0) {
      // Merge the payloads - newer data takes precedence
      const existing = queue[existingIndex];
      const mergedPayload = {
        ...existing.payload,
        hole_quarters: {
          ...existing.payload.hole_quarters,
          ...payload.hole_quarters,
        },
        optional_details: {
          ...existing.payload.optional_details,
          ...payload.optional_details,
        },
        current_hole: Math.max(
          existing.payload.current_hole || 0,
          payload.current_hole || 0
        ),
      };
      queue[existingIndex] = {
        ...existing,
        payload: mergedPayload,
        updatedAt: new Date().toISOString(),
      };
      syncStore.set(STORAGE_KEYS.SYNC_QUEUE, queue);
      console.log('[SyncManager] Merged with existing queue item for game:', gameId);
      notifyListeners();
      return existing.id;
    }
  }

  queue.push(queueItem);
  syncStore.set(STORAGE_KEYS.SYNC_QUEUE, queue);
  
  console.log('[SyncManager] Queued sync:', queueItem.id, type);
  notifyListeners();
  
  // Trigger processing if online
  if (navigator.onLine) {
    scheduleProcessing(1000); // Small delay to batch rapid updates
  }
  
  return queueItem.id;
}

/**
 * Schedule sync processing with debounce
 */
function scheduleProcessing(delay = 0) {
  if (retryTimeoutId) {
    clearTimeout(retryTimeoutId);
  }
  retryTimeoutId = setTimeout(() => {
    processQueue();
  }, delay);
}

/**
 * Process the sync queue
 * @param {Object} options - Processing options
 * @returns {Promise<Object>} Results of sync attempts
 */
export async function processQueue(options = {}) {
  if (isProcessing) {
    console.log('[SyncManager] Already processing queue');
    return { skipped: true };
  }

  if (!navigator.onLine) {
    console.log('[SyncManager] Offline, skipping queue processing');
    return { offline: true };
  }

  const queue = getSyncQueue();
  if (queue.length === 0) {
    console.log('[SyncManager] Queue is empty');
    return { synced: 0, failed: 0 };
  }

  isProcessing = true;
  notifyListeners();

  console.log(`[SyncManager] Processing ${queue.length} queued items...`);

  const results = {
    synced: 0,
    failed: 0,
    errors: [],
    retrying: [],
  };

  const updatedQueue = [];
  const API_URL = process.env.REACT_APP_API_URL || '';
  const MAX_ATTEMPTS = 5;

  for (const item of queue) {
    try {
      // Build the endpoint URL based on type
      let url, method, body;
      
      switch (item.type) {
        case 'quarters-only':
          url = `${API_URL}/games/${item.gameId}/quarters-only`;
          method = 'POST';
          body = JSON.stringify(item.payload);
          break;
        case 'complete-game':
          url = `${API_URL}/games/${item.gameId}/complete`;
          method = 'POST';
          body = JSON.stringify(item.payload || {});
          break;
        default:
          console.warn('[SyncManager] Unknown sync type:', item.type);
          continue;
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        results.synced++;
        console.log('[SyncManager] Synced:', item.id, item.type);
        
        // Update last sync time
        syncStore.set(STORAGE_KEYS.LAST_SYNC, new Date().toISOString());
        
        // Clear errors for this game
        const errors = getSyncErrors().filter(e => e.gameId !== item.gameId);
        syncStore.set(STORAGE_KEYS.SYNC_ERRORS, errors);
      } else {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}`;
        
        // Don't retry client errors (4xx) except 408 (timeout) and 429 (rate limit)
        if (response.status >= 400 && response.status < 500 && 
            response.status !== 408 && response.status !== 429) {
          results.failed++;
          results.errors.push({
            id: item.id,
            gameId: item.gameId,
            type: item.type,
            error: errorMessage,
            permanent: true,
          });
          
          // Store error for UI display
          const errors = getSyncErrors();
          errors.push({
            gameId: item.gameId,
            error: errorMessage,
            timestamp: new Date().toISOString(),
          });
          syncStore.set(STORAGE_KEYS.SYNC_ERRORS, errors.slice(-10)); // Keep last 10
          
          console.error('[SyncManager] Permanent failure:', item.id, errorMessage);
        } else {
          // Retry server errors
          item.attempts++;
          item.lastAttempt = new Date().toISOString();
          item.lastError = errorMessage;
          
          if (item.attempts < MAX_ATTEMPTS) {
            updatedQueue.push(item);
            results.retrying.push(item.id);
          } else {
            results.failed++;
            results.errors.push({
              id: item.id,
              gameId: item.gameId,
              type: item.type,
              error: `Max attempts reached: ${errorMessage}`,
            });
          }
        }
      }
    } catch (error) {
      // Network error - queue for retry
      item.attempts++;
      item.lastAttempt = new Date().toISOString();
      item.lastError = error.message;
      
      if (error.name === 'AbortError') {
        item.lastError = 'Request timed out';
      }
      
      if (item.attempts < MAX_ATTEMPTS) {
        updatedQueue.push(item);
        results.retrying.push(item.id);
        console.log('[SyncManager] Will retry:', item.id, item.lastError);
      } else {
        results.failed++;
        results.errors.push({
          id: item.id,
          gameId: item.gameId,
          type: item.type,
          error: `Max attempts reached: ${item.lastError}`,
        });
        console.error('[SyncManager] Max retries exceeded:', item.id);
      }
    }
  }

  // Update queue with items that need retry
  syncStore.set(STORAGE_KEYS.SYNC_QUEUE, updatedQueue);
  
  isProcessing = false;
  notifyListeners();

  console.log('[SyncManager] Processing complete:', results);

  // Schedule retry for remaining items with exponential backoff
  if (updatedQueue.length > 0 && navigator.onLine) {
    const maxAttempts = Math.max(...updatedQueue.map(i => i.attempts));
    const delay = Math.min(30000, 2000 * Math.pow(2, maxAttempts - 1));
    console.log(`[SyncManager] Scheduling retry in ${delay}ms`);
    scheduleProcessing(delay);
  }

  return results;
}

/**
 * Clear the sync queue (use with caution)
 */
export function clearQueue() {
  syncStore.set(STORAGE_KEYS.SYNC_QUEUE, []);
  syncStore.set(STORAGE_KEYS.SYNC_ERRORS, []);
  notifyListeners();
  console.log('[SyncManager] Queue cleared');
}

/**
 * Remove a specific item from the queue
 */
export function removeFromQueue(itemId) {
  const queue = getSyncQueue();
  const filtered = queue.filter(item => item.id !== itemId);
  syncStore.set(STORAGE_KEYS.SYNC_QUEUE, filtered);
  notifyListeners();
}

/**
 * Force retry all queued items now
 */
export async function forceRetryAll() {
  // Reset attempt counts
  const queue = getSyncQueue();
  queue.forEach(item => {
    item.attempts = 0;
    item.lastError = null;
  });
  syncStore.set(STORAGE_KEYS.SYNC_QUEUE, queue);
  
  return processQueue();
}

/**
 * Setup automatic sync on reconnection
 * @returns {Function} Cleanup function
 */
export function setupAutoSync() {
  const handleOnline = () => {
    console.log('[SyncManager] Connection restored, processing queue...');
    notifyListeners();
    scheduleProcessing(2000); // Small delay after reconnect
  };

  const handleOffline = () => {
    console.log('[SyncManager] Connection lost');
    if (retryTimeoutId) {
      clearTimeout(retryTimeoutId);
      retryTimeoutId = null;
    }
    notifyListeners();
  };

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  // Process any pending items on init if online
  if (navigator.onLine && getPendingSyncCount() > 0) {
    scheduleProcessing(3000);
  }

  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
    if (retryTimeoutId) {
      clearTimeout(retryTimeoutId);
    }
  };
}

/**
 * Sync hole data with offline support
 * This is the main function to use from components
 * 
 * @param {string} gameId - Game ID
 * @param {Object} holeQuarters - Quarters data by hole
 * @param {Object} optionalDetails - Additional hole details
 * @param {number} currentHole - Current hole number
 * @returns {Promise<Object>} Result with success status
 */
export async function syncHoleData(gameId, holeQuarters, optionalDetails, currentHole) {
  const payload = {
    hole_quarters: holeQuarters,
    optional_details: optionalDetails,
    current_hole: currentHole,
  };

  // If offline, queue immediately
  if (!navigator.onLine) {
    const queueId = queueSync(gameId, 'quarters-only', payload);
    return {
      success: true,
      queued: true,
      queueId,
      message: 'Saved locally, will sync when online',
    };
  }

  // Try to sync immediately
  const API_URL = process.env.REACT_APP_API_URL || '';
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout

    const response = await fetch(`${API_URL}/games/${gameId}/quarters-only`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      syncStore.set(STORAGE_KEYS.LAST_SYNC, new Date().toISOString());
      notifyListeners();
      return {
        success: true,
        synced: true,
      };
    }

    // Server error - queue for retry
    const errorData = await response.json().catch(() => ({}));
    const errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}`;
    
    // Don't queue client errors that won't succeed on retry
    if (response.status >= 400 && response.status < 500 && 
        response.status !== 408 && response.status !== 429) {
      return {
        success: false,
        error: errorMessage,
        permanent: true,
      };
    }
    
    // Queue for retry
    const queueId = queueSync(gameId, 'quarters-only', payload);
    return {
      success: true,
      queued: true,
      queueId,
      message: `Sync failed (${errorMessage}), will retry`,
    };

  } catch (error) {
    // Network error - queue for retry
    const queueId = queueSync(gameId, 'quarters-only', payload);
    return {
      success: true,
      queued: true,
      queueId,
      message: error.name === 'AbortError' 
        ? 'Request timed out, will retry' 
        : 'Network error, will retry when online',
    };
  }
}

/**
 * Save game state locally for persistence across page refresh
 * This ensures no data is lost even when offline
 * 
 * @param {string} gameId - Game ID
 * @param {Object} gameState - Full game state to persist
 */
export function saveLocalGameState(gameId, gameState) {
  if (!gameId || !gameState) return false;
  
  const key = `${STORAGE_KEYS.GAME_STATE}-${gameId}`;
  const data = {
    ...gameState,
    savedAt: new Date().toISOString(),
  };
  
  const success = syncStore.set(key, data);
  if (success) {
    console.log('[SyncManager] Game state saved locally:', gameId);
  }
  return success;
}

/**
 * Load game state from local storage
 * Use this to restore state after page refresh
 * 
 * @param {string} gameId - Game ID
 * @returns {Object|null} Saved game state or null
 */
export function loadLocalGameState(gameId) {
  if (!gameId) return null;
  
  const key = `${STORAGE_KEYS.GAME_STATE}-${gameId}`;
  const data = syncStore.get(key, null);
  
  if (data) {
    console.log('[SyncManager] Loaded local game state:', gameId, 'saved at:', data.savedAt);
  }
  return data;
}

/**
 * Clear local game state (call after successful full sync or game completion)
 * 
 * @param {string} gameId - Game ID
 */
export function clearLocalGameState(gameId) {
  if (!gameId) return;
  
  const key = `${STORAGE_KEYS.GAME_STATE}-${gameId}`;
  syncStore.remove(key);
  console.log('[SyncManager] Cleared local game state:', gameId);
}

/**
 * Check if there's local game state newer than what's on server
 * 
 * @param {string} gameId - Game ID
 * @param {string} serverUpdatedAt - Server's last update timestamp
 * @returns {Object|null} Local state if newer, null otherwise
 */
export function getNewerLocalState(gameId, serverUpdatedAt) {
  const localState = loadLocalGameState(gameId);
  if (!localState || !localState.savedAt) return null;
  
  const localTime = new Date(localState.savedAt);
  const serverTime = serverUpdatedAt ? new Date(serverUpdatedAt) : new Date(0);
  
  if (localTime > serverTime) {
    console.log('[SyncManager] Local state is newer than server');
    return localState;
  }
  
  return null;
}

const syncManager = {
  getSyncQueue,
  getPendingSyncCount,
  hasPendingSync,
  getLastSyncTime,
  getSyncErrors,
  addSyncListener,
  queueSync,
  processQueue,
  clearQueue,
  removeFromQueue,
  forceRetryAll,
  setupAutoSync,
  syncHoleData,
  // Local game state persistence
  saveLocalGameState,
  loadLocalGameState,
  clearLocalGameState,
  getNewerLocalState,
};

export default syncManager;
