// frontend/src/components/game/livsow/LivSowTeamPage.jsx
// LIV-Golf-style team profile: identity hero, full roster with weekly
// stats, and the team's transaction history.

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { apiConfig } from '../../../config/api.config';
import { acquireAccessToken } from '../../../services/authToken';
import { teamColor, RoleTag, WeekCell } from './shared';
import LivSowTransactions from './LivSowTransactions';
import TeamEditModal from './TeamEditModal';

const AUTH0_AUDIENCE = import.meta.env.VITE_AUTH0_AUDIENCE;
const tokenOptions = AUTH0_AUDIENCE
  ? { authorizationParams: { audience: AUTH0_AUDIENCE } }
  : undefined;

const ROLE_ORDER = { Captain: 0, Starter: 1, Alternate: 2 };

const LivSowTeamPage = () => {
  const { teamSlug } = useParams();
  const { isAuthenticated, getAccessTokenSilently } = useAuth0();
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [canEdit, setCanEdit] = useState(false);
  const [editing, setEditing] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${apiConfig.baseUrl}/data/livsow/teams/${teamSlug}`);
      if (res.status === 404) throw new Error('Team not found');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setTeam(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [teamSlug]);

  useEffect(() => { load(); }, [load]);

  // Ask the server whether the logged-in user may edit this team (captain
  // or admin). Authoritative check is on the PUT; this just gates the UI.
  useEffect(() => {
    if (!isAuthenticated) { setCanEdit(false); return; }
    let cancelled = false;
    (async () => {
      try {
        const token = await acquireAccessToken(getAccessTokenSilently, tokenOptions);
        const res = await fetch(`${apiConfig.baseUrl}/data/livsow/teams/${teamSlug}/can-edit`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok && !cancelled) setCanEdit((await res.json()).can_edit === true);
      } catch { /* not editable */ }
    })();
    return () => { cancelled = true; };
  }, [teamSlug, isAuthenticated, getAccessTokenSilently]);

  if (loading) {
    return (
      <div style={{ minHeight: '60vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6b7280' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 8 }}>⛳</div>
          Loading team…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: 640, margin: '60px auto', padding: '0 16px', textAlign: 'center' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>🏌️</div>
        <p style={{ color: '#dc2626', marginBottom: 16 }}>{error}</p>
        <Link to="/livsow" style={{ color: '#2563eb', fontWeight: 600, textDecoration: 'none' }}>
          ← Back to LivSow standings
        </Link>
      </div>
    );
  }

  const colors = teamColor(team.name);
  const players = [...(team.players || [])].sort(
    (a, b) => (ROLE_ORDER[a.role] ?? 9) - (ROLE_ORDER[b.role] ?? 9) || a.name.localeCompare(b.name),
  );
  const weeks = team.weeks || [];
  const active = players.filter((p) => p.count > 0).length;
  const content = team.content || {};

  return (
    <div style={{ maxWidth: 760, margin: '0 auto', padding: '24px 16px' }}>
      <Link to="/livsow" style={{ fontSize: 13, color: '#6b7280', textDecoration: 'none' }}>
        ← LivSow standings
      </Link>

      {/* Identity hero */}
      <div style={{
        marginTop: 12, borderRadius: 16, overflow: 'hidden',
        border: '1px solid #e5e7eb', background: '#fff', marginBottom: 20,
      }}>
        <div style={{
          background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.primary}cc 100%)`,
          padding: '28px 24px', color: '#fff',
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            {content.logo_url && (
              <img
                src={content.logo_url}
                alt=""
                style={{ width: 56, height: 56, borderRadius: 12, objectFit: 'cover', background: 'rgba(255,255,255,0.2)' }}
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            )}
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: '2px', opacity: 0.85, textTransform: 'uppercase' }}>
                LivSow Franchise
              </div>
              <h1 style={{ margin: '4px 0 0', fontSize: 30, fontWeight: 800, lineHeight: 1.1 }}>
                {team.name}
              </h1>
              {content.motto && (
                <div style={{ marginTop: 4, fontSize: 14, fontStyle: 'italic', opacity: 0.92 }}>
                  "{content.motto}"
                </div>
              )}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 22, textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: 26, fontWeight: 800 }}>#{team.rank ?? '—'}</div>
              <div style={{ fontSize: 11, opacity: 0.85 }}>RANK</div>
            </div>
            <div>
              <div style={{ fontSize: 26, fontWeight: 800 }}>
                {team.total > 0 ? `+${team.total}` : team.total}
              </div>
              <div style={{ fontSize: 11, opacity: 0.85 }}>POINTS</div>
            </div>
            <div>
              <div style={{ fontSize: 26, fontWeight: 800 }}>{active}/{players.length}</div>
              <div style={{ fontSize: 11, opacity: 0.85 }}>ACTIVE</div>
            </div>
          </div>
        </div>
      </div>

      {/* Captain edit affordance */}
      {canEdit && (
        <div style={{ marginBottom: 16, textAlign: 'right' }}>
          <button
            onClick={() => setEditing(true)}
            style={{
              padding: '8px 16px', borderRadius: 8, border: `1px solid ${colors.primary}`,
              background: '#fff', color: colors.primary, fontWeight: 700, fontSize: 13, cursor: 'pointer',
            }}
          >
            ✏️ Edit team page
          </button>
        </div>
      )}

      {/* Captain's announcement (pinned) */}
      {content.announcement && (
        <div style={{
          marginBottom: 16, padding: '12px 16px', borderRadius: 12,
          background: colors.accent, border: `1px solid ${colors.primary}33`,
          display: 'flex', gap: 10, alignItems: 'flex-start',
        }}>
          <span style={{ fontSize: 16 }}>📣</span>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: colors.primary, marginBottom: 2 }}>
              Captain's Note
            </div>
            <div style={{ fontSize: 14, color: '#374151', lineHeight: 1.45 }}>{content.announcement}</div>
          </div>
        </div>
      )}

      {/* About the team */}
      {content.about && (
        <div style={{ marginBottom: 20, background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
          <h2 style={{ margin: '0 0 10px', fontSize: 15, fontWeight: 700, color: '#374151' }}>About</h2>
          <p style={{ margin: 0, fontSize: 14, color: '#374151', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
            {content.about}
          </p>
        </div>
      )}

      {/* Roster */}
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, overflow: 'hidden', marginBottom: 20 }}>
        <div style={{ padding: '14px 16px', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#374151' }}>Roster</h2>
          {team.sheet_url && (
            <a href={team.sheet_url} target="_blank" rel="noopener noreferrer"
              style={{ fontSize: 12, color: '#15803d', fontWeight: 600, textDecoration: 'none' }}>
              📊 Full Sheet
            </a>
          )}
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: colors.accent }}>
                <th style={{ padding: '8px 16px', textAlign: 'left', fontWeight: 600, color: '#374151', whiteSpace: 'nowrap' }}>Player</th>
                {weeks.map((w) => (
                  <th key={w} style={{ padding: '8px 10px', textAlign: 'center', fontWeight: 600, color: '#374151', whiteSpace: 'nowrap' }}>{w}</th>
                ))}
                <th style={{ padding: '8px 16px', textAlign: 'right', fontWeight: 700, color: '#111827', whiteSpace: 'nowrap' }}>Total</th>
                <th style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 700, color: colors.primary, whiteSpace: 'nowrap' }}
                  title="Sum of player's best 2 scores — their contribution to the team total">
                  Team Pts
                </th>
              </tr>
            </thead>
            <tbody>
              {players.map((p, i) => (
                <tr key={p.name} style={{ background: i % 2 === 0 ? '#fff' : '#f9fafb' }}>
                  <td style={{ padding: '8px 16px', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {p.profile_id ? (
                        <Link
                          to={`/players/${p.profile_id}`}
                          style={{ fontWeight: 600, color: colors.primary, textDecoration: 'none' }}
                        >
                          {p.name}
                        </Link>
                      ) : (
                        <span style={{ fontWeight: 500, color: '#111827' }}>{p.name}</span>
                      )}
                      <RoleTag role={p.role} />
                    </div>
                  </td>
                  {weeks.map((w) => (
                    <td key={w} style={{ padding: '8px 10px', textAlign: 'center' }}>
                      <WeekCell value={p.weeks?.[w]} />
                    </td>
                  ))}
                  <td style={{ padding: '8px 16px', textAlign: 'right', fontWeight: 700 }}>
                    <WeekCell value={p.total} />
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                    {p.best_scores?.length > 0 ? (
                      <span style={{ fontWeight: 700, color: colors.primary, fontSize: 13 }}>
                        {p.team_contribution > 0 ? `+${p.team_contribution}` : p.team_contribution}
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
      </div>

      {/* Transactions */}
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
        <h2 style={{ margin: '0 0 14px', fontSize: 15, fontWeight: 700, color: '#374151' }}>
          Transactions
          {team.transactions?.length > 0 && (
            <span style={{ fontWeight: 400, color: '#9ca3af', fontSize: 13 }}> ({team.transactions.length})</span>
          )}
        </h2>
        <LivSowTransactions
          transactions={team.transactions}
          emptyText="No moves yet — signings, releases, and trades will appear here automatically."
        />
      </div>

      {editing && (
        <TeamEditModal
          slug={teamSlug}
          teamName={team.name}
          accent={colors.primary}
          initial={content}
          onClose={() => setEditing(false)}
          onSaved={(updated) => {
            setTeam((t) => ({ ...t, content: updated }));
            setEditing(false);
          }}
        />
      )}
    </div>
  );
};

export default LivSowTeamPage;
