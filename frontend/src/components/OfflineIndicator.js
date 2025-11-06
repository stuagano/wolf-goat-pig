import React, { useState, useEffect } from 'react';
import { setupConnectivityListeners, isOffline } from '../serviceWorkerRegistration';

/**
 * Offline Indicator Component
 *
 * Shows a banner when the user is offline (common on golf courses).
 * Indicates that the game will continue to work using cached data
 * and localStorage, syncing when connection is restored.
 */
const OfflineIndicator = ({ showPersistenceMode = false }) => {
  const [offline, setOffline] = useState(isOffline());
  const [justWentOnline, setJustWentOnline] = useState(false);
  const [persistenceMode, setPersistenceMode] = useState('unknown');

  useEffect(() => {
    // Initial check
    setOffline(!navigator.onLine);

    // Setup listeners
    const cleanup = setupConnectivityListeners(
      () => {
        setOffline(false);
        setJustWentOnline(true);
        setTimeout(() => setJustWentOnline(false), 3000);
      },
      () => {
        setOffline(true);
        setJustWentOnline(false);
      }
    );

    return cleanup;
  }, []);

  // Check persistence mode from localStorage or last API response
  useEffect(() => {
    const checkPersistence = () => {
      try {
        const lastGameState = localStorage.getItem('wolf-goat-pig-game-state');
        if (lastGameState) {
          const parsed = JSON.parse(lastGameState);
          if (parsed.offline_mode) {
            setPersistenceMode('offline');
          } else if (parsed.fallback_mode) {
            setPersistenceMode('fallback');
          } else {
            setPersistenceMode('database');
          }
        }
      } catch (error) {
        console.error('Failed to check persistence mode:', error);
      }
    };

    checkPersistence();
  }, [offline]);

  if (justWentOnline) {
    return (
      <div style={styles.banner} className="online-banner">
        <div style={styles.container}>
          <div style={styles.iconContainer}>
            <svg style={styles.icon} fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          </div>
          <div style={styles.content}>
            <p style={styles.title}>Back Online</p>
            <p style={styles.message}>
              Connection restored. Syncing game data...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!offline && !showPersistenceMode) {
    return null;
  }

  if (offline) {
    return (
      <div style={styles.offlineBanner} className="offline-banner">
        <div style={styles.container}>
          <div style={styles.iconContainer}>
            <svg style={styles.icon} fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div style={styles.content}>
            <p style={styles.title}>Offline Mode</p>
            <p style={styles.message}>
              No connection. Game continues using saved data. Changes will sync when connection returns.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (showPersistenceMode && persistenceMode === 'fallback') {
    return (
      <div style={styles.warningBanner} className="fallback-banner">
        <div style={styles.container}>
          <div style={styles.iconContainer}>
            <svg style={styles.icon} fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div style={styles.content}>
            <p style={styles.title}>Temporary Storage</p>
            <p style={styles.message}>
              Game saved in memory only. Will persist until server restart.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

const styles = {
  banner: {
    backgroundColor: '#4caf50',
    color: 'white',
    padding: '12px 16px',
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 9999,
    boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
    animation: 'slideDown 0.3s ease-out'
  },
  offlineBanner: {
    backgroundColor: '#ff9800',
    color: 'white',
    padding: '12px 16px',
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 9999,
    boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
  },
  warningBanner: {
    backgroundColor: '#ffc107',
    color: '#000',
    padding: '12px 16px',
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 9999,
    boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
  },
  container: {
    display: 'flex',
    alignItems: 'center',
    maxWidth: '1200px',
    margin: '0 auto'
  },
  iconContainer: {
    flexShrink: 0,
    marginRight: '12px'
  },
  icon: {
    width: '24px',
    height: '24px'
  },
  content: {
    flex: 1
  },
  title: {
    margin: 0,
    fontWeight: 600,
    fontSize: '14px',
    marginBottom: '4px'
  },
  message: {
    margin: 0,
    fontSize: '12px',
    opacity: 0.9
  }
};

export default OfflineIndicator;
