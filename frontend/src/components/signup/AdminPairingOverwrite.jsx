import React, { useState } from 'react';
import { api } from '../../api/client';
import { errorDetail } from '../../api/http';
import { acquireAccessToken, apiTokenOptions } from '../../services/authToken';

/**
 * Admin-only control that overwrites official pairings for one signup day.
 * The generate endpoint deletes the saved pairing when force=true, then writes
 * a new random draw. Notifications stay off so a redraw does not re-email the group.
 */
const AdminPairingOverwrite = ({ date, getAccessTokenSilently, hasPairings, onOverwritten }) => {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);

  const overwrite = async () => {
    setBusy(true);
    setMessage(null);
    try {
      const token = await acquireAccessToken(getAccessTokenSilently, apiTokenOptions);
      const { data, error } = await api.POST('/pairings/{date}/generate', {
        params: {
          path: { date },
          query: { force: true, send_notifications: false },
        },
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!data) {
        throw new Error(errorDetail(error) || "Couldn't overwrite pairings");
      }
      setConfirming(false);
      setMessage(data.message || 'Pairings overwritten');
      if (onOverwritten) await onOverwritten();
    } catch (err) {
      setMessage(err.message || "Couldn't overwrite pairings");
    } finally {
      setBusy(false);
    }
  };

  const label = hasPairings ? 'Overwrite pairings' : 'Generate pairings';

  return (
    <div style={{ marginTop: '12px', textAlign: 'center' }}>
      {!confirming ? (
        <button
          type="button"
          onClick={() => {
            setMessage(null);
            setConfirming(true);
          }}
          disabled={busy}
          style={{
            background: '#166534',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 16px',
            fontSize: '14px',
            fontWeight: '700',
            cursor: busy ? 'not-allowed' : 'pointer',
          }}
        >
          {label}
        </button>
      ) : (
        <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '13px', color: '#92400e', fontWeight: '600' }}>
            {hasPairings
              ? 'Replace this day’s official pairings?'
              : 'Generate official pairings for this day?'}
          </span>
          <button
            type="button"
            onClick={overwrite}
            disabled={busy}
            style={{
              background: '#b45309',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 14px',
              fontSize: '13px',
              fontWeight: '700',
              cursor: busy ? 'not-allowed' : 'pointer',
            }}
          >
            {busy ? 'Working…' : 'Confirm overwrite'}
          </button>
          <button
            type="button"
            onClick={() => setConfirming(false)}
            disabled={busy}
            style={{
              background: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 14px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
        </div>
      )}
      {message && (
        <div style={{ marginTop: '8px', fontSize: '13px', color: '#374151' }}>{message}</div>
      )}
    </div>
  );
};

export default AdminPairingOverwrite;
