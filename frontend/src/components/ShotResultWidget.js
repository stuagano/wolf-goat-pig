/**
 * ShotResultWidget - Displays shot result information and outcome
 *
 * Shows:
 * - Shot outcome (fairway, green, rough, hazard, etc.)
 * - Distance information
 * - Shot quality metrics
 * - Next shot recommendations
 */

import React from 'react';
import PropTypes from 'prop-types';

const ShotResultWidget = ({
  shotResult,
  player,
  hole,
  className = '',
  onNextShot,
  children
}) => {
  if (!shotResult) {
    return (
      <div className={`shot-result-widget ${className}`}>
        {children || <p>No shot result available</p>}
      </div>
    );
  }

  const {
    outcome,
    distance,
    accuracy,
    lie,
    penalties = 0,
    recommendation
  } = shotResult;

  return (
    <div className={`shot-result-widget ${className}`}>
      {children}

      <div className="shot-outcome">
        <h3>Shot Result</h3>
        <div className="outcome-badge">
          {outcome}
        </div>
      </div>

      {distance !== undefined && (
        <div className="shot-distance">
          <p>Distance: {distance} yards</p>
        </div>
      )}

      {accuracy !== undefined && (
        <div className="shot-accuracy">
          <p>Accuracy: {accuracy}%</p>
        </div>
      )}

      {lie && (
        <div className="ball-lie">
          <p>Lie: {lie}</p>
        </div>
      )}

      {penalties > 0 && (
        <div className="penalties">
          <p className="warning">Penalties: {penalties}</p>
        </div>
      )}

      {player && (
        <div className="player-info">
          <p>{player.name}</p>
          {player.handicap && <span>Handicap: {player.handicap}</span>}
        </div>
      )}

      {hole && (
        <div className="hole-info">
          <p>Hole {hole.number} - Par {hole.par}</p>
          {hole.yardage && <span>{hole.yardage} yards</span>}
        </div>
      )}

      {recommendation && (
        <div className="recommendation">
          <h4>Recommendation</h4>
          <p>{recommendation}</p>
        </div>
      )}

      {onNextShot && (
        <button onClick={onNextShot} className="next-shot-btn">
          Continue
        </button>
      )}
    </div>
  );
};

ShotResultWidget.propTypes = {
  shotResult: PropTypes.shape({
    outcome: PropTypes.string,
    distance: PropTypes.number,
    accuracy: PropTypes.number,
    lie: PropTypes.string,
    penalties: PropTypes.number,
    recommendation: PropTypes.string
  }),
  player: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    handicap: PropTypes.number
  }),
  hole: PropTypes.shape({
    number: PropTypes.number,
    par: PropTypes.number,
    yardage: PropTypes.number
  }),
  className: PropTypes.string,
  onNextShot: PropTypes.func,
  children: PropTypes.node
};

export default ShotResultWidget;
