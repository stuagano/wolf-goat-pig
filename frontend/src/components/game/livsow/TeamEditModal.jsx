// frontend/src/components/game/livsow/TeamEditModal.jsx
// Captain-only no-code editor for a team's franchise page: motto, about
// blurb, announcement, and logo URL. Auth + authorization enforced server
// side (PUT /data/livsow/teams/{slug}/content).

import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { useAuth0 } from '@auth0/auth0-react';
import { apiConfig } from '../../../config/api.config';
import { acquireAccessToken } from '../../../services/authToken';

const AUTH0_AUDIENCE = import.meta.env.VITE_AUTH0_AUDIENCE;
const tokenOptions = AUTH0_AUDIENCE
  ? { authorizationParams: { audience: AUTH0_AUDIENCE } }
  : undefined;

const fieldLabel = { fontSize: 13, fontWeight: 600, color: '#374151', marginBottom: 4, display: 'block' };
const fieldBox = {
  width: '100%', padding: '9px 11px', borderRadius: 8, border: '1px solid #d1d5db',
  fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box',
};

const TeamEditModal = ({ slug, teamName, accent, initial, onClose, onSaved }) => {
  const { getAccessTokenSilently } = useAuth0();
  const [motto, setMotto] = useState(initial.motto || '');
  const [about, setAbout] = useState(initial.about || '');
  const [announcement, setAnnouncement] = useState(initial.announcement || '');
  const [logoUrl, setLogoUrl] = useState(initial.logo_url || '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const token = await acquireAccessToken(getAccessTokenSilently, tokenOptions);
      const res = await fetch(`${apiConfig.baseUrl}/data/livsow/teams/${slug}/content`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ motto, about, announcement, logo_url: logoUrl }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      onSaved(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 2000,
        display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
        padding: '24px 16px', overflowY: 'auto',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: '#fff', borderRadius: 16, maxWidth: 520, width: '100%',
          padding: 24, marginTop: 24,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800, color: accent }}>
            Edit {teamName}
          </h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', color: '#9ca3af' }}>
            ×
          </button>
        </div>
        <p style={{ margin: '0 0 18px', fontSize: 12, color: '#9ca3af' }}>
          You're the captain — this is your team's page. Changes show for everyone.
        </p>

        <label style={fieldLabel}>Team motto / tagline</label>
        <input
          style={{ ...fieldBox, marginBottom: 14 }}
          value={motto}
          onChange={(e) => setMotto(e.target.value)}
          maxLength={120}
          placeholder="e.g. Fear the Beta"
        />

        <label style={fieldLabel}>About the team</label>
        <textarea
          style={{ ...fieldBox, marginBottom: 14, resize: 'vertical', minHeight: 80 }}
          value={about}
          onChange={(e) => setAbout(e.target.value)}
          maxLength={2000}
          rows={4}
          placeholder="A paragraph or two about your squad…"
        />

        <label style={fieldLabel}>Captain's announcement <span style={{ fontWeight: 400, color: '#9ca3af' }}>(pinned banner; clear to remove)</span></label>
        <input
          style={{ ...fieldBox, marginBottom: 14 }}
          value={announcement}
          onChange={(e) => setAnnouncement(e.target.value)}
          maxLength={500}
          placeholder="e.g. Tee time moved to 8am Sunday"
        />

        <label style={fieldLabel}>Team logo URL <span style={{ fontWeight: 400, color: '#9ca3af' }}>(paste an image link)</span></label>
        <input
          style={fieldBox}
          value={logoUrl}
          onChange={(e) => setLogoUrl(e.target.value)}
          maxLength={600}
          placeholder="https://…/logo.png"
        />
        {logoUrl && (
          <img
            src={logoUrl}
            alt="logo preview"
            style={{ marginTop: 8, maxHeight: 64, borderRadius: 8, display: 'block' }}
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        )}

        {error && (
          <div style={{ marginTop: 14, fontSize: 13, color: '#dc2626' }}>Couldn't save: {error}</div>
        )}

        <div style={{ display: 'flex', gap: 10, marginTop: 22, justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{ padding: '9px 18px', borderRadius: 8, border: '1px solid #d1d5db', background: '#fff', cursor: 'pointer', fontSize: 14 }}
          >
            Cancel
          </button>
          <button
            onClick={save}
            disabled={saving}
            style={{
              padding: '9px 20px', borderRadius: 8, border: 'none', fontSize: 14, fontWeight: 700,
              background: saving ? '#d1d5db' : accent, color: '#fff',
              cursor: saving ? 'wait' : 'pointer',
            }}
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
};

TeamEditModal.propTypes = {
  slug: PropTypes.string.isRequired,
  teamName: PropTypes.string.isRequired,
  accent: PropTypes.string.isRequired,
  initial: PropTypes.object.isRequired,
  onClose: PropTypes.func.isRequired,
  onSaved: PropTypes.func.isRequired,
};

export default TeamEditModal;
