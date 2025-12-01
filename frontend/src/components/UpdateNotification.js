/**
 * UpdateNotification Component
 *
 * Displays a notification when a new version of the app is available.
 * Allows users to update immediately or dismiss the notification.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  APP_VERSION,
  checkForUpdates,
  forceRefresh,
  dismissUpdate,
  isUpdateDismissed,
} from '../services/cacheManager';

const styles = {
  container: {
    position: 'fixed',
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
    backgroundColor: '#1f2937',
    color: '#ffffff',
    padding: '16px 24px',
    borderRadius: '12px',
    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.3)',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    zIndex: 10000,
    maxWidth: '90vw',
    animation: 'slideUp 0.3s ease-out',
  },
  icon: {
    fontSize: '24px',
    flexShrink: 0,
  },
  content: {
    flex: 1,
  },
  title: {
    fontWeight: '600',
    marginBottom: '4px',
    fontSize: '14px',
  },
  message: {
    fontSize: '12px',
    color: '#9ca3af',
  },
  buttons: {
    display: 'flex',
    gap: '8px',
    flexShrink: 0,
  },
  updateButton: {
    backgroundColor: '#059669',
    color: '#ffffff',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: '500',
    fontSize: '13px',
    transition: 'background-color 0.2s',
  },
  dismissButton: {
    backgroundColor: 'transparent',
    color: '#9ca3af',
    border: '1px solid #4b5563',
    padding: '8px 12px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '13px',
    transition: 'all 0.2s',
  },
  updating: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    color: '#9ca3af',
    fontSize: '13px',
  },
  spinner: {
    width: '16px',
    height: '16px',
    border: '2px solid #4b5563',
    borderTopColor: '#059669',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
};

// CSS keyframes
const keyframes = `
  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateX(-50%) translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
`;

export function UpdateNotification({ onUpdate }) {
  const [updateInfo, setUpdateInfo] = useState(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  // Check for updates on mount and periodically
  const checkUpdates = useCallback(async () => {
    const result = await checkForUpdates();

    if (result.updateAvailable && !isUpdateDismissed(result.serverVersion)) {
      setUpdateInfo(result);
    }
  }, []);

  useEffect(() => {
    // Inject keyframes
    const styleEl = document.createElement('style');
    styleEl.textContent = keyframes;
    document.head.appendChild(styleEl);

    // Initial check after a short delay
    const initialTimeout = setTimeout(checkUpdates, 3000);

    // Listen for update events from cache manager
    const handleUpdateAvailable = (event) => {
      if (!isUpdateDismissed(event.detail.serverVersion)) {
        setUpdateInfo(event.detail);
      }
    };

    window.addEventListener('appUpdateAvailable', handleUpdateAvailable);

    // Listen for service worker updates
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        // New service worker took control - reload
        window.location.reload();
      });
    }

    return () => {
      clearTimeout(initialTimeout);
      window.removeEventListener('appUpdateAvailable', handleUpdateAvailable);
      document.head.removeChild(styleEl);
    };
  }, [checkUpdates]);

  const handleUpdate = async () => {
    setIsUpdating(true);

    try {
      if (onUpdate) {
        await onUpdate();
      }
      await forceRefresh();
    } catch (error) {
      console.error('[UpdateNotification] Update failed:', error);
      setIsUpdating(false);
    }
  };

  const handleDismiss = () => {
    if (updateInfo?.serverVersion) {
      dismissUpdate(updateInfo.serverVersion);
    }
    setDismissed(true);
    setUpdateInfo(null);
  };

  // Don't render if no update or dismissed
  if (!updateInfo || dismissed) {
    return null;
  }

  return (
    <div style={styles.container} role="alert" aria-live="polite">
      <span style={styles.icon} role="img" aria-label="Update available">
        🔄
      </span>

      <div style={styles.content}>
        <div style={styles.title}>Update Available</div>
        <div style={styles.message}>
          Version {updateInfo.serverVersion} is ready
          {updateInfo.releaseNotes && ` - ${updateInfo.releaseNotes}`}
        </div>
      </div>

      <div style={styles.buttons}>
        {isUpdating ? (
          <div style={styles.updating}>
            <div style={styles.spinner} />
            <span>Updating...</span>
          </div>
        ) : (
          <>
            <button
              style={styles.dismissButton}
              onClick={handleDismiss}
              aria-label="Dismiss update notification"
            >
              Later
            </button>
            <button
              style={styles.updateButton}
              onClick={handleUpdate}
              aria-label="Update app now"
            >
              Update Now
            </button>
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Hook to manually trigger update check
 */
export function useUpdateCheck() {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [checking, setChecking] = useState(false);

  const check = useCallback(async () => {
    setChecking(true);
    try {
      const result = await checkForUpdates();
      setUpdateAvailable(result.updateAvailable);
      return result;
    } finally {
      setChecking(false);
    }
  }, []);

  const update = useCallback(async () => {
    await forceRefresh();
  }, []);

  return {
    updateAvailable,
    checking,
    currentVersion: APP_VERSION,
    check,
    update,
  };
}

export default UpdateNotification;
