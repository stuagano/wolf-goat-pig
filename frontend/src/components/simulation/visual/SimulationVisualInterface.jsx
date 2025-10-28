// frontend/src/components/simulation/visual/SimulationVisualInterface.jsx
import React from 'react';
import PropTypes from 'prop-types';
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
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      gap: '16px',
      padding: '16px',
      maxWidth: '1400px',
      margin: '0 auto'
    }}>
      {/* Top 35% - Hole Visualization */}
      <div
        data-section="visualization"
        style={{
          flex: '0 0 35%',
          minHeight: '300px',
          maxHeight: '400px'
        }}
      >
        <HoleVisualization
          hole={gameState?.hole_info}
          players={gameState?.players || []}
        />
      </div>

      {/* Middle 25% - Game State Cards */}
      <div
        data-section="cards"
        style={{
          flex: '0 0 25%',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '16px',
          minHeight: '200px'
        }}
      >
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
      <div
        data-section="buttons"
        style={{
          flex: '0 0 40%',
          minHeight: '250px'
        }}
      >
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
