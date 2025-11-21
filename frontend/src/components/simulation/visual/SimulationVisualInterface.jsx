// frontend/src/components/simulation/visual/SimulationVisualInterface.jsx
import React from 'react';
import PropTypes from 'prop-types';
import './styles.css';
import {
  HoleVisualization,
  PlayersCard,
  BettingCard
} from './index';
import Scorecard from '../../game/Scorecard';
import SimulationDecisionPanel from '../SimulationDecisionPanel';
import { Card } from '../../ui';

const SimulationVisualInterface = ({
  gameState = {},
  shotState = {},
  shotProbabilities = {},
  interactionNeeded = null,
  hasNextShot = false,
  loading = false,
  pokerState = {},
  feedback = [],
  onMakeDecision = () => {},
  onNextShot = () => {},
  onNextHole = () => {},
  onEditHole = () => {}
}) => {
  return (
    <div className="simulation-visual-interface">
      {/* Fixed Scorecard at the very top */}
      <div style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        backgroundColor: '#fff',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: '16px'
      }}>
        <Scorecard
          players={gameState?.players || []}
          holeHistory={gameState?.hole_history || []}
          currentHole={gameState?.current_hole || 1}
          onEditHole={onEditHole}
        />
      </div>

      {/* Left-Right Layout Container */}
      <div className="simulation-main-container">
        {/* Left Side - Visualization */}
        <div className="simulation-left-section">
          <div className="visualization-section">
            <HoleVisualization
              hole={gameState?.hole_info}
              players={gameState?.players || []}
            />
          </div>

          {/* Feedback Messages */}
          {feedback && feedback.length > 0 && (
            <div style={{ marginTop: '16px' }}>
              <Card variant="info" style={{ maxWidth: '100%' }}>
                <h3 style={{ marginTop: 0, marginBottom: '12px', fontSize: '16px', fontWeight: 'bold' }}>
                  📢 Game Updates
                </h3>
                <div style={{ maxHeight: '150px', overflowY: 'auto', overflowX: 'hidden' }}>
                  {feedback.slice(-5).reverse().map((msg, index) => (
                    <div
                      key={index}
                      style={{
                        padding: '8px 12px',
                        marginBottom: '6px',
                        backgroundColor: 'rgba(0, 0, 0, 0.05)',
                        borderRadius: '4px',
                        fontSize: '14px',
                        borderLeft: '3px solid #2196F3',
                        wordBreak: 'break-word',
                        overflowWrap: 'break-word'
                      }}
                    >
                      {msg}
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}
        </div>

        {/* Right Side - Cards and Information */}
        <div className="simulation-right-section">
          {/* Game State Cards */}
          <div className="cards-section">
            <PlayersCard
              players={gameState?.players || []}
              captainId={gameState?.captain_id}
            />
            <BettingCard
              betting={gameState?.betting}
              baseWager={gameState?.base_wager || 1}
              pokerState={pokerState}
              shotProbabilities={shotProbabilities}
            />
          </div>
        </div>
      </div>

      {/* Bottom - Decision Panel with Cards */}
      <div className="buttons-section">
        <SimulationDecisionPanel
          gameState={gameState}
          interactionNeeded={interactionNeeded}
          onDecision={onMakeDecision}
          onNextShot={onNextShot}
          onNextHole={onNextHole}
          hasNextShot={hasNextShot}
        />
      </div>
    </div>
  );
};

SimulationVisualInterface.propTypes = {
  gameState: PropTypes.object,
  shotState: PropTypes.object,
  shotProbabilities: PropTypes.object,
  interactionNeeded: PropTypes.object,
  hasNextShot: PropTypes.bool,
  loading: PropTypes.bool,
  pokerState: PropTypes.object,
  feedback: PropTypes.array,
  onMakeDecision: PropTypes.func,
  onNextShot: PropTypes.func,
  onNextHole: PropTypes.func,
  onEditHole: PropTypes.func
};

export default SimulationVisualInterface;
