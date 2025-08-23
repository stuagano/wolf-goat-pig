import React from 'react';
import { useTheme } from '../../theme/Provider';
import { Button, Card } from '../ui';

const GamePlay = ({
  gameState,
  onEndSimulation,
  interactionNeeded,
  onMakeDecision,
  feedback,
  shotState,
  shotProbabilities,
  onNextShot,
  hasNextShot
}) => {
  const theme = useTheme();

  const resetSimulation = () => {
    if (window.confirm("Are you sure you want to end this simulation?")) {
      onEndSimulation();
    }
  };

  const makeDecision = (decision) => {
    onMakeDecision(decision);
  };

  const getAvailablePartners = () => {
    if (!gameState) return [];
    return gameState.players.filter(p => p.id !== "human" && p.id !== gameState.captain_id);
  };

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: 20 }}>
      {/* Game Header */}
      <Card>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ color: theme.colors.primary, margin: 0 }}>
              🎮 Simulation - Hole {gameState?.current_hole || 1}
            </h2>
            {gameState?.selected_course && (
              <p style={{ margin: "4px 0 0 0", color: theme.colors.textSecondary, fontSize: 14 }}>
                Playing on: <strong>{gameState.selected_course}</strong>
              </p>
            )}
          </div>
          <Button
            variant="error"
            onClick={resetSimulation}
          >
            End Simulation
          </Button>
        </div>
        <p style={{ margin: "8px 0 0 0", color: theme.colors.textSecondary }}>
          {gameState?.game_status_message || ""}
        </p>
      </Card>
      
      {/* Player Scores */}
      <Card>
        <h3>Current Standings</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
          {gameState?.players?.map(player => (
            <div 
              key={player.id} 
              style={{ 
                padding: 12, 
                border: `2px solid ${player.id === "human" ? theme.colors.primary : theme.colors.border}`, 
                borderRadius: 8,
                background: player.id === "human" ? "#f0f8ff" : theme.colors.background
              }}
            >
              <div style={{ fontWeight: "bold" }}>
                {player.id === "human" ? "🧑 " : "💻 "}{player.name}
              </div>
              <div>Handicap: {player.handicap}</div>
              <div style={{ 
                fontSize: 18, 
                fontWeight: "bold", 
                color: player.points >= 0 ? theme.colors.success : theme.colors.error 
              }}>
                {player.points >= 0 ? "+" : ""}{player.points} pts
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Interactive Decision Making */}
      {interactionNeeded && (
        <Card 
          variant="warning"
          style={{
            ...theme.cardStyle,
            border: `4px solid ${theme.colors.primary}`,
            backgroundColor: '#f0f8ff'
          }}
        >
          <h3 style={{ color: theme.colors.primary, marginBottom: 16 }}>🤔 Your Decision</h3>
          
          {interactionNeeded.type === 'captain_decision' && (
            <div>
              <p style={{ marginBottom: 16, fontSize: 16 }}>
                <strong>You are the Captain for this hole!</strong> Choose your strategy:
              </p>
              
              <div style={{ 
                background: theme.colors.primary,
                color: 'white',
                padding: 12,
                borderRadius: 8,
                marginBottom: 16,
                textAlign: 'center'
              }}>
                <div style={{ fontSize: 18, fontWeight: 'bold' }}>
                  Hole {gameState.current_hole} - Par {gameState.hole_par}
                </div>
                <div style={{ fontSize: 14, marginTop: 4 }}>
                  Base Wager: ${gameState.base_wager}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <h4>Request a Partner:</h4>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                    {getAvailablePartners().map(partner => (
                      <Button
                        key={partner.id}
                        variant="primary"
                        onClick={() => makeDecision({
                          type: 'request_partner',
                          partner_id: partner.id
                        })}
                      >
                        Partner with {partner.name}
                      </Button>
                    ))}
                  </div>
                </div>
                
                <div style={{ textAlign: 'center', margin: '16px 0' }}>
                  <strong>— OR —</strong>
                </div>
                
                <div style={{ textAlign: 'center' }}>
                  <Button
                    variant="warning"
                    size="large"
                    onClick={() => makeDecision({
                      type: 'go_solo'
                    })}
                  >
                    🚀 Go Solo (Double the wager!)
                  </Button>
                </div>
              </div>
            </div>
          )}

          {interactionNeeded.type === 'partnership_response' && (
            <div>
              <p style={{ marginBottom: 16, fontSize: 16 }}>
                <strong>{interactionNeeded.captain_name}</strong> has requested you as their partner!
              </p>
              
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                <Button
                  variant="success"
                  onClick={() => makeDecision({
                    type: 'accept_partnership'
                  })}
                >
                  ✅ Accept Partnership
                </Button>
                
                <Button
                  variant="error"
                  onClick={() => makeDecision({
                    type: 'decline_partnership'
                  })}
                >
                  ❌ Decline Partnership
                </Button>
              </div>
            </div>
          )}

          {interactionNeeded.type === 'double_offer' && (
            <div>
              <p style={{ marginBottom: 16, fontSize: 16 }}>
                A <strong>Double</strong> has been offered! This will double the current wager.
              </p>
              
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                <Button
                  variant="success"
                  onClick={() => makeDecision({
                    type: 'accept_double'
                  })}
                >
                  ✅ Accept Double
                </Button>
                
                <Button
                  variant="error"
                  onClick={() => makeDecision({
                    type: 'decline_double'
                  })}
                >
                  ❌ Decline Double
                </Button>
              </div>
            </div>
          )}

          {interactionNeeded.type === 'double_response' && (
            <div>
              <p style={{ marginBottom: 16, fontSize: 16 }}>
                Your team is considering offering a <strong>Double</strong>. Do you want to proceed?
              </p>
              
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                <Button
                  variant="primary"
                  onClick={() => makeDecision({
                    type: 'offer_double'
                  })}
                >
                  💰 Offer Double
                </Button>
                
                <Button
                  variant="secondary"
                  onClick={() => makeDecision({
                    type: 'no_double'
                  })}
                >
                  Continue Without Double
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Shot-by-Shot Controls */}
      {hasNextShot && !interactionNeeded && (
        <Card style={{ background: '#f0fff4', border: '2px solid #48bb78' }}>
          <h3>⛳ Ready to Play</h3>
          <p style={{ marginBottom: 16 }}>
            Click the button below to play the next shot in the simulation.
          </p>
          <div style={{ textAlign: 'center' }}>
            <Button
              variant="primary"
              size="large"
              onClick={onNextShot}
            >
              🏌️ Play Next Shot
            </Button>
          </div>
        </Card>
      )}

      {/* Shot Analysis (when available) */}
      {shotState && (
        <Card>
          <h3>📊 Shot Analysis</h3>
          <div style={{ marginBottom: 16 }}>
            <strong>Current Shot:</strong> {shotState.description}
          </div>
          
          {shotProbabilities && (
            <div style={{ marginBottom: 16 }}>
              <h4>Shot Probabilities:</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
                {Object.entries(shotProbabilities).map(([outcome, probability]) => (
                  <div 
                    key={outcome}
                    style={{
                      padding: 8,
                      background: theme.colors.background,
                      border: `1px solid ${theme.colors.border}`,
                      borderRadius: 6,
                      textAlign: 'center'
                    }}
                  >
                    <div style={{ fontWeight: 'bold' }}>{outcome}</div>
                    <div style={{ fontSize: '18px', color: theme.colors.primary }}>
                      {(probability * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Feedback Panel */}
      {feedback && feedback.length > 0 && (
        <Card variant="success">
          <h3>📚 Educational Feedback</h3>
          <div style={{ maxHeight: 300, overflowY: 'auto' }}>
            {feedback.map((item, index) => (
              <div 
                key={index}
                style={{
                  marginBottom: 12,
                  padding: 12,
                  background: theme.colors.background,
                  borderRadius: 6,
                  borderLeft: `4px solid ${theme.colors.success}`
                }}
              >
                <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                  {item.title || `Feedback ${index + 1}`}
                </div>
                <div style={{ fontSize: 14 }}>
                  {item.message || item}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Game Progress */}
      <Card>
        <h3>🎯 Game Progress</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 16 }}>
          <div>
            <div style={{ fontSize: 14, color: theme.colors.textSecondary }}>Current Hole</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: theme.colors.primary }}>
              {gameState?.current_hole || 1}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 14, color: theme.colors.textSecondary }}>Holes Remaining</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: theme.colors.accent }}>
              {18 - (gameState?.current_hole || 1) + 1}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 14, color: theme.colors.textSecondary }}>Base Wager</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: theme.colors.warning }}>
              ${gameState?.base_wager || 0}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default GamePlay;