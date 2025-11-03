// frontend/src/components/game/LargeScoringButtons.jsx
import React, { useState } from 'react';
import { useTheme } from '../../theme/Provider';
import '../../styles/mobile-touch.css';

const LargeScoringButtons = ({
  gameState,
  onScoreSubmit,
  onAction,
  loading = false
}) => {
  const theme = useTheme();
  const [scores, setScores] = useState({});
  const [showScoreEntry, setShowScoreEntry] = useState(true);
  const [pressedButton, setPressedButton] = useState(null); // Track which button is pressed

  const updateScore = (playerId, value) => {
    setScores(prev => ({ ...prev, [playerId]: value }));
  };

  const canCalculate = () => {
    if (!gameState?.players) return false;
    if (!["partners", "solo"].includes(gameState.teams?.type)) return false;

    // Check all players have scores
    return gameState.players.every(p => scores[p.id] !== undefined && scores[p.id] !== null);
  };

  const handleCalculatePoints = async () => {
    if (onScoreSubmit) {
      await onScoreSubmit(scores);
      setScores({});
      setShowScoreEntry(false);
    }
  };

  const renderLargeButton = (key, icon, label, onClick, variant = 'primary', disabled = false) => {
    const buttonId = `large-btn-${key}`;
    const isPressed = pressedButton === buttonId;

    const getButtonColor = () => {
      if (disabled) return theme.colors.textSecondary;
      switch (variant) {
        case 'success': return '#388e3c';
        case 'warning': return '#f57c00';
        case 'error': return '#d32f2f';
        default: return theme.colors.primary;
      }
    };

    return (
      <button
        key={key}
        onClick={onClick}
        disabled={disabled || loading}
        className="touch-optimized"
        style={{
          minHeight: '100px', // Increased from 80px for glove use
          fontSize: '22px', // Increased from 18px for better visibility
          fontWeight: 'bold',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '10px', // Increased from 8px
          padding: '20px', // Increased from 16px
          border: 'none',
          borderRadius: '16px', // Increased from 12px
          background: disabled ? '#e0e0e0' : getButtonColor(),
          color: disabled ? '#9e9e9e' : 'white',
          cursor: disabled ? 'not-allowed' : 'pointer',
          boxShadow: disabled ? 'none' : isPressed ? '0 2px 6px rgba(0,0,0,0.2)' : '0 4px 12px rgba(0,0,0,0.15)',
          transition: 'all 0.15s ease',
          width: '100%',
          opacity: disabled ? 0.6 : 1,
          transform: loading ? 'scale(0.98)' : isPressed ? 'scale(0.96)' : 'scale(1)',
          touchAction: 'manipulation' // Prevent double-tap zoom
        }}
        onTouchStart={(e) => {
          if (!disabled && !loading) {
            setPressedButton(buttonId);
          }
        }}
        onTouchEnd={(e) => {
          if (!disabled && !loading) {
            setPressedButton(null);
          }
        }}
        onTouchCancel={(e) => {
          if (!disabled && !loading) {
            setPressedButton(null);
          }
        }}
        onMouseDown={(e) => {
          if (!disabled && !loading) {
            setPressedButton(buttonId);
          }
        }}
        onMouseUp={(e) => {
          if (!disabled && !loading) {
            setPressedButton(null);
          }
        }}
        onMouseLeave={(e) => {
          if (!disabled && !loading) {
            setPressedButton(null);
          }
        }}
      >
        <span style={{ fontSize: '32px' }} className="outdoor-visibility-light">{icon}</span>
        <span style={{ fontSize: '18px', textAlign: 'center' }} className="outdoor-visibility-light">{label}</span>
      </button>
    );
  };

  // Score selection buttons for a player
  const renderScoreSelector = (player) => {
    const playerScore = scores[player.id];
    const holePar = gameState.hole_par || 4;
    const commonScores = [holePar - 2, holePar - 1, holePar, holePar + 1, holePar + 2];

    return (
      <div key={player.id}
           className="touch-optimized"
           style={{
        background: theme.colors.paper,
        borderRadius: '16px',
        padding: '20px', // Increased from 16px
        marginBottom: '20px', // Increased from 16px
        border: `3px solid ${playerScore !== undefined ? theme.colors.success : theme.colors.border}` // Thicker border
      }}>
        <h3 style={{
          margin: '0 0 16px 0', // Increased spacing
          fontSize: '24px', // Increased from 20px
          color: theme.colors.primary,
          fontWeight: 'bold'
        }}>
          {player.name}
          <span style={{
            fontSize: '16px', // Increased from 14px
            color: theme.colors.textSecondary,
            fontWeight: 'normal',
            marginLeft: '10px'
          }}>
            (Hdcp {player.handicap})
          </span>
        </h3>

        <div
          className="score-grid-mobile"
          style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          gap: '12px', // Increased from 8px for easier glove tapping
          marginBottom: '12px'
        }}>
          {commonScores.map(score => {
            const diff = score - holePar;
            const getScoreLabel = () => {
              if (diff <= -3) return 'Albatross';
              if (diff === -2) return 'Eagle';
              if (diff === -1) return 'Birdie';
              if (diff === 0) return 'Par';
              if (diff === 1) return 'Bogey';
              if (diff === 2) return 'Double';
              return `+${diff}`;
            };

            const getScoreColor = () => {
              if (diff <= -2) return '#2e7d32'; // Eagle - green
              if (diff === -1) return '#1976d2'; // Birdie - blue
              if (diff === 0) return '#616161'; // Par - gray
              if (diff === 1) return '#f57c00'; // Bogey - orange
              return '#d32f2f'; // Double+ - red
            };

            const isSelected = playerScore === score;
            const buttonId = `score-${player.id}-${score}`;
            const isPressedScore = pressedButton === buttonId;

            return (
              <button
                key={score}
                onClick={() => updateScore(player.id, score)}
                className="touch-optimized"
                style={{
                  minHeight: '90px', // Increased from 70px for glove use
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px', // Increased from 4px
                  padding: '12px', // Increased from 8px
                  border: isSelected ? `4px solid ${getScoreColor()}` : '3px solid #e0e0e0', // Thicker borders
                  borderRadius: '12px', // Increased from 8px
                  background: isSelected ? `${getScoreColor()}25` : 'white', // Stronger highlight
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  fontWeight: isSelected ? 'bold' : 'normal',
                  transform: isPressedScore ? 'scale(0.95)' : 'scale(1)',
                  touchAction: 'manipulation'
                }}
                onTouchStart={() => setPressedButton(buttonId)}
                onTouchEnd={() => setPressedButton(null)}
                onTouchCancel={() => setPressedButton(null)}
                onMouseDown={() => setPressedButton(buttonId)}
                onMouseUp={() => setPressedButton(null)}
                onMouseLeave={() => setPressedButton(null)}
              >
                <span style={{
                  fontSize: '28px', // Increased from 24px
                  fontWeight: 'bold',
                  color: getScoreColor()
                }}>
                  {score}
                </span>
                <span style={{
                  fontSize: '13px', // Increased from 11px
                  color: getScoreColor(),
                  fontWeight: 'bold',
                  textTransform: 'uppercase'
                }}>
                  {getScoreLabel()}
                </span>
              </button>
            );
          })}
        </div>

        {/* Custom score input for unusual scores */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input
            type="number"
            placeholder="Other score..."
            value={playerScore !== undefined && !commonScores.includes(playerScore) ? playerScore : ''}
            onChange={(e) => {
              const val = e.target.value ? parseInt(e.target.value) : undefined;
              if (val) updateScore(player.id, val);
            }}
            style={{
              flex: 1,
              padding: '16px', // Increased from 12px
              fontSize: '20px', // Increased from 16px for better visibility
              border: `3px solid ${theme.colors.border}`, // Thicker border
              borderRadius: '12px', // Increased from 8px
              background: theme.colors.background,
              minHeight: '60px' // Ensure minimum touch target height
            }}
          />
          {playerScore !== undefined && (
            <button
              onClick={() => {
                const newScores = { ...scores };
                delete newScores[player.id];
                setScores(newScores);
              }}
              className="touch-optimized"
              style={{
                padding: '16px 20px', // Increased padding
                fontSize: '20px', // Increased from 16px
                border: 'none',
                borderRadius: '12px',
                background: theme.colors.error,
                color: 'white',
                cursor: 'pointer',
                fontWeight: 'bold',
                minHeight: '60px', // Match input height
                touchAction: 'manipulation'
              }}
            >
              ✕ Clear
            </button>
          )}
        </div>

        {playerScore !== undefined && (
          <div style={{
            marginTop: '12px',
            padding: '8px',
            background: theme.colors.success,
            color: 'white',
            borderRadius: '8px',
            textAlign: 'center',
            fontWeight: 'bold',
            fontSize: '16px'
          }}>
            ✓ Score: {playerScore}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="touch-optimized" style={{ width: '100%' }}>
      {/* Score Entry Section */}
      {showScoreEntry && (
        <div style={{
          ...theme.cardStyle,
          marginBottom: '20px' // Increased spacing
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '20px' // Increased spacing
          }}>
            <h2 style={{
              margin: 0,
              fontSize: '26px', // Increased from 22px
              color: theme.colors.primary,
              fontWeight: 'bold'
            }}>
              Enter Scores
            </h2>
            <div style={{
              padding: '10px 16px', // Increased padding
              background: theme.colors.accent,
              color: 'white',
              borderRadius: '12px', // Increased from 8px
              fontSize: '18px', // Increased from 14px
              fontWeight: 'bold',
              minHeight: '50px', // Add minimum height for touch
              display: 'flex',
              alignItems: 'center'
            }}>
              Par {gameState.hole_par || 4}
            </div>
          </div>

          {gameState?.players?.map(player => renderScoreSelector(player))}

          <div style={{ marginTop: '16px' }}>
            {renderLargeButton(
              'calculate',
              '✓',
              'Calculate Points',
              handleCalculatePoints,
              'success',
              !canCalculate()
            )}
          </div>

          {!canCalculate() && (
            <div style={{
              marginTop: '16px', // Increased spacing
              padding: '16px', // Increased padding
              background: '#fff3cd',
              color: '#856404',
              borderRadius: '12px', // Increased from 8px
              fontSize: '18px', // Increased from 14px
              textAlign: 'center',
              fontWeight: 'bold', // Added for emphasis
              border: '2px solid #ffc107' // Added border for visibility
            }}>
              Enter all player scores to continue
            </div>
          )}
        </div>
      )}

      {/* Betting Actions */}
      {["partners", "solo"].includes(gameState?.teams?.type) && (
        <div style={{
          ...theme.cardStyle,
          marginBottom: '20px' // Increased spacing
        }}>
          <h2 style={{
            margin: '0 0 20px 0', // Increased spacing
            fontSize: '24px', // Increased from 22px
            color: theme.colors.primary,
            fontWeight: 'bold'
          }}>
            Betting Actions
          </h2>

          {/* Show Accept/Decline buttons when a double has been offered */}
          {gameState.doubled_status ? (
            <div
              className="touch-spacing-large"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '16px'
              }}>
              <div style={{
                gridColumn: '1 / -1',
                padding: '16px',
                background: '#fff3cd',
                borderRadius: '12px',
                border: '2px solid #ffc107',
                textAlign: 'center',
                fontSize: '18px',
                fontWeight: 'bold',
                color: '#856404'
              }}>
                ⚠️ Double has been offered! Choose to Accept or Decline
              </div>

              {renderLargeButton(
                'accept-double',
                '✅',
                'Accept Double',
                () => {
                  if (window.confirm('Accept the double? This will double the wager.')) {
                    onAction("accept_double", {
                      team_id: gameState.responding_team_id || "team2",
                      accepted: true
                    });
                  }
                },
                'success'
              )}

              {renderLargeButton(
                'decline-double',
                '❌',
                'Decline Double',
                () => {
                  if (window.confirm('Decline the double? Offering team wins the hole.')) {
                    onAction("decline_double", {
                      team_id: gameState.responding_team_id || "team2",
                      accepted: false
                    });
                  }
                },
                'error'
              )}
            </div>
          ) : (
            // Show normal betting actions when no double is pending
            <div
              className="touch-spacing-large"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '16px'
              }}>
              {renderLargeButton(
                'offer-double',
                '💰',
                'Offer Double',
                () => onAction("offer_double", {
                  offering_team_id: "team1",
                  target_team_id: "team2",
                  player_id: gameState.captain_id
                }),
                'warning'
              )}

              {!gameState.player_float_used?.[gameState.captain_id] && renderLargeButton(
                'invoke-float',
                '🎈',
                'Invoke Float',
                () => onAction("invoke_float", { captain_id: gameState.captain_id }),
                'primary'
              )}

              {renderLargeButton(
                'toggle-option',
                '🔄',
                'Toggle Option',
                () => onAction("toggle_option", { captain_id: gameState.captain_id }),
                'primary'
              )}
            </div>
          )}
        </div>
      )}

      {/* Go Solo / Partnership Decision - shown before teams are formed */}
      {gameState?.teams?.type === "pending" && (
        <div style={{
          ...theme.cardStyle,
          marginBottom: '20px',
          background: '#e3f2fd',
          border: '3px solid #2196f3'
        }}>
          <h2 style={{
            margin: '0 0 12px 0',
            fontSize: '22px',
            color: '#1976d2',
            fontWeight: 'bold'
          }}>
            Captain's Decision
          </h2>
          <p style={{
            fontSize: '16px',
            color: theme.colors.textSecondary,
            marginBottom: '16px',
            lineHeight: '1.5'
          }}>
            Captain can choose a partner or go solo (1 vs 3)
          </p>

          <div
            className="touch-spacing-large"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px'
            }}>
            {renderLargeButton(
              'go-solo',
              '👤',
              'Go Solo (1 vs 3)',
              () => {
                if (window.confirm('Captain goes solo? Wager will be doubled!')) {
                  onAction("go_solo", { captain_id: gameState.captain_id });
                }
              },
              'warning'
            )}

            {gameState.players?.filter(p => p.id !== gameState.captain_id).map(player =>
              renderLargeButton(
                `partner-${player.id}`,
                '🤝',
                `Partner with ${player.name}`,
                () => onAction("request_partner", {
                  captain_id: gameState.captain_id,
                  partner_id: player.id
                }),
                'primary'
              )
            )}
          </div>
        </div>
      )}

      {/* Carry-Over Status Indicator */}
      {gameState?.carry_over && (
        <div style={{
          ...theme.cardStyle,
          marginBottom: '20px',
          background: 'linear-gradient(135deg, #ffd700 0%, #ffed4e 100%)',
          border: '4px solid #ffa000',
          padding: '20px'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{
              fontSize: '48px',
              lineHeight: 1
            }}>
              🔄
            </div>
            <div style={{ flex: 1 }}>
              <h3 style={{
                margin: '0 0 8px 0',
                fontSize: '24px',
                fontWeight: 'bold',
                color: '#000'
              }}>
                CARRY OVER
              </h3>
              <p style={{
                margin: 0,
                fontSize: '18px',
                color: '#000',
                lineHeight: 1.4
              }}>
                Previous hole was tied! Wager has been doubled for this hole.
              </p>
            </div>
            <div style={{
              fontSize: '32px',
              fontWeight: 'bold',
              color: '#d32f2f',
              textAlign: 'center',
              minWidth: '100px'
            }}>
              ${gameState.current_wager || gameState.base_wager}
            </div>
          </div>
        </div>
      )}


      {/* Concede/Fold Hole */}
      {["partners", "solo"].includes(gameState?.teams?.type) && (
        <div style={{
          ...theme.cardStyle,
          marginBottom: '20px', // Increased spacing
          background: '#fff5f5',
          border: '3px solid #d32f2f' // Thicker border for emphasis
        }}>
          <h2 style={{
            margin: '0 0 12px 0', // Increased spacing
            fontSize: '22px', // Increased from 18px
            color: theme.colors.error,
            fontWeight: 'bold'
          }}>
            Fold / Concede Hole
          </h2>
          <p style={{
            fontSize: '16px', // Increased from 13px
            color: theme.colors.textSecondary,
            marginBottom: '16px', // Increased spacing
            lineHeight: '1.5'
          }}>
            Give up this hole and forfeit the wager
          </p>

          <div
            className="touch-spacing-large"
            style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', // Slightly larger minimum
            gap: '16px' // Increased from 12px
          }}>
            {gameState.teams.type === "partners" && (
              <>
                {renderLargeButton(
                  'concede-team1',
                  '🏳️',
                  'Team 1 Concedes',
                  () => {
                    if (window.confirm('Team 1 will forfeit the wager. Continue?')) {
                      onAction("concede_hole", { conceding_team_id: "team1" });
                    }
                  },
                  'error'
                )}
                {renderLargeButton(
                  'concede-team2',
                  '🏳️',
                  'Team 2 Concedes',
                  () => {
                    if (window.confirm('Team 2 will forfeit the wager. Continue?')) {
                      onAction("concede_hole", { conceding_team_id: "team2" });
                    }
                  },
                  'error'
                )}
              </>
            )}

            {gameState.teams.type === "solo" && (
              <>
                {renderLargeButton(
                  'concede-captain',
                  '🏳️',
                  'Captain Concedes',
                  () => {
                    if (window.confirm('Captain will forfeit the wager. Continue?')) {
                      onAction("concede_hole", { conceding_team_id: "captain" });
                    }
                  },
                  'error'
                )}
                {renderLargeButton(
                  'concede-opponents',
                  '🏳️',
                  'Opponents Concede',
                  () => {
                    if (window.confirm('Opponents will forfeit the wager. Continue?')) {
                      onAction("concede_hole", { conceding_team_id: "opponents" });
                    }
                  },
                  'error'
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Next Hole Button */}
      <div style={{
        ...theme.cardStyle,
        marginBottom: '20px' // Increased spacing
      }}>
        {renderLargeButton(
          'next-hole',
          '➡️',
          'Next Hole',
          () => onAction("next_hole"),
          'primary'
        )}
      </div>
    </div>
  );
};

export default LargeScoringButtons;
