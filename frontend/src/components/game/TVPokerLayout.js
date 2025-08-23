import React, { useState, useEffect } from 'react';
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
  const theme = useTheme();
  const [selectedOption, setSelectedOption] = useState(null);

  // Handle shot progression button click
  const handlePlayShot = () => {
    if (onPlayNextShot && gameState?.hasNextShot && !gameState?.interactionNeeded) {
      onPlayNextShot();
    }
  };

  const styles = {
    container: {
      display: 'grid',
      gridTemplateColumns: '250px 1fr 300px',
      gridTemplateRows: '60px 1fr 150px',
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
      background: '#2a2a2a',
      borderRadius: '8px',
      padding: '15px',
      overflowY: 'auto',
      boxShadow: '0 2px 10px rgba(0,0,0,0.5)'
    },
    courseView: {
      background: 'linear-gradient(to bottom, #87CEEB, #98D98E)',
      borderRadius: '8px',
      padding: '20px',
      position: 'relative',
      boxShadow: '0 2px 10px rgba(0,0,0,0.5)'
    },
    metricsPanel: {
      background: '#2a2a2a',
      borderRadius: '8px',
      padding: '15px',
      overflowY: 'auto',
      boxShadow: '0 2px 10px rgba(0,0,0,0.5)'
    },
    actionFeed: {
      gridColumn: '1 / -1',
      background: '#2a2a2a',
      borderRadius: '8px',
      padding: '15px',
      overflowY: 'auto',
      maxHeight: '150px',
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

  // Sample data for demonstration
  const players = gameState?.players || [
    { id: 'human', name: 'Stuart', handicap: 18, points: 3, status: 'captain', isCurrent: true },
    { id: 'comp1', name: 'Clive', handicap: 8, points: -2, status: 'partner' },
    { id: 'comp2', name: 'Gary', handicap: 12, points: 1, status: 'opponent' },
    { id: 'comp3', name: 'Bernard', handicap: 15, points: 0, status: 'opponent' }
  ];

  const winProbabilities = probabilities?.win || {
    'Stuart': 28,
    'Clive': 35,
    'Gary': 22,
    'Bernard': 15
  };

  const shotProbabilities = probabilities?.shot || {
    'Great': 15,
    'Good': 45,
    'OK': 30,
    'Poor': 10
  };

  const partnershipEVs = probabilities?.partnerships || {
    'Clive': 2.3,
    'Gary': 1.1,
    'Bernard': -0.5,
    'Solo': 3.5
  };

  const feedItems = [
    { icon: '🏌️', text: 'Stuart hits driver 245 yards to fairway', impact: '+3%' },
    { icon: '📊', text: 'Win probability update: Stuart 28% → 31%' },
    { icon: '🏌️', text: 'Clive hits 3-wood 220 yards to rough', impact: '-3%' },
    { icon: '📊', text: 'Win probability update: Clive 35% → 32%' }
  ];

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
        <h3 style={{ margin: '0 0 15px 0', color: '#2a2a2a' }}>Hole Layout</h3>
        <div style={{ position: 'relative', height: '400px', background: 'rgba(255,255,255,0.3)', borderRadius: '8px', padding: '20px' }}>
          <div style={{ position: 'absolute', top: '20px', left: '50%', transform: 'translateX(-50%)' }}>
            🚩 Tee
          </div>
          <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', fontSize: '24px' }}>
            ⛳ 185 yards to pin
          </div>
          <div style={{ position: 'absolute', bottom: '40px', left: '30%' }}>
            🏌️ Stuart
          </div>
          <div style={{ position: 'absolute', bottom: '40px', left: '45%' }}>
            🏌️ Clive
          </div>
          <div style={{ position: 'absolute', bottom: '40px', left: '60%' }}>
            🏌️ Gary
          </div>
          <div style={{ position: 'absolute', bottom: '40px', left: '75%' }}>
            🏌️ Bernard
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