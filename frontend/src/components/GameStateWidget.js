import React from 'react';

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

const GameStateWidget = ({ gameState, holeState, onAction }) => {
  // Use holeState from props or fallback to gameState.hole_state
  const effectiveHoleState = holeState || gameState?.hole_state;
  
  if (!gameState || !effectiveHoleState) return null;

  const getPhaseColor = (phase) => {
    switch (phase) {
      case 'regular': return COLORS.primary;
      case 'vinnie_variation': return COLORS.vinnie;
      case 'hoepfinger': return COLORS.hoepfinger;
      default: return COLORS.muted;
    }
  };

  const getPhaseIcon = (phase) => {
    switch (phase) {
      case 'regular': return '🏌️';
      case 'vinnie_variation': return '🎯';
      case 'hoepfinger': return '👑';
      default: return '❓';
    }
  };

  const getTeamTypeIcon = (type) => {
    switch (type) {
      case 'partners': return '🤝';
      case 'solo': return '👤';
      case 'pending': return '⏳';
      default: return '❓';
    }
  };

  return (
    <div style={{
      background: COLORS.card,
      borderRadius: 16,
      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
      padding: 20,
      margin: '12px 0'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            background: getPhaseColor(gameState.game_phase),
            color: 'white',
            width: 48,
            height: 48,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 24
          }}>
            {getPhaseIcon(gameState.game_phase)}
          </div>
          <div>
            <h2 style={{ margin: 0, color: COLORS.text }}>
              Hole {gameState.current_hole}
            </h2>
            <div style={{ color: COLORS.muted, fontSize: 14 }}>
              {gameState.game_phase?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Regular Play'}
            </div>
          </div>
        </div>
        
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 24, fontWeight: 600, color: COLORS.text }}>
            Par {effectiveHoleState.hole_par || 4}
          </div>
          <div style={{ fontSize: 14, color: COLORS.muted }}>
            Stroke Index {effectiveHoleState.stroke_index || 'N/A'}
          </div>
        </div>
      </div>

      {/* Hole Information Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: 16,
        marginBottom: 20
      }}>
        {/* Team Formation */}
        <div style={{
          background: '#f8f9fa',
          padding: 16,
          borderRadius: 12,
          border: `2px solid ${effectiveHoleState.teams?.type === 'pending' ? COLORS.warning : COLORS.success}`
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{ fontSize: 20 }}>{getTeamTypeIcon(effectiveHoleState.teams.type)}</span>
            <h4 style={{ margin: 0, color: COLORS.text }}>
              Team Formation
            </h4>
          </div>
          
          {effectiveHoleState.teams.type === 'partners' && (
            <div>
              <div style={{ marginBottom: 8 }}>
                <strong style={{ color: COLORS.primary }}>Team 1:</strong> {effectiveHoleState.teams.team1.join(', ')}
              </div>
              <div>
                <strong style={{ color: COLORS.accent }}>Team 2:</strong> {effectiveHoleState.teams.team2.join(', ')}
              </div>
            </div>
          )}
          
          {effectiveHoleState.teams.type === 'solo' && (
            <div>
              <div style={{ marginBottom: 8 }}>
                <strong style={{ color: COLORS.primary }}>Solo:</strong> {effectiveHoleState.teams.solo_player}
              </div>
              <div>
                <strong style={{ color: COLORS.accent }}>Opponents:</strong> {effectiveHoleState.teams.opponents.join(', ')}
              </div>
            </div>
          )}
          
          {effectiveHoleState.teams.type === 'pending' && (
            <div style={{ color: COLORS.warning, fontStyle: 'italic' }}>
              Waiting for team formation...
            </div>
          )}
        </div>

        {/* Betting State */}
        <div style={{
          background: '#f8f9fa',
          padding: 16,
          borderRadius: 12
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{ fontSize: 20 }}>💰</span>
            <h4 style={{ margin: 0, color: COLORS.text }}>
              Betting State
            </h4>
          </div>
          
          <div style={{ marginBottom: 8 }}>
            <strong>Current Wager:</strong> {effectiveHoleState.betting.current_wager} quarters
          </div>
          
          <div style={{ marginBottom: 8 }}>
            <strong>Base Wager:</strong> {effectiveHoleState.betting.base_wager} quarters
          </div>
          
          {effectiveHoleState.betting.doubled && (
            <div style={{ color: COLORS.warning, fontWeight: 600 }}>
              ⚡ Doubled!
            </div>
          )}
          
          {effectiveHoleState.betting.redoubled && (
            <div style={{ color: COLORS.error, fontWeight: 600 }}>
              ⚡⚡ Redoubled!
            </div>
          )}
        </div>

        {/* Shot Progression */}
        <div style={{
          background: '#f8f9fa',
          padding: 16,
          borderRadius: 12
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <span style={{ fontSize: 20 }}>🎯</span>
            <h4 style={{ margin: 0, color: COLORS.text }}>
              Shot Progression
            </h4>
          </div>
          
          <div style={{ marginBottom: 8 }}>
            <strong>Shot #{effectiveHoleState.current_shot_number}</strong>
          </div>
          
          <div style={{ marginBottom: 8 }}>
            <strong>Next to Hit:</strong> {effectiveHoleState.next_player_to_hit || 'TBD'}
          </div>
          
          <div style={{ marginBottom: 8 }}>
            <strong>Line of Scrimmage:</strong> {effectiveHoleState.line_of_scrimmage || 'Not set'}
          </div>
          
          {effectiveHoleState.hole_complete && (
            <div style={{ color: COLORS.success, fontWeight: 600 }}>
              ✅ Hole Complete!
            </div>
          )}
        </div>
      </div>

      {/* Stroke Advantages */}
      {effectiveHoleState.stroke_advantages && Object.keys(effectiveHoleState.stroke_advantages).length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ margin: '0 0 12px 0', color: COLORS.text }}>
            🎯 Handicap Stroke Advantages (Creecher Feature)
          </h4>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 12
          }}>
            {gameState.players.map((player) => {
              const strokeAdv = effectiveHoleState.stroke_advantages[player.id];
              if (!strokeAdv) return null;
              
              return (
                <div key={player.id} style={{
                  background: strokeAdv.strokes_received > 0 ? '#e3f2fd' : '#f5f5f5',
                  padding: 12,
                  borderRadius: 8,
                  border: strokeAdv.strokes_received > 0 ? `2px solid ${COLORS.accent}` : '2px solid transparent'
                }}>
                  <div style={{ fontWeight: 600, color: COLORS.text, marginBottom: 4 }}>
                    {player.name}
                  </div>
                  
                  <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                    Handicap: {player.handicap}
                  </div>
                  
                  <div style={{ 
                    fontSize: 14, 
                    color: strokeAdv.strokes_received > 0 ? COLORS.accent : COLORS.muted,
                    fontWeight: 'bold'
                  }}>
                    {strokeAdv.strokes_received > 0 ? (
                      <>
                        {strokeAdv.strokes_received === 1 ? '● Full Stroke' : 
                         strokeAdv.strokes_received === 0.5 ? '◐ Half Stroke' : 
                         `● ${strokeAdv.strokes_received} Strokes`}
                      </>
                    ) : (
                      'No Strokes'
                    )}
                  </div>
                  
                  <div style={{ fontSize: 11, color: COLORS.muted, marginTop: 4 }}>
                    Stroke Index {effectiveHoleState.stroke_index}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Player Status */}
      <div style={{ marginBottom: 20 }}>
        <h4 style={{ margin: '0 0 12px 0', color: COLORS.text }}>
          👥 Player Status
        </h4>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: 12
        }}>
          {gameState.players.map((player) => {
            const ballPosition = effectiveHoleState.ball_positions[player.id];
            const strokeAdv = effectiveHoleState.stroke_advantages[player.id];
            
            return (
              <div key={player.id} style={{
                background: '#f8f9fa',
                padding: 12,
                borderRadius: 8,
                border: ballPosition ? `2px solid ${COLORS.primary}` : '2px solid transparent'
              }}>
                <div style={{ fontWeight: 600, color: COLORS.text, marginBottom: 4 }}>
                  {player.name}
                </div>
                
                <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                  Handicap: {player.handicap} | Points: {player.points}
                </div>
                
                {strokeAdv && (
                  <div style={{ 
                    fontSize: 12, 
                    color: strokeAdv.strokes_received > 0 ? COLORS.accent : COLORS.muted, 
                    marginBottom: 4,
                    fontWeight: strokeAdv.strokes_received > 0 ? 'bold' : 'normal'
                  }}>
                    {strokeAdv.strokes_received > 0 ? (
                      <>
                        {strokeAdv.strokes_received === 1 ? '●' : 
                         strokeAdv.strokes_received === 0.5 ? '◐' : 
                         `●x${strokeAdv.strokes_received}`} 
                        +{strokeAdv.strokes_received} strokes
                      </>
                    ) : (
                      'No strokes'
                    )}
                  </div>
                )}
                
                {ballPosition ? (
                  <div style={{ fontSize: 12, color: COLORS.primary }}>
                    {Math.round(ballPosition.distance_to_pin)} yds • Shot #{ballPosition.shot_count}
                  </div>
                ) : (
                  <div style={{ fontSize: 12, color: COLORS.muted }}>
                    Not yet hit
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Special Rules */}
      {effectiveHoleState.betting.special_rules && Object.values(effectiveHoleState.betting.special_rules).some(rule => rule) && (
        <div style={{
          background: '#fff3cd',
          border: `1px solid ${COLORS.warning}`,
          borderRadius: 8,
          padding: 12,
          marginTop: 16
        }}>
          <h4 style={{ margin: '0 0 8px 0', color: COLORS.warning }}>
            ⚡ Special Rules Active
          </h4>
          <div style={{ fontSize: 14 }}>
            {effectiveHoleState.betting.special_rules.float_invoked && '🦅 Float Invoked • '}
            {effectiveHoleState.betting.special_rules.option_invoked && '🎯 Option Invoked • '}
            {effectiveHoleState.betting.special_rules.duncan_invoked && '👑 Duncan Invoked • '}
            {effectiveHoleState.betting.special_rules.tunkarri_invoked && '🦘 Tunkarri Invoked'}
          </div>
        </div>
      )}
    </div>
  );
};

export default GameStateWidget; 