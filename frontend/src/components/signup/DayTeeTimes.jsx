import React, { useEffect, useRef, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { acquireAccessToken, apiTokenOptions } from '../../services/authToken';
import { api } from '../../api/client';

/**
 * The club's posted tee times for one day. Loaded and saved per date, so text
 * entered for one day never shows up on another. Saves when the box loses focus.
 *
 * @param {object} props
 * @param {string} props.date - YYYY-MM-DD
 */
const DayTeeTimes = ({ date }) => {
  const { isAuthenticated, getAccessTokenSilently } = useAuth0();
  const [text, setText] = useState('');
  const [savedText, setSavedText] = useState('');
  // loading | idle | saving | saved | loadError | saveError
  const [status, setStatus] = useState('loading');
  const [reloadCount, setReloadCount] = useState(0);
  // The day on screen; late save responses for a day the user already left are dropped.
  const dateRef = useRef(date);
  dateRef.current = date;
  // Only the newest load may apply, so A → B → A can't let the first A land last.
  const loadSeq = useRef(0);

  useEffect(() => {
    if (!date) return;
    const seq = ++loadSeq.current;
    setText('');
    setSavedText('');
    setStatus('loading');
    api.GET('/signups/tee-times/{date}', { params: { path: { date } } })
      .then(({ data, error }) => {
        if (seq !== loadSeq.current) return;
        if (error) {
          setStatus('loadError');
          return;
        }
        const loaded = data?.tee_times ?? '';
        setText(loaded);
        setSavedText(loaded);
        setStatus('idle');
      })
      .catch(() => {
        if (seq === loadSeq.current) setStatus('loadError');
      });
  }, [date, reloadCount]);

  // Editing is locked until the day's real text has loaded (so a blank box can't
  // overwrite it) and while a save is in flight (so saves can't land out of order).
  const locked = !isAuthenticated || ['loading', 'loadError', 'saving'].includes(status);

  const save = async () => {
    if (locked || text === savedText) return;
    // Capture the day being edited: blur fires before a click on another day.
    const editedDate = date;
    const editedText = text;
    setStatus('saving');
    try {
      const token = await acquireAccessToken(getAccessTokenSilently, apiTokenOptions);
      const { error } = await api.PUT('/signups/tee-times/{date}', {
        params: { path: { date: editedDate } },
        headers: { Authorization: `Bearer ${token}` },
        body: { tee_times: editedText },
      });
      if (dateRef.current !== editedDate) return;
      if (error) {
        setStatus('saveError');
        return;
      }
      setSavedText(editedText);
      setStatus('saved');
    } catch {
      if (dateRef.current === editedDate) setStatus('saveError');
    }
  };

  const statusText = {
    loading: 'Loading…',
    saving: 'Saving…',
    saved: 'Saved',
    loadError: 'Couldn’t load tee times.',
    saveError: 'Couldn’t save tee times. Click in the box and out again to retry.',
  }[status];
  const isError = status === 'loadError' || status === 'saveError';

  return (
    <div style={{
      background: '#f9fafb',
      borderRadius: '8px',
      border: '1px solid #e5e7eb',
      padding: '16px'
    }}>
      <h3 style={{
        margin: '0 0 12px 0',
        fontSize: '15px',
        fontWeight: '700',
        color: '#374151'
      }}>
        Tee Times
      </h3>

      <textarea
        aria-label="Tee times"
        placeholder={isAuthenticated
          ? "Enter tee times...\ne.g., 12:48 (1-4)\n12:56 (5-8)\n1:04 (9-12)"
          : 'No tee times posted yet. Sign in to add them.'}
        value={text}
        readOnly={locked}
        disabled={status === 'loading'}
        maxLength={2000}
        onChange={(e) => setText(e.target.value)}
        onBlur={save}
        style={{
          width: '100%',
          minHeight: '120px',
          padding: '10px',
          fontSize: '14px',
          border: '1px solid #d1d5db',
          borderRadius: '6px',
          resize: 'vertical',
          boxSizing: 'border-box',
          fontFamily: 'inherit'
        }}
      />
      {statusText && (
        <p
          role={isError ? 'alert' : 'status'}
          style={{ margin: '6px 0 0', fontSize: '12px', color: isError ? '#b91c1c' : '#6b7280' }}
        >
          {statusText}
          {status === 'loadError' && (
            <button
              type="button"
              onClick={() => setReloadCount((n) => n + 1)}
              style={{ marginLeft: '8px', minHeight: '32px', cursor: 'pointer' }}
            >
              Retry
            </button>
          )}
        </p>
      )}
    </div>
  );
};

export default DayTeeTimes;
