import React, { useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || '';

const COLORS = {
  primary: '#1976d2',
  accent: '#00bcd4',
  warning: '#ff9800',
  error: '#d32f2f',
  success: '#388e3c',
  bg: '#f9fafe',
  card: '#fff',
  border: '#e0e0e0',
  text: '#222',
  muted: '#888',
  hoepfinger: '#9c27b0',
  vinnie: '#795548'
};

const cardStyle = {
  background: COLORS.card,
  borderRadius: 12,
  boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
  padding: 16,
  marginBottom: 18,
  border: `1px solid ${COLORS.border}`,
};

const buttonStyle = {
  background: COLORS.primary,
  color: '#fff',
  border: 'none',
  borderRadius: 8,
  padding: '12px 20px',
  fontWeight: 600,
  fontSize: 16,
  margin: '4px',
  cursor: 'pointer',
  transition: 'background 0.2s',
};

const WolfGoatPigGame = () => {
  const [gameState, setGameState] = useState(null);
  const [playerCount, setPlayerCount] = useState(4);
  const [players, setPlayers] = useState([]);
  const [gameStarted, setGameStarted] = useState(false);
  const [currentAction, setCurrentAction] = useState(null);
  const [message, setMessage] = useState('');
  const [scores, setScores] = useState({});
  const [showRules, setShowRules] = useState(false);

  useEffect(() => {
    // Initialize default players based on count
    const defaultNames = ['Bob', 'Scott', 'Vince', 'Mike', 'Terry', 'Bill'];
    const defaultHandicaps = [10.5, 15, 8, 20.5, 12, 18];
    
    const newPlayers = Array.from({ length: playerCount }, (_, i) => ({
      id: `p${i + 1}`,
      name: defaultNames[i] || `Player ${i + 1}`,
      handicap: defaultHandicaps[i] || 15
    }));
    
    setPlayers(newPlayers);
  }, [playerCount]);

  const startGame = async () => {
    try {
      const response = await fetch(`${API_URL}/wgp/start-game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_count: playerCount,
          players: players,
          double_points_round: false,
          annual_banquet: false
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setGameState(data.game_state);
        setGameStarted(true);
        setMessage('Game started! Time to toss the tees!');
      } else {
        setMessage('Error starting game');
      }
    } catch (error) {
      setMessage('Network error starting game');
    }
  };

  const makeAction = async (action, params = {}) => {
    try {
      const response = await fetch(`${API_URL}/wgp/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      
      if (response.ok) {
        const data = await response.json();
        setGameState(data.game_state || gameState);
        setMessage(data.message || 'Action completed');
        setCurrentAction(null);
        
        // Update UI based on action result
        if (data.status === 'pending') {
          setCurrentAction({
            type: action,
            awaiting: data.awaiting_response,
            ...data
          });
        }
      } else {
        const error = await response.json();
        setMessage(`Error: ${error.detail || 'Action failed'}`);
      }
    } catch (error) {
      setMessage('Network error');
    }
  };

  const submitScores = async () => {
    try {
      const response = await fetch(`${API_URL}/wgp/enter-scores`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scores })
      });
      
      if (response.ok) {
        const data = await response.json();
        setGameState(data.game_state);
        setMessage(data.message);
        setScores({});
        
        // Check if game is finished
        if (data.status === 'game_finished') {
          setMessage(`Game finished! Winner(s): ${data.winner_names.join(', ')}`);
        }
      } else {
        setMessage('Error submitting scores');
      }
    } catch (error) {
      setMessage('Network error submitting scores');
    }
  };

  const advanceHole = async () => {
    await makeAction('advance-hole');
  };

  const renderGameSetup = () => (
    <div style={cardStyle}>
      <h2>Wolf Goat Pig Game Setup</h2>
      
      <div style={{ marginBottom: 20 }}>
        <label>Number of Players: </label>
        <select 
          value={playerCount} 
          onChange={(e) => setPlayerCount(Number(e.target.value))}
          style={{ padding: 8, margin: '0 10px' }}
        >
          <option value={4}>4 Players</option>
          <option value={5}>5 Players</option>
          <option value={6}>6 Players</option>
        </select>
      </div>

      <div style={{ marginBottom: 20 }}>
        <h3>Player Configuration</h3>
        {players.map((player, index) => (
          <div key={player.id} style={{ margin: '10px 0', display: 'flex', alignItems: 'center' }}>
            <span style={{ width: 60 }}>P{index + 1}:</span>
            <input
              type="text"
              value={player.name}
              onChange={(e) => {
                const newPlayers = [...players];
                newPlayers[index].name = e.target.value;
                setPlayers(newPlayers);
              }}
              style={{ padding: 8, margin: '0 10px', width: 120 }}
              placeholder="Name"
            />
            <input
              type="number"
              value={player.handicap}
              onChange={(e) => {
                const newPlayers = [...players];
                newPlayers[index].handicap = parseFloat(e.target.value) || 0;
                setPlayers(newPlayers);
              }}
              style={{ padding: 8, margin: '0 10px', width: 80 }}
              placeholder="HCP"
              step="0.5"
            />
          </div>
        ))}
      </div>

      <button onClick={startGame} style={buttonStyle}>
        Start Wolf Goat Pig Game
      </button>
      
      <button 
        onClick={() => setShowRules(!showRules)} 
        style={{...buttonStyle, background: COLORS.accent, marginLeft: 10}}
      >
        {showRules ? 'Hide Rules' : 'Show Rules'}
      </button>
      
      {showRules && renderRulesReference()}
    </div>
  );

  const renderRulesReference = () => (
    <div style={{...cardStyle, marginTop: 20, maxHeight: 400, overflow: 'auto'}}>
      <h3>Wolf Goat Pig Rules Summary</h3>
      <div style={{ fontSize: 14, lineHeight: 1.6 }}>
        <h4>Basic Game Flow:</h4>
        <ul>
          <li><strong>Captain:</strong> First player in hitting order each hole</li>
          <li><strong>Partnership:</strong> Captain may request a partner for best ball</li>
          <li><strong>Solo (Pig):</strong> Captain or Aardvark may go alone vs. others</li>
          <li><strong>Aardvark:</strong> 5th/6th players in 5/6-man games</li>
        </ul>
        
        <h4>Special Phases:</h4>
        <ul>
          <li><strong>Vinnie's Variation:</strong> Holes 13-16 in 4-man (double base bet)</li>
          <li><strong>Hoepfinger:</strong> Final holes - Goat chooses hitting position</li>
          <li><strong>Joe's Special:</strong> Goat sets hole value in Hoepfinger (2, 4, or 8 quarters)</li>
        </ul>
        
        <h4>Betting Rules:</h4>
        <ul>
          <li><strong>The Float:</strong> Captain may double base wager (once per round)</li>
          <li><strong>The Option:</strong> Auto-double if Captain is furthest down</li>
          <li><strong>Doubles:</strong> Teams may offer/accept doubles during play</li>
          <li><strong>The Duncan/Tunkarri:</strong> 3-for-2 payout when going solo</li>
          <li><strong>Karl Marx Rule:</strong> Furthest down player pays/receives less</li>
        </ul>
      </div>
    </div>
  );

  const renderGameState = () => {
    if (!gameState) return null;

    const { current_hole, game_phase, players, hole_state } = gameState;
    const { hitting_order, teams, betting } = hole_state || {};

    return (
      <div>
        {/* Game Header */}
        <div style={{...cardStyle, background: getPhaseColor(game_phase)}}>
          <h2 style={{ color: '#fff', margin: 0 }}>
            Hole {current_hole} - {getPhaseDisplayName(game_phase)}
          </h2>
          <div style={{ color: '#fff', marginTop: 8 }}>
            Base Wager: {betting?.base_wager || 1} quarters | 
            Current Wager: {betting?.current_wager || 1} quarters
            {betting?.special_rules && renderSpecialRules(betting.special_rules)}
          </div>
        </div>

        {/* Player Standings */}
        <div style={cardStyle}>
          <h3>Player Standings</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
            {players?.map(player => (
              <div key={player.id} style={{
                padding: 10,
                border: `2px solid ${player.points < 0 ? COLORS.error : COLORS.success}`,
                borderRadius: 8,
                background: player.points === Math.min(...players.map(p => p.points)) ? '#ffebee' : '#fff'
              }}>
                <div style={{ fontWeight: 'bold' }}>{player.name}</div>
                <div>Points: {player.points}</div>
                <div>HCP: {player.handicap}</div>
                <div style={{ fontSize: 12, color: COLORS.muted }}>
                  {player.float_used && '🏃 Float Used'} 
                  {player.solo_count > 0 && ` 🐷 Solo: ${player.solo_count}`}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Hitting Order */}
        {hitting_order && (
          <div style={cardStyle}>
            <h3>Hitting Order</h3>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {hitting_order.map((playerId, index) => {
                const player = players?.find(p => p.id === playerId);
                const isCaptain = index === 0;
                const isAardvark = isPlayerAardvark(index, playerCount);
                const isGoat = player && player.points === Math.min(...players.map(p => p.points));
                
                return (
                  <div key={playerId} style={{
                    padding: '8px 12px',
                    borderRadius: 8,
                    background: isCaptain ? COLORS.primary : isAardvark ? COLORS.warning : COLORS.bg,
                    color: isCaptain || isAardvark ? '#fff' : COLORS.text,
                    border: isGoat ? `3px solid ${COLORS.error}` : 'none'
                  }}>
                    <div style={{ fontWeight: 'bold' }}>
                      {index + 1}. {player?.name}
                      {isCaptain && ' 👑'}
                      {isAardvark && ' 🐘'}
                      {isGoat && ' 🐐'}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Team Formation & Actions */}
        {renderTeamFormation()}
        
        {/* Current Action */}
        {renderCurrentAction()}

        {/* Score Entry */}
        {renderScoreEntry()}

        {/* Message */}
        {message && (
          <div style={{
            ...cardStyle,
            background: message.includes('Error') ? COLORS.error : COLORS.success,
            color: '#fff'
          }}>
            {message}
          </div>
        )}
      </div>
    );
  };

  const renderTeamFormation = () => {
    if (!gameState?.hole_state?.teams) return null;

    const { teams, betting } = gameState.hole_state;
    const { players } = gameState;

    return (
      <div style={cardStyle}>
        <h3>Team Formation</h3>
        
        {teams.type === 'pending' && (
          <div>
            <p>Captain {getPlayerName(teams.captain)} needs to choose:</p>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button 
                onClick={() => makeAction('captain-go-solo', { captain_id: teams.captain })}
                style={{...buttonStyle, background: COLORS.warning}}
              >
                Go Solo (Pig) 🐷
              </button>
              
              {players?.filter(p => p.id !== teams.captain).map(player => (
                <button
                  key={player.id}
                  onClick={() => makeAction('request-partner', { 
                    captain_id: teams.captain, 
                    partner_id: player.id 
                  })}
                  style={buttonStyle}
                >
                  Partner with {player.name}
                </button>
              ))}
              
              {!betting?.float_invoked && (
                <button
                  onClick={() => makeAction('invoke-float', { captain_id: teams.captain })}
                  style={{...buttonStyle, background: COLORS.accent}}
                >
                  Invoke Float 🏃
                </button>
              )}
            </div>
          </div>
        )}

        {teams.type === 'partners' && (
          <div>
            <div style={{ display: 'flex', gap: 20 }}>
              <div style={{ 
                padding: 10, 
                border: `2px solid ${COLORS.primary}`, 
                borderRadius: 8,
                background: '#e3f2fd'
              }}>
                <strong>Team 1:</strong> {teams.team1?.map(id => getPlayerName(id)).join(' & ')}
              </div>
              <div style={{ 
                padding: 10, 
                border: `2px solid ${COLORS.error}`, 
                borderRadius: 8,
                background: '#ffebee'
              }}>
                <strong>Team 2:</strong> {teams.team2?.map(id => getPlayerName(id)).join(' & ')}
              </div>
            </div>
          </div>
        )}

        {teams.type === 'solo' && (
          <div>
            <div style={{ 
              padding: 10, 
              border: `2px solid ${COLORS.warning}`, 
              borderRadius: 8,
              background: '#fff3e0',
              marginBottom: 10
            }}>
              <strong>Solo Player:</strong> {getPlayerName(teams.solo_player)} 🐷
            </div>
            <div style={{ 
              padding: 10, 
              border: `2px solid ${COLORS.primary}`, 
              borderRadius: 8,
              background: '#e3f2fd'
            }}>
              <strong>Opponents:</strong> {teams.opponents?.map(id => getPlayerName(id)).join(', ')}
            </div>
          </div>
        )}

        {/* Betting Actions */}
        {renderBettingActions()}
      </div>
    );
  };

  const renderBettingActions = () => {
    const { teams, betting } = gameState.hole_state;
    
    if (teams.type === 'pending') return null;

    return (
      <div style={{ marginTop: 15 }}>
        <h4>Betting Actions</h4>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {!betting?.doubled && (
            <button
              onClick={() => makeAction('offer-double')}
              style={{...buttonStyle, background: COLORS.warning}}
            >
              Offer Double
            </button>
          )}
          
          {betting?.doubled && (
            <>
              <button
                onClick={() => makeAction('accept-double')}
                style={{...buttonStyle, background: COLORS.success}}
              >
                Accept Double
              </button>
              <button
                onClick={() => makeAction('decline-double')}
                style={{...buttonStyle, background: COLORS.error}}
              >
                Decline Double
              </button>
            </>
          )}
        </div>
      </div>
    );
  };

  const renderCurrentAction = () => {
    if (!currentAction) return null;

    return (
      <div style={{...cardStyle, background: '#fff3e0', border: `2px solid ${COLORS.warning}`}}>
        <h3>Action Required</h3>
        <p>{currentAction.message}</p>
        
        {currentAction.type === 'request-partner' && currentAction.awaiting_response && (
          <div>
            <p>Waiting for {getPlayerName(currentAction.awaiting_response)} to respond...</p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                onClick={() => makeAction('respond-partnership', {
                  partner_id: currentAction.awaiting_response,
                  accept: true
                })}
                style={{...buttonStyle, background: COLORS.success}}
              >
                Accept Partnership
              </button>
              <button
                onClick={() => makeAction('respond-partnership', {
                  partner_id: currentAction.awaiting_response,
                  accept: false
                })}
                style={{...buttonStyle, background: COLORS.error}}
              >
                Decline Partnership
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderScoreEntry = () => {
    const { teams } = gameState?.hole_state || {};
    
    if (teams?.type === 'pending') return null;

    return (
      <div style={cardStyle}>
        <h3>Enter Hole Scores</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
          {gameState?.players?.map(player => (
            <div key={player.id} style={{ padding: 10, border: `1px solid ${COLORS.border}`, borderRadius: 8 }}>
              <label style={{ display: 'block', marginBottom: 5, fontWeight: 'bold' }}>
                {player.name}:
              </label>
              <input
                type="number"
                value={scores[player.id] || ''}
                onChange={(e) => setScores({
                  ...scores,
                  [player.id]: parseInt(e.target.value) || 0
                })}
                style={{ padding: 8, width: '100%' }}
                placeholder="Score"
                min="1"
                max="15"
              />
            </div>
          ))}
        </div>
        
        <div style={{ marginTop: 15 }}>
          <button
            onClick={submitScores}
            disabled={Object.keys(scores).length !== gameState?.players?.length}
            style={{
              ...buttonStyle,
              background: Object.keys(scores).length === gameState?.players?.length 
                ? COLORS.success 
                : COLORS.muted
            }}
          >
            Submit Scores
          </button>
          
          {gameState?.current_hole < 18 && (
            <button
              onClick={advanceHole}
              style={{...buttonStyle, background: COLORS.accent, marginLeft: 10}}
            >
              Next Hole →
            </button>
          )}
        </div>
      </div>
    );
  };

  const renderSpecialRules = (specialRules) => {
    const active = Object.entries(specialRules).filter(([key, value]) => value);
    if (active.length === 0) return null;

    return (
      <div style={{ marginTop: 5, fontSize: 12 }}>
        {active.map(([rule, value]) => (
          <span key={rule} style={{ marginRight: 10 }}>
            {getSpecialRuleDisplay(rule, value)}
          </span>
        ))}
      </div>
    );
  };

  // Helper functions
  const getPlayerName = (playerId) => {
    const player = gameState?.players?.find(p => p.id === playerId);
    return player?.name || playerId;
  };

  const isPlayerAardvark = (index, playerCount) => {
    if (playerCount === 4) return false;
    if (playerCount === 5) return index === 4;
    return index === 4 || index === 5;
  };

  const getPhaseColor = (phase) => {
    switch (phase) {
      case 'hoepfinger': return COLORS.hoepfinger;
      case 'vinnie_variation': return COLORS.vinnie;
      default: return COLORS.primary;
    }
  };

  const getPhaseDisplayName = (phase) => {
    switch (phase) {
      case 'hoepfinger': return 'Hoepfinger Phase';
      case 'vinnie_variation': return "Vinnie's Variation";
      default: return 'Regular Play';
    }
  };

  const getSpecialRuleDisplay = (rule, value) => {
    const displays = {
      float_invoked: '🏃 Float',
      option_invoked: '⚡ Option',
      duncan_invoked: '👑 Duncan',
      tunkarri_invoked: '🐘 Tunkarri',
      joes_special_value: `🎯 Joe's Special: ${value}`
    };
    return displays[rule] || `${rule}: ${value}`;
  };

  return (
    <div style={{ padding: 20, background: COLORS.bg, minHeight: '100vh' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <h1 style={{ textAlign: 'center', color: COLORS.primary, marginBottom: 30 }}>
          🐺 Wolf Goat Pig 🐐 🐷
        </h1>
        
        {!gameStarted ? renderGameSetup() : renderGameState()}
      </div>
    </div>
  );
};

export default WolfGoatPigGame;