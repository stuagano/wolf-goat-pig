// frontend/src/components/chat/GroupMeFeed.jsx
// Embeddable GroupMe feed (e.g. on the LivSow home page): recent messages
// with "Load older" pagination back through the full group history, and a
// link to /chat for posting. Polls the head page every 60s.

import React, { useState, useEffect, useRef, useCallback } from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { apiConfig } from '../../config/api.config';
import { Message } from './MessageParts';

const API_URL = apiConfig.baseUrl;
const POLL_MS = 60000;
const PAGE_SIZE = 40;

const GroupMeFeed = ({ height = 420 }) => {
  const [messages, setMessages] = useState([]);
  const [configured, setConfigured] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [reachedStart, setReachedStart] = useState(false);
  const scrollRef = useRef(null);
  const stickToBottomRef = useRef(true);

  const mergeNewer = useCallback((incoming) => {
    setMessages((prev) => {
      const known = new Set(prev.map((m) => m.id));
      const fresh = incoming.filter((m) => !known.has(m.id));
      return fresh.length ? [...prev, ...fresh] : prev;
    });
  }, []);

  // Track emptiness without re-creating loadHead per message change
  const messagesEmptyRef = useRef(true);
  useEffect(() => {
    messagesEmptyRef.current = messages.length === 0;
  }, [messages]);

  const loadHead = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/groupme/messages?limit=${PAGE_SIZE}`);
      if (!res.ok) return;
      const data = await res.json();
      if (data.configured === false) {
        setConfigured(false);
        return;
      }
      if (messagesEmptyRef.current) {
        setMessages(data.messages || []);
      } else {
        mergeNewer(data.messages || []);
      }
    } catch {
      // transient — keep what we have
    } finally {
      setLoading(false);
    }
  }, [mergeNewer]);

  useEffect(() => {
    loadHead();
    const t = setInterval(loadHead, POLL_MS);
    return () => clearInterval(t);
  }, [loadHead]);

  // Stick to bottom when new messages arrive (unless user scrolled up)
  useEffect(() => {
    const el = scrollRef.current;
    if (el && stickToBottomRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  const onScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    stickToBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
  };

  const loadOlder = async () => {
    if (loadingOlder || messages.length === 0) return;
    setLoadingOlder(true);
    const el = scrollRef.current;
    const prevHeight = el ? el.scrollHeight : 0;
    try {
      const oldest = messages[0].id;
      const res = await fetch(
        `${API_URL}/groupme/messages?limit=${PAGE_SIZE}&before_id=${encodeURIComponent(oldest)}`,
      );
      if (!res.ok) throw new Error();
      const data = await res.json();
      const older = data.messages || [];
      if (older.length === 0) {
        setReachedStart(true);
      } else {
        stickToBottomRef.current = false;
        setMessages((prev) => {
          const known = new Set(prev.map((m) => m.id));
          return [...older.filter((m) => !known.has(m.id)), ...prev];
        });
        // keep the viewport anchored where the user was
        requestAnimationFrame(() => {
          if (el) el.scrollTop = el.scrollHeight - prevHeight;
        });
      }
    } catch {
      // leave as-is; user can retry
    } finally {
      setLoadingOlder(false);
    }
  };

  if (!configured) return null;

  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', overflow: 'hidden' }}>
      <div style={{
        padding: '12px 16px', borderBottom: '1px solid #f3f4f6',
        display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
      }}>
        <h2 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: '#374151' }}>
          💬 League Chat
        </h2>
        <Link to="/chat" style={{ fontSize: 12, color: '#2563eb', fontWeight: 600, textDecoration: 'none' }}>
          Open full chat →
        </Link>
      </div>

      <div
        ref={scrollRef}
        onScroll={onScroll}
        style={{ height, overflowY: 'auto', padding: '8px 16px' }}
      >
        {loading ? (
          <p style={{ color: '#9ca3af', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
            Loading chat…
          </p>
        ) : (
          <>
            <div style={{ textAlign: 'center', padding: '6px 0 10px' }}>
              {reachedStart ? (
                <span style={{ fontSize: 11, color: '#9ca3af' }}>— beginning of group history —</span>
              ) : (
                <button
                  onClick={loadOlder}
                  disabled={loadingOlder}
                  style={{
                    fontSize: 12, fontWeight: 600, color: '#2563eb',
                    background: '#eff6ff', border: '1px solid #bfdbfe',
                    borderRadius: 9999, padding: '4px 14px',
                    cursor: loadingOlder ? 'wait' : 'pointer',
                  }}
                >
                  {loadingOlder ? 'Loading…' : '↑ Load older messages'}
                </button>
              )}
            </div>
            {messages.map((m) => (
              <Message key={m.id} m={m} />
            ))}
          </>
        )}
      </div>
    </div>
  );
};

GroupMeFeed.propTypes = {
  height: PropTypes.number,
};

export default GroupMeFeed;
