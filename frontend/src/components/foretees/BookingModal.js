import React, { useState, useEffect } from 'react';
import { useTheme } from '../../theme/Provider';

const TRANSPORT_OPTIONS = [
  { value: 'WLK', label: 'Walking' },
  { value: 'CRT', label: 'Cart' },
  { value: 'PC', label: 'Push Cart' },
];

const BookingModal = ({ isOpen, onClose, onConfirm, slot, loading }) => {
  const theme = useTheme();
  const [transportMode, setTransportMode] = useState('WLK');

  useEffect(() => {
    if (isOpen) setTransportMode('WLK');
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  if (!isOpen || !slot) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.5)',
          zIndex: 2000,
        }}
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 2001,
          ...theme.cardStyle,
          padding: 24,
          minWidth: 320,
          maxWidth: 420,
          width: '90vw',
        }}
      >
        <h3 style={{ color: theme.colors.primary, margin: '0 0 16px' }}>
          Book Tee Time
        </h3>

        <div style={{ marginBottom: 16, color: theme.colors.textPrimary }}>
          <div style={{ fontSize: 20, fontWeight: 700 }}>{slot.time}</div>
          <div style={{ fontSize: 14, color: theme.colors.textSecondary }}>
            {slot.date}
          </div>
        </div>

        {slot.players && slot.players.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: theme.colors.textSecondary, marginBottom: 4 }}>
              Playing with:
            </div>
            {slot.players.map((p, i) => (
              <div key={i} style={{ fontSize: 14, color: theme.colors.textPrimary, padding: '2px 0' }}>
                {p.name}
                {p.transport && (
                  <span style={{
                    marginLeft: 8,
                    fontSize: 12,
                    color: theme.colors.textSecondary,
                    background: theme.isDark ? '#374151' : '#f3f4f6',
                    padding: '1px 6px',
                    borderRadius: 4,
                  }}>
                    {p.transport}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        <div style={{ marginBottom: 20 }}>
          <label
            style={{
              display: 'block',
              fontSize: 13,
              fontWeight: 600,
              color: theme.colors.textSecondary,
              marginBottom: 6,
            }}
          >
            Transport Mode
          </label>
          <select
            value={transportMode}
            onChange={(e) => setTransportMode(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: 8,
              border: `1px solid ${theme.colors.border || '#ccc'}`,
              background: theme.colors.surface || theme.colors.background,
              color: theme.colors.textPrimary,
              fontSize: 16,
            }}
          >
            {TRANSPORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={onClose}
            disabled={loading}
            style={{
              flex: 1,
              padding: '12px 16px',
              borderRadius: 8,
              border: `1px solid ${theme.colors.border || '#ccc'}`,
              background: 'transparent',
              color: theme.colors.textPrimary,
              fontSize: 15,
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm({ transportMode })}
            disabled={loading}
            style={{
              flex: 1,
              padding: '12px 16px',
              borderRadius: 8,
              border: 'none',
              background: loading ? '#9ca3af' : '#10b981',
              color: '#fff',
              fontSize: 15,
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Booking...' : 'Confirm Booking'}
          </button>
        </div>
      </div>
    </>
  );
};

export default BookingModal;
