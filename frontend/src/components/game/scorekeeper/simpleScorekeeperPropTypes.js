// frontend/src/components/game/scorekeeper/simpleScorekeeperPropTypes.js
// PropTypes for SimpleScorekeeper, moved verbatim.

import PropTypes from "prop-types";

/**
 * PropTypes for SimpleScorekeeper
 * Specific shapes for better validation and documentation
 */
const simpleScorekeeperPropTypes = {
  /** Unique game identifier */
  gameId: PropTypes.string.isRequired,

  /** Array of player objects */
  players: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      handicap: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      user_id: PropTypes.string,
      tee_order: PropTypes.number,
      is_authenticated: PropTypes.bool,
      ghin_id: PropTypes.string,
    }),
  ).isRequired,

  /** Base wager amount in quarters (default: 1) */
  baseWager: PropTypes.number,

  /** History of completed holes */
  initialHoleHistory: PropTypes.arrayOf(
    PropTypes.shape({
      hole: PropTypes.number.isRequired,
      points_delta: PropTypes.objectOf(PropTypes.number),
      gross_scores: PropTypes.objectOf(PropTypes.number),
      teams: PropTypes.shape({
        type: PropTypes.oneOf(["partners", "solo"]),
        team1: PropTypes.arrayOf(PropTypes.string),
        team2: PropTypes.arrayOf(PropTypes.string),
        captain: PropTypes.string,
        opponents: PropTypes.arrayOf(PropTypes.string),
      }),
      winner: PropTypes.oneOf([
        "team1",
        "team2",
        "captain",
        "opponents",
        "push",
        null,
      ]),
      wager: PropTypes.number,
      phase: PropTypes.string,
      rotation_order: PropTypes.arrayOf(PropTypes.string),
      captain_index: PropTypes.number,
      notes: PropTypes.string,
      float_invoked_by: PropTypes.string,
      option_invoked_by: PropTypes.string,
      duncan_invoked: PropTypes.bool,
      option_turned_off: PropTypes.bool,
      betting_events: PropTypes.arrayOf(
        PropTypes.shape({
          eventId: PropTypes.string,
          eventType: PropTypes.string,
          hole: PropTypes.number,
          actor: PropTypes.string,
          timestamp: PropTypes.string,
          details: PropTypes.object,
        }),
      ),
    }),
  ),

  /** Starting hole number (default: 1) */
  initialCurrentHole: PropTypes.number,

  /** Name of the golf course */
  courseName: PropTypes.string,

  /** Pre-calculated stroke allocation from backend */
  initialStrokeAllocation: PropTypes.objectOf(
    PropTypes.objectOf(PropTypes.number),
  ),
};

export default simpleScorekeeperPropTypes;
