// frontend/src/components/simulation/visual/SimulationVisualInterface.jsx
import React from 'react';
import PropTypes from 'prop-types';
import './styles.css';
import {
  HoleVisualization,
  PlayersCard,
  BettingCard,
  ShotContextCard,
  DecisionButtons
} from './index';

const SimulationVisualInterface = ({
  gameState = {},
  shotState = {},
  shotProbabilities = {},
  interactionNeeded = null,
  hasNextShot = false,
  loading = false,
  pokerState = {},
  onMakeDecision = () => {},
  onNextShot = () => {}
}) => {
  return (
    <div className="simulation-visual-interface">
      {/* Top 35% - Hole Visualization */}
      <div className="visualization-section">
        <HoleVisualization
          hole={gameState?.hole_info}
          players={gameState?.players || []}
        />
      </div>

      {/* Middle 25% - Game State Cards */}
      <div className="cards-section">
        <PlayersCard
          players={gameState?.players || []}
          captainId={gameState?.captain_id}
        />
        <BettingCard
          betting={gameState?.betting}
          baseWager={gameState?.base_wager || 1}
          pokerState={pokerState}
        />
        <ShotContextCard
          shotState={shotState}
          holeState={gameState?.hole_state}
          probabilities={shotProbabilities}
        />
      </div>

      {/* Bottom 40% - Decision Buttons */}
      <div className="buttons-section">
        <DecisionButtons
          interactionNeeded={interactionNeeded}
          hasNextShot={hasNextShot}
          onDecision={onMakeDecision}
          onNextShot={onNextShot}
          loading={loading}
          gameState={gameState}
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
  onMakeDecision: PropTypes.func,
  onNextShot: PropTypes.func
};

export default SimulationVisualInterface;
