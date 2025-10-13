import React from 'react';
import { useTheme } from '../../theme/Provider';
import { Button, Card } from '../ui';
import SimulationDecisionPanel from './SimulationDecisionPanel';

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

      <SimulationDecisionPanel
        gameState={gameState}
        interactionNeeded={interactionNeeded}
        onDecision={makeDecision}
        onNextShot={onNextShot}
        hasNextShot={hasNextShot}
      />

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