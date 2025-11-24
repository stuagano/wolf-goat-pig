import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../theme/Provider';

const EnhancedScoringWidget = ({ gameState, holeState, onScoreUpdate, onAction }) => {
  const theme = useTheme();
  const [scores, setScores] = useState({});
  const [showingAnimation, setShowingAnimation] = useState(false);
  const [recentScoreChange, setRecentScoreChange] = useState(null);
  const [editMode, setEditMode] = useState(false);

  useEffect(() => {
    // Initialize scores from game state
    if (gameState?.players) {
      const initialScores = {};
      gameState.players.forEach(player => {
        const playerHoleData = holeState?.ball_positions?.[player.id];
        initialScores[player.id] = playerHoleData?.final_score || '';
      });
      setScores(initialScores);
    }
  }, [gameState, holeState]);

  const updateScore = (playerId, score) => {
    const numericScore = parseInt(score) || '';
    const oldScore = scores[playerId];
    
    setScores(prev => ({ ...prev, [playerId]: numericScore }));
    
    // Show animation for score changes
    if (oldScore !== numericScore && numericScore !== '') {
      setRecentScoreChange({ playerId, oldScore, newScore: numericScore });
      setShowingAnimation(true);
      setTimeout(() => {
        setShowingAnimation(false);
        setRecentScoreChange(null);
      }, 2000);
    }
    
    if (onScoreUpdate) {
      onScoreUpdate(playerId, numericScore);
    }
  };

  const getScoreColor = (score, par) => {
    if (!score || score === '') return theme.colors.textSecondary;
    const diff = score - par;
    if (diff <= -2) return theme.colors.success; // Eagle or better
    if (diff === -1) return '#2196f3'; // Birdie (blue)
    if (diff === 0) return theme.colors.textPrimary; // Par
    if (diff === 1) return theme.colors.warning; // Bogey
    return theme.colors.error; // Double bogey or worse
  };

  const getScoreLabel = (score, par) => {
    if (!score || score === '') return '';
    const diff = score - par;
    if (diff <= -3) return '🦅 Albatross';
    if (diff === -2) return '🦅 Eagle';
    if (diff === -1) return '🐦 Birdie';
    if (diff === 0) return '📍 Par';
    if (diff === 1) return '🤏 Bogey';
    if (diff === 2) return '😬 Double';
    return `😵 +${diff}`;
  };

  const calculateTeamScores = () => {
    if (!holeState?.teams || holeState.teams.type === 'pending') {
      return null;
    }

    if (holeState.teams.type === 'partners') {
      const team1Score = Math.min(
        ...(holeState.teams.team1 || []).map(pid => scores[pid] || 999).filter(s => s !== 999)
      );
      const team2Score = Math.min(
        ...(holeState.teams.team2 || []).map(pid => scores[pid] || 999).filter(s => s !== 999)
      );
      
      return {
        type: 'partners',
        team1: { players: holeState.teams.team1, score: team1Score === 999 ? null : team1Score },
        team2: { players: holeState.teams.team2, score: team2Score === 999 ? null : team2Score }
      };
    }

    if (holeState.teams.type === 'solo') {
      const soloScore = scores[holeState.teams.solo_player] || null;
      const opponentScore = Math.min(
        ...(holeState.teams.opponents || []).map(pid => scores[pid] || 999).filter(s => s !== 999)
      );
      
      return {
        type: 'solo',
        solo: { player: holeState.teams.solo_player, score: soloScore },
        opponents: { players: holeState.teams.opponents, score: opponentScore === 999 ? null : opponentScore }
      };
    }

    return null;
  };

  const submitHoleScores = async () => {
    const allScoresEntered = gameState.players.every(player => 
      scores[player.id] && scores[player.id] !== ''
    );
    
    if (!allScoresEntered) {
      alert('Please enter all player scores before submitting');
      return;
    }

    if (onAction) {
      await onAction('SUBMIT_HOLE_SCORES', { scores });
    }
    setEditMode(false);
  };

  const teamScores = calculateTeamScores();
  const holePar = holeState?.hole_par || 4;

  return (
    <div style={{
      background: theme.colors.background,
      borderRadius: 16,
      padding: 24,
      margin: '12px 0',
      boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
      border: `2px solid ${theme.colors.primary}`,
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Animated background for score updates */}
      {showingAnimation && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'linear-gradient(45deg, rgba(76,175,80,0.1), rgba(33,150,243,0.1))',
          animation: 'pulse 2s ease-in-out',
          pointerEvents: 'none',
          zIndex: 0
        }} />
      )}

      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
        position: 'relative',
        zIndex: 1
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            background: 'linear-gradient(135deg, #4CAF50, #2196F3)',
            color: 'white',
            width: 48,
            height: 48,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 24,
            boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
          }}>
            🏌️
          </div>
          <div>
            <h2 style={{ margin: 0, color: theme.colors.primary, fontSize: 24, fontWeight: 700 }}>
              Hole {gameState?.current_hole || 1} Scoring
            </h2>
            <div style={{ color: theme.colors.textSecondary, fontSize: 14 }}>
              Par {holePar} • Stroke Index {holeState?.stroke_index || 'N/A'}
            </div>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setEditMode(!editMode)}
            style={{
              background: editMode ? theme.colors.warning : theme.colors.secondary,
              color: 'white',
              border: 'none',
              borderRadius: 8,
              padding: '8px 16px',
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            {editMode ? '✏️ Editing' : '📝 Edit Scores'}
          </button>
        </div>
      </div>

      {/* Player Score Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 16,
        marginBottom: 24,
        position: 'relative',
        zIndex: 1
      }}>
        {gameState?.players?.map((player) => {
          const playerScore = scores[player.id];
          const strokeAdv = holeState?.stroke_advantages?.[player.id];
          const ballPosition = holeState?.ball_positions?.[player.id];
          const isRecentChange = recentScoreChange?.playerId === player.id;
          
          return (
            <div key={player.id} style={{
              background: theme.colors.card,
              borderRadius: 12,
              padding: 16,
              border: `2px solid ${isRecentChange ? theme.colors.success : 'transparent'}`,
              boxShadow: isRecentChange ? '0 0 20px rgba(76,175,80,0.3)' : '0 2px 8px rgba(0,0,0,0.1)',
              transition: 'all 0.3s ease',
              transform: isRecentChange ? 'scale(1.02)' : 'scale(1)'
            }}>
              {/* Player Header */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 12
              }}>
                <div>
                  <div style={{ 
                    fontSize: 18, 
                    fontWeight: 700, 
                    color: theme.colors.textPrimary,
                    marginBottom: 2
                  }}>
                    {player.name}
                  </div>
                  <div style={{ 
                    fontSize: 12, 
                    color: theme.colors.textSecondary 
                  }}>
                    Handicap {player.handicap} • {player.points} pts
                  </div>
                </div>
                
                {strokeAdv?.strokes_received > 0 && (
                  <div style={{
                    background: theme.colors.accent,
                    color: 'white',
                    borderRadius: 20,
                    padding: '4px 8px',
                    fontSize: 12,
                    fontWeight: 600
                  }}>
                    +{strokeAdv.strokes_received} {strokeAdv.strokes_received === 1 ? 'stroke' : 'strokes'}
                  </div>
                )}
              </div>

              {/* Score Input/Display */}
              <div style={{ marginBottom: 12 }}>
                {editMode ? (
                  <input
                    type="number"
                    value={playerScore}
                    onChange={(e) => updateScore(player.id, e.target.value)}
                    min="1"
                    max="15"
                    style={{
                      width: '100%',
                      padding: '12px',
                      fontSize: 24,
                      fontWeight: 700,
                      textAlign: 'center',
                      border: `2px solid ${theme.colors.border}`,
                      borderRadius: 8,
                      background: theme.colors.background,
                      color: getScoreColor(playerScore, holePar)
                    }}
                    placeholder="Score"
                  />
                ) : (
                  <div style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: 32,
                    fontWeight: 700,
                    textAlign: 'center',
                    color: getScoreColor(playerScore, holePar),
                    background: '#f8f9fa',
                    borderRadius: 8,
                    minHeight: 60,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    {playerScore || '—'}
                  </div>
                )}
              </div>

              {/* Score Label */}
              <div style={{
                textAlign: 'center',
                fontSize: 14,
                fontWeight: 600,
                color: getScoreColor(playerScore, holePar),
                marginBottom: 8
              }}>
                {getScoreLabel(playerScore, holePar)}
              </div>

              {/* Ball Position Info */}
              {ballPosition && (
                <div style={{
                  fontSize: 12,
                  color: theme.colors.textSecondary,
                  textAlign: 'center',
                  padding: '6px',
                  background: '#f0f8ff',
                  borderRadius: 6
                }}>
                  📍 {Math.round(ballPosition.distance_to_pin)} yds from pin • Shot #{ballPosition.shot_count}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Team Score Summary */}
      {teamScores && (
        <div style={{
          background: 'linear-gradient(135deg, #f8f9fa, #e3f2fd)',
          borderRadius: 12,
          padding: 16,
          marginBottom: 20,
          border: `2px solid ${theme.colors.accent}`,
          position: 'relative',
          zIndex: 1
        }}>
          <h3 style={{ 
            margin: '0 0 16px 0', 
            color: theme.colors.primary,
            textAlign: 'center',
            fontSize: 18,
            fontWeight: 700
          }}>
            🏆 Team Scores
          </h3>
          
          {teamScores.type === 'partners' ? (
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto 1fr',
              alignItems: 'center',
              gap: 16
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 14, color: theme.colors.textSecondary, marginBottom: 4 }}>
                  Team 1
                </div>
                <div style={{ 
                  fontSize: 32, 
                  fontWeight: 700,
                  color: teamScores.team1.score ? getScoreColor(teamScores.team1.score, holePar) : theme.colors.textSecondary
                }}>
                  {teamScores.team1.score || '—'}
                </div>
                <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
                  {teamScores.team1.players.map(pid => 
                    gameState.players.find(p => p.id === pid)?.name
                  ).join(' & ')}
                </div>
              </div>
              
              <div style={{ 
                fontSize: 24, 
                fontWeight: 700, 
                color: theme.colors.accent 
              }}>
                vs
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 14, color: theme.colors.textSecondary, marginBottom: 4 }}>
                  Team 2
                </div>
                <div style={{ 
                  fontSize: 32, 
                  fontWeight: 700,
                  color: teamScores.team2.score ? getScoreColor(teamScores.team2.score, holePar) : theme.colors.textSecondary
                }}>
                  {teamScores.team2.score || '—'}
                </div>
                <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
                  {teamScores.team2.players.map(pid => 
                    gameState.players.find(p => p.id === pid)?.name
                  ).join(' & ')}
                </div>
              </div>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr auto 1fr',
              alignItems: 'center',
              gap: 16
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 14, color: theme.colors.textSecondary, marginBottom: 4 }}>
                  Solo Player
                </div>
                <div style={{ 
                  fontSize: 32, 
                  fontWeight: 700,
                  color: teamScores.solo.score ? getScoreColor(teamScores.solo.score, holePar) : theme.colors.textSecondary
                }}>
                  {teamScores.solo.score || '—'}
                </div>
                <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
                  {gameState.players.find(p => p.id === teamScores.solo.player)?.name}
                </div>
              </div>
              
              <div style={{ 
                fontSize: 24, 
                fontWeight: 700, 
                color: theme.colors.accent 
              }}>
                vs
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 14, color: theme.colors.textSecondary, marginBottom: 4 }}>
                  Opponents
                </div>
                <div style={{ 
                  fontSize: 32, 
                  fontWeight: 700,
                  color: teamScores.opponents.score ? getScoreColor(teamScores.opponents.score, holePar) : theme.colors.textSecondary
                }}>
                  {teamScores.opponents.score || '—'}
                </div>
                <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
                  {teamScores.opponents.players.map(pid => 
                    gameState.players.find(p => p.id === pid)?.name
                  ).join(' & ')}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Submit Button */}
      {editMode && (
        <div style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <button
            onClick={submitHoleScores}
            style={{
              background: 'linear-gradient(135deg, #4CAF50, #2196F3)',
              color: 'white',
              border: 'none',
              borderRadius: 12,
              padding: '16px 32px',
              fontSize: 18,
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
              transition: 'all 0.2s',
              transform: 'translateY(0)'
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 6px 20px rgba(0,0,0,0.3)';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 16px rgba(0,0,0,0.2)';
            }}
          >
            🏌️ Complete Hole & Calculate Points
          </button>
        </div>
      )}

      {/* Animation styles injected into head */}
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes pulse {
            0%, 100% { opacity: 0.1; }
            50% { opacity: 0.3; }
          }
        `
      }} />
    </div>
  );
};

EnhancedScoringWidget.propTypes = {
  gameState: PropTypes.shape({
    players: PropTypes.arrayOf(PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      handicap: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    })),
  }),
  holeState: PropTypes.shape({
    teams: PropTypes.shape({
      type: PropTypes.string,
      team1: PropTypes.arrayOf(PropTypes.string),
      team2: PropTypes.arrayOf(PropTypes.string),
      solo_player: PropTypes.string,
      opponents: PropTypes.arrayOf(PropTypes.string),
    }),
    ball_positions: PropTypes.objectOf(PropTypes.shape({
      final_score: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    })),
  }),
  onScoreUpdate: PropTypes.func,
  onAction: PropTypes.func,
};

export default EnhancedScoringWidget;