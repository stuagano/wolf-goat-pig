// frontend/src/components/game/livsow/shared.jsx
// Shared LivSow primitives: team identity colors, slugs, and table cells.

import React from 'react';

// LIV-style team identity — fixed palette for the known franchises,
// deterministic hash fallback for anything new the organizer adds.
export const TEAM_COLORS = {
  'High Beta': { primary: '#7C3AED', accent: '#EDE9FE' }, // violet
  "Saks' Smash": { primary: '#DC2626', accent: '#FEE2E2' }, // red
  "Knudsen's Ironheads": { primary: '#374151', accent: '#F3F4F6' }, // iron gray
  'Ripper Golf Club': { primary: '#EA580C', accent: '#FFEDD5' }, // orange
  'Vice Grips': { primary: '#0891B2', accent: '#CFFAFE' }, // cyan
  "Sutorius' Aces": { primary: '#16A34A', accent: '#DCFCE7' }, // green
};

const FALLBACK_PRIMARIES = ['#2563EB', '#9333EA', '#C2410C', '#0D9488', '#BE185D', '#4D7C0F'];

export const teamColor = (name) => {
  if (TEAM_COLORS[name]) return TEAM_COLORS[name];
  let h = 0;
  for (const ch of name || '') h = (h * 31 + ch.charCodeAt(0)) % 997;
  return { primary: FALLBACK_PRIMARIES[h % FALLBACK_PRIMARIES.length], accent: '#F3F4F6' };
};

// Must match the backend's _livsow_slugify (unified_data.py)
export const slugify = (name) =>
  (name || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

export function RoleTag({ role }) {
  const styles = {
    Captain: { bg: '#dbeafe', text: '#1d4ed8' },
    Starter: { bg: '#dcfce7', text: '#15803d' },
    Alternate: { bg: '#f3f4f6', text: '#4b5563' },
  };
  const s = styles[role] || styles.Alternate;
  return (
    <span style={{
      fontSize: '10px', fontWeight: 600, padding: '1px 6px',
      borderRadius: '9999px', background: s.bg, color: s.text,
    }}>
      {role}
    </span>
  );
}

export function WeekCell({ value }) {
  if (value === null || value === undefined || value === '') {
    return <span style={{ color: '#d1d5db' }}>—</span>;
  }
  const color = value > 0 ? '#16a34a' : value < 0 ? '#dc2626' : '#6b7280';
  return <span style={{ color, fontWeight: value !== 0 ? 600 : 400 }}>{value > 0 ? `+${value}` : value}</span>;
}

// Transaction type → badge styling (baseball-reference vibe, but in color)
export const TXN_BADGES = {
  signed: { label: 'SIGNED', bg: '#dcfce7', text: '#15803d' },
  released: { label: 'RELEASED', bg: '#fee2e2', text: '#b91c1c' },
  traded: { label: 'TRADE', bg: '#dbeafe', text: '#1d4ed8' },
  role_change: { label: 'ROLE', bg: '#f3f4f6', text: '#4b5563' },
  joined: { label: 'NEW FA', bg: '#fef9c3', text: '#a16207' },
  departed: { label: 'DEPARTED', bg: '#f3f4f6', text: '#6b7280' },
  renamed: { label: 'CORRECTION', bg: '#f3f4f6', text: '#9ca3af' },
};

export function TxnBadge({ type }) {
  const b = TXN_BADGES[type] || { label: type?.toUpperCase() || '?', bg: '#f3f4f6', text: '#4b5563' };
  return (
    <span style={{
      fontSize: '10px', fontWeight: 700, letterSpacing: '0.5px',
      padding: '2px 7px', borderRadius: '4px', background: b.bg, color: b.text,
      whiteSpace: 'nowrap',
    }}>
      {b.label}
    </span>
  );
}

export const formatTxnDate = (iso) => {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return iso;
  }
};
