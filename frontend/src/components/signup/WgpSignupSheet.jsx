import React, { useState, useEffect, useCallback } from 'react';
import { useTheme } from '../../theme/Provider';
import { useAuth0 } from '@auth0/auth0-react';
import { apiConfig } from '../../config/api.config';

const API_URL = apiConfig.baseUrl;

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

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

export default function WgpSignupSheet() {
  const theme = useTheme();
  const { isAuthenticated, getAccessTokenSilently } = useAuth0();

  const [date, setDate] = useState(getNextSunday);
  const [slots, setSlots] = useState([]);
  const [loadingSheet, setLoadingSheet] = useState(false);
  const [sheetError, setSheetError] = useState('');
  const [playerProfile, setPlayerProfile] = useState(null);
  const [signingUp, setSigningUp] = useState(false);
  const [signupMessage, setSignupMessage] = useState(null);
  const [upcomingDays, setUpcomingDays] = useState([]);
  const [loadingUpcoming, setLoadingUpcoming] = useState(true);

  useEffect(() => {
    (async () => {
      setLoadingUpcoming(true);
      try {
        const resp = await fetch(`${API_URL}/tee-sheet/upcoming?start=${todayIso()}&days=14`);
        if (resp.ok) setUpcomingDays(await resp.json());
      } catch { /* non-fatal */ } finally {
        setLoadingUpcoming(false);
      }
    })();
  }, []);

  const refreshUpcomingCount = useCallback(async (targetDate) => {
    try {
      const resp = await fetch(`${API_URL}/tee-sheet?date=${targetDate}`);
      if (!resp.ok) return;
      const data = await resp.json();
      setUpcomingDays(prev =>
        prev.map(d => d.date === targetDate ? { ...d, signed_up_count: data.signed_up_count } : d)
      );
    } catch { /* non-fatal */ }
  }, []);

  const fetchSignups = useCallback(async () => {
    setLoadingSheet(true);
    setSheetError('');
    try {
      const resp = await fetch(`${API_URL}/tee-sheet?date=${date}`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      setSlots(data.slots || []);
      setUpcomingDays(prev =>
        prev.map(d => d.date === date ? { ...d, signed_up_count: data.signed_up_count } : d)
      );
    } catch {
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
      } catch { /* non-fatal */ }
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
      await refreshUpcomingCount(date);
    } catch (err) {
      setSignupMessage({ type: 'error', text: err.message });
    } finally {
      setSigningUp(false);
    }
  };

  const pill = (day) => {
    const isSelected = day.date === date;
    const count = day.signed_up_count;
    const isSunday = day.weekday === 'Sunday';
    return (
      <button
        key={day.date}
        onClick={() => setDate(day.date)}
        style={{
          minWidth: 58,
          padding: '8px 6px',
          borderRadius: 10,
          border: isSelected
            ? `2px solid ${theme.colors.primary}`
            : `2px solid ${isSunday ? theme.colors.primary + '44' : '#e0e0e0'}`,
          background: isSelected ? theme.colors.primary : (isSunday ? theme.colors.primary + '0d' : 'white'),
          color: isSelected ? 'white' : theme.colors.textPrimary,
          cursor: 'pointer',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 3,
          flexShrink: 0,
        }}
      >
        <div style={{ fontSize: 11, fontWeight: 600, opacity: isSelected ? 0.85 : 0.6 }}>{day.short}</div>
        <div style={{ fontSize: 14, fontWeight: 700 }}>{day.label}</div>
        <div style={{
          fontSize: 12,
          fontWeight: 700,
          color: isSelected ? 'rgba(255,255,255,0.9)' : (count > 0 ? (theme.colors.success || '#2e7d32') : theme.colors.textSecondary),
        }}>
          {count < 0 ? '—' : count === 0 ? '0' : `${count} ✓`}
        </div>
      </button>
    );
  };

  return (
    <div style={{ maxWidth: 640 }}>
      {/* Day strip */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, color: theme.colors.textSecondary, marginBottom: 8 }}>
          Upcoming
        </div>
        <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 6, WebkitOverflowScrolling: 'touch' }}>
          {loadingUpcoming
            ? Array.from({ length: 7 }).map((_, i) => (
                <div key={i} style={{ minWidth: 58, height: 64, borderRadius: 10, background: '#f0f0f0', flexShrink: 0 }} />
              ))
            : upcomingDays.map(pill)
          }
        </div>
        <div style={{ marginTop: 6, fontSize: 13, color: theme.colors.textSecondary }}>{formatDate(date)}</div>
      </div>

      {/* Who's playing */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, color: theme.colors.textSecondary }}>
            Who's Playing
          </div>
          <button onClick={fetchSignups} disabled={loadingSheet} style={{ background: 'none', border: 'none', color: theme.colors.primary, cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>
            {loadingSheet ? '...' : 'Refresh'}
          </button>
        </div>

        {sheetError ? (
          <div style={{ padding: 12, background: '#fff3f3', border: '1px solid #fcc', borderRadius: 8, color: theme.colors.error, fontSize: 14 }}>
            {sheetError}
          </div>
        ) : loadingSheet ? (
          <div style={{ color: theme.colors.textSecondary, fontSize: 14, padding: '12px 0' }}>Loading sign-ups...</div>
        ) : filledSlots.length === 0 ? (
          <div style={{ padding: 16, background: '#f8f9fa', borderRadius: 8, color: theme.colors.textSecondary, fontSize: 14, textAlign: 'center' }}>
            No one has signed up yet — be the first!
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {filledSlots.map((slot, i) => {
              const isMe = myName && slot.name?.toLowerCase() === myName.toLowerCase();
              return (
                <div key={slot.slot} style={{
                  display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', borderRadius: 8,
                  background: isMe ? '#e8f5e9' : (i % 2 === 0 ? 'white' : '#f9f9f9'),
                  border: isMe ? `1px solid ${theme.colors.success || '#4caf50'}` : '1px solid #eee',
                }}>
                  <div style={{
                    width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                    background: isMe ? (theme.colors.success || '#4caf50') : theme.colors.primary,
                    color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700,
                  }}>
                    {i + 1}
                  </div>
                  <div style={{ flex: 1 }}>
                    <span style={{ fontWeight: isMe ? 700 : 500, fontSize: 15 }}>{slot.name}</span>
                    {isMe && <span style={{ marginLeft: 6, fontSize: 12, color: theme.colors.success || '#4caf50', fontWeight: 600 }}>(you)</span>}
                    {slot.notes && <div style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 2 }}>{slot.notes}</div>}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Sign me up */}
      <div style={{ padding: 16, background: '#f0f7ff', borderRadius: 10, border: `1px solid ${theme.colors.primary}22` }}>
        <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, color: theme.colors.textSecondary, marginBottom: 10 }}>
          Sign Up
        </div>
        {!isAuthenticated ? (
          <p style={{ color: theme.colors.textSecondary, fontSize: 14, margin: 0 }}>Log in to sign yourself up.</p>
        ) : isAlreadySignedUp ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: theme.colors.success || '#2e7d32', fontWeight: 600, fontSize: 15 }}>
            <span style={{ fontSize: 20 }}>✓</span>
            <span>You're on the tee sheet as <strong>{myName}</strong></span>
          </div>
        ) : (
          <>
            {myName ? (
              <p style={{ margin: '0 0 12px 0', color: theme.colors.textSecondary, fontSize: 14 }}>
                Signing up as <strong style={{ color: theme.colors.textPrimary }}>{myName}</strong>
              </p>
            ) : (
              <p style={{ margin: '0 0 12px 0', color: theme.colors.textSecondary, fontSize: 14 }}>Loading your profile...</p>
            )}
            <button
              onClick={handleSignup}
              disabled={signingUp || !myName}
              style={{
                ...theme.buttonStyle,
                fontSize: 15, padding: '12px 24px', width: '100%',
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
            marginTop: 12, padding: 10, borderRadius: 6, fontSize: 14, fontWeight: 500,
            background: signupMessage.type === 'success' ? '#e8f5e9' : '#ffebee',
            color: signupMessage.type === 'success' ? '#2e7d32' : theme.colors.error,
          }}>
            {signupMessage.type === 'success' ? '✓ ' : '✗ '}{signupMessage.text}
          </div>
        )}
      </div>

      <div style={{ marginTop: 12, textAlign: 'right' }}>
        <a
          href={`https://thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi?date=${date}`}
          target="_blank" rel="noopener noreferrer"
          style={{ fontSize: 12, color: theme.colors.textSecondary }}
        >
          View original tee sheet →
        </a>
      </div>
    </div>
  );
}
