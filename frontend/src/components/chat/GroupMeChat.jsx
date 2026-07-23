// frontend/src/components/chat/GroupMeChat.jsx
// League chat — a live window into the GroupMe group. Reads via the backend
// bridge (20s server cache, 30s client poll); posting goes through the
// GroupMe bot so web messages land in everyone's GroupMe app.

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { apiConfig } from '../../config/api.config';
import { acquireAccessToken } from '../../services/authToken';
import { Message } from './MessageParts';

const API_URL = apiConfig.baseUrl;
const POLL_MS = 30000;
const AUTH0_AUDIENCE = import.meta.env.VITE_AUTH0_AUDIENCE;
const tokenOptions = AUTH0_AUDIENCE
  ? { authorizationParams: { audience: AUTH0_AUDIENCE } }
  : undefined;

const GroupMeChat = () => {
  const { isAuthenticated, getAccessTokenSilently, loginWithRedirect } = useAuth0();
  const [messages, setMessages] = useState([]);
  const [configured, setConfigured] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState(null);
  const bottomRef = useRef(null);
  const firstLoadRef = useRef(true);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/groupme/messages?limit=60`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setConfigured(data.configured !== false);
      setMessages(data.messages || []);
      setError(data.error || null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, [load]);

  // Scroll to newest on first load and when new messages arrive
  useEffect(() => {
    if (messages.length === 0) return;
    bottomRef.current?.scrollIntoView({ behavior: firstLoadRef.current ? 'auto' : 'smooth' });
    firstLoadRef.current = false;
  }, [messages]);

  const send = async () => {
    const text = draft.trim();
    if (!text || sending) return;
    setSending(true);
    setSendError(null);
    try {
      const token = await acquireAccessToken(getAccessTokenSilently, tokenOptions);
      const res = await fetch(`${API_URL}/groupme/messages`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      setDraft('');
      // Show the message quickly — bridge busts its cache on post
      setTimeout(load, 1500);
    } catch (e) {
      setSendError(e.message);
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6b7280' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>💬</div>
          Loading league chat…
        </div>
      </div>
    );
  }

  if (!configured) {
    return (
      <div style={{ maxWidth: 560, margin: '60px auto', padding: '0 16px', textAlign: 'center' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>💬</div>
        <h2 style={{ margin: '0 0 8px', fontSize: 18, color: '#374151' }}>League chat isn't connected yet</h2>
        <p style={{ color: '#6b7280', fontSize: 14 }}>
          The GroupMe bridge needs its access token configured on the server.
        </p>
      </div>
    );
  }

  return (
    <div style={{
      maxWidth: 680, margin: '0 auto', padding: '16px',
      display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#111827' }}>💬 League Chat</h1>
        <span style={{ fontSize: 11, color: '#9ca3af' }}>live from GroupMe · refreshes every 30s</span>
      </div>

      {error && (
        <div style={{ padding: '8px 12px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 8, color: '#b45309', fontSize: 12, marginBottom: 8 }}>
          ⚠️ Trouble reaching GroupMe ({error}) — showing the latest messages we have.
        </div>
      )}

      <div style={{
        flex: 1, overflowY: 'auto', background: '#fff',
        border: '1px solid #e5e7eb', borderRadius: 14, padding: '10px 16px',
      }}>
        {messages.length === 0 ? (
          <p style={{ color: '#9ca3af', fontStyle: 'italic', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
            No messages yet.
          </p>
        ) : (
          messages.map((m) => <Message key={m.id} m={m} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* Composer */}
      <div style={{ marginTop: 10 }}>
        {isAuthenticated ? (
          <>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type="text"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') send(); }}
                placeholder="Message the group…"
                maxLength={850}
                disabled={sending}
                style={{
                  flex: 1, padding: '11px 14px', borderRadius: 10,
                  border: '1px solid #d1d5db', fontSize: 14, outline: 'none',
                }}
              />
              <button
                onClick={send}
                disabled={sending || draft.trim() === ''}
                style={{
                  padding: '11px 20px', borderRadius: 10, border: 'none',
                  background: sending || draft.trim() === '' ? '#d1d5db' : '#16a34a',
                  color: '#fff', fontWeight: 700, fontSize: 14,
                  cursor: sending || draft.trim() === '' ? 'not-allowed' : 'pointer',
                }}
              >
                {sending ? '…' : 'Send'}
              </button>
            </div>
            {sendError && (
              <div style={{ fontSize: 12, color: '#dc2626', marginTop: 6 }}>
                Couldn't send: {sendError}
              </div>
            )}
            <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 6 }}>
              Posts to the real GroupMe — everyone sees it in the app too.
            </div>
          </>
        ) : (
          <button
            onClick={() => loginWithRedirect()}
            style={{
              width: '100%', padding: '11px', borderRadius: 10,
              border: '1px solid #d1d5db', background: '#f9fafb',
              color: '#374151', fontSize: 14, cursor: 'pointer',
            }}
          >
            Log in to post to the group
          </button>
        )}
      </div>
    </div>
  );
};

export default GroupMeChat;
