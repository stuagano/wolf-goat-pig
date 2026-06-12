import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiConfig } from '../../config/api.config';
import { RoleTag, WeekCell, slugify, teamColor } from './livsow/shared';
import LivSowTransactions from './livsow/LivSowTransactions';
import GroupMeFeed from '../chat/GroupMeFeed';

const MEDAL_COLORS = {
  1: { bg: '#fbbf24', text: '#78350f', label: '🥇' },
  2: { bg: '#9ca3af', text: '#1f2937', label: '🥈' },
  3: { bg: '#d97706', text: '#fff7ed', label: '🥉' },
};

function TeamCard({ team, weeks, isExpanded, onToggle }) {
  const medal = MEDAL_COLORS[team.rank];
  const rankBg = medal ? medal.bg : '#f3f4f6';
  const rankText = medal ? medal.text : '#374151';

  return (
    <div style={{
      background: '#fff',
      border: isExpanded ? '2px solid #2563eb' : '1px solid #e5e7eb',
      borderRadius: '12px',
      overflow: 'hidden',
      marginBottom: '12px',
    }}>
      {/* Team header row */}
      <button
        onClick={onToggle}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '14px 16px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        {/* Rank badge */}
        <div style={{
          minWidth: 36, height: 36, borderRadius: '50%',
          background: rankBg, color: rankText,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '14px', fontWeight: 700,
        }}>
          {medal ? medal.label : team.rank}
        </div>

        {/* Team name — links to the franchise page */}
        <div style={{ flex: 1 }}>
          <Link
            to={`/livsow/teams/${slugify(team.name)}`}
            onClick={(e) => e.stopPropagation()}
            style={{
              fontSize: '16px', fontWeight: 700, textDecoration: 'none',
              color: teamColor(team.name).primary,
            }}
          >
            {team.name} →
          </Link>
          <div style={{ fontSize: '12px', color: '#6b7280' }}>
            {team.players.length} players · {team.players.filter(p => p.count > 0).length} active
          </div>
        </div>

        {/* Total */}
        <div style={{ textAlign: 'right' }}>
          <div style={{
            fontSize: '22px', fontWeight: 800,
            color: team.total > 0 ? '#16a34a' : team.total < 0 ? '#dc2626' : '#374151',
          }}>
            {team.total > 0 ? `+${team.total}` : team.total}
          </div>
          <div style={{ fontSize: '11px', color: '#9ca3af' }}>pts</div>
        </div>

        <span style={{ color: '#9ca3af', fontSize: '16px' }}>{isExpanded ? '▲' : '▼'}</span>
      </button>

      {/* Expanded player table */}
      {isExpanded && (
        <div style={{ borderTop: '1px solid #e5e7eb', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
            <thead>
              <tr style={{ background: '#f9fafb' }}>
                <th style={{ padding: '8px 16px', textAlign: 'left', fontWeight: 600, color: '#374151', whiteSpace: 'nowrap' }}>Player</th>
                {weeks.map(w => (
                  <th key={w} style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 600, color: '#374151', whiteSpace: 'nowrap' }}>{w}</th>
                ))}
                <th style={{ padding: '8px 16px', textAlign: 'right', fontWeight: 700, color: '#111827', whiteSpace: 'nowrap' }}>Total</th>
                <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 700, color: '#2563eb', whiteSpace: 'nowrap' }} title="Sum of player's best 2 scores — their contribution to team total">Team Pts</th>
              </tr>
            </thead>
            <tbody>
              {team.players.map((p, i) => (
                <tr key={p.name} style={{ background: i % 2 === 0 ? '#fff' : '#f9fafb' }}>
                  <td style={{ padding: '8px 16px', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontWeight: 500, color: '#111827' }}>{p.name}</span>
                      <RoleTag role={p.role} />
                    </div>
                  </td>
                  {weeks.map(w => (
                    <td key={w} style={{ padding: '8px 10px', textAlign: 'center' }}>
                      <WeekCell value={p.weeks?.[w]} />
                    </td>
                  ))}
                  <td style={{ padding: '8px 16px', textAlign: 'right', fontWeight: 700 }}>
                    <WeekCell value={p.total} />
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    {p.best_scores?.length > 0 ? (
                      <span style={{
                        fontWeight: 700,
                        color: p.team_contribution > 0 ? '#2563eb' : p.team_contribution < 0 ? '#dc2626' : '#9ca3af',
                        fontSize: '13px',
                      }}>
                        {p.team_contribution > 0 ? `+${p.team_contribution}` : p.team_contribution}
                        <span style={{ fontWeight: 400, fontSize: '11px', color: '#9ca3af', marginLeft: '4px' }}>
                          ({p.best_scores.map(s => s > 0 ? `+${s}` : s).join(', ')})
                        </span>
                      </span>
                    ) : (
                      <span style={{ color: '#d1d5db' }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const LivSowLeaderboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedTeam, setExpandedTeam] = useState(null);
  const [showFreeAgents, setShowFreeAgents] = useState(false);
  const [recentMoves, setRecentMoves] = useState([]);

  useEffect(() => {
    // Best-effort: recent transactions feed — page works without it
    fetch(`${apiConfig.baseUrl}/data/livsow/transactions?limit=10`)
      .then(r => (r.ok ? r.json() : null))
      .then(d => { if (d?.transactions) setRecentMoves(d.transactions); })
      .catch(() => {});
  }, []);

  const load = async (refresh = false) => {
    try {
      setLoading(true);
      setError(null);
      const url = `${apiConfig.baseUrl}/data/livsow/leaderboard${refresh ? '?refresh=true' : ''}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      // Default: expand the top team
      if (json.teams?.length > 0 && expandedTeam === null) {
        setExpandedTeam(json.teams[0].name);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <div style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: '#6b7280' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>⛳</div>
          Loading LivSow standings…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: 640, margin: '60px auto', padding: '0 16px', textAlign: 'center' }}>
        <div style={{ fontSize: '32px', marginBottom: '8px' }}>⚠️</div>
        <p style={{ color: '#dc2626', marginBottom: '16px' }}>Failed to load: {error}</p>
        <button
          onClick={() => load(true)}
          style={{ padding: '10px 24px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
        >
          Retry
        </button>
      </div>
    );
  }

  const { teams = [], weeks = [], free_agents = [], sheet_url } = data || {};
  const activeFA = free_agents.filter(p => p.count > 0);

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: '24px 16px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '24px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '26px', fontWeight: 800, color: '#111827' }}>⛳ LivSow</h1>
          <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#6b7280' }}>Weekly stableford · running team totals</p>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {sheet_url && (
            <a
              href={sheet_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                padding: '8px 14px', background: '#f0fdf4', border: '1px solid #bbf7d0',
                color: '#15803d', borderRadius: '8px', fontSize: '13px', fontWeight: 600,
                textDecoration: 'none',
              }}
            >
              📊 Full Sheet
            </a>
          )}
          <button
            onClick={() => load(true)}
            style={{
              padding: '8px 14px', background: '#eff6ff', border: '1px solid #bfdbfe',
              color: '#2563eb', borderRadius: '8px', fontSize: '13px', fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Scoring key */}
      <div style={{
        background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px',
        padding: '10px 14px', marginBottom: '20px', fontSize: '12px', color: '#64748b',
        display: 'flex', flexWrap: 'wrap', gap: '12px',
      }}>
        <span>🦅 Eagle +5</span>
        <span>🐦 Birdie +2</span>
        <span>⚖️ Par 0</span>
        <span>😬 Bogey −1</span>
        <span>💀 Double −3</span>
      </div>

      {/* Team standings */}
      {teams.map(team => (
        <TeamCard
          key={team.name}
          team={team}
          weeks={weeks}
          isExpanded={expandedTeam === team.name}
          onToggle={() => setExpandedTeam(expandedTeam === team.name ? null : team.name)}
        />
      ))}

      {/* Free agents */}
      {activeFA.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <button
            onClick={() => setShowFreeAgents(v => !v)}
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: '14px', fontWeight: 600, color: '#374151', padding: '4px 0',
            }}
          >
            <span>Free Agents ({activeFA.length})</span>
            <span style={{ color: '#9ca3af' }}>{showFreeAgents ? '▲' : '▼'}</span>
          </button>
          {showFreeAgents && (
            <div style={{ marginTop: '8px', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    <th style={{ padding: '8px 16px', textAlign: 'left', fontWeight: 600 }}>Player</th>
                    {weeks.map(w => (
                      <th key={w} style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 600 }}>{w}</th>
                    ))}
                    <th style={{ padding: '8px 16px', textAlign: 'right', fontWeight: 700 }}>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {activeFA.map((p, i) => (
                    <tr key={p.name} style={{ background: i % 2 === 0 ? '#fff' : '#f9fafb' }}>
                      <td style={{ padding: '8px 16px', fontWeight: 500 }}>{p.name}</td>
                      {weeks.map(w => (
                        <td key={w} style={{ padding: '8px 10px', textAlign: 'center' }}>
                          <WeekCell value={p.weeks?.[w]} />
                        </td>
                      ))}
                      <td style={{ padding: '8px 16px', textAlign: 'right', fontWeight: 700 }}>
                        <WeekCell value={p.total} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* League chat — live window into the GroupMe group */}
      <div style={{ marginTop: '24px' }}>
        <GroupMeFeed height={440} />
      </div>

      {/* Recent moves — auto-detected from roster changes */}
      {recentMoves.length > 0 && (
        <div style={{ marginTop: '24px', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '16px 20px' }}>
          <h2 style={{ margin: '0 0 14px', fontSize: '15px', fontWeight: 700, color: '#374151' }}>
            Recent Moves
          </h2>
          <LivSowTransactions transactions={recentMoves} />
        </div>
      )}
    </div>
  );
};

export default LivSowLeaderboard;
