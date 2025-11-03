// frontend/src/components/game/LargeScoringButtons.jsx
import React, { useState } from 'react';
import { useTheme } from '../../theme/Provider';
import '../../styles/mobile-touch.css';

const LargeScoringButtons = ({
  gameState,
  onScoreSubmit,
  onSaveScores,
  onAction,
  loading = false
}) => {
  const theme = useTheme();
  const [scores, setScores] = useState({});
  const [pressedButton, setPressedButton] = useState(null); // Track which button is pressed

  const updateScore = (playerId, value) => {
    setScores(prev => ({ ...prev, [playerId]: value }));
  };

  const canSave = () => {
    if (!gameState?.players) return false;
    // Check if at least one score is entered
    return Object.keys(scores).some(pid => scores[pid] !== undefined && scores[pid] !== null);
  };

  const canCalculate = () => {
    if (!gameState?.players) return false;
    if (!["partners", "solo"].includes(gameState.teams?.type)) return false;

    // Check all players have scores
    return gameState.players.every(p => scores[p.id] !== undefined && scores[p.id] !== null);
  };

  const handleSaveScores = async () => {
    if (onSaveScores) {
      await onSaveScores(scores);
      // Don't clear scores after saving - user can continue editing
    }
  };

  const handleCalculatePoints = async () => {
    if (onScoreSubmit) {
      await onScoreSubmit(scores);
      setScores({});
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
      {/* Game Status Indicators - ALWAYS VISIBLE */}
      <div style={{
        ...theme.cardStyle,
        marginBottom: '20px',
        background: theme.colors.background,
        border: `2px solid ${theme.colors.border}`,
        padding: '12px'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '12px'
        }}>
          {/* Float Status - ALWAYS VISIBLE */}
          <div style={{
            padding: '10px',
            background: '#fff3cd',
            borderRadius: '8px',
            border: '2px solid #ffc107',
            textAlign: 'center',
            opacity: (gameState?.player_float_used && Object.keys(gameState.player_float_used || {}).some(id => gameState.player_float_used[id])) ? 1 : 0.3
          }}>
            <div style={{ fontSize: '24px', marginBottom: '4px' }}>🎈</div>
            <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#856404' }}>
              Float Active
            </div>
            <div style={{ fontSize: '12px', color: '#856404', marginTop: '2px' }}>
              2x Wager
            </div>
          </div>

          {/* Doubled Status - ALWAYS VISIBLE */}
          <div style={{
            padding: '10px',
            background: '#f8d7da',
            borderRadius: '8px',
            border: '2px solid #f5c6cb',
            textAlign: 'center',
            opacity: gameState?.doubled_status ? 1 : 0.3
          }}>
            <div style={{ fontSize: '24px', marginBottom: '4px' }}>💰</div>
            <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#721c24' }}>
              Doubled!
            </div>
            <div style={{ fontSize: '12px', color: '#721c24', marginTop: '2px' }}>
              Stakes Raised
            </div>
          </div>

          {/* Option Status - ALWAYS VISIBLE */}
          <div style={{
            padding: '10px',
            background: '#d1ecf1',
            borderRadius: '8px',
            border: '2px solid #bee5eb',
            textAlign: 'center',
            opacity: gameState?.option_active ? 1 : 0.3
          }}>
            <div style={{ fontSize: '24px', marginBottom: '4px' }}>⚡</div>
            <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#0c5460' }}>
              Option Active
            </div>
            <div style={{ fontSize: '12px', color: '#0c5460', marginTop: '2px' }}>
              Auto-Double
            </div>
          </div>

          {/* Current Wager Display */}
          <div style={{
            padding: '10px',
            background: theme.colors.primary,
            borderRadius: '8px',
            border: `2px solid ${theme.colors.primary}`,
            textAlign: 'center',
            color: 'white'
          }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '4px' }}>
              {gameState?.current_wager || gameState?.base_wager || 1}q
            </div>
            <div style={{ fontSize: '12px', opacity: 0.9 }}>
              Current Wager
            </div>
          </div>
        </div>
      </div>

      {/* Score Entry Section - ALWAYS VISIBLE */}
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
            Par {gameState?.hole_par || 4}
          </div>
        </div>

        {gameState?.players?.map(player => renderScoreSelector(player))}

        <div style={{
          marginTop: '16px',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '12px'
        }}>
          {renderLargeButton(
            'save',
            '💾',
            'Save Scores',
            handleSaveScores,
            'primary',
            !canSave() || !onSaveScores
          )}
          {renderLargeButton(
            'calculate',
            '✓',
            'Calculate Points',
            handleCalculatePoints,
            'success',
            !canCalculate()
          )}
        </div>

        {/* Warning message - ALWAYS VISIBLE */}
        <div style={{
          marginTop: '16px', // Increased spacing
          padding: '16px', // Increased padding
          background: '#fff3cd',
          color: '#856404',
          borderRadius: '12px', // Increased from 8px
          fontSize: '18px', // Increased from 14px
          textAlign: 'center',
          fontWeight: 'bold', // Added for emphasis
          border: '2px solid #ffc107', // Added border for visibility
          opacity: !canCalculate() ? 1 : 0.3
        }}>
          Enter all player scores to continue
        </div>
      </div>

      {/* Betting Actions - ALWAYS VISIBLE */}
      <div style={{
        ...theme.cardStyle,
        marginBottom: '20px', // Increased spacing
        opacity: ["partners", "solo"].includes(gameState?.teams?.type) ? 1 : 0.3
      }}>
        <h2 style={{
          margin: '0 0 20px 0', // Increased spacing
          fontSize: '24px', // Increased from 22px
          color: theme.colors.primary,
          fontWeight: 'bold'
        }}>
          Betting Actions {!["partners", "solo"].includes(gameState?.teams?.type) && '(Not Available)'}
        </h2>

        {/* Accept/Decline buttons - ALWAYS VISIBLE, opacity when not doubled */}
        <div
          className="touch-spacing-large"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
            opacity: gameState?.doubled_status ? 1 : 0.3,
            marginBottom: '16px'
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
                  team_id: gameState?.responding_team_id || "team2",
                  accepted: true
                });
              }
            },
            'success',
            !gameState?.doubled_status
          )}

          {renderLargeButton(
            'decline-double',
            '❌',
            'Decline Double',
            () => {
              if (window.confirm('Decline the double? Offering team wins the hole.')) {
                onAction("decline_double", {
                  team_id: gameState?.responding_team_id || "team2",
                  accepted: false
                });
              }
            },
            'error',
            !gameState?.doubled_status
          )}
        </div>

        {/* Normal betting actions - ALWAYS VISIBLE, opacity when doubled */}
        <div
          className="touch-spacing-large"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
            opacity: !gameState?.doubled_status ? 1 : 0.3
          }}>
          {renderLargeButton(
            'offer-double',
            '💰',
            'Offer Double',
            () => onAction("offer_double", {
              offering_team_id: "team1",
              target_team_id: "team2",
              player_id: gameState?.captain_id
            }),
            'warning',
            gameState?.doubled_status
          )}

          {renderLargeButton(
            'invoke-float',
            '🎈',
            gameState?.player_float_used?.[gameState?.captain_id] ? 'Float Used' : 'Invoke Float',
            () => onAction("invoke_float", { captain_id: gameState?.captain_id }),
            'primary',
            gameState?.player_float_used?.[gameState?.captain_id] || gameState?.doubled_status
          )}

          {renderLargeButton(
            'toggle-option',
            '🔄',
            'Toggle Option',
            () => onAction("toggle_option", { captain_id: gameState?.captain_id }),
            'primary',
            gameState?.doubled_status
          )}
        </div>
      </div>

      {/* Go Solo / Partnership Decision - ALWAYS VISIBLE */}
      <div style={{
        ...theme.cardStyle,
        marginBottom: '20px',
        background: '#e3f2fd',
        border: '3px solid #2196f3',
        opacity: (gameState?.teams?.type === "pending" && !gameState?.teams?.requested) ? 1 : 0.3
      }}>
        <h2 style={{
          margin: '0 0 12px 0',
          fontSize: '22px',
          color: '#1976d2',
          fontWeight: 'bold'
        }}>
          Captain's Decision {!(gameState?.teams?.type === "pending" && !gameState?.teams?.requested) && '(Not Active)'}
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
                onAction("go_solo", { captain_id: gameState?.captain_id });
              }
            },
            'warning',
            !(gameState?.teams?.type === "pending" && !gameState?.teams?.requested)
          )}

          {(gameState?.players || []).filter(p => p.id !== gameState?.captain_id).map(player =>
            renderLargeButton(
              `partner-${player.id}`,
              '🤝',
              `Partner with ${player.name}`,
              () => onAction("request_partner", {
                captain_id: gameState?.captain_id,
                partner_id: player.id
              }),
              'primary',
              !(gameState?.teams?.type === "pending" && !gameState?.teams?.requested)
            )
          )}
        </div>
      </div>

      {/* Partnership Acceptance - ALWAYS VISIBLE */}
      <div style={{
        ...theme.cardStyle,
        marginBottom: '20px',
        background: '#e8f5e9',
        border: '3px solid #4caf50',
        boxShadow: '0 4px 16px rgba(76, 175, 80, 0.3)',
        opacity: (gameState?.teams?.type === "pending" && gameState?.teams?.requested) ? 1 : 0.3
      }}>
        <h2 style={{
          margin: '0 0 12px 0',
          fontSize: '24px',
          color: theme.colors.success,
          fontWeight: 'bold',
          textAlign: 'center'
        }}>
          🤝 CONFIRM PARTNERSHIP {!(gameState?.teams?.type === "pending" && gameState?.teams?.requested) && '(Not Active)'}
        </h2>
        <p style={{
          fontSize: '18px',
          textAlign: 'center',
          marginBottom: '16px',
          lineHeight: '1.5'
        }}>
          <strong>{gameState?.players?.find(p => p.id === gameState?.captain_id)?.name || 'Captain'}</strong> wants{' '}
          <strong>{gameState?.players?.find(p => p.id === gameState?.teams?.requested)?.name || 'you'}</strong> as partner
        </p>
        <p style={{
          fontSize: '16px',
          color: theme.colors.textSecondary,
          marginBottom: '20px',
          textAlign: 'center',
          lineHeight: '1.5'
        }}>
          Does {gameState?.players?.find(p => p.id === gameState?.teams?.requested)?.name || 'partner'} accept?
        </p>

        <div
          className="touch-spacing-large"
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr',
            gap: '16px'
          }}>
          {renderLargeButton(
            'accept-partnership',
            '✅',
            'Accept Partnership',
            () => onAction("accept_partner", {
              partner_id: gameState?.teams?.requested,
              accepted: true
            }),
            'success',
            !(gameState?.teams?.type === "pending" && gameState?.teams?.requested)
          )}

          {renderLargeButton(
            'decline-partnership',
            '❌',
            `Decline (${gameState?.players?.find(p => p.id === gameState?.captain_id)?.name || 'Captain'} Goes Solo)`,
            () => {
              if (window.confirm('Decline partnership? Captain will go solo and wager doubles!')) {
                onAction("decline_partner", {
                  partner_id: gameState?.teams?.requested,
                  accepted: false
                });
              }
            },
            'error',
            !(gameState?.teams?.type === "pending" && gameState?.teams?.requested)
          )}
        </div>
      </div>

      {/* Hoepfinger Phase - Joe's Special Wager Selection - ALWAYS VISIBLE */}
      <div style={{
        ...theme.cardStyle,
        marginBottom: '20px',
        background: 'linear-gradient(135deg, #ff6b6b 0%, #ffd93d 100%)',
        border: '4px solid #d32f2f',
        padding: '20px',
        opacity: (gameState?.game_phase === "hoepfinger" && gameState?.goat_id && !gameState?.joes_special_set) ? 1 : 0.3
      }}>
        <h2 style={{
          margin: '0 0 16px 0',
          fontSize: '26px',
          color: '#000',
          fontWeight: 'bold',
          textAlign: 'center'
        }}>
          🎯 HOEPFINGER PHASE - JOE'S SPECIAL {!(gameState?.game_phase === "hoepfinger" && gameState?.goat_id && !gameState?.joes_special_set) && '(Not Active)'}
        </h2>
        <p style={{
          fontSize: '18px',
          textAlign: 'center',
          marginBottom: '20px',
          color: '#000',
          lineHeight: '1.5'
        }}>
          <strong>{gameState?.players?.find(p => p.id === gameState?.goat_id)?.name || 'The Goat'}</strong> is the Goat!<br />
          Choose the starting wager for this hole:
        </p>

        <div
          className="touch-spacing-large"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '16px'
          }}>
          {[2, 4, 8].map(value =>
            renderLargeButton(
              `joes-special-${value}`,
              `${value}q`,
              `${value} Quarters`,
              () => {
                if (window.confirm(`Set hole value to ${value} quarters?`)) {
                  onAction("invoke_joes_special", {
                    goat_id: gameState?.goat_id,
                    selected_value: value
                  });
                }
              },
              value === 8 ? 'error' : value === 4 ? 'warning' : 'primary',
              !(gameState?.game_phase === "hoepfinger" && gameState?.goat_id && !gameState?.joes_special_set)
            )
          )}
        </div>

        <p style={{
          fontSize: '14px',
          textAlign: 'center',
          marginTop: '16px',
          color: '#000',
          fontStyle: 'italic'
        }}>
          Note: No doubling until all players have teed off
        </p>
      </div>

      {/* Hoepfinger Phase Indicator - ALWAYS VISIBLE */}
      <div style={{
        ...theme.cardStyle,
        marginBottom: '20px',
        background: 'linear-gradient(135deg, #6a11cb 0%, #2575fc 100%)',
        border: '3px solid #6a11cb',
        padding: '16px',
        color: 'white',
        opacity: gameState?.game_phase === "hoepfinger" ? 1 : 0.3
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <div style={{ fontSize: '36px' }}>🐐</div>
          <div style={{ flex: 1 }}>
            <h3 style={{
              margin: '0 0 4px 0',
              fontSize: '20px',
              fontWeight: 'bold'
            }}>
              HOEPFINGER PHASE {gameState?.game_phase === "hoepfinger" ? 'ACTIVE' : '(Not Active)'}
            </h3>
            <p style={{
              margin: 0,
              fontSize: '15px',
              opacity: 0.9
            }}>
              The Goat ({gameState?.players?.find(p => p.id === gameState?.goat_id)?.name || 'None'}) chooses hitting position each hole
            </p>
          </div>
        </div>
      </div>

      {/* Carry-Over Status Indicator - ALWAYS VISIBLE */}
      <div style={{
        ...theme.cardStyle,
        marginBottom: '20px',
        background: 'linear-gradient(135deg, #ffd700 0%, #ffed4e 100%)',
        border: '4px solid #ffa000',
        padding: '20px',
        opacity: gameState?.carry_over ? 1 : 0.3
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
              CARRY OVER {!gameState?.carry_over && '(Not Active)'}
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
            ${gameState?.current_wager || gameState?.base_wager || 0}
          </div>
        </div>
      </div>


      {/* Concede/Fold Hole - ALWAYS VISIBLE */}
      <div style={{
        ...theme.cardStyle,
        marginBottom: '20px', // Increased spacing
        background: '#fff5f5',
        border: '3px solid #d32f2f', // Thicker border for emphasis
        opacity: ["partners", "solo"].includes(gameState?.teams?.type) ? 1 : 0.3
      }}>
        <h2 style={{
          margin: '0 0 12px 0', // Increased spacing
          fontSize: '22px', // Increased from 18px
          color: theme.colors.error,
          fontWeight: 'bold'
        }}>
          Fold / Concede Hole {!["partners", "solo"].includes(gameState?.teams?.type) && '(Not Available)'}
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
          {/* Partners buttons - ALWAYS VISIBLE */}
          {renderLargeButton(
            'concede-team1',
            '🏳️',
            'Team 1 Concedes',
            () => {
              if (window.confirm('Team 1 will forfeit the wager. Continue?')) {
                onAction("concede_hole", { conceding_team_id: "team1" });
              }
            },
            'error',
            gameState?.teams?.type !== "partners"
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
            'error',
            gameState?.teams?.type !== "partners"
          )}

          {/* Solo buttons - ALWAYS VISIBLE */}
          {renderLargeButton(
            'concede-captain',
            '🏳️',
            'Captain Concedes',
            () => {
              if (window.confirm('Captain will forfeit the wager. Continue?')) {
                onAction("concede_hole", { conceding_team_id: "captain" });
              }
            },
            'error',
            gameState?.teams?.type !== "solo"
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
            'error',
            gameState?.teams?.type !== "solo"
          )}
        </div>
      </div>

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
