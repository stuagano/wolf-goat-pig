// frontend/src/components/game/scorekeeper/StuartModePanel.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import { apiConfig } from '../../../config/api.config';
import { generateInsights } from '../../../utils/stuartModeInsights';

const SOLO_BADGE = {
  go:      { label: 'Solo ✓', bg: '#4CAF50', color: 'white' },
  caution: { label: 'Solo ⚠',  bg: '#F59E0B', color: 'white' },
  avoid:   { label: 'Solo ✗',  bg: '#f44336', color: 'white' },
};

const StuartModePanel = ({
  players,
  currentHole,
  strokeAllocation,
  playerStandings,
  courseData,
  currentWager,
  theme,
}) => {
  const insights = generateInsights({
    players,
    currentHole,
    strokeAllocation,
    playerStandings,
    courseData,
    currentWager,
  });

  const badge = SOLO_BADGE[insights.soloRecommendation];

  // ── Whisperer state ───────────────────────────────────────────────────
  const [whispererMessages, setWhispererMessages] = useState([]);
  const [whispererOpen, setWhispererOpen] = useState(false);
  const [whispererLoading, setWhispererLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  // ── API helper ────────────────────────────────────────────────────────
  // messagesSnapshot must be passed explicitly by the caller so the API
  // receives the latest history even before a state re-render completes.
  const callCommissioner = useCallback(async (prompt, messagesSnapshot) => {
    setWhispererLoading(true);
    setWhispererOpen(true);
    try {
      const resp = await fetch(`${apiConfig.baseUrl}/api/commissioner/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: prompt,
          game_state: {
            players,
            current_hole: currentHole,
            standings: playerStandings,
            stroke_allocation: strokeAllocation,
            current_wager: currentWager,
            course_data: courseData,
            whisperer_mode: true,
            insights: {
              headline: insights.headline,
              solo_recommendation: insights.soloRecommendation,
              threats: insights.threats.map(t => ({
                name: t.player.name,
                handicap: t.player.handicap,
                threat_score: t.threatScore,
                stroke_situation: t.strokeSituation,
                hungry: t.hungry,
                quarters: t.quarters,
              })),
            },
            conversation_history: messagesSnapshot
              .slice(-10)
              .map(m => `${m.type === 'whisperer' ? 'Commissioner' : 'Stuart'}: ${m.text}`)
              .join('\n'),
          },
        }),
      });
      const json = await resp.json();
      const text = json?.data?.response || json?.detail || 'Sorry, I could not get a response.';
      setWhispererMessages(prev => [...prev, { type: 'whisperer', text, timestamp: new Date() }]);
    } catch {
      setWhispererMessages(prev => [...prev, {
        type: 'whisperer',
        text: 'Connection error — try again.',
        timestamp: new Date(),
      }]);
    } finally {
      setWhispererLoading(false);
    }
    // insights is intentionally excluded — it is a new object on every render
    // and callCommissioner only fires on hole change via the proactive useEffect.
  }, [players, currentHole, playerStandings, strokeAllocation, currentWager, courseData]);

  // ── Proactive briefing on hole change ─────────────────────────────────
  useEffect(() => {
    callCommissioner(
      `Give me a quick strategic briefing for hole ${currentHole}. Be direct and specific — focus on who I need to watch, whether to go solo, and any quarter context that matters.`,
      whispererMessages,
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentHole]);
  // whispererMessages is intentionally excluded: adding it would re-fire the briefing
  // on every message. The snapshot passed here is the history at the moment of hole
  // change, which is the correct context window for the new briefing.

  // ── Auto-scroll on new message ────────────────────────────────────────
  useEffect(() => {
    if (messagesEndRef.current?.scrollIntoView) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [whispererMessages]);

  // ── User send handler ─────────────────────────────────────────────────
  const handleSend = async () => {
    if (!inputValue.trim() || whispererLoading) return;
    const text = inputValue.trim();
    setInputValue('');
    const updatedMessages = [...whispererMessages, { type: 'user', text, timestamp: new Date() }];
    setWhispererMessages(updatedMessages);
    await callCommissioner(text, updatedMessages);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const standingsRows = [...players].sort((a, b) => {
    const qa = playerStandings?.[a.id]?.quarters ?? 0;
    const qb = playerStandings?.[b.id]?.quarters ?? 0;
    return qb - qa;
  });

  return (
    <div
      style={{
        background: theme.colors.paper,
        border: `2px solid #F59E0B`,
        borderRadius: '12px',
        marginBottom: '16px',
        overflow: 'hidden',
      }}
    >
      {/* Strategy tip section */}
      <div
        style={{
          background: 'linear-gradient(135deg, #92400E, #F59E0B)',
          color: 'white',
          padding: '12px 16px',
        }}
      >
        <div
          style={{
            fontSize: '11px',
            fontWeight: 'bold',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            opacity: 0.9,
            marginBottom: '8px',
          }}
        >
          🧠 Stuart Mode
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
          <span
            data-testid="solo-recommendation"
            style={{
              background: badge.bg,
              color: badge.color,
              padding: '4px 10px',
              borderRadius: '12px',
              fontSize: '12px',
              fontWeight: 'bold',
              whiteSpace: 'nowrap',
              flexShrink: 0,
              border: '2px solid rgba(255,255,255,0.4)',
            }}
          >
            {badge.label}
          </span>

          <div>
            <div style={{ fontSize: '15px', fontWeight: 'bold', marginBottom: '4px' }}>
              {insights.headline}
            </div>
            <div style={{ fontSize: '12px', opacity: 0.9, lineHeight: 1.4 }}>
              {insights.detail}
            </div>
          </div>
        </div>
      </div>

      {/* Standings strip */}
      <div style={{ padding: '10px 16px' }}>
        <div
          style={{
            fontSize: '10px',
            textTransform: 'uppercase',
            letterSpacing: '1px',
            color: theme.colors.textSecondary,
            marginBottom: '6px',
          }}
        >
          Quarter Standings
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {standingsRows.map(player => {
            const entry = insights.threats.find(t => t.player.id === player.id);
            const quarters = playerStandings?.[player.id]?.quarters ?? 0;
            const isStuart = player.is_authenticated;
            const isHungry = entry?.hungry;

            const qColor = quarters > 0 ? '#4CAF50' : quarters < 0 ? '#f44336' : '#9CA3AF';
            const qLabel = quarters > 0 ? `+${quarters}q` : `${quarters}q`;

            return (
              <div
                key={player.id}
                data-testid={`standing-${player.id}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '4px 8px',
                  borderRadius: '8px',
                  background: isStuart ? 'rgba(245,158,11,0.08)' : 'transparent',
                  border: isStuart ? '1px solid rgba(245,158,11,0.3)' : '1px solid transparent',
                }}
              >
                <span
                  style={{
                    fontSize: '13px',
                    fontWeight: isStuart ? 'bold' : '500',
                    color: theme.colors.textPrimary,
                  }}
                >
                  {player.name}
                  {isStuart && ' ←'}
                </span>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {isHungry && (
                    <span
                      data-testid={`hungry-${player.id}`}
                      style={{
                        fontSize: '11px',
                        color: '#f44336',
                        fontWeight: 'bold',
                      }}
                    >
                      ⚠️ hungry
                    </span>
                  )}
                  <span
                    style={{
                      fontSize: '13px',
                      fontWeight: 'bold',
                      color: qColor,
                      minWidth: '40px',
                      textAlign: 'right',
                    }}
                  >
                    {qLabel}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Whisperer: Ask Commissioner ────────────────────────────────── */}
      <div style={{ borderTop: '1px solid rgba(245,158,11,0.3)' }}>

        {/* Toggle header */}
        <button
          data-testid="whisperer-toggle"
          onClick={() => setWhispererOpen(o => !o)}
          style={{
            width: '100%',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '8px 16px',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            color: theme.colors.textPrimary,
          }}
        >
          <span style={{ fontSize: '12px', fontWeight: 'bold' }}>Ask Commissioner 🤫</span>
          <span style={{ fontSize: '11px', color: theme.colors.textSecondary }}>
            {whispererOpen ? '▲' : '▼'}
          </span>
        </button>

        {/* Message history (shown when open) */}
        {whispererOpen && (
          <div
            data-testid="whisperer-messages"
            style={{
              maxHeight: '220px',
              overflowY: 'auto',
              padding: '0 8px 4px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            {whispererMessages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: msg.type === 'user' ? 'flex-end' : 'flex-start',
                  alignItems: 'flex-start',
                  gap: '4px',
                }}
              >
                {msg.type === 'whisperer' && (
                  <span style={{ fontSize: '14px', flexShrink: 0 }}>🤫</span>
                )}
                <div
                  style={{
                    background: msg.type === 'whisperer'
                      ? 'rgba(245,158,11,0.1)'
                      : 'rgba(0,0,0,0.06)',
                    borderRadius: '8px',
                    padding: '6px 10px',
                    maxWidth: '85%',
                    fontSize: '13px',
                    lineHeight: 1.4,
                    color: theme.colors.textPrimary,
                  }}
                >
                  {msg.type === 'user' && (
                    <div style={{
                      fontSize: '10px',
                      fontWeight: 'bold',
                      marginBottom: '2px',
                      textAlign: 'right',
                      color: theme.colors.textSecondary,
                    }}>
                      You
                    </div>
                  )}
                  {msg.text}
                </div>
              </div>
            ))}

            {whispererLoading && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '4px 0',
              }}>
                <span style={{ fontSize: '14px' }}>🤫</span>
                <span style={{ fontSize: '13px', color: theme.colors.textSecondary }}>...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

        {/* Input row */}
        <div style={{
          display: 'flex',
          gap: '8px',
          padding: '8px 12px 10px',
          alignItems: 'center',
        }}>
          <input
            type="text"
            placeholder="Ask something..."
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={whispererLoading}
            style={{
              flex: 1,
              border: `1px solid rgba(245,158,11,${whispererLoading ? '0.2' : '0.5'})`,
              borderRadius: '8px',
              padding: '6px 10px',
              fontSize: '13px',
              outline: 'none',
              background: 'transparent',
              color: theme.colors.textPrimary,
              opacity: whispererLoading ? 0.5 : 1,
            }}
          />
          <button
            data-testid="whisperer-send"
            onClick={handleSend}
            disabled={whispererLoading || !inputValue.trim()}
            style={{
              background: '#F59E0B',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '6px 12px',
              fontSize: '14px',
              cursor: whispererLoading || !inputValue.trim() ? 'not-allowed' : 'pointer',
              opacity: whispererLoading || !inputValue.trim() ? 0.5 : 1,
              flexShrink: 0,
            }}
          >
            →
          </button>
        </div>

      </div>
    </div>
  );
};

StuartModePanel.propTypes = {
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    handicap: PropTypes.number.isRequired,
    is_authenticated: PropTypes.bool,
  })).isRequired,
  currentHole: PropTypes.number.isRequired,
  strokeAllocation: PropTypes.object,
  playerStandings: PropTypes.object,
  courseData: PropTypes.object,
  currentWager: PropTypes.number.isRequired,
  theme: PropTypes.object.isRequired,
};

export default StuartModePanel;
