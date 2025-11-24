/**
 * GameStateWidget - Displays real-time game state information
 *
 * Shows:
 * - Current hole information
 * - Team formations
 * - Betting state
 * - Stroke advantages
 * - Ball positions
 * - Player status
 */

import React from 'react';
import PropTypes from 'prop-types';

const GameStateWidget = ({
  holeState,
  players = [],
  className = '',
  onTeamChange,
  onBettingAction
}) => {
  if (!holeState) {
    return (
      <div className={`game-state-widget ${className}`}>
        <p>No game state available</p>
      </div>
    );
  }

  const {
    hole_number,
    hole_par,
    stroke_index,
    current_shot_number,
    teams = {},
    betting = {},
    ball_positions = {},
    stroke_advantages = {}
  } = holeState;

  return (
    <div className={`game-state-widget ${className}`}>
      <div className="hole-info">
        <h3>Hole {hole_number}</h3>
        <p>Par {hole_par} | Stroke Index {stroke_index}</p>
        <p>Shot {current_shot_number}</p>
      </div>

      {teams.type && (
        <div className="team-info">
          <h4>Teams: {teams.type}</h4>
          {teams.team1 && (
            <div className="team">
              Team 1: {teams.team1.map(id =>
                players.find(p => p.id === id)?.name || id
              ).join(', ')}
            </div>
          )}
          {teams.team2 && (
            <div className="team">
              Team 2: {teams.team2.map(id =>
                players.find(p => p.id === id)?.name || id
              ).join(', ')}
            </div>
          )}
        </div>
      )}

      {betting.base_wager !== undefined && (
        <div className="betting-info">
          <h4>Betting</h4>
          <p>Base Wager: ${betting.base_wager}</p>
          <p>Current Wager: ${betting.current_wager || betting.base_wager}</p>
          {betting.doubled && <span className="badge">Doubled</span>}
          {betting.redoubled && <span className="badge">Redoubled</span>}
        </div>
      )}

      {Object.keys(stroke_advantages).length > 0 && (
        <div className="stroke-advantages">
          <h4>Stroke Advantages</h4>
          {Object.entries(stroke_advantages).map(([playerId, advantage]) => (
            <div key={playerId}>
              {players.find(p => p.id === playerId)?.name || playerId}: {advantage}
            </div>
          ))}
        </div>
      )}

      {Object.keys(ball_positions).length > 0 && (
        <div className="ball-positions">
          <h4>Ball Positions</h4>
          {Object.entries(ball_positions).map(([playerId, position]) => (
            <div key={playerId}>
              {players.find(p => p.id === playerId)?.name || playerId}: {position}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

GameStateWidget.propTypes = {
  holeState: PropTypes.shape({
    hole_number: PropTypes.number,
    hole_par: PropTypes.number,
    stroke_index: PropTypes.number,
    current_shot_number: PropTypes.number,
    hole_complete: PropTypes.bool,
    wagering_closed: PropTypes.bool,
    teams: PropTypes.shape({
      type: PropTypes.string,
      team1: PropTypes.arrayOf(PropTypes.string),
      team2: PropTypes.arrayOf(PropTypes.string),
    }),
    betting: PropTypes.shape({
      base_wager: PropTypes.number,
      current_wager: PropTypes.number,
      doubled: PropTypes.bool,
      redoubled: PropTypes.bool,
    }),
    ball_positions: PropTypes.objectOf(PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.object
    ])),
    stroke_advantages: PropTypes.objectOf(PropTypes.number)
  }),
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    handicap: PropTypes.number,
    points: PropTypes.number
  })),
  className: PropTypes.string,
  onTeamChange: PropTypes.func,
  onBettingAction: PropTypes.func
};

export default GameStateWidget;
