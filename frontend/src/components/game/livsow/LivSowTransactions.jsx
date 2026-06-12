// frontend/src/components/game/livsow/LivSowTransactions.jsx
// Baseball-reference-style transaction log. Rows sharing a snapshot_id are
// grouped under one dateline (so both halves of a swap read as one trade).

import React from 'react';
import PropTypes from 'prop-types';
import { TxnBadge, formatTxnDate } from './shared';

const LivSowTransactions = ({ transactions, emptyText }) => {
  if (!transactions || transactions.length === 0) {
    return (
      <p style={{ margin: 0, color: '#9ca3af', fontStyle: 'italic', fontSize: 13 }}>
        {emptyText || 'No transactions yet — moves appear here automatically when rosters change.'}
      </p>
    );
  }

  // Group consecutive rows by snapshot_id (API is newest-first)
  const groups = [];
  for (const t of transactions) {
    const last = groups[groups.length - 1];
    if (last && last.snapshotId === t.snapshot_id) {
      last.rows.push(t);
    } else {
      groups.push({ snapshotId: t.snapshot_id, date: t.detected_at, week: t.week, rows: [t] });
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {groups.map((g) => (
        <div key={`${g.snapshotId}-${g.date}`}>
          <div style={{
            fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px',
            color: '#6b7280', marginBottom: 6, display: 'flex', gap: 8, alignItems: 'baseline',
          }}>
            {formatTxnDate(g.date)}
            {g.week && <span style={{ fontWeight: 400, color: '#9ca3af' }}>week of {g.week}</span>}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {g.rows.map((t) => (
              <div key={t.id} style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: '8px 12px', background: '#f9fafb', borderRadius: 8,
              }}>
                <TxnBadge type={t.type} />
                <span style={{ fontSize: 13, color: '#374151', lineHeight: 1.45 }}>
                  {t.description}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

LivSowTransactions.propTypes = {
  transactions: PropTypes.array,
  emptyText: PropTypes.string,
};

export default LivSowTransactions;
