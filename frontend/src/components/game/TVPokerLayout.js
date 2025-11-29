import React, { useState } from 'react';
import { useTheme } from '../../theme/Provider';

/**
 * TV Poker-style layout for Wolf-Goat-Pig
 * Always shows all metrics, probabilities, and game state
 */
const TVPokerLayout = ({
  gameState,
  shotState,
  probabilities,
  onDecision,
  onPlayNextShot
}) => {
  // eslint-disable-next-line no-unused-vars
  const theme = useTheme();
  // eslint-disable-next-line no-unused-vars
  const [selectedOption, setSelectedOption] = useState(null);

  // Handle shot progression button click
  const handlePlayShot = () => {
    if (onPlayNextShot && gameState?.hasNextShot && !gameState?.interactionNeeded) {
      onPlayNextShot();
    }
  };

  // Export hole feed data for review
  const exportHoleFeed = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      hole: gameState?.current_hole || 1,
      par: gameState?.hole_par || 4,
      distance: gameState?.hole_distance || 0,
      players: players.map(p => ({
        id: p.id,
        name: p.name,
        handicap: p.handicap,
        points: p.points,
        status: p.status
      })),
      ballPositions: gameState?.hole_state?.ball_positions || {},
      currentShot: gameState?.hole_state?.current_shot_number || 1,
      nextPlayer: gameState?.hole_state?.next_player_to_hit,
      feedback: gameState?.feedback || [],
      gameComplete: gameState?.hole_state?.hole_complete || false,
      probabilities: probabilities,
      shotState: shotState
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `hole-${gameState?.current_hole || 1}-feed-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const styles = {
    container: {
      display: 'grid',
      gridTemplateColumns: '250px 1fr 300px',
      gridTemplateRows: '60px 200px 300px 1fr',
      gap: '10px',
      height: '100vh',
      padding: '10px',
      background: '#1a1a1a',
      color: '#fff',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    },
    topBar: {
      gridColumn: '1 / -1',
      background: 'linear-gradient(90deg, #2a2a2a, #3a3a3a)',
      borderRadius: '8px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px',
      fontSize: '18px',
      fontWeight: 'bold',
      boxShadow: '0 2px 10px rgba(0,0,0,0.5)'
    },
    playerPanel: {
      gridRow: '3 / 5',
      background: '#2a2a2a',
      borderRadius: '8px',
      padding: '15px',
      overflowY: 'auto',
      boxShadow: '0 2px 10px rgba(0,0,0,0.5)'
    },
    courseView: {
      gridRow: '3',
      background: 'linear-gradient(to bottom, #87CEEB, #98D98E)',
      borderRadius: '8px',
      padding: '15px',
      position: 'relative',
      boxShadow: '0 2px 10px rgba(0,0,0,0.5)'
    },
    metricsPanel: {
      gridRow: '3 / 5',
      background: '#2a2a2a',
      borderRadius: '8px',
      padding: '15px',
      overflowY: 'auto',
      boxShadow: '0 2px 10px rgba(0,0,0,0.5)'
    },
    actionFeed: {
      gridColumn: '1 / -1',
      gridRow: '2',
      background: '#2a2a2a',
      borderRadius: '8px',
      padding: '15px',
      overflowY: 'auto',
      maxHeight: '200px',
      boxShadow: '0 2px 10px rgba(0,0,0,0.5)'
    },
    playerCard: {
      background: '#3a3a3a',
      borderRadius: '6px',
      padding: '12px',
      marginBottom: '10px',
      border: '2px solid transparent',
      transition: 'all 0.3s'
    },
    playerCardActive: {
      border: '2px solid #4CAF50',
      background: '#3f4f3f'
    },
    playerCardCaptain: {
      border: '2px solid #FFD700',
      background: '#4a4530'
    },
    metricSection: {
      marginBottom: '20px',
      padding: '12px',
      background: '#3a3a3a',
      borderRadius: '6px'
    },
    probabilityBar: {
      height: '24px',
      background: '#4a4a4a',
      borderRadius: '12px',
      overflow: 'hidden',
      marginBottom: '8px',
      position: 'relative'
    },
    probabilityFill: {
      height: '100%',
      background: 'linear-gradient(90deg, #4CAF50, #8BC34A)',
      transition: 'width 0.5s ease',
      display: 'flex',
      alignItems: 'center',
      paddingLeft: '8px',
      fontSize: '12px',
      fontWeight: 'bold'
    },
    decisionOverlay: {
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    },
    decisionPanel: {
      background: '#2a2a2a',
      borderRadius: '12px',
      padding: '30px',
      maxWidth: '600px',
      width: '90%',
      boxShadow: '0 10px 40px rgba(0,0,0,0.8)'
    },
    decisionOption: {
      background: '#3a3a3a',
      border: '2px solid #4a4a4a',
      borderRadius: '8px',
      padding: '15px',
      marginBottom: '10px',
      cursor: 'pointer',
      transition: 'all 0.3s',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    },
    decisionOptionHover: {
      background: '#4a4a4a',
      border: '2px solid #4CAF50',
      transform: 'translateX(5px)'
    },
    evBadge: {
      background: '#4CAF50',
      color: '#fff',
      padding: '4px 8px',
      borderRadius: '4px',
      fontSize: '14px',
      fontWeight: 'bold'
    },
    evBadgeNegative: {
      background: '#f44336'
    },
    feedItem: {
      padding: '8px',
      borderBottom: '1px solid #3a3a3a',
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      fontSize: '14px'
    },
    feedIcon: {
      fontSize: '20px'
    },
    autoPlayControl: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      background: '#3a3a3a',
      padding: '8px 15px',
      borderRadius: '6px'
    }
  };

  // Use real player data from game state
  const players = gameState?.players || [];

  // Generate win probabilities based on real players
  const winProbabilities = probabilities?.win || (() => {
    const probs = {};
    players.forEach((player, index) => {
      // Simple probability distribution for demo
      const baseProbabilities = [28, 35, 22, 15];
      probs[player.name] = baseProbabilities[index] || 20;
    });
    return probs;
  })();

  const shotProbabilities = probabilities?.shot || {
    'Great': 15,
    'Good': 45,
    'OK': 30,
    'Poor': 10
  };

  // Generate partnership EVs based on real players (excluding human player)
  const partnershipEVs = probabilities?.partnerships || (() => {
    const evs = {};
    players.forEach((player, index) => {
      if (player.id !== 'human') {
        // Simple EV distribution for demo
        const baseEVs = [2.3, 1.1, -0.5];
        evs[player.name] = baseEVs[index - 1] || 0.5;
      }
    });
    evs['Solo'] = 3.5;
    return evs;
  })();

  // Use clean feedback messages from backend
  const feedItems = (gameState?.feedback || []).slice(-4).map((item, index) => {
    const text = typeof item === 'string' ? item : item?.message || 'Game update';
    
    // Determine icon based on message content
    let icon = '📢';
    if (text.includes('🏌️')) icon = '🏌️';
    if (text.includes('🎯')) icon = '🎯';
    if (text.includes('😬')) icon = '😬';
    if (text.includes('🎮')) icon = '🎮';
    
    // Determine impact for color coding
    let impact = null;
    if (text.includes('excellent') || text.includes('Great shot')) impact = '+';
    if (text.includes('poor') || text.includes('Tough break')) impact = '-';
    
    return { icon, text, impact };
  });

  return (
    <div style={styles.container}>
      {/* Top Status Bar */}
      <div style={styles.topBar}>
        <div>Hole {gameState?.current_hole || 1} | Par {gameState?.hole_par || 4} | {gameState?.hole_distance || 435} yards</div>
        <div>Base Wager: ${gameState?.base_wager || 10} | {gameState?.multiplier || '1'}x Active</div>
        <div style={styles.autoPlayControl}>
          {gameState?.hasNextShot && !gameState?.interactionNeeded && (
            <button 
              onClick={handlePlayShot}
              style={{
                background: '#4CAF50',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 'bold',
                fontSize: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginRight: '10px'
              }}
            >
              ⛳ Play Next Shot
            </button>
          )}
          {gameState?.interactionNeeded && (
            <div style={{ 
              color: '#FFD700', 
              fontWeight: 'bold',
              padding: '10px',
              background: 'rgba(255, 215, 0, 0.2)',
              borderRadius: '6px',
              marginRight: '10px'
            }}>
              ⚠️ Decision Required
            </div>
          )}
          <button 
            onClick={exportHoleFeed}
            style={{
              background: '#2196F3',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
            title="Export hole data for analysis"
          >
            📊 Export Feed
          </button>
        </div>
      </div>

      {/* Player Panel */}
      <div style={styles.playerPanel}>
        <h3 style={{ margin: '0 0 15px 0' }}>Players</h3>
        {players.map(player => (
          <div 
            key={player.id}
            style={{
              ...styles.playerCard,
              ...(player.isCurrent ? styles.playerCardActive : {}),
              ...(player.status === 'captain' ? styles.playerCardCaptain : {})
            }}
          >
            <div style={{ fontSize: '18px', marginBottom: '5px' }}>
              {player.id === 'human' ? '👤' : '💻'} {player.name}
            </div>
            <div style={{ fontSize: '14px', color: '#aaa' }}>
              Hdcp: {player.handicap}
            </div>
            <div style={{ fontSize: '16px', fontWeight: 'bold', color: player.points >= 0 ? '#4CAF50' : '#f44336' }}>
              {player.points >= 0 ? '+' : ''}{player.points} pts
            </div>
            {player.status && (
              <div style={{ fontSize: '12px', color: '#FFD700', marginTop: '5px' }}>
                {player.status.toUpperCase()}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Course View */}
      <div style={styles.courseView}>
        <h3 style={{ margin: '0 0 10px 0', color: '#2a2a2a', fontSize: '16px' }}>
          Hole {gameState?.current_hole || 1} Progress
        </h3>
        <div style={{ position: 'relative', height: '240px', background: 'rgba(255,255,255,0.3)', borderRadius: '8px', padding: '15px' }}>
          
          {/* Tee */}
          <div style={{ position: 'absolute', top: '20px', left: '50%', transform: 'translateX(-50%)', textAlign: 'center' }}>
            <div>🚩</div>
            <div style={{ fontSize: '12px', color: '#2a2a2a' }}>Tee</div>
          </div>
          
          {/* Pin */}
          <div style={{ position: 'absolute', bottom: '20px', right: '20px', textAlign: 'center' }}>
            <div style={{ fontSize: '24px' }}>⛳</div>
            <div style={{ fontSize: '12px', color: '#2a2a2a' }}>Pin</div>
          </div>
          
          {/* Ball Positions on Course */}
          {(() => {
            const ballPositions = gameState?.hole_state?.ball_positions || {};
            const maxDistance = 400; // Approximate max hole length for scaling
            
            return Object.entries(ballPositions).map(([playerId, position]) => {
              if (!position || position.distance_to_pin === null) return null;
              
              // Find player info
              const player = players.find(p => p.id === playerId);
              if (!player) return null;
              
              // Calculate position on course (0% = pin, 100% = tee)
              const distancePercent = Math.min(100, (position.distance_to_pin / maxDistance) * 100);
              const leftPosition = 100 - distancePercent; // Flip so pin is right side
              
              // Color coding based on lie type
              let ballColor = '#ffffff';
              let borderColor = '#4CAF50';
              if (position.lie_type === 'rough') {
                ballColor = '#8BC34A';
                borderColor = '#689F38';
              } else if (position.lie_type === 'sand') {
                ballColor = '#FFC107';
                borderColor = '#FF8F00';
              } else if (position.lie_type === 'fairway') {
                ballColor = '#4CAF50';
                borderColor = '#2E7D32';
              }
              
              return (
                <div
                  key={playerId}
                  style={{
                    position: 'absolute',
                    left: `${leftPosition}%`,
                    top: '50%',
                    transform: 'translate(-50%, -50%)',
                    textAlign: 'center',
                    zIndex: 10
                  }}
                >
                  {/* Ball */}
                  <div
                    style={{
                      width: '16px',
                      height: '16px',
                      borderRadius: '50%',
                      background: ballColor,
                      border: `3px solid ${borderColor}`,
                      margin: '0 auto 4px',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
                    }}
                  />
                  {/* Player name */}
                  <div
                    style={{
                      fontSize: '10px',
                      color: '#2a2a2a',
                      fontWeight: 'bold',
                      background: 'rgba(255,255,255,0.9)',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      whiteSpace: 'nowrap'
                    }}
                  >
                    {player.name}
                  </div>
                  {/* Distance */}
                  <div
                    style={{
                      fontSize: '9px',
                      color: '#666',
                      background: 'rgba(255,255,255,0.8)',
                      padding: '1px 4px',
                      borderRadius: '2px',
                      marginTop: '2px'
                    }}
                  >
                    {Math.round(position.distance_to_pin)}yd
                  </div>
                </div>
              );
            });
          })()}
          
          {/* Current Player Indicator */}
          <div style={{
            position: 'absolute',
            bottom: '10px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(0,0,0,0.8)',
            color: 'white',
            padding: '8px 16px',
            borderRadius: '6px',
            textAlign: 'center',
            fontSize: '14px'
          }}>
            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
              Shot #{gameState?.hole_state?.current_shot_number || 1}
            </div>
            <div>
              {gameState?.hole_state?.next_player_to_hit ? 
                `${players.find(p => p.id === gameState.hole_state.next_player_to_hit)?.name || gameState.hole_state.next_player_to_hit}'s turn` : 
                'Ready to play'}
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Panel */}
      <div style={styles.metricsPanel}>
        <h3 style={{ margin: '0 0 15px 0' }}>Live Analytics</h3>
        
        {/* Win Probabilities */}
        <div style={styles.metricSection}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>Win Probability</h4>
          {Object.entries(winProbabilities).map(([player, prob]) => (
            <div key={player}>
              <div style={{ fontSize: '12px', marginBottom: '4px' }}>{player}</div>
              <div style={styles.probabilityBar}>
                <div style={{ ...styles.probabilityFill, width: `${prob}%` }}>
                  {prob}%
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Shot Success */}
        <div style={styles.metricSection}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>Shot Success</h4>
          {Object.entries(shotProbabilities).map(([outcome, prob]) => (
            <div key={outcome} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
              <span style={{ fontSize: '12px' }}>{outcome}</span>
              <span style={{ fontSize: '12px', fontWeight: 'bold' }}>{prob}%</span>
            </div>
          ))}
        </div>

        {/* Partnership EVs */}
        <div style={styles.metricSection}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>Partnership EV</h4>
          {Object.entries(partnershipEVs).map(([partner, ev]) => (
            <div key={partner} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
              <span style={{ fontSize: '12px' }}>{partner}</span>
              <span style={{ 
                fontSize: '12px', 
                fontWeight: 'bold',
                color: ev >= 0 ? '#4CAF50' : '#f44336'
              }}>
                {ev >= 0 ? '+' : ''}{ev}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Action Feed */}
      <div style={styles.actionFeed}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>Action Feed</h4>
        {feedItems.map((item, index) => (
          <div key={index} style={styles.feedItem}>
            <span style={styles.feedIcon}>{item.icon}</span>
            <span style={{ flex: 1 }}>{item.text}</span>
            {item.impact && (
              <span style={{ color: item.impact.startsWith('+') ? '#4CAF50' : '#f44336', fontSize: '12px' }}>
                {item.impact}
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Decision Overlay */}
      {gameState?.interactionNeeded && (
        <div style={styles.decisionOverlay}>
          <div style={styles.decisionPanel}>
            <h2 style={{ margin: '0 0 20px 0', textAlign: 'center' }}>
              🎯 YOUR DECISION AS CAPTAIN
            </h2>
            
            <div 
              style={styles.decisionOption}
              onMouseEnter={(e) => e.currentTarget.style = {...styles.decisionOption, ...styles.decisionOptionHover}}
              onMouseLeave={(e) => e.currentTarget.style = styles.decisionOption}
              onClick={() => onDecision({ type: 'partner', player: 'Clive' })}
            >
              <span>Partner with Clive</span>
              <span style={styles.evBadge}>EV: +2.3</span>
            </div>

            <div 
              style={styles.decisionOption}
              onClick={() => onDecision({ type: 'partner', player: 'Gary' })}
            >
              <span>Partner with Gary</span>
              <span style={styles.evBadge}>EV: +1.1</span>
            </div>

            <div 
              style={styles.decisionOption}
              onClick={() => onDecision({ type: 'partner', player: 'Bernard' })}
            >
              <span>Partner with Bernard</span>
              <span style={{ ...styles.evBadge, ...styles.evBadgeNegative }}>EV: -0.5</span>
            </div>

            <div 
              style={{
                ...styles.decisionOption,
                background: '#4a4530',
                border: '2px solid #FFD700'
              }}
              onClick={() => onDecision({ type: 'solo' })}
            >
              <span><strong>Go Solo (2x Wager)</strong></span>
              <span style={styles.evBadge}>EV: +3.5</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TVPokerLayout;