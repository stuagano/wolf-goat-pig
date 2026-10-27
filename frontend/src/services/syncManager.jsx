/**
 * Sync Manager - Offline-First Data Synchronization
 *
 * Handles unreliable network conditions (like on a golf course) by:
 * 1. Saving all data locally first (optimistic update)
 * 2. Queueing sync requests for background processing
 * 3. Automatically retrying when connectivity is restored
 * 4. Providing sync status for UI feedback
 *
 * Course-signal notes:
 * - `navigator.onLine` is a hint, not truth — we still queue on timeout/network fail
 *   even when the browser claims to be online.
 * - Hole `scores` queue items are never dropped after max attempts; they keep
 *   retrying with capped backoff until a POST succeeds.
 * - If the queue was emptied but local still has holes the server lacks, we
 *   re-seed the queue from the local snapshot on load/reconnect.
 */

import { createNamespacedStorage } from '../utils/storage';
import { apiConfig } from '../config/api.config';
import { localHasUnsyncedHoles } from './gameReconcile';

let authenticatedFetch = async () => { throw new Error('Sign in to sync scores'); };

/** Interactive hole-submit timeout — fail into the queue quickly on flaky signal. */
const INTERACTIVE_TIMEOUT_MS = 10000;
/** Background drain timeout — allow a bit more for catch-up after reconnect. */
const QUEUE_TIMEOUT_MS = 30000;
const MAX_ATTEMPTS = 5;

/**
 * Correlation id so a failed score save can be traced to its server log line.
 * Opaque and bounded on both ends: we only echo a server reference that looks
 * like an id, so an error message can never carry round or player data.
 */
const SAFE_REQUEST_ID = /^[A-Za-z0-9_-]{8,64}$/;

function newRequestId() {
  return `wgp-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function safeRequestId(value) {
  return value && SAFE_REQUEST_ID.test(value) ? value : undefined;
}

/** Append the reference a user can quote when a save fails. */
function withReference(message, requestId) {
  return requestId ? `${message} (Reference: ${requestId})` : message;
}

// Convert internal queue payload {hole_quarters, optional_details, current_hole}
// to the /scores API shape {holes: [...], current_hole}
export function toScoresPayload({ hole_quarters, optional_details, current_hole, expected_revision }) {
  const holes = Object.keys(hole_quarters || {}).map((holeStr) => {
    const details = (optional_details || {})[holeStr] || {};
    return {
      hole_number: parseInt(holeStr, 10),
      quarters: hole_quarters[holeStr],
      gross_scores: details.gross_scores || null,
      notes: details.notes || null,
      teams: details.teams || null,
      winner: details.winner || null,
      wager: details.wager || null,
      phase: details.phase || null,
      float_invoked_by: details.float_invoked_by || null,
      option_invoked_by: details.option_invoked_by || null,
      duncan_invoked: details.duncan_invoked || false,
      joes_special_wager: details.joes_special_wager ?? null,
      aardvark_requested_team: details.aardvark_requested_team || null,
      aardvark_tossed: details.aardvark_tossed || false,
      aardvark_solo: details.aardvark_solo || false,
      aardvark_ping_ponged: details.aardvark_ping_ponged || false,
      carry_over_applied: details.carry_over_applied || false,
    };
  });
  return { holes, current_hole, expected_revision };
}

/**
 * Rebuild a /scores queue payload from the local write-buffer snapshot.
 * Used when local is ahead of the server but the sync queue is empty
 * (max-retries previously dropped the item, or a reload mid-flight).
 */
export function buildScoresPayloadFromLocal(localState) {
  const hole_quarters = {};
  const optional_details = {};
  (localState?.holeHistory || []).forEach((hole) => {
    if (hole?.hole == null) return;
    const key = String(hole.hole);
    if (hole.points_delta) {
      hole_quarters[key] = hole.points_delta;
    }
    optional_details[key] = {
      teams: hole.teams || null,
      winner: hole.winner || null,
      wager: hole.wager ?? null,
      gross_scores: hole.gross_scores || null,
      phase: hole.phase || null,
      notes: hole.notes || null,
      float_invoked_by: hole.float_invoked_by || null,
      option_invoked_by: hole.option_invoked_by || null,
      duncan_invoked: hole.duncan_invoked || false,
      joes_special_wager: hole.joes_special_wager ?? null,
      aardvark_requested_team: hole.aardvark_requested_team || null,
      aardvark_tossed: hole.aardvark_tossed || false,
      aardvark_solo: hole.aardvark_solo || false,
      aardvark_ping_ponged: hole.aardvark_ping_ponged || false,
      carry_over_applied: hole.carry_over_applied || false,
    };
  });
  return {
    hole_quarters,
    optional_details,
    current_hole: localState?.currentHole || 1,
    expected_revision: localState?.expectedRevision,
  };
}

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
// Only an edit merged while this exact predecessor is in flight inherits its
// acknowledgement. Old/offline snapshots are never rebased just by game ID.
const inFlightScores = new Map();
let retryTimeoutId = null;
// Bounded receipts for mounted editors, keyed to the exact uploaded queue
// revision. These are observations, not a second queue or a persistence claim.
let queueOutcomes = [];

function recordQueueOutcome(item, state, error) {
  queueOutcomes.push({ queueId: item.id, queueVersion: item.version || 1, state, error });
  queueOutcomes = queueOutcomes.slice(-50);
}

export function getQueueOutcome(queueId, queueVersion) {
  const receipt = queueOutcomes.findLast(
    item => item.queueId === queueId && item.queueVersion === queueVersion,
  );
  if (receipt) return receipt;
  const item = getSyncQueue().find(item => item.id === queueId);
  if (item && (item.version || 1) === queueVersion) return { state: 'pending' };
  // Cleared, superseded, evicted receipt, or reload: never infer success from
  // absence, nor promise retries for a revision that is no longer queued.
  return { state: 'unknown' };
}

function persistQueue(queue) {
  if (!syncStore.set(STORAGE_KEYS.SYNC_QUEUE, queue)) {
    throw new Error('Unable to store the correction on this device. Keep your edits open and retry saving.');
  }
}

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
 * @param {string} type - Request type (e.g., 'scores', 'complete-game')
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
    requestKey: options.requestKey || crypto.randomUUID(),
    priority: options.priority || 'normal', // 'high', 'normal', 'low'
    ...options,
    version: 1,
  };

  // For hole syncs, we can merge with existing queue items for same game
  // This prevents duplicate syncs if user submits multiple holes while offline
  if (type === 'scores') {
    const existingIndex = queue.findIndex(
      item => item.gameId === gameId && item.type === 'scores' && !item.reviewRequired
    );
    
    if (existingIndex >= 0) {
      // Merge the payloads - newer data takes precedence
      const existing = queue[existingIndex];
      const mergedPayload = {
        ...existing.payload,
        expected_revision: payload.expected_revision ?? existing.payload.expected_revision,
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
      // A drain may still be awaiting another game after this predecessor's
      // request has finished. Keep the earlier proof until settlement, but only
      // across the same key/baseline; a stale replacement cannot inherit it.
      const predecessor = inFlightScores.get(existing.id) || existing.predecessor;
      const inheritsPredecessor = predecessor &&
        predecessor.requestKey === existing.requestKey &&
        predecessor.version <= (existing.version || 1) &&
        predecessor.expectedRevision === existing.payload.expected_revision &&
        predecessor.expectedRevision === mergedPayload.expected_revision;
      // A rejection carries its evidence onto the merged item: pending local
      // work stays in one place and stays held for review, never auto-retried.
      queue[existingIndex] = {
        ...existing,
        ...(options.reviewRequired
          ? { reviewRequired: true, review: options.review, lastError: options.lastError || existing.lastError }
          : {}),
        payload: mergedPayload,
        predecessor: inheritsPredecessor ? predecessor : null,
        version: (existing.version || 1) + 1,
        updatedAt: new Date().toISOString(),
      };
      persistQueue(queue);
      notifyListeners();
      return existing.id;
    }
  }

  queue.push(queueItem);
  persistQueue(queue);
  
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
    return { skipped: true };
  }

  if (!navigator.onLine) {
    return { offline: true };
  }

  const queue = getSyncQueue();
  if (queue.length === 0) {
    return { synced: 0, failed: 0 };
  }

  isProcessing = true;
  notifyListeners();

  const results = {
    synced: 0,
    failed: 0,
    errors: [],
    retrying: [],
  };

  const updatedQueue = [];
  const API_URL = apiConfig.baseUrl;

  for (const item of queue) {
    if (item.reviewRequired) { updatedQueue.push(item); continue; }
    try {
      // Build the endpoint URL based on type
      let url, method, body;
      
      switch (item.type) {
        case 'scores':
          url = `${API_URL}/games/${item.gameId}/scores`;
          method = 'POST';
          body = JSON.stringify(toScoresPayload(item.payload));
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
      const timeoutId = setTimeout(() => controller.abort(), QUEUE_TIMEOUT_MS);

      if (item.type === 'scores') inFlightScores.set(item.id, {
        version: item.version || 1, requestKey: item.requestKey, expectedRevision: item.payload.expected_revision,
      });
      const response = await authenticatedFetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': item.requestKey,
          ...(item.type === 'scores' ? { 'X-Request-ID': newRequestId() } : {}),
        },
        body,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const accepted = await response.json().catch(() => ({}));
        const local = loadLocalGameState(item.gameId);
        if (local && Number.isInteger(accepted.revision)) {
          saveLocalGameState(item.gameId, { ...local, expectedRevision: accepted.revision, gameStatus: accepted.game_status || local.gameStatus });
        }
        item.acceptedRevision = accepted.revision;
        recordQueueOutcome(item, 'synced');
        results.synced++;
        // Update last sync time
        syncStore.set(STORAGE_KEYS.LAST_SYNC, new Date().toISOString());
        
        // Clear errors for this game
        const errors = getSyncErrors().filter(e => e.gameId !== item.gameId);
        syncStore.set(STORAGE_KEYS.SYNC_ERRORS, errors);
      } else {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = withReference(
          errorData.detail || errorData.message || `HTTP ${response.status}`,
          safeRequestId(response.headers?.get?.('X-Request-ID')),
        );
        
        if (response.status === 409) {
          item.reviewRequired = true;
          item.review = errorData.detail || errorData;
          item.lastError = 'Round changed. Review or reload before submitting again; your pending edits are retained.';
          updatedQueue.push(item);
          recordQueueOutcome(item, 'rejected', item.lastError);
          const errors = getSyncErrors();
          errors.push({ queueId: item.id, queueVersion: item.version || 1, gameId: item.gameId, error: item.lastError });
          syncStore.set(STORAGE_KEYS.SYNC_ERRORS, errors.slice(-10));
          continue;
        }
        // Don't retry client errors (4xx) except 408 (timeout) and 429 (rate limit)
        if (response.status >= 400 && response.status < 500 && 
            response.status !== 401 && response.status !== 403 &&
            response.status !== 408 && response.status !== 429) {
          recordQueueOutcome(item, 'rejected', errorMessage);
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
            queueId: item.id,
            queueVersion: item.version || 1,
            gameId: item.gameId,
            error: errorMessage,
            timestamp: new Date().toISOString(),
          });
          syncStore.set(STORAGE_KEYS.SYNC_ERRORS, errors.slice(-10)); // Keep last 10
          
          console.error('[SyncManager] Permanent failure:', item.id, errorMessage);
        } else {
          // Retry server errors
          requeueForRetry(item, errorMessage, updatedQueue, results);
        }
      }
    } catch (error) {
      // Network error - queue for retry
      const message =
        error.name === 'AbortError' ? 'Request timed out' : error.message;
      requeueForRetry(item, message, updatedQueue, results);
    } finally {
      inFlightScores.delete(item.id);
    }
  }

  // Preserve requests added/merged while an HTTP attempt was in flight. Only
  // settle the exact revisions in this drain's snapshot.
  const remainingQueue = getSyncQueue().flatMap(current => {
    const attempted = queue.find(item => item.id === current.id);
    if (!attempted) return [current];
    if ((current.version || 1) !== (attempted.version || 1)) {
      if (attempted.reviewRequired) return [{ ...current, reviewRequired: true, review: attempted.review, lastError: attempted.lastError }];
      const parent = current.predecessor;
      if (!current.reviewRequired && Number.isInteger(attempted.acceptedRevision) &&
          parent?.version === (attempted.version || 1) && parent?.requestKey === attempted.requestKey &&
          parent?.expectedRevision === current.payload.expected_revision &&
          parent?.expectedRevision === attempted.payload.expected_revision) {
        return [{ ...current, predecessor: null, payload: { ...current.payload, expected_revision: attempted.acceptedRevision } }];
      }
      return [current];
    }
    const retry = updatedQueue.find(item => item.id === current.id);
    return retry ? [retry] : [];
  });
  syncStore.set(STORAGE_KEYS.SYNC_QUEUE, remainingQueue);
  
  isProcessing = false;
  notifyListeners();

  // Schedule retry for remaining items with exponential backoff
  if (remainingQueue.some(item => !item.reviewRequired) && navigator.onLine) {
    const maxAttempts = Math.max(...remainingQueue.map(i => i.attempts));
    const delay = Math.min(30000, 2000 * Math.pow(2, Math.max(0, maxAttempts - 1)));
    scheduleProcessing(delay);
  }

  return results;
}

/**
 * Keep a failed item in the queue. Hole scores never drop — on a golf course
 * you can burn through MAX_ATTEMPTS while signal is dead; dropping them would
 * leave local ahead of the server with nothing left to drain.
 */
function requeueForRetry(item, errorMessage, updatedQueue, results) {
  item.attempts = (item.attempts || 0) + 1;
  item.lastAttempt = new Date().toISOString();
  item.lastError = errorMessage;

  const keepForever = item.type === 'scores';
  if (item.attempts < MAX_ATTEMPTS || keepForever) {
    if (keepForever && item.attempts >= MAX_ATTEMPTS) {
      // Cap the counter so backoff stays at the max delay, but never drop.
      item.attempts = MAX_ATTEMPTS;
    }
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
    console.error('[SyncManager] Max retries exceeded:', item.id);
  }
}

/**
 * Clear the sync queue (use with caution)
 */
export function clearQueue() {
  syncStore.set(STORAGE_KEYS.SYNC_QUEUE, []);
  syncStore.set(STORAGE_KEYS.SYNC_ERRORS, []);
  notifyListeners();
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
 * Setup automatic sync on reconnection / tab focus
 * @returns {Function} Cleanup function
 */
export function setupAutoSync(fetchWithAuth) {
  if (fetchWithAuth) authenticatedFetch = fetchWithAuth;
  const wakeAndDrain = () => {
    // Fresh signal after a dead stretch — give score uploads another full try.
    const queue = getSyncQueue();
    let touched = false;
    queue.forEach((item) => {
      if (item.type === 'scores' && (item.attempts || 0) > 0) {
        item.attempts = 0;
        item.lastError = null;
        touched = true;
      }
    });
    if (touched) {
      syncStore.set(STORAGE_KEYS.SYNC_QUEUE, queue);
    }
    notifyListeners();
    scheduleProcessing(1500);
  };

  const handleOnline = () => {
    wakeAndDrain();
  };

  const handleOffline = () => {
    if (retryTimeoutId) {
      clearTimeout(retryTimeoutId);
      retryTimeoutId = null;
    }
    notifyListeners();
  };

  const handleVisibility = () => {
    if (document.visibilityState === 'visible' && navigator.onLine) {
      if (getPendingSyncCount() > 0) {
        wakeAndDrain();
      }
    }
  };

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);
  document.addEventListener('visibilitychange', handleVisibility);

  // Process any pending items on init if online
  if (navigator.onLine && getPendingSyncCount() > 0) {
    scheduleProcessing(3000);
  }

  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
    document.removeEventListener('visibilitychange', handleVisibility);
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
export async function syncHoleData(gameId, holeQuarters, optionalDetails, currentHole, expectedRevision) {
  const requestKey = crypto.randomUUID();
  const payload = {
    expected_revision: expectedRevision ?? loadLocalGameState(gameId)?.expectedRevision,
    hole_quarters: holeQuarters,
    optional_details: optionalDetails,
    current_hole: currentHole,
  };

  // If offline, queue immediately
  if (!navigator.onLine) {
    const queueId = queueSync(gameId, 'scores', payload, { requestKey });
    return {
      success: true,
      queued: true,
      queueId,
      queueVersion: getSyncQueue().find(item => item.id === queueId)?.version,
      message: 'Saved locally, will sync when online',
    };
  }

  // Try to sync immediately
  const API_URL = apiConfig.baseUrl;
  const requestId = newRequestId();

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), INTERACTIVE_TIMEOUT_MS);

    const response = await authenticatedFetch(`${API_URL}/games/${gameId}/scores`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId,
        'Idempotency-Key': requestKey,
      },
      body: JSON.stringify(toScoresPayload(payload)),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const accepted = await response.json().catch(() => ({}));
      const local = loadLocalGameState(gameId);
      if (local && Number.isInteger(accepted.revision)) {
        saveLocalGameState(gameId, { ...local, expectedRevision: accepted.revision, gameStatus: accepted.game_status || local.gameStatus });
      }
      syncStore.set(STORAGE_KEYS.LAST_SYNC, new Date().toISOString());
      notifyListeners();
      return {
        success: true,
        synced: true,
      };
    }

    // Server error - queue for retry. The server's id is authoritative; only
    // expose it when it passes the same bounded-id rule as the backend.
    const responseId = safeRequestId(response.headers?.get?.('X-Request-ID'));
    const errorData = await response.json().catch(() => ({}));
    const errorMessage = withReference(
      errorData.detail || errorData.message || `HTTP ${response.status}`,
      responseId,
    );
    
    if (response.status === 409) {
      const message = 'Round changed. Review or reload before submitting again; your pending edits are retained.';
      const queueId = queueSync(gameId, 'scores', payload, { requestKey, reviewRequired: true, review: errorData.detail || errorData });
      return { success: false, reviewRequired: true, queueId, error: message, permanent: true };
    }
    // Don't queue client errors that won't succeed on retry
    if (response.status >= 400 && response.status < 500 && 
        response.status !== 401 && response.status !== 403 &&
        response.status !== 408 && response.status !== 429) {
      return {
        success: false,
        error: errorMessage,
        requestId: responseId,
        permanent: true,
      };
    }
    
    // Queue for retry
    const queueId = queueSync(gameId, 'scores', payload, { requestKey });
    return {
      success: true,
      queued: true,
      queueId,
      queueVersion: getSyncQueue().find(item => item.id === queueId)?.version,
      requestId: responseId,
      message: `Pending sync (${errorMessage}); will retry`,
    };

  } catch (error) {
    // Network error - queue for retry
    const queueId = queueSync(gameId, 'scores', payload, { requestKey });
    return {
      success: true,
      queued: true,
      queueId,
      queueVersion: getSyncQueue().find(item => item.id === queueId)?.version,
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
    return localState;
  }
  
  return null;
}

/**
 * True iff this specific game has an edit queued for sync. Per-game, unlike the
 * global hasPendingSync(). Drives the "local is authoritative only while it
 * holds unsynced work" rule.
 */
export function hasPendingSyncForGame(gameId) {
  return getSyncQueue().some((item) => item.gameId === gameId);
}

/**
 * If local is ahead of the server (or already queued), make sure a scores
 * sync item exists and kick the drain. Returns true when work was queued/pending.
 */
export function ensureScoresQueued(gameId, serverState = null) {
  const localState = loadLocalGameState(gameId);
  if (!serverState || serverState.gameStatus === 'completed' || localState?.gameStatus === 'completed' ||
      localState?.currentHole > 18 || serverState.expectedRevision !== localState?.expectedRevision) return false;
  const needsSync =
    hasPendingSyncForGame(gameId) ||
    localHasUnsyncedHoles(localState, serverState);

  if (!needsSync) {
    return false;
  }

  if (!hasPendingSyncForGame(gameId) && localState?.holeHistory?.length) {
    queueSync(gameId, 'scores', buildScoresPayloadFromLocal(localState));
  }

  if (typeof navigator === 'undefined' || navigator.onLine) {
    scheduleProcessing(500);
  }
  return true;
}

/**
 * Reconcile local cache vs server truth on load.
 * - Pending edits, OR local holds holes the server lacks (an in-flight sync that
 *   hasn't landed): re-seed the queue from local if needed and LEAVE the local
 *   cache so no unsynced work is lost.
 * - Otherwise the server is authoritative — overwrite the local cache with the
 *   server state so stale/duplicated local can't resurface.
 *
 * `serverState` MUST already be in the local cache shape
 * ({ holeHistory, currentHole, playerStandings }), mapped from GET /state.
 */
export function reconcileOnLoad(gameId, serverState) {
  if (!serverState) return;
  const localState = loadLocalGameState(gameId);
  const queue = getSyncQueue();
  let changed = false;
  queue.forEach(item => {
    if (item.gameId === gameId && (serverState.gameStatus === 'completed' ||
        item.payload.expected_revision !== serverState.expectedRevision)) {
      item.reviewRequired = true;
      item.lastError = 'Server round changed. Pending edits retained for review.';
      changed = true;
    }
  });
  if (changed) { persistQueue(queue); notifyListeners(); }
  if (hasPendingSyncForGame(gameId) || localHasUnsyncedHoles(localState, serverState)) {
    ensureScoresQueued(gameId, serverState);
    return;
  }
  if (serverState) {
    // Preserve roster snapshot fields when healing hole history from server.
    saveLocalGameState(gameId, {
      ...localState,
      ...serverState,
      players: serverState.players || localState?.players,
      baseWager: serverState.baseWager ?? localState?.baseWager,
      courseName: serverState.courseName || localState?.courseName,
    });
  }
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
  toScoresPayload,
  buildScoresPayloadFromLocal,
  ensureScoresQueued,
  // Local game state persistence
  saveLocalGameState,
  loadLocalGameState,
  clearLocalGameState,
  getNewerLocalState,
  hasPendingSyncForGame,
  reconcileOnLoad,
};

export default syncManager;
