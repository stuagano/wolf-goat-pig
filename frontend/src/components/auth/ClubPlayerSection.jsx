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
  const [message, setMessage] = useState(null);

  const isLinked = Boolean(profile?.legacy_name);
  const showSelector = !loading && (!isLinked || editing);
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
      await updateLegacyName(legacyName);
      setEditing(false);
      setMessage({ type: 'success', text: `Club player linked as ${legacyName}.` });
    } catch (error) {
      setMessage({ type: 'error', text: error.message || 'Could not link club player.' });
    }
  };

  const messageIsSuccess = message?.type === 'success';

  return (
    <div id="club-player" style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
        <div>
          <h3 style={{ ...sectionTitle, marginBottom: 4 }}>Club Player</h3>
          <p style={{ margin: 0, color: theme.colors.textSecondary, fontSize: 14 }}>
            Link your Wing Point tee-sheet name to sign up and post rounds.
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
          Linked as {profile.legacy_name}
        </div>
      )}

      {message && (
        <div style={{
          marginTop: 16,
          padding: '10px 14px',
          borderRadius: 8,
          background: messageIsSuccess ? '#ecfdf5' : '#fef2f2',
          color: messageIsSuccess ? '#166534' : '#991b1b',
        }}>
          {message.text}
        </div>
      )}

      {showSelector && (
        <LegacyNameSelector
          currentName={profile?.legacy_name}
          onSelect={handleSelect}
          suggestedName={!isLinked ? legacyNameSuggestion : null}
          allowSkip={false}
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
