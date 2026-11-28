import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTheme } from '../theme/Provider';
import { apiConfig } from '../config/api.config';

const API_URL = apiConfig.baseUrl;

function formatSignupDate(isoDate) {
  const [year, month, day] = String(isoDate || '').split('-').map(Number);
  if (!year || !month || !day) return isoDate || '';
  return new Date(year, month - 1, day).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function errorMessage(body, fallback) {
  if (typeof body?.detail === 'string' && body.detail) return body.detail;
  return fallback;
}

function CancelSignupPage() {
  const { token } = useParams();
  const theme = useTheme();
  const [view, setView] = useState({ phase: 'loading' });

  useEffect(() => {
    let ignore = false;
    fetch(`${API_URL}/signups/cancel/${encodeURIComponent(token)}`, { method: 'GET' })
      .then(async (response) => {
        const body = await response.json().catch(() => ({}));
        if (ignore) return;
        if (!response.ok) {
          setView({
            phase: 'error',
            message: errorMessage(body, 'This cancel link is not valid.'),
          });
          return;
        }
        setView({ phase: 'ready', signup: body });
      })
      .catch(() => {
        if (!ignore) {
          setView({ phase: 'error', message: 'Could not reach Wolf Goat Pig. Try the link again.' });
        }
      });
    return () => {
      ignore = true;
    };
  }, [token]);

  const confirmCancel = async () => {
    setView((current) => ({ ...current, phase: 'submitting' }));
    try {
      const response = await fetch(`${API_URL}/signups/cancel/${encodeURIComponent(token)}`, {
        method: 'POST',
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        setView({ phase: 'error', message: errorMessage(body, 'Could not cancel this signup.') });
        return;
      }
      setView({ phase: 'done', result: body });
    } catch {
      setView({ phase: 'error', message: 'Could not reach Wolf Goat Pig. Try the link again.' });
    }
  };

  const card = {
    ...(theme.cardStyle || {}),
    maxWidth: 480,
    margin: '48px auto',
    padding: 32,
    background: theme.colors?.paper || theme.colors?.background || '#fff',
    color: theme.colors?.textPrimary,
  };

  if (view.phase === 'loading') {
    return <main style={card}><p>Checking your signup…</p></main>;
  }

  if (view.phase === 'error') {
    return (
      <main style={card}>
        <h1 style={{ color: theme.colors?.textPrimary }}>Can't make it?</h1>
        <p role="alert">{view.message}</p>
      </main>
    );
  }

  if (view.phase === 'done') {
    const when = formatSignupDate(view.result.date);
    return (
      <main style={card}>
        <h1 style={{ color: theme.colors?.textPrimary }}>Signup cancelled</h1>
        <p>You're off the sheet for Wolf Goat Pig on {when}.</p>
        {view.result.legacy_sync === 'failed' && (
          <p role="alert">
            Removed in the app, but the live tee sheet was not updated. Tell the sheet owner.
          </p>
        )}
      </main>
    );
  }

  const signup = view.signup;
  const when = formatSignupDate(signup.date);
  if (!signup.can_cancel) {
    const message = signup.status === 'cancelled'
      ? 'This signup is already cancelled.'
      : 'This signup can no longer be cancelled.';
    return (
      <main style={card}>
        <h1 style={{ color: theme.colors?.textPrimary }}>Can't make it?</h1>
        <p>{message}</p>
        <p>{signup.player_name} · {when}</p>
      </main>
    );
  }

  return (
    <main style={card}>
      <h1 style={{ color: theme.colors?.textPrimary }}>Can't make it?</h1>
      <p>
        {signup.player_name}, this will take you off Wolf Goat Pig on {when}.
      </p>
      <button
        type="button"
        style={theme.buttonStyle}
        disabled={view.phase === 'submitting'}
        onClick={confirmCancel}
      >
        {view.phase === 'submitting' ? 'Cancelling…' : 'Cancel my signup'}
      </button>
    </main>
  );
}

export default CancelSignupPage;
