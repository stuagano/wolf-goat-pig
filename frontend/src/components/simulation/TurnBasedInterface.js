import React, { useState, useEffect } from 'react';
import { useTheme } from '../../theme/Provider';
import { Button, Card } from '../ui';

const TurnBasedInterface = ({
  gameState,
  onMakeDecision,
  interactionNeeded,
  feedback,
  shotState,
  onNextShot,
  hasNextShot
}) => {
  const theme = useTheme();
  const [currentDecisionType, setCurrentDecisionType] = useState(null);
  const [showPartnershipPrompt, setShowPartnershipPrompt] = useState(false);
  const [showDoublePrompt, setShowDoublePrompt] = useState(false);
  
  // Determine whose turn it is and what decision is needed
  useEffect(() => {
    if (interactionNeeded && gameState?.pending_decision) {
      const decision = gameState.pending_decision;
      setCurrentDecisionType(decision.type);
      
      if (decision.type === 'partnership_request') {
        setShowPartnershipPrompt(true);
      } else if (decision.type === 'double_offer') {
        setShowDoublePrompt(true);
      }
    } else {
      setCurrentDecisionType(null);
      setShowPartnershipPrompt(false);
      setShowDoublePrompt(false);
    }
  }, [interactionNeeded, gameState]);

  const getCaptainInfo = () => {
    if (!gameState) return null;
    
    const captain = gameState.players?.find(p => p.id === gameState.captain_id);
    const rotationOrder = gameState.rotation_order || [];
    const currentPosition = rotationOrder.indexOf(gameState.captain_id) + 1;
    
    return {
      captain,
      position: currentPosition,
      isHuman: captain?.id === 'human'
    };
  };

  const getAvailablePartners = () => {
    if (!gameState) return [];
    
    // Partners can only be selected from players who have hit their tee shot
    // but before the next player in order hits
    const rotationOrder = gameState.rotation_order || [];
    const captainIndex = rotationOrder.indexOf(gameState.captain_id);
    const shotsPlayed = gameState.shots_played || [];
    
    return gameState.players.filter(player => {
      if (player.id === gameState.captain_id) return false; // Captain can't partner with self
      
      const playerIndex = rotationOrder.indexOf(player.id);
      if (playerIndex <= captainIndex) return false; // Only later players in rotation
      
      // Check if player has hit tee shot
      const hasHitTeeShot = shotsPlayed.some(shot => 
        shot.player_id === player.id && shot.shot_number === 1
      );
      
      // Check if next player has hit yet (invitation must be before next shot)
      const nextPlayerIndex = playerIndex + 1;
      if (nextPlayerIndex < rotationOrder.length) {
        const nextPlayerId = rotationOrder[nextPlayerIndex];
        const nextPlayerHasHit = shotsPlayed.some(shot => 
          shot.player_id === nextPlayerId && shot.shot_number === 1
        );
        if (nextPlayerHasHit) return false; // Too late to invite this player
      }
      
      return hasHitTeeShot;
    });
  };

  const getTeamDisplay = () => {
    if (!gameState?.teams) return null;
    
    const teams = gameState.teams;
    let teamDisplay = [];
    
    if (teams.type === 'partners' && teams.team1.length > 0) {
      const team1Names = teams.team1.map(id => 
        gameState.players.find(p => p.id === id)?.name || id
      );
      const team2Names = teams.team2.map(id => 
        gameState.players.find(p => p.id === id)?.name || id
      );
      
      teamDisplay.push({
        name: `${team1Names.join(' & ')} vs ${team2Names.join(' & ')}`,
        type: 'partnership'
      });
    } else if (teams.solo_player) {
      const soloName = gameState.players.find(p => p.id === teams.solo_player)?.name || teams.solo_player;
      const opponentNames = teams.opponents.map(id => 
        gameState.players.find(p => p.id === id)?.name || id
      );
      
      teamDisplay.push({
        name: `${soloName} (Solo) vs ${opponentNames.join(', ')}`,
        type: 'solo'
      });
    }
    
    return teamDisplay;
  };

  const getCurrentWager = () => {
    if (!gameState?.betting) return 1;
    return gameState.betting.current_wager || 1;
  };

  const getFurthestFromHole = () => {
    if (!gameState?.ball_positions) return null;
    
    let furthestDistance = -1;
    let furthestPlayer = null;
    
    gameState.ball_positions.forEach(pos => {
      if (!pos.holed && pos.distance_to_pin > furthestDistance) {
        furthestDistance = pos.distance_to_pin;
        furthestPlayer = gameState.players.find(p => p.id === pos.player_id);
      }
    });
    
    return furthestPlayer;
  };

  const renderCaptainPhase = () => {
    const captainInfo = getCaptainInfo();
    if (!captainInfo) return null;
    
    const availablePartners = getAvailablePartners();
    
    return (
      <Card style={{ border: `3px solid ${theme.colors.primary}`, backgroundColor: '#f8f9fa' }}>
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <h2 style={{ color: theme.colors.primary, margin: 0 }}>
            ⚡ Captain Phase - Hole {gameState?.current_hole || 1}
          </h2>
          <p style={{ margin: '8px 0', fontSize: 16, fontWeight: 500 }}>
            {captainInfo.isHuman ? '🧑 You are' : `💻 ${captainInfo.captain?.name} is`} the Captain 
            (Position {captainInfo.position})
          </p>
          <p style={{ margin: '4px 0', color: theme.colors.textSecondary }}>
            Base wager: <strong>{getCurrentWager()} quarter{getCurrentWager() !== 1 ? 's' : ''}</strong>
          </p>
        </div>

        {captainInfo.isHuman && availablePartners.length > 0 && (
          <div>
            <h3 style={{ marginBottom: 12 }}>Partnership Invitations Available:</h3>
            <div style={{ display: 'grid', gap: 12, marginBottom: 16 }}>
              {availablePartners.map(partner => (
                <div key={partner.id} style={{
                  padding: 12,
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: 6,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  backgroundColor: theme.colors.background
                }}>
                  <div>
                    <div style={{ fontWeight: 500 }}>💻 {partner.name}</div>
                    <div style={{ fontSize: 14, color: theme.colors.textSecondary }}>
                      Handicap: {partner.handicap} | Tee shot completed
                    </div>
                  </div>
                  <Button
                    onClick={() => onMakeDecision({
                      type: 'partnership_request',
                      player_id: 'human',
                      partner_id: partner.id
                    })}
                    style={{ whiteSpace: 'nowrap' }}
                  >
                    "Will you be my partner?"
                  </Button>
                </div>
              ))}
            </div>
            
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <Button
                variant="error"
                onClick={() => onMakeDecision({
                  type: 'go_solo',
                  player_id: 'human'
                })}
                style={{ marginRight: 12 }}
              >
                🐷 Go Solo (Pig)
              </Button>
              <Button
                variant="secondary"
                onClick={() => onMakeDecision({
                  type: 'wait_for_fourth',
                  player_id: 'human'
                })}
              >
                ⏱️ Wait for 4th Player
              </Button>
            </div>
          </div>
        )}

        {availablePartners.length === 0 && captainInfo.isHuman && (
          <div style={{ textAlign: 'center' }}>
            <p style={{ color: theme.colors.textSecondary, marginBottom: 16 }}>
              No partnership invitations available yet. Waiting for players to complete tee shots...
            </p>
          </div>
        )}
      </Card>
    );
  };

  const renderPartnershipPrompt = () => {
    if (!showPartnershipPrompt || !gameState?.pending_decision) return null;
    
    const decision = gameState.pending_decision;
    const captain = gameState.players?.find(p => p.id === decision.from_player);
    
    return (
      <Card style={{ 
        border: `4px solid ${theme.colors.warning}`, 
        backgroundColor: '#fff8e1',
        animation: 'pulse 2s infinite'
      }}>
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ color: theme.colors.warning, margin: '0 0 16px 0' }}>
            🤝 Partnership Invitation
          </h2>
          <p style={{ fontSize: 18, marginBottom: 20 }}>
            💻 <strong>{captain?.name}</strong> asks: "Will you be my partner?"
          </p>
          <p style={{ color: theme.colors.textSecondary, marginBottom: 24 }}>
            Current wager: <strong>{getCurrentWager()} quarter{getCurrentWager() !== 1 ? 's' : ''}</strong>
            {getCurrentWager() > 1 && <span> | If declined: <strong>{getCurrentWager() * 2} quarters</strong></span>}
          </p>
          
          <div style={{ display: 'flex', justifyContent: 'center', gap: 16 }}>
            <Button
              variant="success"
              onClick={() => {
                onMakeDecision({
                  type: 'partnership_response',
                  player_id: 'human',
                  accepted: true
                });
                setShowPartnershipPrompt(false);
              }}
              style={{ padding: '12px 24px', fontSize: 16 }}
            >
              ✅ "Yes, I'll be your partner"
            </Button>
            <Button
              variant="error"
              onClick={() => {
                onMakeDecision({
                  type: 'partnership_response',
                  player_id: 'human',
                  accepted: false
                });
                setShowPartnershipPrompt(false);
              }}
              style={{ padding: '12px 24px', fontSize: 16 }}
            >
              ❌ "No, I decline" (You go solo)
            </Button>
          </div>
          
          <p style={{ fontSize: 14, color: theme.colors.textSecondary, marginTop: 16 }}>
            💡 Declining doubles the bet and you compete alone vs the other 3 players
          </p>
        </div>
      </Card>
    );
  };

  const renderMatchPlayPhase = () => {
    const teams = getTeamDisplay();
    const furthestPlayer = getFurthestFromHole();
    
    return (
      <Card>
        <h3 style={{ color: theme.colors.primary, marginBottom: 16 }}>
          ⛳ Match Play - Hole {gameState?.current_hole || 1}
        </h3>
        
        {teams && teams.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <h4>Team Formation:</h4>
            {teams.map((team, index) => (
              <div key={index} style={{ 
                padding: 8, 
                backgroundColor: team.type === 'solo' ? '#ffebee' : '#e8f5e9',
                borderRadius: 4,
                marginBottom: 8
              }}>
                <strong>{team.name}</strong>
              </div>
            ))}
            <p style={{ color: theme.colors.textSecondary, fontSize: 14 }}>
              Current wager: <strong>{getCurrentWager()} quarter{getCurrentWager() !== 1 ? 's' : ''}</strong>
            </p>
          </div>
        )}
        
        {furthestPlayer && (
          <div style={{ 
            padding: 12, 
            border: `2px solid ${theme.colors.primary}`,
            borderRadius: 6,
            backgroundColor: '#f0f8ff',
            marginBottom: 16
          }}>
            <strong>🎯 Next to Play:</strong> {furthestPlayer.name} (furthest from hole)
          </div>
        )}

        {hasNextShot && (
          <div style={{ textAlign: 'center' }}>
            <Button
              onClick={onNextShot}
              style={{ padding: '12px 24px', fontSize: 16 }}
            >
              ⚡ Play Next Shot
            </Button>
          </div>
        )}
      </Card>
    );
  };

  const renderBettingOpportunities = () => {
    if (!gameState?.ball_positions || gameState.betting?.in_hole) return null;
    
    // Check Line of Scrimmage rule
    const furthestFromHole = getFurthestFromHole();
    const humanPosition = gameState.ball_positions?.find(pos => pos.player_id === 'human');
    const canOfferDouble = !furthestFromHole || humanPosition?.distance_to_pin >= furthestFromHole.distance_to_pin;
    
    return (
      <Card style={{ borderLeft: `4px solid ${theme.colors.success}` }}>
        <h4 style={{ color: theme.colors.success, marginBottom: 12 }}>
          💰 Betting Opportunities
        </h4>
        
        {canOfferDouble ? (
          <div style={{ marginBottom: 12 }}>
            <Button
              variant="success"
              onClick={() => onMakeDecision({
                type: 'double_offer',
                player_id: 'human'
              })}
              style={{ marginRight: 8 }}
            >
              ⬆️ "Will you accept our double?"
            </Button>
            <span style={{ fontSize: 14, color: theme.colors.textSecondary }}>
              (Stakes: {getCurrentWager()} → {getCurrentWager() * 2} quarters)
            </span>
          </div>
        ) : (
          <p style={{ color: theme.colors.textSecondary, fontSize: 14 }}>
            ⛔ Cannot offer double - Line of Scrimmage rule (you've passed furthest ball)
          </p>
        )}
        
        <p style={{ fontSize: 12, color: theme.colors.textSecondary }}>
          💡 No betting allowed once any ball is holed ("in the hole" rule)
        </p>
      </Card>
    );
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 20 }}>
      {/* Feedback Messages */}
      {feedback && feedback.length > 0 && (
        <Card variant="info" style={{ marginBottom: 16 }}>
          {feedback.map((msg, index) => (
            <div key={index} style={{ marginBottom: 8 }}>
              {msg}
            </div>
          ))}
        </Card>
      )}

      {/* Partnership Prompt (highest priority) */}
      {renderPartnershipPrompt()}

      {/* Captain Phase */}
      {gameState?.phase === 'captain_selection' && renderCaptainPhase()}

      {/* Match Play Phase */}
      {gameState?.phase === 'match_play' && renderMatchPlayPhase()}

      {/* Betting Opportunities */}
      {gameState?.phase === 'match_play' && renderBettingOpportunities()}

      {/* Current Shot State */}
      {shotState && (
        <Card style={{ marginTop: 16 }}>
          <h4>📊 Current Shot Analysis</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16 }}>
            <div>
              <strong>Player:</strong> {shotState.player_name}<br/>
              <strong>Distance:</strong> {shotState.distance_to_pin}ft<br/>
              <strong>Lie:</strong> {shotState.lie_type}
            </div>
            <div>
              <strong>Shot Quality:</strong> {shotState.shot_quality}<br/>
              <strong>Shots Taken:</strong> {shotState.shot_count}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default TurnBasedInterface;