// frontend/src/components/chat/MessageParts.jsx
// Shared GroupMe message rendering — used by the full /chat page and the
// embedded feed on the LivSow home page.

import React from 'react';

export const timeLabel = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  return sameDay
    ? d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    : d.toLocaleDateString([], { month: 'short', day: 'numeric' }) +
        ' ' +
        d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
};

export function Message({ m }) {
  if (m.is_system) {
    return (
      <div style={{ textAlign: 'center', fontSize: 12, color: '#9ca3af', padding: '4px 0' }}>
        {m.text}
      </div>
    );
  }
  return (
    <div style={{ display: 'flex', gap: 10, padding: '6px 0', alignItems: 'flex-start' }}>
      {m.avatar_url ? (
        <img
          src={`${m.avatar_url}.avatar`}
          alt=""
          style={{ width: 34, height: 34, borderRadius: '50%', flexShrink: 0, objectFit: 'cover' }}
        />
      ) : (
        <div style={{
          width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
          background: '#e0e7ff', color: '#4338ca', display: 'flex',
          alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 14,
        }}>
          {(m.name || '?').charAt(0).toUpperCase()}
        </div>
      )}
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'baseline', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 600, fontSize: 13, color: '#111827' }}>{m.name}</span>
          <span style={{ fontSize: 11, color: '#9ca3af' }}>{timeLabel(m.created_at)}</span>
          {m.likes > 0 && (
            <span style={{ fontSize: 11, color: '#dc2626' }}>♥ {m.likes}</span>
          )}
        </div>
        {m.text && (
          <div style={{ fontSize: 14, color: '#374151', lineHeight: 1.45, wordBreak: 'break-word' }}>
            {m.text}
          </div>
        )}
        {m.images?.map((url) => (
          <img
            key={url}
            src={url}
            alt="shared"
            style={{ maxWidth: 260, maxHeight: 260, borderRadius: 10, marginTop: 6, display: 'block' }}
          />
        ))}
      </div>
    </div>
  );
}
