// frontend/src/hooks/useScorekeeperSync.js
// SimpleScorekeeper data-sync effects, moved verbatim: course-data fetch,
// local game-state persistence, standings initialization from hole history,
// and per-hole rotation/wager fetch.
//
// The single object parameter is destructured immediately so every dependency
// array below is byte-identical to the original component. Call-order note:
// invoke AFTER useStuartMode in the parent — these effects ran after the
// Stuart cluster in the original component, and the Stuart double-offer
// effect reads wager state set here.

import { useState, useEffect } from "react";
import { apiConfig } from "../config/api.config";
import syncManager from "../services/syncManager";

const API_URL = apiConfig.baseUrl;

const createPlayerMap = (players, getValue) =>
  Object.fromEntries(players.map((p) => [p.id, getValue(p)]));

const useScorekeeperSync = ({
  gameId,
  courseName,
  baseWager,
  players,
  holeHistory,
  currentHole,
  playerStandings,
  setCourseData,
  setPlayerStandings,
  setNextHoleWager,
  setCurrentWager,
}) => {
  const [courseDataError, setCourseDataError] = useState(null);
  const [courseDataLoading, setCourseDataLoading] = useState(false);
  // (rotationError state is declared mid-block below, moved verbatim)

  // Fetch course data
  useEffect(() => {
    const fetchCourseData = async () => {
      setCourseDataLoading(true);
      setCourseDataError(null);
      try {
        // Fetch course details
        const courseResponse = await fetch(`${API_URL}/courses`);
        if (!courseResponse.ok) {
          throw new Error(
            `Failed to fetch courses: ${courseResponse.status} ${courseResponse.statusText}`,
          );
        }

        const coursesData = await courseResponse.json();
        if (!coursesData || typeof coursesData !== "object") {
          throw new Error("Invalid courses response: expected object");
        }

        // /courses returns an object with course names as keys, not an array
        const course = coursesData[courseName];
        if (!course) {
          throw new Error(`Course "${courseName}" not found in courses data`);
        }

        // Validate course data structure
        if (!course.holes || !Array.isArray(course.holes)) {
          throw new Error(`Course "${courseName}" has invalid holes data`);
        }

        setCourseData(course);
      } catch (err) {
        console.error("Error fetching course data:", err);
        setCourseDataError(err.message);
        // Don't set courseData to null - keep any existing data
      } finally {
        setCourseDataLoading(false);
      }
    };

    if (courseName) {
      fetchCourseData();
    }
  }, [courseName]);

  // Save game state locally whenever holeHistory changes (survives page refresh)
  useEffect(() => {
    if (gameId && holeHistory.length > 0) {
      syncManager.saveLocalGameState(gameId, {
        holeHistory,
        currentHole,
        playerStandings,
      });
    }
  }, [gameId, holeHistory, currentHole, playerStandings]);

  // Initialize player standings from hole history
  useEffect(() => {
    const standings = createPlayerMap(players, (p) => ({
      quarters: 0,
      name: p.name,
      soloCount: 0,
      floatCount: 0,
      optionCount: 0,
    }));

    // Recalculate quarters and usage stats from hole history
    holeHistory.forEach((hole) => {
      // Track quarters
      if (hole.points_delta) {
        Object.entries(hole.points_delta).forEach(([playerId, points]) => {
          if (standings[playerId]) {
            standings[playerId].quarters += points;
          }
        });
      }

      // Track solo usage
      if (hole.teams?.type === "solo" && hole.teams?.captain) {
        if (standings[hole.teams.captain]) {
          standings[hole.teams.captain].soloCount += 1;
        }
      }

      // Track float usage
      if (hole.float_invoked_by && standings[hole.float_invoked_by]) {
        standings[hole.float_invoked_by].floatCount += 1;
      }

      // Track option usage
      if (hole.option_invoked_by && standings[hole.option_invoked_by]) {
        standings[hole.option_invoked_by].optionCount += 1;
      }
    });

    setPlayerStandings(standings);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- setPlayerStandings is stable (useCallback)
  }, [players, holeHistory]);

  // Rotation and per-hole wager are computed client-side (in the game reducer).
  // The old backend endpoints (/next-rotation, /next-hole-wager) were never
  // implemented and 404'd on every hole, surfacing a spurious "Rotation/Wager
  // Error" banner for every game. The fetch's only real effect in production was
  // its error-fallback: resetting the wager to base on each hole change. Keep
  // exactly that, drop the dead network calls, and the banner is gone.
  // rotationError is retained (always null) so callers' destructuring is stable.
  const [rotationError] = useState(null);

  useEffect(() => {
    if (!gameId) return;
    setNextHoleWager(baseWager);
    setCurrentWager(baseWager);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- setters are stable (useCallback), only trigger on data changes
  }, [gameId, currentHole, holeHistory, baseWager]);

  return { courseDataLoading, courseDataError, rotationError };
};

export default useScorekeeperSync;
