/**
 * AppFooter Component
 *
 * Displays version information and cache management controls.
 * Provides users visibility into app version and manual cache clearing.
 */

import React, { useState, useCallback } from 'react';
import { useTheme } from '../theme/Provider';
import {
  APP_VERSION,
  BUILD_TIMESTAMP,
  checkForUpdates,
  forceRefresh,
  clearAllCaches,
  getCacheStats,
} from '../services/cacheManager';

const AppFooter = () => {
  const theme = useTheme();
  const [isChecking, setIsChecking] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [updateStatus, setUpdateStatus] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [cacheStats, setCacheStats] = useState(null);
  const [isVersionHovered, setIsVersionHovered] = useState(false);

  const handleCheckUpdates = useCallback(async () => {
    setIsChecking(true);
    setUpdateStatus(null);

    try {
      const result = await checkForUpdates();

      if (result.updateAvailable) {
        setUpdateStatus({
          type: 'update',
          message: `Update available: v${result.serverVersion}`,
          serverVersion: result.serverVersion,
        });
      } else if (result.error) {
        setUpdateStatus({
          type: 'error',
          message: `Check failed: ${result.error}`,
        });
      } else {
        setUpdateStatus({
          type: 'current',
          message: 'You have the latest version!',
        });
      }
    } catch (error) {
      setUpdateStatus({
        type: 'error',
        message: 'Failed to check for updates',
      });
    } finally {
      setIsChecking(false);
    }
  }, []);

  const handleClearCache = useCallback(async () => {
    if (!window.confirm('Clear all cached data? This may require reloading the page.')) {
      return;
    }

    setIsClearing(true);

    try {
      await clearAllCaches();
      setUpdateStatus({
        type: 'success',
        message: 'Cache cleared successfully!',
      });
      // Offer to reload
      if (window.confirm('Cache cleared. Reload the page now?')) {
        window.location.reload();
      }
    } catch (error) {
      setUpdateStatus({
        type: 'error',
        message: 'Failed to clear cache',
      });
    } finally {
      setIsClearing(false);
    }
  }, []);

  const handleForceRefresh = useCallback(async () => {
    if (!window.confirm('Force refresh will clear all caches and reload the app. Continue?')) {
      return;
    }
    await forceRefresh();
  }, []);

  const handleShowDetails = useCallback(async () => {
    if (!showDetails) {
      const stats = await getCacheStats();
      setCacheStats(stats);
    }
    setShowDetails(!showDetails);
  }, [showDetails]);

  const formatBuildTime = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
      return timestamp;
    }
  };

  const footerStyle = {
    background: theme.colors.cardBackground || theme.colors.background,
    borderTop: `1px solid ${theme.colors.border}`,
    padding: '16px 20px',
    marginTop: '40px',
  };

  const containerStyle = {
    maxWidth: '1200px',
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  };

  const rowStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '12px',
  };

  const versionInfoStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    fontSize: '13px',
    color: theme.colors.textSecondary,
    flexWrap: 'wrap',
    cursor: 'pointer',
    padding: '4px 8px',
    borderRadius: '6px',
    transition: 'background 0.2s',
    background: isVersionHovered ? (theme.colors.border + '40') : 'transparent',
  };

  const buttonGroupStyle = {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  };

  const smallButtonStyle = {
    background: 'transparent',
    color: theme.colors.textSecondary,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: '6px',
    padding: '6px 12px',
    fontSize: '12px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  };

  const statusStyle = {
    padding: '8px 12px',
    borderRadius: '6px',
    fontSize: '13px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  };

  const getStatusColors = (type) => {
    switch (type) {
      case 'update':
        return { background: '#FEF3C7', color: '#92400E', border: '1px solid #F59E0B' };
      case 'success':
      case 'current':
        return { background: '#D1FAE5', color: '#065F46', border: '1px solid #10B981' };
      case 'error':
        return { background: '#FEE2E2', color: '#991B1B', border: '1px solid #EF4444' };
      default:
        return { background: theme.colors.border, color: theme.colors.text, border: 'none' };
    }
  };

  const detailsStyle = {
    background: theme.colors.background,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: '8px',
    padding: '16px',
    marginTop: '8px',
    fontSize: '13px',
  };

  return (
    <footer style={footerStyle}>
      <div style={containerStyle}>
        <div style={rowStyle}>
          {/* Version Info - clickable to show details */}
          <div
            style={versionInfoStyle}
            onClick={handleShowDetails}
            onKeyDown={(e) => e.key === 'Enter' && handleShowDetails()}
            onMouseEnter={() => setIsVersionHovered(true)}
            onMouseLeave={() => setIsVersionHovered(false)}
            role="button"
            tabIndex={0}
            title="Click to show build details"
          >
            <span>
              <strong>Version:</strong> {APP_VERSION}
            </span>
            <span>|</span>
            <span>
              <strong>Built:</strong> {formatBuildTime(BUILD_TIMESTAMP)}
            </span>
          </div>

          {/* Action Buttons */}
          <div style={buttonGroupStyle}>
            <button
              style={smallButtonStyle}
              onClick={handleCheckUpdates}
              disabled={isChecking}
              title="Check for app updates"
            >
              {isChecking ? '⏳' : '🔄'} Check Updates
            </button>
            <button
              style={smallButtonStyle}
              onClick={handleClearCache}
              disabled={isClearing}
              title="Clear browser cache"
            >
              {isClearing ? '⏳' : '🗑️'} Clear Cache
            </button>
            <button
              style={smallButtonStyle}
              onClick={handleForceRefresh}
              title="Force refresh (clears cache and reloads)"
            >
              ⚡ Force Refresh
            </button>
            <button
              style={smallButtonStyle}
              onClick={handleShowDetails}
              title="Show cache details"
            >
              {showDetails ? '▼' : '▶'} Details
            </button>
          </div>
        </div>

        {/* Status Message */}
        {updateStatus && (
          <div style={{ ...statusStyle, ...getStatusColors(updateStatus.type) }}>
            {updateStatus.type === 'update' && '⚠️'}
            {updateStatus.type === 'success' && '✅'}
            {updateStatus.type === 'current' && '✅'}
            {updateStatus.type === 'error' && '❌'}
            <span>{updateStatus.message}</span>
            {updateStatus.type === 'update' && (
              <button
                style={{
                  ...smallButtonStyle,
                  background: '#059669',
                  color: '#fff',
                  border: 'none',
                  marginLeft: '8px',
                }}
                onClick={handleForceRefresh}
              >
                Update Now
              </button>
            )}
            <button
              style={{
                ...smallButtonStyle,
                padding: '4px 8px',
                marginLeft: 'auto',
              }}
              onClick={() => setUpdateStatus(null)}
            >
              ✕
            </button>
          </div>
        )}

        {/* Detailed Info */}
        {showDetails && (
          <div style={detailsStyle}>
            <h4 style={{ margin: '0 0 12px 0', color: theme.colors.primary }}>
              Cache Information
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
              <div>
                <strong>App Version:</strong> {APP_VERSION}
              </div>
              <div>
                <strong>Build Time:</strong> {formatBuildTime(BUILD_TIMESTAMP)}
              </div>
              {cacheStats && (
                <>
                  <div>
                    <strong>Cache Names:</strong> {cacheStats.cacheNames.length > 0 ? cacheStats.cacheNames.join(', ') : 'None'}
                  </div>
                  <div>
                    <strong>Cached Entries:</strong> {cacheStats.entries}
                  </div>
                </>
              )}
              <div>
                <strong>Service Worker:</strong> {'serviceWorker' in navigator ? 'Supported' : 'Not supported'}
              </div>
            </div>
            <p style={{ margin: '12px 0 0 0', color: theme.colors.textSecondary, fontSize: '12px' }}>
              Tip: If the app seems outdated, use "Force Refresh" to get the latest version.
            </p>
          </div>
        )}
      </div>
    </footer>
  );
};

export default AppFooter;
