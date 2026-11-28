import React, { useEffect, useState } from 'react';
import usePlayerProfile from '../../hooks/usePlayerProfile';
import LegacyNameSelector from './LegacyNameSelector';

const ClubPlayerSection = ({ cardStyle, sectionTitle, theme }) => {
  const {
    profile,
    loading,
    legacyNameSuggestion,
    updateLegacyName,
  } = usePlayerProfile();
  const [editing, setEditing] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [message, setMessage] = useState(null);

  const rosterName = profile?.legacy_name && !profile.legacy_name.includes('@')
    ? profile.legacy_name
    : null;
  const isLinked = Boolean(rosterName);
  const showSelector = !loading && (editing || (!isLinked && !dismissed));
  const showLinkedSummary = isLinked && !editing;

  useEffect(() => {
    if (window.location.hash !== '#club-player') return;
    window.setTimeout(() => {
      document.getElementById('club-player')?.scrollIntoView({ behavior: 'smooth' });
    }, 0);
  }, []);

  const handleSelect = async (legacyName) => {
    setMessage(null);
    try {
      const result = await updateLegacyName(legacyName);
      if (result?.status === 'claim_pending') {
        setMessage({ type: 'info', text: result.message });
        return;
      }
      setEditing(false);
      setMessage({ type: 'success', text: `Club player linked as ${legacyName}.` });
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'Could not link club player.' });
    }
  };

  const messageIsError = message?.type === 'error';

  return (
    <div id="club-player" style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
        <div>
          <h3 style={{ ...sectionTitle, marginBottom: 4 }}>Club Player</h3>
          <p style={{ margin: 0, color: theme.colors.textSecondary, fontSize: 14 }}>
            Optional. Sign up with your profile name. Link a tee-sheet name only to attach older rounds.
          </p>
        </div>
        {showLinkedSummary && (
          <button
            type="button"
            onClick={() => {
              setMessage(null);
              setEditing(true);
            }}
            style={{
              ...theme.buttonStyle,
              padding: '8px 14px',
              background: 'transparent',
              color: theme.colors.primary,
              border: `1px solid ${theme.colors.primary}`,
              flexShrink: 0,
            }}
          >
            Change
          </button>
        )}
      </div>

      {loading && (
        <p style={{ color: theme.colors.textSecondary, margin: '16px 0 0' }}>
          Loading club player…
        </p>
      )}

      {showLinkedSummary && (
        <div style={{
          marginTop: 16,
          padding: '12px 16px',
          borderRadius: 8,
          background: theme.isDark ? 'rgba(16, 185, 129, 0.15)' : '#ecfdf5',
          color: theme.colors.success,
          fontWeight: 600,
        }}>
          Linked as {rosterName}
        </div>
      )}

      {message && (
        <div style={{
          marginTop: 16,
          padding: '10px 14px',
          borderRadius: 8,
          background: messageIsError ? '#fef2f2' : '#ecfdf5',
          color: messageIsError ? '#991b1b' : '#166534',
        }}>
          {message.text}
        </div>
      )}

      {!loading && !isLinked && dismissed && (
        <p style={{ margin: '16px 0 0', color: theme.colors.textSecondary, fontSize: 14 }}>
          You can sign up as {profile?.name || 'yourself'}. Linking is optional.
          <button
            type="button"
            onClick={() => setDismissed(false)}
            style={{ marginLeft: 8, background: 'none', border: 'none', color: theme.colors.primary, cursor: 'pointer', padding: 0, fontWeight: 600 }}
          >
            Link club history
          </button>
        </p>
      )}

      {showSelector && (
        <LegacyNameSelector
          currentName={profile?.name || profile?.legacy_name}
          onSelect={handleSelect}
          onSkip={isLinked ? null : () => { setDismissed(true); setMessage(null); }}
          suggestedName={!isLinked ? legacyNameSuggestion : null}
          allowSkip={!isLinked}
        />
      )}

      {editing && (
        <button
          type="button"
          onClick={() => {
            setEditing(false);
            setMessage(null);
          }}
          style={{
            width: '100%',
            padding: 10,
            background: 'transparent',
            border: `1px solid ${theme.colors.border || '#d1d5db'}`,
            borderRadius: 8,
            color: theme.colors.textSecondary,
            cursor: 'pointer',
          }}
        >
          Keep current link
        </button>
      )}
    </div>
  );
};

export default ClubPlayerSection;
