import React from 'react';
import './HoleStrategyDisplay.css';

const HoleStrategyDisplay = ({ holeState, players, gameState }) => {
  if (!holeState || !players) return null;

  const currentHole = gameState?.current_hole || 1;
  const par = holeState.hole_par || 4;
  const yardage = holeState.hole_yardage || 400;
  const handicap = holeState.hole_handicap || 10;
  
  // Get ball positions with defaults
  const positions = holeState.ball_positions || {};
  
  // Calculate who's away (furthest from hole)
  const awayPlayer = Object.entries(positions).reduce((furthest, [playerId, position]) => {
    if (!furthest || position.distance_to_pin > furthest.distance) {
      return { playerId, distance: position.distance_to_pin, position };
    }
    return furthest;
  }, null);

  // Get current betting state
  const bettingState = holeState.betting || {};
  const currentWager = bettingState.current_wager || 1;
  const partnerships = bettingState.partnerships || [];
  const doublesOffered = bettingState.doubles_offered || [];
  
  // Determine hole difficulty
  const getDifficulty = (handicap) => {
    if (handicap <= 6) return { level: 'HARD', color: '#e74c3c', icon: '🔥' };
    if (handicap <= 12) return { level: 'MEDIUM', color: '#f39c12', icon: '⚡' };
    return { level: 'EASY', color: '#27ae60', icon: '✨' };
  };
  
  const difficulty = getDifficulty(handicap);
  
  // Get player status and position
  const getPlayerStatus = (playerId) => {
    const position = positions[playerId];
    if (!position) return { status: 'waiting', color: '#95a5a6' };
    
    if (position.holed) return { status: 'holed', color: '#27ae60', icon: '🏆' };
    if (position.distance_to_pin <= 10) return { status: 'tap-in', color: '#3498db', icon: '👍' };
    if (position.lie_type === 'bunker') return { status: 'trouble', color: '#e74c3c', icon: '⚠️' };
    if (position.lie_type === 'rough') return { status: 'rough', color: '#f39c12', icon: '🌾' };
    if (position.lie_type === 'green') return { status: 'putting', color: '#27ae60', icon: '🎯' };
    return { status: 'fairway', color: '#2ecc71', icon: '✓' };
  };
  
  // Sort players by distance from hole
  const sortedPlayers = [...players].sort((a, b) => {
    const posA = positions[a.id]?.distance_to_pin || 999;
    const posB = positions[b.id]?.distance_to_pin || 999;
    return posA - posB;
  });

  return (
    <div className="hole-strategy-display">
      {/* Hole Header */}
      <div className="hole-header">
        <div className="hole-number">
          <span className="hole-label">HOLE</span>
          <span className="hole-value">{currentHole}</span>
        </div>
        
        <div className="hole-stats">
          <div className="stat-item">
            <span className="stat-label">PAR</span>
            <span className="stat-value">{par}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">YARDS</span>
            <span className="stat-value">{yardage}</span>
          </div>
          <div className={`difficulty-badge ${difficulty.level.toLowerCase()}`}>
            <span className="difficulty-icon">{difficulty.icon}</span>
            <span className="difficulty-text">{difficulty.level}</span>
          </div>
        </div>

        <div className="wager-display">
          <span className="wager-label">POT</span>
          <div className="wager-value">
            <span className="wager-amount">{currentWager}</span>
            <span className="wager-unit">quarters</span>
          </div>
        </div>
      </div>

      {/* Player Positions Grid */}
      <div className="players-grid">
        {sortedPlayers.map((player, index) => {
          const position = positions[player.id];
          const status = getPlayerStatus(player.id);
          const isAway = awayPlayer?.playerId === player.id;
          const shotCount = position?.shot_count || 0;
          const distance = position?.distance_to_pin || '--';
          
          return (
            <div 
              key={player.id} 
              className={`player-card ${isAway ? 'is-away' : ''} ${status.status}`}
            >
              <div className="player-rank">{index + 1}</div>
              
              <div className="player-info">
                <div className="player-name">{player.name}</div>
                <div className="player-stats">
                  <span className="shot-count">
                    {shotCount > 0 ? `${shotCount} ${shotCount === 1 ? 'shot' : 'shots'}` : 'Ready'}
                  </span>
                  {status.icon && <span className="status-icon">{status.icon}</span>}
                </div>
              </div>
              
              <div className="distance-info">
                <div className="distance-value">
                  {position?.holed ? 'IN' : distance}
                </div>
                {!position?.holed && (
                  <div className="distance-label">yards</div>
                )}
              </div>
              
              {isAway && (
                <div className="away-indicator">
                  <span>AWAY</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Active Partnerships */}
      {partnerships.length > 0 && (
        <div className="partnerships-section">
          <div className="section-title">Active Partnerships</div>
          <div className="partnerships-list">
            {partnerships.map((partnership, idx) => (
              <div key={idx} className="partnership-badge">
                <span className="partnership-icon">🤝</span>
                <span className="partnership-players">
                  {partnership.player1} & {partnership.player2}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Betting Actions */}
      {doublesOffered.length > 0 && (
        <div className="betting-section">
          <div className="section-title">Doubles Offered</div>
          <div className="doubles-list">
            {doublesOffered.map((double, idx) => (
              <div key={idx} className="double-badge">
                <span className="double-icon">2️⃣</span>
                <span className="double-player">{double.player}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Strategic Tips */}
      <div className="strategy-tips">
        <div className="tip-item">
          <span className="tip-icon">💡</span>
          <span className="tip-text">
            {difficulty.level === 'HARD' 
              ? "Tough hole - consider partnership to share risk"
              : difficulty.level === 'EASY'
              ? "Scoring opportunity - going solo could pay off"
              : "Balanced hole - play to your strengths"}
          </span>
        </div>
        
        {awayPlayer && (
          <div className="tip-item">
            <span className="tip-icon">📍</span>
            <span className="tip-text">
              {players.find(p => p.id === awayPlayer.playerId)?.name} is away at {awayPlayer.distance} yards
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default HoleStrategyDisplay;