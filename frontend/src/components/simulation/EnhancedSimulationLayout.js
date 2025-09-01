import React from 'react';
import { useTheme } from '../../theme/Provider';
import { Timeline, PokerBettingPanel } from './';

/**
 * Enhanced Simulation Layout with Timeline and Poker Betting
 * Combines the TV Poker layout with Texas Hold'em style betting and timeline
 */
const EnhancedSimulationLayout = ({
  gameState,
  shotState,
  probabilities,
  onDecision,
  onPlayNextShot,
  timelineEvents = [],
  timelineLoading = false,
  pokerState = {},
  bettingOptions = [],
  onBettingAction,
  currentPlayer = 'human'
}) => {
  // const theme = useTheme(); // Removed - not currently used

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
      shotState: shotState,
      timelineEvents: timelineEvents,
      pokerState: pokerState
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `wgp-hole-${gameState?.current_hole || 1}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Handle shot progression button click
  const handlePlayShot = () => {
    if (onPlayNextShot && gameState?.hasNextShot && !gameState?.interactionNeeded) {
      onPlayNextShot();
    }
  };

  const styles = {
    container: {
      display: 'grid',
      gridTemplateColumns: '2fr 3fr 2fr',
      gridTemplateRows: 'auto 1fr auto',
      gap: '20px',
      padding: '20px',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1a4d2e 0%, #0d2818 100%)',
      color: '#fff',
      fontFamily: 'Arial, sans-serif'
    },
    topBar: {
      gridColumn: '1 / -1',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      background: 'rgba(0,0,0,0.5)',
      padding: '15px 25px',
      borderRadius: '10px',
      fontSize: '16px',
      fontWeight: 'bold'
    },
    leftPanel: {
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    },
    centerPanel: {
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    },
    rightPanel: {
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    },
    playerPanel: {
      background: 'rgba(0,0,0,0.4)',
      padding: '20px',
      borderRadius: '10px',
      border: '2px solid rgba(255,255,255,0.1)'
    },
    playerCard: {
      background: 'rgba(255,255,255,0.1)',
      padding: '15px',
      borderRadius: '8px',
      marginBottom: '10px',
      border: '1px solid rgba(255,255,255,0.2)'
    },
    playerCardActive: {
      border: '2px solid #FFD700',
      background: 'rgba(255, 215, 0, 0.2)'
    },
    courseView: {
      background: 'rgba(76, 175, 80, 0.3)',
      padding: '20px',
      borderRadius: '10px',
      border: '2px solid rgba(76, 175, 80, 0.5)',
      minHeight: '300px'
    },
    metricsPanel: {
      background: 'rgba(0,0,0,0.4)',
      padding: '20px',
      borderRadius: '10px',
      border: '2px solid rgba(255,255,255,0.1)'
    },
    metricSection: {
      marginBottom: '20px'
    },
    probabilityBar: {
      background: 'rgba(255,255,255,0.2)',
      borderRadius: '4px',
      height: '20px',
      marginBottom: '8px',
      overflow: 'hidden'
    },
    probabilityFill: {
      background: 'linear-gradient(90deg, #4CAF50, #2196F3)',
      height: '100%',
      borderRadius: '4px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '12px',
      fontWeight: 'bold',
      color: 'white'
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

  // Generate partnership EVs
  const partnershipEVs = probabilities?.partnerships || (() => {
    const evs = {};
    players.forEach((player, index) => {
      if (player.id !== 'human') {
        const baseEVs = [2.3, 1.1, -0.5];
        evs[player.name] = baseEVs[index - 1] || 0.5;
      }
    });
    evs['Solo'] = 3.5;
    return evs;
  })();

  return (
    <div style={styles.container}>
      {/* Top Status Bar */}
      <div style={styles.topBar}>
        <div>
          Hole {gameState?.current_hole || 1} | Par {gameState?.hole_par || 4} | {gameState?.hole_distance || 435} yards
        </div>
        <div>
          Base Wager: ${gameState?.base_wager || 10} | {gameState?.multiplier || '1'}x Active
        </div>
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
                gap: '8px'
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
              borderRadius: '6px'
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
              fontWeight: 'bold'
            }}
          >
            📊 Export Feed
          </button>
        </div>
      </div>

      {/* Left Panel - Players and Timeline */}
      <div style={styles.leftPanel}>
        {/* Player Panel */}
        <div style={styles.playerPanel}>
          <h3 style={{ margin: '0 0 15px 0' }}>Players</h3>
          {players.map(player => (
            <div 
              key={player.id}
              style={{
                ...styles.playerCard,
                ...(player.isCurrent ? styles.playerCardActive : {})
              }}
            >
              <div style={{ fontSize: '18px', marginBottom: '5px' }}>
                {player.id === 'human' ? '👤' : '💻'} {player.name}
              </div>
              <div style={{ fontSize: '14px', color: '#aaa' }}>
                Hdcp: {player.handicap}
              </div>
              <div style={{ 
                fontSize: '16px', 
                fontWeight: 'bold', 
                color: player.points >= 0 ? '#4CAF50' : '#f44336' 
              }}>
                {player.points >= 0 ? '+' : ''}{player.points} pts
              </div>
            </div>
          ))}
        </div>

        {/* Timeline Component */}
        <div style={{ flex: 1 }}>
          <Timeline 
            events={timelineEvents}
            loading={timelineLoading}
            maxHeight={400}
            autoScroll={true}
            showPokerStyle={true}
          />
        </div>
      </div>

      {/* Center Panel - Course View */}
      <div style={styles.centerPanel}>
        <div style={styles.courseView}>
          <h3 style={{ margin: '0 0 10px 0', color: '#2a2a2a', fontSize: '16px' }}>
            Hole {gameState?.current_hole || 1} Progress
          </h3>
          <div style={{ 
            position: 'relative', 
            height: '240px', 
            background: 'rgba(255,255,255,0.3)', 
            borderRadius: '8px', 
            padding: '15px' 
          }}>
            
            {/* Tee */}
            <div style={{ 
              position: 'absolute', 
              top: '20px', 
              left: '50%', 
              transform: 'translateX(-50%)', 
              textAlign: 'center' 
            }}>
              <div>🚩</div>
              <div style={{ fontSize: '12px', color: '#2a2a2a' }}>Tee</div>
            </div>
            
            {/* Pin */}
            <div style={{ 
              position: 'absolute', 
              bottom: '20px', 
              right: '20px', 
              textAlign: 'center' 
            }}>
              <div style={{ fontSize: '24px' }}>⛳</div>
              <div style={{ fontSize: '12px', color: '#2a2a2a' }}>Pin</div>
            </div>
            
            {/* Ball Positions */}
            {(() => {
              const ballPositions = gameState?.hole_state?.ball_positions || {};
              const maxDistance = 400;
              
              return Object.entries(ballPositions).map(([playerId, position]) => {
                if (!position || position.distance_to_pin === null) return null;
                
                const player = players.find(p => p.id === playerId);
                if (!player) return null;
                
                const distancePercent = Math.min(100, (position.distance_to_pin / maxDistance) * 100);
                const leftPosition = 100 - distancePercent;
                
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
                    <div style={{
                      fontSize: '10px',
                      background: 'rgba(0,0,0,0.8)',
                      color: 'white',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      whiteSpace: 'nowrap'
                    }}>
                      {player.name}
                    </div>
                    <div style={{
                      fontSize: '9px',
                      color: '#2a2a2a',
                      marginTop: '2px'
                    }}>
                      {Math.round(position.distance_to_pin)}yd
                    </div>
                  </div>
                );
              });
            })()}

            {/* Shot Info */}
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

        {/* Poker Betting Panel */}
        <div style={{ flex: 1 }}>
          <PokerBettingPanel
            pokerState={pokerState}
            bettingOptions={bettingOptions}
            onBettingAction={onBettingAction}
            currentPlayer={currentPlayer}
            disabled={!gameState?.interactionNeeded && bettingOptions.length === 0}
          />
        </div>
      </div>

      {/* Right Panel - Analytics */}
      <div style={styles.rightPanel}>
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
              <div key={outcome} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                marginBottom: '5px' 
              }}>
                <span style={{ fontSize: '12px' }}>{outcome}</span>
                <span style={{ fontSize: '12px', fontWeight: 'bold' }}>{prob}%</span>
              </div>
            ))}
          </div>

          {/* Partnership EVs */}
          <div style={styles.metricSection}>
            <h4 style={{ margin: '0 0 10px 0', fontSize: '14px' }}>Partnership EV</h4>
            {Object.entries(partnershipEVs).map(([partner, ev]) => (
              <div key={partner} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                marginBottom: '5px' 
              }}>
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
      </div>
    </div>
  );
};

export default EnhancedSimulationLayout;