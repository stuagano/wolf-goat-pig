import React, { useState, useEffect, useCallback } from 'react';
import { useTheme } from '../theme/Provider';

const InteractivePlayerCard = ({ 
  player, 
  gameState, 
  holeState, 
  expanded = false, 
  onClick,
  showFullStats = false 
}) => {
  const theme = useTheme();
  const [isExpanded, setIsExpanded] = useState(expanded);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch player statistics when expanded
  const fetchPlayerStats = useCallback(async () => {
    setLoading(true);
    try {
      const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_URL}/players/${player.id}/statistics`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching player stats:', error);
    } finally {
      setLoading(false);
    }
  }, [player.id]);

  useEffect(() => {
    if (isExpanded && showFullStats && !stats) {
      fetchPlayerStats();
    }
  }, [fetchPlayerStats, isExpanded, showFullStats, stats]);

  const handleCardClick = () => {
    if (onClick) {
      onClick(player);
    } else {
      setIsExpanded(!isExpanded);
    }
  };

  const getPlayerStatus = () => {
    const ballPosition = holeState?.ball_positions?.[player.id];
    
    if (!ballPosition) return 'waiting';
    if (ballPosition.final_score) return 'finished';
    if (ballPosition.distance_to_pin <= 5) return 'putting';
    if (ballPosition.distance_to_pin <= 150) return 'approach';
    return 'tee_shot';
  };

  const getStatusColor = (status) => {
    const colors = {
      'waiting': theme.colors.textSecondary,
      'finished': theme.colors.success,
      'putting': '#9C27B0',
      'approach': '#FF9800',
      'tee_shot': theme.colors.primary
    };
    return colors[status] || theme.colors.textSecondary;
  };

  const getStatusIcon = (status) => {
    const icons = {
      'waiting': '⏳',
      'finished': '✅',
      'putting': '⛳',
      'approach': '🎯',
      'tee_shot': '🏌️'
    };
    return icons[status] || '❓';
  };

  const getPerformanceColor = (value, type) => {
    if (type === 'scoring') {
      if (value >= 85) return theme.colors.success;
      if (value >= 75) return theme.colors.primary;
      if (value >= 65) return theme.colors.warning;
      return theme.colors.error;
    }
    // Default color scaling
    if (value >= 0.8) return theme.colors.success;
    if (value >= 0.6) return theme.colors.primary;
    if (value >= 0.4) return theme.colors.warning;
    return theme.colors.error;
  };

  const ballPosition = holeState?.ball_positions?.[player.id];
  const strokeAdv = holeState?.stroke_advantages?.[player.id];
  const status = getPlayerStatus();
  
  return (
    <div
      onClick={handleCardClick}
      style={{
        background: isExpanded ? 
          'linear-gradient(135deg, #ffffff, #f8f9fa)' : 
          theme.colors.card,
        borderRadius: 16,
        padding: isExpanded ? 24 : 16,
        margin: '8px 0',
        boxShadow: isExpanded ? 
          '0 12px 40px rgba(0,0,0,0.15)' : 
          '0 4px 12px rgba(0,0,0,0.08)',
        border: `2px solid ${getStatusColor(status)}`,
        cursor: 'pointer',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        position: 'relative',
        overflow: 'hidden',
        transform: isExpanded ? 'scale(1.02)' : 'scale(1)'
      }}
      onMouseOver={(e) => {
        if (!isExpanded) {
          e.currentTarget.style.transform = 'scale(1.02) translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
        }
      }}
      onMouseOut={(e) => {
        if (!isExpanded) {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
        }
      }}
    >
      {/* Status indicator */}
      <div style={{
        position: 'absolute',
        top: 12,
        right: 12,
        background: getStatusColor(status),
        color: 'white',
        borderRadius: '50%',
        width: 32,
        height: 32,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 14,
        fontWeight: 600,
        zIndex: 2
      }}>
        {getStatusIcon(status)}
      </div>

      {/* Main player info */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        marginBottom: isExpanded ? 20 : 0
      }}>
        {/* Avatar */}
        <div style={{
          width: isExpanded ? 64 : 48,
          height: isExpanded ? 64 : 48,
          borderRadius: '50%',
          background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.accent})`,
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: isExpanded ? 24 : 18,
          fontWeight: 700,
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
          flexShrink: 0
        }}>
          {player.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
        </div>

        {/* Player details */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: isExpanded ? 22 : 18,
            fontWeight: 700,
            color: theme.colors.textPrimary,
            marginBottom: 4,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {player.name}
          </div>
          
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            fontSize: 14,
            color: theme.colors.textSecondary
          }}>
            <span>Handicap {player.handicap}</span>
            <span>•</span>
            <span style={{ 
              color: player.points >= 0 ? theme.colors.success : theme.colors.error,
              fontWeight: 600
            }}>
              {player.points >= 0 ? '+' : ''}{player.points} pts
            </span>
          </div>
        </div>
      </div>

      {/* Current hole status */}
      {ballPosition && (
        <div style={{
          background: 'rgba(33, 150, 243, 0.08)',
          borderRadius: 8,
          padding: 12,
          marginBottom: isExpanded ? 16 : 0,
          border: '1px solid rgba(33, 150, 243, 0.2)'
        }}>
          <div style={{ 
            fontSize: 12, 
            color: theme.colors.textSecondary, 
            marginBottom: 4,
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Current Hole Status
          </div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <span style={{ fontWeight: 600 }}>
                📍 {Math.round(ballPosition.distance_to_pin)} yards from pin
              </span>
            </div>
            <div style={{ 
              fontSize: 14, 
              color: theme.colors.primary,
              fontWeight: 600
            }}>
              Shot #{ballPosition.shot_count}
            </div>
          </div>
          
          {ballPosition.final_score && (
            <div style={{ 
              marginTop: 8,
              fontSize: 16,
              fontWeight: 700,
              color: theme.colors.success
            }}>
              Final Score: {ballPosition.final_score}
            </div>
          )}
        </div>
      )}

      {/* Stroke advantage */}
      {strokeAdv?.strokes_received > 0 && (
        <div style={{
          background: theme.colors.accent + '20',
          borderRadius: 8,
          padding: 8,
          marginBottom: isExpanded ? 16 : 0,
          textAlign: 'center',
          border: `1px solid ${theme.colors.accent}40`
        }}>
          <div style={{
            fontSize: 14,
            fontWeight: 600,
            color: theme.colors.accent
          }}>
            +{strokeAdv.strokes_received} {strokeAdv.strokes_received === 1 ? 'Stroke' : 'Strokes'}
          </div>
        </div>
      )}

      {/* Expanded content */}
      {isExpanded && (
        <div style={{
          borderTop: `1px solid ${theme.colors.border}`,
          paddingTop: 16
        }}>
          {/* Performance metrics */}
          <div style={{ marginBottom: 20 }}>
            <h4 style={{ 
              margin: '0 0 12px 0', 
              color: theme.colors.primary,
              fontSize: 16,
              fontWeight: 600
            }}>
              📊 Performance Metrics
            </h4>
            
            {loading ? (
              <div style={{ textAlign: 'center', padding: 20 }}>
                <div style={{
                  width: 24,
                  height: 24,
                  border: `2px solid ${theme.colors.border}`,
                  borderTop: `2px solid ${theme.colors.primary}`,
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  margin: '0 auto'
                }} />
              </div>
            ) : stats ? (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                gap: 12
              }}>
                {Object.entries(stats).map(([key, value]) => (
                  <div key={key} style={{
                    background: '#f8f9fa',
                    borderRadius: 8,
                    padding: 12,
                    textAlign: 'center',
                    border: '1px solid rgba(0,0,0,0.08)'
                  }}>
                    <div style={{ 
                      fontSize: 11, 
                      color: theme.colors.textSecondary, 
                      marginBottom: 4,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px'
                    }}>
                      {key.replace(/_/g, ' ')}
                    </div>
                    <div style={{ 
                      fontSize: 16, 
                      fontWeight: 700, 
                      color: getPerformanceColor(value, key)
                    }}>
                      {typeof value === 'number' ? 
                        (value < 1 ? `${(value * 100).toFixed(0)}%` : value.toFixed(1)) : 
                        value}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{
                textAlign: 'center',
                padding: 20,
                color: theme.colors.textSecondary,
                fontSize: 14
              }}>
                Click to load detailed statistics
              </div>
            )}
          </div>

          {/* Recent performance trend */}
          {stats?.recent_scores && (
            <div style={{ marginBottom: 20 }}>
              <h4 style={{ 
                margin: '0 0 12px 0', 
                color: theme.colors.primary,
                fontSize: 16,
                fontWeight: 600
              }}>
                📈 Recent Performance
              </h4>
              <div style={{
                display: 'flex',
                gap: 4,
                alignItems: 'end',
                height: 40,
                padding: '0 8px'
              }}>
                {stats.recent_scores.slice(-10).map((score, index) => (
                  <div
                    key={index}
                    style={{
                      flex: 1,
                      background: getPerformanceColor(score / 100, 'scoring'),
                      height: `${Math.max(8, (score / Math.max(...stats.recent_scores)) * 40)}px`,
                      borderRadius: '2px 2px 0 0',
                      opacity: 0.8,
                      minWidth: 3
                    }}
                    title={`Score: ${score}`}
                  />
                ))}
              </div>
              <div style={{
                fontSize: 12,
                color: theme.colors.textSecondary,
                textAlign: 'center',
                marginTop: 4
              }}>
                Last 10 rounds
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div style={{
            display: 'flex',
            gap: 8,
            justifyContent: 'center'
          }}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                // Handle view full profile
              }}
              style={{
                background: theme.colors.primary,
                color: 'white',
                border: 'none',
                borderRadius: 8,
                padding: '8px 16px',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              👤 Full Profile
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                // Handle message player
              }}
              style={{
                background: theme.colors.secondary,
                color: 'white',
                border: 'none',
                borderRadius: 8,
                padding: '8px 16px',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              💬 Message
            </button>
          </div>
        </div>
      )}

      {/* Click indicator */}
      {!isExpanded && (
        <div style={{
          position: 'absolute',
          bottom: 8,
          right: 8,
          fontSize: 12,
          color: theme.colors.textSecondary,
          opacity: 0.6
        }}>
          Click for details
        </div>
      )}

      {/* Animation styles injected into head */}
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `
      }} />
    </div>
  );
};

export default InteractivePlayerCard;
