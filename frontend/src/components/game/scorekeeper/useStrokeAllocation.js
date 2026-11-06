// frontend/src/components/game/scorekeeper/useStrokeAllocation.js
// Stroke allocation memo for SimpleScorekeeper, moved verbatim.

import { useMemo } from "react";
// NOTE: only getStrokesForHole is shared with utils/strokeAllocation — its
// calculateStrokeAllocation applies USGA course-handicap conversion, which
// this component's raw-handicap fallback intentionally does not.
import { getStrokesForHole } from "../../../utils/strokeAllocation";

/**
 * Create an object keyed by player ID from a list of players
 * @param {Array} players - Array of player objects with id property
 * @param {Function} getValue - Function that takes a player and returns the value
 * @returns {Object} Object with player IDs as keys
 */
const createPlayerMap = (players, getValue) =>
  Object.fromEntries(players.map((p) => [p.id, getValue(p)]));

// Use stroke allocation from backend if provided (preferred - calculated with Creecher Feature rules)
// Falls back to local calculation only if backend data is not available
const useStrokeAllocation = ({
  courseData,
  localPlayers,
  initialStrokeAllocation,
}) =>
  useMemo(() => {
    // If we have stroke allocation from the backend, use it (it's more accurate)
    if (
      initialStrokeAllocation &&
      Object.keys(initialStrokeAllocation).length > 0
    ) {
      return initialStrokeAllocation;
    }

    // Fallback: calculate locally if backend didn't provide stroke allocation
    if (!courseData?.holes) return {};

    const allocation = {};

    // Calculate net handicaps relative to lowest handicap player
    const playerHandicaps = createPlayerMap(
      localPlayers,
      (p) => p.handicap || 0,
    );

    // Safe array bounds: ensure we have values before calling Math.min
    const handicapValues = Object.values(playerHandicaps);
    const lowestHandicap =
      handicapValues.length > 0 ? Math.min(...handicapValues) : 0;

    const netHandicaps = {};
    Object.entries(playerHandicaps).forEach(([playerId, handicap]) => {
      netHandicaps[playerId] = Math.max(0, handicap - lowestHandicap);
    });

    // getStrokesForHole imported from utils/strokeAllocation (Creecher Feature).
    localPlayers.forEach((player) => {
      allocation[player.id] = {};
      const netHandicap = netHandicaps[player.id];

      for (let holeNum = 1; holeNum <= 18; holeNum++) {
        const holeData = courseData.holes.find(
          (h) => h.hole_number === holeNum,
        );
        if (holeData?.handicap) {
          allocation[player.id][holeNum] = getStrokesForHole(
            netHandicap,
            holeData.handicap,
          );
        }
      }
    });

    return allocation;
  }, [courseData, localPlayers, initialStrokeAllocation]);

export default useStrokeAllocation;
