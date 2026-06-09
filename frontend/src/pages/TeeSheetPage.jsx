import React, { useState, useEffect, useCallback } from 'react';
import { useTheme } from '../theme/Provider';
import { useAuth0 } from '@auth0/auth0-react';
import { apiConfig } from '../config/api.config';

const API_URL = apiConfig.baseUrl;

function getNextSunday() {
  const d = new Date();
  const day = d.getDay();
  if (day !== 0) d.setDate(d.getDate() + (7 - day));
  return d.toISOString().slice(0, 10);
}

function formatDate(isoDate) {
  const [year, month, day] = isoDate.split('-').map(Number);
  const d = new Date(year, month - 1, day);
  return d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
}

export default function TeeSheetPage() {
  const theme = useTheme();
  const { isAuthenticated, getAccessTokenSilently } = useAuth0();

  const [date, setDate] = useState(getNextSunday);
  const [slots, setSlots] = useState([]);
  const [loadingSheet, setLoadingSheet] = useState(false);
  const [sheetError, setSheetError] = useState('');
  const [playerProfile, setPlayerProfile] = useState(null);
  const [signingUp, setSigningUp] = useState(false);
  const [signupMessage, setSignupMessage] = useState(null); // {type: 'success'|'error', text}

  const fetchSignups = useCallback(async () => {
    setLoadingSheet(true);
    setSheetError('');
    try {
      const resp = await fetch(`${API_URL}/tee-sheet?date=${date}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setSlots(data.slots || []);
    } catch (err) {
      setSheetError('Could not load sign-ups. The tee sheet may be unavailable.');
    } finally {
      setLoadingSheet(false);
    }
  }, [date]);

  useEffect(() => {
    fetchSignups();
    setSignupMessage(null);
  }, [fetchSignups]);

  useEffect(() => {
    if (!isAuthenticated) return;
    (async () => {
      try {
        const token = await getAccessTokenSilently();
        const resp = await fetch(`${API_URL}/players/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (resp.ok) setPlayerProfile(await resp.json());
      } catch {
        // non-fatal — user just won't see their name pre-filled
      }
    })();
  }, [isAuthenticated, getAccessTokenSilently]);

  const myName = playerProfile?.legacy_name || playerProfile?.name || '';
  const filledSlots = slots.filter(s => s.name);
  const isAlreadySignedUp = myName && filledSlots.some(
    s => s.name?.toLowerCase() === myName.toLowerCase()
  );

  const handleSignup = async () => {
    if (!myName) return;
    setSigningUp(true);
    setSignupMessage(null);
    try {
      const resp = await fetch(`${API_URL}/tee-sheet/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, name: myName }),
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || 'Signup failed');
      setSignupMessage({ type: 'success', text: `You're signed up as ${myName}!` });
      await fetchSignups();
    } catch (err) {
      setSignupMessage({ type: 'error', text: err.message });
    } finally {
      setSigningUp(false);
    }
  };

  const cardStyle = {
    ...theme.cardStyle,
    maxWidth: 600,
    margin: '0 auto',
    padding: 24,
  };

  const sectionLabel = {
    fontSize: 12,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: 1,
    color: theme.colors.textSecondary,
    marginBottom: 8,
  };

  return (
    <div style={{ maxWidth: 640, margin: '0 auto', padding: '20px 16px', fontFamily: theme.typography.fontFamily }}>
      {/* Header */}
      <div style={cardStyle}>
        <h1 style={{ color: theme.colors.primary, margin: '0 0 4px 0', fontSize: 26 }}>
          Tee Sheet
        </h1>
        <p style={{ color: theme.colors.textSecondary, margin: '0 0 20px 0', fontSize: 14 }}>
          See who's playing and sign yourself up
        </p>

        {/* Date picker */}
        <div style={{ marginBottom: 24 }}>
          <div style={sectionLabel}>Date</div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <input
              type="date"
              value={date}
              onChange={e => setDate(e.target.value)}
              style={{
                padding: '10px 14px',
                borderRadius: 8,
                border: `1px solid ${theme.colors.border || '#ddd'}`,
                fontSize: 15,
                fontFamily: theme.typography.fontFamily,
                background: 'white',
              }}
            />
            <button
              onClick={() => setDate(getNextSunday())}
              style={{
                padding: '10px 14px',
                borderRadius: 8,
                border: `1px solid ${theme.colors.primary}`,
                background: 'transparent',
                color: theme.colors.primary,
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              Next Sunday
            </button>
          </div>
          <div style={{ marginTop: 6, fontSize: 13, color: theme.colors.textSecondary }}>
            {formatDate(date)}
          </div>
        </div>

        {/* Sign-up list */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <div style={sectionLabel}>Who's Playing</div>
            <button
              onClick={fetchSignups}
              disabled={loadingSheet}
              style={{
                background: 'none',
                border: 'none',
                color: theme.colors.primary,
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 600,
                padding: '2px 6px',
              }}
            >
              {loadingSheet ? '...' : 'Refresh'}
            </button>
          </div>

          {sheetError ? (
            <div style={{
              padding: 12,
              background: '#fff3f3',
              border: '1px solid #fcc',
              borderRadius: 8,
              color: theme.colors.error,
              fontSize: 14,
            }}>
              {sheetError}
            </div>
          ) : loadingSheet ? (
            <div style={{ color: theme.colors.textSecondary, fontSize: 14, padding: '12px 0' }}>
              Loading sign-ups...
            </div>
          ) : filledSlots.length === 0 ? (
            <div style={{
              padding: 16,
              background: '#f8f9fa',
              borderRadius: 8,
              color: theme.colors.textSecondary,
              fontSize: 14,
              textAlign: 'center',
            }}>
              No one has signed up yet — be the first!
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {filledSlots.map((slot, i) => {
                const isMe = myName && slot.name?.toLowerCase() === myName.toLowerCase();
                return (
                  <div
                    key={slot.slot}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      padding: '10px 14px',
                      borderRadius: 8,
                      background: isMe ? '#e8f5e9' : (i % 2 === 0 ? 'white' : '#f9f9f9'),
                      border: isMe ? `1px solid ${theme.colors.success || '#4caf50'}` : '1px solid #eee',
                    }}
                  >
                    <div style={{
                      width: 28,
                      height: 28,
                      borderRadius: '50%',
                      background: isMe ? (theme.colors.success || '#4caf50') : theme.colors.primary,
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 13,
                      fontWeight: 700,
                      flexShrink: 0,
                    }}>
                      {i + 1}
                    </div>
                    <div style={{ flex: 1 }}>
                      <span style={{ fontWeight: isMe ? 700 : 500, fontSize: 15 }}>
                        {slot.name}
                      </span>
                      {isMe && (
                        <span style={{ marginLeft: 6, fontSize: 12, color: theme.colors.success || '#4caf50', fontWeight: 600 }}>
                          (you)
                        </span>
                      )}
                      {slot.notes && (
                        <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 2 }}>
                          {slot.notes}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Sign me up section */}
        <div style={{
          padding: 16,
          background: '#f0f7ff',
          borderRadius: 10,
          border: `1px solid ${theme.colors.primary}22`,
        }}>
          <div style={sectionLabel}>Sign Up</div>

          {!isAuthenticated ? (
            <p style={{ color: theme.colors.textSecondary, fontSize: 14, margin: 0 }}>
              Log in to sign yourself up for this date.
            </p>
          ) : isAlreadySignedUp ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              color: theme.colors.success || '#2e7d32',
              fontWeight: 600,
              fontSize: 15,
            }}>
              <span style={{ fontSize: 20 }}>✓</span>
              <span>You're on the tee sheet as <strong>{myName}</strong></span>
            </div>
          ) : (
            <>
              {myName && (
                <p style={{ margin: '0 0 12px 0', color: theme.colors.textSecondary, fontSize: 14 }}>
                  Signing up as <strong style={{ color: theme.colors.textPrimary }}>{myName}</strong>
                </p>
              )}
              {!myName && (
                <p style={{ margin: '0 0 12px 0', color: theme.colors.textSecondary, fontSize: 14 }}>
                  Loading your profile...
                </p>
              )}
              <button
                onClick={handleSignup}
                disabled={signingUp || !myName}
                style={{
                  ...theme.buttonStyle,
                  fontSize: 15,
                  padding: '12px 24px',
                  width: '100%',
                  background: (!myName || signingUp) ? theme.colors.textSecondary : theme.colors.primary,
                  cursor: (!myName || signingUp) ? 'not-allowed' : 'pointer',
                }}
              >
                {signingUp ? 'Signing you up...' : 'Sign Me Up'}
              </button>
            </>
          )}

          {signupMessage && (
            <div style={{
              marginTop: 12,
              padding: 10,
              borderRadius: 6,
              background: signupMessage.type === 'success' ? '#e8f5e9' : '#ffebee',
              color: signupMessage.type === 'success' ? '#2e7d32' : theme.colors.error,
              fontSize: 14,
              fontWeight: 500,
            }}>
              {signupMessage.type === 'success' ? '✓ ' : '✗ '}{signupMessage.text}
            </div>
          )}
        </div>

        {/* Legacy link */}
        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <a
            href={`https://thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi?date=${date}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ fontSize: 13, color: theme.colors.textSecondary }}
          >
            View original tee sheet →
          </a>
        </div>
      </div>
    </div>
  );
}
