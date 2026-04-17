// frontend/src/components/game/scorekeeper/StuartModePanel.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { generateInsights } from '../../../utils/stuartModeInsights';

const SOLO_BADGE = {
  go:      { label: 'Solo ✓', bg: '#4CAF50', color: 'white' },
  caution: { label: 'Solo ⚠',  bg: '#FF9800', color: 'white' },
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
