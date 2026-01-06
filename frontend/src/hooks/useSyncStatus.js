/**
 * useSyncStatus Hook
 * 
 * Provides real-time sync status for UI components.
 * Shows pending sync count, online/offline status, and last sync time.
 */

import { useState, useEffect, useCallback } from 'react';
import syncManager from '../services/syncManager';

/**
 * Hook to monitor sync status
 * @returns {Object} Sync status object
 */
export function useSyncStatus() {
  const [status, setStatus] = useState({
    pendingCount: syncManager.getPendingSyncCount(),
    isProcessing: false,
    lastSync: syncManager.getLastSyncTime(),
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    errors: syncManager.getSyncErrors(),
  });

  useEffect(() => {
    // Subscribe to sync status changes
    const unsubscribe = syncManager.addSyncListener(newStatus => {
      setStatus(newStatus);
    });

    // Setup auto-sync on mount
    const cleanupAutoSync = syncManager.setupAutoSync();

    return () => {
      unsubscribe();
      cleanupAutoSync();
    };
  }, []);

  // Force refresh status
  const refresh = useCallback(() => {
    setStatus({
      pendingCount: syncManager.getPendingSyncCount(),
      isProcessing: false,
      lastSync: syncManager.getLastSyncTime(),
      isOnline: navigator.onLine,
      errors: syncManager.getSyncErrors(),
    });
  }, []);

  // Force retry all pending
  const forceRetry = useCallback(async () => {
    return syncManager.forceRetryAll();
  }, []);

  // Clear all pending syncs
  const clearPending = useCallback(() => {
    syncManager.clearQueue();
  }, []);

  return {
    ...status,
    refresh,
    forceRetry,
    clearPending,
    hasPendingSync: status.pendingCount > 0,
  };
}

/**
 * Hook for syncing hole data with offline support
 * @param {string} gameId - The game ID
 * @returns {Object} Sync functions and status
 */
export function useHoleSync(gameId) {
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastError, setLastError] = useState(null);
  const syncStatus = useSyncStatus();

  const syncHole = useCallback(async (holeQuarters, optionalDetails, currentHole) => {
    if (!gameId) {
      return { success: false, error: 'No game ID' };
    }

    setIsSyncing(true);
    setLastError(null);

    try {
      const result = await syncManager.syncHoleData(
        gameId,
        holeQuarters,
        optionalDetails,
        currentHole
      );

      if (!result.success && result.error) {
        setLastError(result.error);
      }

      return result;
    } catch (error) {
      setLastError(error.message);
      return { success: false, error: error.message };
    } finally {
      setIsSyncing(false);
    }
  }, [gameId]);

  return {
    syncHole,
    isSyncing,
    lastError,
    clearError: () => setLastError(null),
    ...syncStatus,
  };
}

export default useSyncStatus;
