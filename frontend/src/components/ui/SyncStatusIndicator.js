/**
 * SyncStatusIndicator Component
 * 
 * Shows the current sync status - pending uploads, online/offline state,
 * and allows manual retry of failed syncs.
 */

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useSyncStatus } from '../hooks/useSyncStatus';
import { useTheme } from '../theme/Provider';

/**
 * Compact indicator for header/nav bar
 */
export function SyncStatusBadge({ onClick }) {
  const { pendingCount, isOnline, isProcessing } = useSyncStatus();
  const theme = useTheme();

  if (pendingCount === 0 && isOnline) {
    return null; // Don't show when everything is synced
  }

  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px 12px',
        borderRadius: '20px',
        border: 'none',
        background: !isOnline 
          ? '#ff9800' 
          : pendingCount > 0 
            ? '#2196f3' 
            : theme.colors.success,
        color: 'white',
        fontSize: '12px',
        fontWeight: 'bold',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
    >
      {isProcessing ? (
        <>
          <span className="sync-spinner">↻</span>
          <span>Syncing...</span>
        </>
      ) : !isOnline ? (
        <>
          <span>📵</span>
          <span>Offline</span>
          {pendingCount > 0 && <span>({pendingCount})</span>}
        </>
      ) : pendingCount > 0 ? (
        <>
          <span>☁️</span>
          <span>{pendingCount} pending</span>
        </>
      ) : (
        <>
          <span>✓</span>
          <span>Synced</span>
        </>
      )}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .sync-spinner {
          display: inline-block;
          animation: spin 1s linear infinite;
        }
      `}</style>
    </button>
  );
}

SyncStatusBadge.propTypes = {
  onClick: PropTypes.func,
};

/**
 * Full sync status panel with details and controls
 */
export function SyncStatusPanel({ onClose }) {
  const theme = useTheme();
  const { 
    pendingCount, 
    isOnline, 
    isProcessing, 
    lastSync, 
    errors,
    forceRetry,
    clearPending,
  } = useSyncStatus();
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      await forceRetry();
    } finally {
      setIsRetrying(false);
    }
  };

  const formatTime = (isoString) => {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div style={{
      background: theme.colors.paper,
      borderRadius: '12px',
      padding: '16px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
      maxWidth: '320px',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
      }}>
        <h3 style={{ margin: 0, fontSize: '16px', color: theme.colors.textPrimary }}>
          Sync Status
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '20px',
              cursor: 'pointer',
              color: theme.colors.textSecondary,
            }}
          >
            ×
          </button>
        )}
      </div>

      {/* Connection Status */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '10px 12px',
        background: isOnline ? '#e8f5e9' : '#fff3e0',
        borderRadius: '8px',
        marginBottom: '12px',
      }}>
        <span style={{ fontSize: '20px' }}>
          {isOnline ? '🌐' : '📵'}
        </span>
        <div>
          <div style={{ 
            fontWeight: 'bold', 
            color: isOnline ? '#2e7d32' : '#ef6c00',
            fontSize: '14px',
          }}>
            {isOnline ? 'Connected' : 'Offline'}
          </div>
          <div style={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            {isOnline 
              ? 'Data will sync automatically' 
              : 'Data saved locally, will sync when online'}
          </div>
        </div>
      </div>

      {/* Pending Syncs */}
      <div style={{
        padding: '12px',
        background: theme.colors.backgroundSecondary,
        borderRadius: '8px',
        marginBottom: '12px',
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ 
              fontSize: '24px', 
              fontWeight: 'bold',
              color: pendingCount > 0 ? '#1976d2' : theme.colors.success,
            }}>
              {pendingCount}
            </div>
            <div style={{ fontSize: '12px', color: theme.colors.textSecondary }}>
              Pending uploads
            </div>
          </div>
          {pendingCount > 0 && isOnline && (
            <button
              onClick={handleRetry}
              disabled={isRetrying || isProcessing}
              style={{
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                background: isRetrying || isProcessing ? '#ccc' : '#1976d2',
                color: 'white',
                fontSize: '13px',
                fontWeight: 'bold',
                cursor: isRetrying || isProcessing ? 'not-allowed' : 'pointer',
              }}
            >
              {isRetrying || isProcessing ? 'Syncing...' : 'Sync Now'}
            </button>
          )}
        </div>
      </div>

      {/* Last Sync */}
      <div style={{
        fontSize: '12px',
        color: theme.colors.textSecondary,
        marginBottom: '12px',
      }}>
        Last synced: {formatTime(lastSync)}
      </div>

      {/* Errors */}
      {errors && errors.length > 0 && (
        <div style={{
          background: '#ffebee',
          padding: '10px 12px',
          borderRadius: '8px',
          marginBottom: '12px',
        }}>
          <div style={{ 
            fontWeight: 'bold', 
            color: '#c62828',
            fontSize: '13px',
            marginBottom: '6px',
          }}>
            Recent Errors
          </div>
          {errors.slice(-3).map((error, idx) => (
            <div key={idx} style={{ 
              fontSize: '11px', 
              color: '#b71c1c',
              marginBottom: '4px',
            }}>
              {error.error}
            </div>
          ))}
        </div>
      )}

      {/* Clear Queue (only if pending) */}
      {pendingCount > 0 && (
        <button
          onClick={() => {
            if (window.confirm('Clear all pending syncs? Local data will be preserved but not uploaded.')) {
              clearPending();
            }
          }}
          style={{
            width: '100%',
            padding: '8px',
            borderRadius: '6px',
            border: `1px solid ${theme.colors.border}`,
            background: 'white',
            color: theme.colors.textSecondary,
            fontSize: '12px',
            cursor: 'pointer',
          }}
        >
          Clear Pending Queue
        </button>
      )}
    </div>
  );
}

SyncStatusPanel.propTypes = {
  onClose: PropTypes.func,
};

/**
 * Inline banner for showing sync status at top of page
 */
export function SyncStatusBanner() {
  // eslint-disable-next-line no-unused-vars
  const theme = useTheme(); // Available for future theming
  const { pendingCount, isOnline, isProcessing, forceRetry } = useSyncStatus();
  const [showDetails, setShowDetails] = useState(false);

  // Don't show if everything is synced and online
  if (pendingCount === 0 && isOnline) {
    return null;
  }

  return (
    <div style={{
      background: !isOnline 
        ? 'linear-gradient(135deg, #ff9800, #f57c00)' 
        : '#e3f2fd',
      padding: '10px 16px',
      borderRadius: '8px',
      marginBottom: '12px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '10px',
        color: !isOnline ? 'white' : '#1565c0',
      }}>
        <span style={{ fontSize: '18px' }}>
          {!isOnline ? '📵' : isProcessing ? '⏳' : '☁️'}
        </span>
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
            {!isOnline 
              ? 'Playing Offline' 
              : isProcessing 
                ? 'Syncing...' 
                : `${pendingCount} hole${pendingCount !== 1 ? 's' : ''} pending upload`}
          </div>
          <div style={{ fontSize: '12px', opacity: 0.9 }}>
            {!isOnline 
              ? 'Data saved locally, will sync when back online'
              : 'Will retry automatically'}
          </div>
        </div>
      </div>
      
      <div style={{ display: 'flex', gap: '8px' }}>
        {isOnline && pendingCount > 0 && !isProcessing && (
          <button
            onClick={forceRetry}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: 'none',
              background: 'white',
              color: '#1565c0',
              fontSize: '12px',
              fontWeight: 'bold',
              cursor: 'pointer',
            }}
          >
            Retry Now
          </button>
        )}
        <button
          onClick={() => setShowDetails(!showDetails)}
          style={{
            padding: '6px 12px',
            borderRadius: '6px',
            border: !isOnline ? '1px solid rgba(255,255,255,0.5)' : '1px solid #1565c0',
            background: 'transparent',
            color: !isOnline ? 'white' : '#1565c0',
            fontSize: '12px',
            cursor: 'pointer',
          }}
        >
          {showDetails ? 'Hide' : 'Details'}
        </button>
      </div>

      {showDetails && (
        <div style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          marginTop: '8px',
          zIndex: 100,
        }}>
          <SyncStatusPanel onClose={() => setShowDetails(false)} />
        </div>
      )}
    </div>
  );
}

export default SyncStatusBanner;
