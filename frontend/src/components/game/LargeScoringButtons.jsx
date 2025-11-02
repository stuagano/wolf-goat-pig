// frontend/src/components/game/LargeScoringButtons.jsx
import React, { useState } from 'react';
import { useTheme } from '../../theme/Provider';

const LargeScoringButtons = ({
  gameState,
  onScoreSubmit,
  onAction,
  loading = false
}) => {
  const theme = useTheme();
  const [scores, setScores] = useState({});
  const [showScoreEntry, setShowScoreEntry] = useState(true);

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
        style={{
          minHeight: '80px',
          fontSize: '18px',
          fontWeight: 'bold',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          padding: '16px',
          border: 'none',
          borderRadius: '12px',
          background: disabled ? '#e0e0e0' : getButtonColor(),
          color: disabled ? '#9e9e9e' : 'white',
          cursor: disabled ? 'not-allowed' : 'pointer',
          boxShadow: disabled ? 'none' : '0 4px 12px rgba(0,0,0,0.15)',
          transition: 'all 0.2s ease',
          width: '100%',
          opacity: disabled ? 0.6 : 1,
          transform: loading ? 'scale(0.98)' : 'scale(1)'
        }}
        onMouseOver={(e) => {
          if (!disabled && !loading) {
            e.currentTarget.style.transform = 'scale(1.02)';
            e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.2)';
          }
        }}
        onMouseOut={(e) => {
          if (!disabled && !loading) {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
          }
        }}
      >
        <span style={{ fontSize: '28px' }}>{icon}</span>
        <span style={{ fontSize: '16px', textAlign: 'center' }}>{label}</span>
      </button>
    );
  };

  // Score selection buttons for a player
  const renderScoreSelector = (player) => {
    const playerScore = scores[player.id];
    const holePar = gameState.hole_par || 4;
    const commonScores = [holePar - 2, holePar - 1, holePar, holePar + 1, holePar + 2];

    return (
      <div key={player.id} style={{
        background: theme.colors.paper,
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '16px',
        border: `2px solid ${playerScore !== undefined ? theme.colors.success : theme.colors.border}`
      }}>
        <h3 style={{
          margin: '0 0 12px 0',
          fontSize: '20px',
          color: theme.colors.primary,
          fontWeight: 'bold'
        }}>
          {player.name}
          <span style={{
            fontSize: '14px',
            color: theme.colors.textSecondary,
            fontWeight: 'normal',
            marginLeft: '8px'
          }}>
            (Hdcp {player.handicap})
          </span>
        </h3>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          gap: '8px',
          marginBottom: '8px'
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

            return (
              <button
                key={score}
                onClick={() => updateScore(player.id, score)}
                style={{
                  minHeight: '70px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '4px',
                  padding: '8px',
                  border: isSelected ? `3px solid ${getScoreColor()}` : '2px solid #e0e0e0',
                  borderRadius: '8px',
                  background: isSelected ? `${getScoreColor()}15` : 'white',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  fontWeight: isSelected ? 'bold' : 'normal'
                }}
                onMouseOver={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = '#f5f5f5';
                    e.currentTarget.style.borderColor = getScoreColor();
                  }
                }}
                onMouseOut={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = 'white';
                    e.currentTarget.style.borderColor = '#e0e0e0';
                  }
                }}
              >
                <span style={{
                  fontSize: '24px',
                  fontWeight: 'bold',
                  color: getScoreColor()
                }}>
                  {score}
                </span>
                <span style={{
                  fontSize: '11px',
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
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
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
              padding: '12px',
              fontSize: '16px',
              border: `2px solid ${theme.colors.border}`,
              borderRadius: '8px',
              background: theme.colors.background
            }}
          />
          {playerScore !== undefined && (
            <button
              onClick={() => {
                const newScores = { ...scores };
                delete newScores[player.id];
                setScores(newScores);
              }}
              style={{
                padding: '12px 16px',
                fontSize: '16px',
                border: 'none',
                borderRadius: '8px',
                background: theme.colors.error,
                color: 'white',
                cursor: 'pointer',
                fontWeight: 'bold'
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
    <div style={{ width: '100%' }}>
      {/* Score Entry Section */}
      {showScoreEntry && (
        <div style={{
          ...theme.cardStyle,
          marginBottom: '16px'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <h2 style={{
              margin: 0,
              fontSize: '22px',
              color: theme.colors.primary,
              fontWeight: 'bold'
            }}>
              Enter Scores
            </h2>
            <div style={{
              padding: '6px 12px',
              background: theme.colors.accent,
              color: 'white',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 'bold'
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
              marginTop: '12px',
              padding: '12px',
              background: '#fff3cd',
              color: '#856404',
              borderRadius: '8px',
              fontSize: '14px',
              textAlign: 'center'
            }}>
              Enter all player scores to continue
            </div>
          )}
        </div>
      )}

      {/* Betting Actions */}
      {["partners", "solo"].includes(gameState?.teams?.type) && !gameState?.doubled_status && (
        <div style={{
          ...theme.cardStyle,
          marginBottom: '16px'
        }}>
          <h2 style={{
            margin: '0 0 16px 0',
            fontSize: '22px',
            color: theme.colors.primary,
            fontWeight: 'bold'
          }}>
            Betting Actions
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '12px'
          }}>
            {!gameState.doubled_status && renderLargeButton(
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
        </div>
      )}

      {/* Next Hole Button */}
      <div style={{
        ...theme.cardStyle,
        marginBottom: '16px'
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
