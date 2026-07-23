import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { useAccessToken } from '../../hooks/useAccessToken';
import { apiConfig } from '../../config/api.config';

const API_URL = apiConfig.baseUrl;
const POLL_INTERVAL_MS = 60_000;

const MATCH_TYPES = new Set(['match_found', 'match_accepted', 'match_declined', 'match_confirmed']);

const relativeTime = (isoStr) => {
  if (!isoStr) return '';
  const diff = Date.now() - new Date(isoStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
};

const NotificationBell = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth0();
  const { getToken } = useAccessToken();
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);

  const fetchNotifications = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const token = await getToken();
      const res = await fetch(`${API_URL}/notifications?unread_only=true&limit=10`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setNotifications(data.filter(n => MATCH_TYPES.has(n.notification_type)));
      }
    } catch {
      // silent — bell is non-critical
    }
  }, [isAuthenticated, getToken]);

  useEffect(() => {
    fetchNotifications();
    const id = setInterval(fetchNotifications, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchNotifications]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const markAllRead = useCallback(async () => {
    try {
      const token = await getToken();
      await fetch(`${API_URL}/notifications/read-all`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotifications([]);
    } catch {
      // silent
    }
  }, [getToken]);

  const handleNotificationClick = useCallback(async (n) => {
    try {
      const token = await getToken();
      await fetch(`${API_URL}/notifications/${n.id}/read`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      // silent
    }
    setNotifications(prev => prev.filter(x => x.id !== n.id));
    setOpen(false);
    navigate('/account');
  }, [getToken, navigate]);

  if (!isAuthenticated || notifications.length === 0) return null;

  return (
    <div ref={dropdownRef} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          background: 'transparent',
          border: '2px solid rgba(255,255,255,0.5)',
          borderRadius: 8,
          padding: '6px 10px',
          cursor: 'pointer',
          color: '#fff',
          fontSize: 18,
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
        }}
        aria-label={`${notifications.length} unread match notification${notifications.length !== 1 ? 's' : ''}`}
      >
        🔔
        <span style={{
          position: 'absolute',
          top: -4,
          right: -4,
          background: '#ef4444',
          color: '#fff',
          fontSize: 11,
          fontWeight: 700,
          borderRadius: '50%',
          width: 18,
          height: 18,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          lineHeight: 1,
        }}>
          {notifications.length > 9 ? '9+' : notifications.length}
        </span>
      </button>

      {open && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 8px)',
          right: 0,
          width: 300,
          background: '#fff',
          borderRadius: 12,
          boxShadow: '0 4px 24px rgba(0,0,0,0.18)',
          zIndex: 2000,
          overflow: 'hidden',
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 16px',
            borderBottom: '1px solid #e5e7eb',
          }}>
            <span style={{ fontWeight: 700, fontSize: 14, color: '#1f2937' }}>
              Match Notifications
            </span>
            <button
              onClick={markAllRead}
              style={{
                background: 'none',
                border: 'none',
                fontSize: 12,
                color: '#6b7280',
                cursor: 'pointer',
                padding: '2px 6px',
              }}
            >
              Mark all read
            </button>
          </div>

          <div style={{ maxHeight: 320, overflowY: 'auto' }}>
            {notifications.map(n => (
              <button
                key={n.id}
                onClick={() => handleNotificationClick(n)}
                style={{
                  display: 'block',
                  width: '100%',
                  textAlign: 'left',
                  padding: '12px 16px',
                  background: 'none',
                  border: 'none',
                  borderBottom: '1px solid #f3f4f6',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <span style={{ fontSize: 20, flexShrink: 0 }}>
                    {n.notification_type === 'match_found' ? '⛳' :
                     n.notification_type === 'match_confirmed' ? '✅' :
                     n.notification_type === 'match_accepted' ? '👍' : '📬'}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, color: '#1f2937', lineHeight: 1.4 }}>
                      {n.message}
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>
                      {relativeTime(n.created_at)} · tap to view in Account
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
