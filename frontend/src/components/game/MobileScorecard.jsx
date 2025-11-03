// frontend/src/components/game/MobileScorecard.jsx
import React, { useState } from 'react';
import { useTheme } from '../../theme/Provider';
import '../../styles/mobile-touch.css';

/**
 * Mobile-optimized scorecard for game managers
 * Replaces traditional paper scorecard with easy-to-read digital version
 * Optimized for glove-friendly touch interaction on phones
 */
const MobileScorecard = ({ gameState }) => {
  const theme = useTheme();
  const [viewMode, setViewMode] = useState('standings'); // 'standings' or 'detailed'

  if (!gameState || !gameState.players) return null;

  // Calculate current standings (total quarters/points won)
  const getCurrentStandings = () => {
    return gameState.players
      .map(player => ({
        ...player,
        quarters: player.points || 0
      }))
      .sort((a, b) => b.quarters - a.quarters);
  };

  // Get hole history if available
  const getHoleHistory = () => {
    return gameState.hole_history || [];
  };

  const standings = getCurrentStandings();
  const currentHole = gameState.current_hole || 1;
  const holeHistory = getHoleHistory();

  // Render compact standings view (default for game manager)
  const renderStandingsView = () => (
    <div>
      {/* Current Hole Banner */}
      <div style={{
        background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.accent})`,
        color: 'white',
        padding: '20px',
        borderRadius: '16px 16px 0 0',
        textAlign: 'center',
        marginBottom: '2px'
      }}>
        <div style={{ fontSize: '18px', marginBottom: '8px', opacity: 0.9 }}>
          Current Hole
        </div>
        <div style={{ fontSize: '48px', fontWeight: 'bold', lineHeight: 1 }}>
          {currentHole}
        </div>
        <div style={{ fontSize: '16px', marginTop: '8px', opacity: 0.9 }}>
          Par {gameState.hole_par || 4}
        </div>
      </div>

      {/* Player Standings */}
      <div style={{
        background: theme.colors.paper,
        borderRadius: '0 0 16px 16px',
        overflow: 'hidden'
      }}>
        <div style={{
          padding: '16px 20px',
          background: theme.colors.backgroundSecondary,
          borderBottom: `3px solid ${theme.colors.border}`,
          fontSize: '18px',
          fontWeight: 'bold',
          color: theme.colors.textPrimary
        }}>
          Current Standings
        </div>

        {standings.map((player, index) => {
          const isLeader = index === 0 && player.quarters > 0;
          const isLast = index === standings.length - 1 && player.quarters < 0;

          return (
            <div
              key={player.id}
              className="touch-optimized"
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '20px',
                borderBottom: index < standings.length - 1 ? `2px solid ${theme.colors.border}` : 'none',
                background: isLeader ? 'rgba(76, 175, 80, 0.1)' :
                           isLast ? 'rgba(244, 67, 54, 0.1)' :
                           'white'
              }}
            >
              {/* Position & Name */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1 }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: isLeader ? '#4CAF50' :
                             isLast ? '#f44336' :
                             theme.colors.backgroundSecondary,
                  color: isLeader || isLast ? 'white' : theme.colors.textSecondary,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '18px',
                  fontWeight: 'bold'
                }}>
                  {index + 1}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: '22px',
                    fontWeight: 'bold',
                    color: theme.colors.textPrimary
                  }}>
                    {player.name}
                  </div>
                  <div style={{
                    fontSize: '14px',
                    color: theme.colors.textSecondary,
                    marginTop: '2px'
                  }}>
                    Handicap {player.handicap}
                  </div>
                </div>
              </div>

              {/* Quarters/Points */}
              <div style={{
                fontSize: '32px',
                fontWeight: 'bold',
                color: player.quarters > 0 ? '#4CAF50' :
                       player.quarters < 0 ? '#f44336' :
                       theme.colors.textSecondary,
                minWidth: '100px',
                textAlign: 'right'
              }}>
                {player.quarters > 0 ? '+' : ''}{player.quarters}
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Stats */}
      <div style={{
        marginTop: '16px',
        padding: '20px',
        background: theme.colors.paper,
        borderRadius: '16px',
        border: `2px solid ${theme.colors.border}`
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '16px'
        }}>
          <div>
            <div style={{
              fontSize: '14px',
              color: theme.colors.textSecondary,
              marginBottom: '4px'
            }}>
              Base Wager
            </div>
            <div style={{
              fontSize: '24px',
              fontWeight: 'bold',
              color: theme.colors.primary
            }}>
              ${gameState.base_wager || 0.25}
            </div>
          </div>
          <div>
            <div style={{
              fontSize: '14px',
              color: theme.colors.textSecondary,
              marginBottom: '4px'
            }}>
              Current Wager
            </div>
            <div style={{
              fontSize: '24px',
              fontWeight: 'bold',
              color: gameState.current_wager > gameState.base_wager ?
                theme.colors.warning : theme.colors.primary
            }}>
              ${gameState.current_wager || gameState.base_wager || 0.25}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Render detailed hole-by-hole view
  const renderDetailedView = () => {
    const holes = Array.from({ length: Math.max(currentHole, 9) }, (_, i) => i + 1);

    return (
      <div style={{
        background: theme.colors.paper,
        borderRadius: '16px',
        overflow: 'hidden'
      }}>
        <div style={{
          padding: '16px 20px',
          background: theme.colors.backgroundSecondary,
          borderBottom: `3px solid ${theme.colors.border}`,
          fontSize: '18px',
          fontWeight: 'bold',
          color: theme.colors.textPrimary
        }}>
          Hole-by-Hole Scorecard
        </div>

        <div style={{ overflowX: 'auto', padding: '16px' }}>
          <table style={{
            width: '100%',
            borderCollapse: 'collapse',
            fontSize: '16px',
            minWidth: '600px'
          }}>
            <thead>
              <tr style={{ backgroundColor: theme.colors.backgroundSecondary }}>
                <th style={{
                  padding: '12px 8px',
                  textAlign: 'left',
                  borderBottom: `2px solid ${theme.colors.border}`,
                  fontSize: '14px',
                  fontWeight: 'bold',
                  position: 'sticky',
                  left: 0,
                  background: theme.colors.backgroundSecondary,
                  zIndex: 1
                }}>
                  PLAYER
                </th>
                {holes.map(hole => (
                  <th
                    key={hole}
                    style={{
                      padding: '12px 8px',
                      textAlign: 'center',
                      borderBottom: `2px solid ${theme.colors.border}`,
                      fontSize: '14px',
                      fontWeight: hole === currentHole ? 'bold' : 'normal',
                      background: hole === currentHole ? 'rgba(255, 215, 0, 0.2)' : 'transparent',
                      color: hole === currentHole ? '#FFD700' : 'inherit'
                    }}
                  >
                    {hole}
                  </th>
                ))}
                <th style={{
                  padding: '12px 8px',
                  textAlign: 'center',
                  borderBottom: `2px solid ${theme.colors.border}`,
                  fontSize: '14px',
                  fontWeight: 'bold',
                  borderLeft: `2px solid ${theme.colors.border}`
                }}>
                  TOTAL
                </th>
              </tr>
            </thead>
            <tbody>
              {standings.map((player, idx) => {
                return (
                  <tr
                    key={player.id}
                    style={{
                      backgroundColor: idx % 2 === 0 ? 'rgba(0, 0, 0, 0.02)' : 'transparent'
                    }}
                  >
                    <td style={{
                      padding: '12px 8px',
                      fontWeight: 'bold',
                      borderBottom: `1px solid ${theme.colors.border}`,
                      position: 'sticky',
                      left: 0,
                      background: idx % 2 === 0 ? 'rgba(0, 0, 0, 0.02)' : 'white',
                      zIndex: 1,
                      fontSize: '16px'
                    }}>
                      {player.name}
                    </td>
                    {holes.map(hole => {
                      const holeData = holeHistory.find(h => h.hole === hole);
                      const playerHoleData = holeData?.points_delta?.[player.id];
                      const isCurrentHole = hole === currentHole;

                      return (
                        <td
                          key={hole}
                          style={{
                            padding: '12px 8px',
                            textAlign: 'center',
                            borderBottom: `1px solid ${theme.colors.border}`,
                            background: isCurrentHole ? 'rgba(255, 215, 0, 0.1)' : 'transparent',
                            fontWeight: playerHoleData && playerHoleData !== 0 ? 'bold' : 'normal',
                            color: playerHoleData > 0 ? '#4CAF50' :
                                   playerHoleData < 0 ? '#f44336' :
                                   theme.colors.textSecondary,
                            fontSize: '16px'
                          }}
                        >
                          {holeData ? (
                            playerHoleData && playerHoleData !== 0 ? (
                              playerHoleData > 0 ? `+${playerHoleData}` : playerHoleData
                            ) : '-'
                          ) : ''}
                        </td>
                      );
                    })}
                    <td style={{
                      padding: '12px 8px',
                      textAlign: 'center',
                      borderBottom: `1px solid ${theme.colors.border}`,
                      borderLeft: `2px solid ${theme.colors.border}`,
                      fontWeight: 'bold',
                      fontSize: '18px',
                      color: player.quarters > 0 ? '#4CAF50' :
                             player.quarters < 0 ? '#f44336' :
                             theme.colors.textSecondary
                    }}>
                      {player.quarters > 0 ? `+${player.quarters}` : player.quarters || '-'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="touch-optimized" style={{
      background: theme.colors.background,
      borderRadius: '16px',
      overflow: 'hidden'
    }}>
      {/* View Toggle Buttons */}
      <div
        className="touch-spacing-large"
        style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '16px',
        padding: '16px',
        background: theme.colors.paper,
        borderRadius: '16px'
      }}>
        <button
          onClick={() => setViewMode('standings')}
          className="touch-optimized"
          style={{
            flex: 1,
            minHeight: '60px',
            padding: '16px',
            fontSize: '18px',
            fontWeight: 'bold',
            border: viewMode === 'standings' ? `3px solid ${theme.colors.primary}` : `2px solid ${theme.colors.border}`,
            borderRadius: '12px',
            background: viewMode === 'standings' ? theme.colors.primary : 'white',
            color: viewMode === 'standings' ? 'white' : theme.colors.textPrimary,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            touchAction: 'manipulation'
          }}
        >
          📊 Standings
        </button>
        <button
          onClick={() => setViewMode('detailed')}
          className="touch-optimized"
          style={{
            flex: 1,
            minHeight: '60px',
            padding: '16px',
            fontSize: '18px',
            fontWeight: 'bold',
            border: viewMode === 'detailed' ? `3px solid ${theme.colors.primary}` : `2px solid ${theme.colors.border}`,
            borderRadius: '12px',
            background: viewMode === 'detailed' ? theme.colors.primary : 'white',
            color: viewMode === 'detailed' ? 'white' : theme.colors.textPrimary,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            touchAction: 'manipulation'
          }}
        >
          📋 Scorecard
        </button>
      </div>

      {/* Content based on view mode */}
      {viewMode === 'standings' ? renderStandingsView() : renderDetailedView()}
    </div>
  );
};

export default MobileScorecard;
