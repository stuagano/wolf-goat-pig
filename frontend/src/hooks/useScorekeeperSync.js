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
  setIsHoepfinger,
  setGoatId,
  setPhase,
  setRotationOrder,
  setCaptainIndex,
  setJoesSpecialWager,
  setNextHoleWager,
  setCurrentWager,
  setCarryOver,
  setVinniesVariation,
  setOptionActive,
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

  // Track rotation/wager loading errors
  const [rotationError, setRotationError] = useState(null);

  // Fetch rotation and wager info when hole changes
  useEffect(() => {
    const fetchRotationAndWager = async () => {
      setRotationError(null);
      try {
        // Fetch next rotation
        const rotationRes = await fetch(
          `${API_URL}/games/${gameId}/next-rotation`,
        );
        if (!rotationRes.ok) {
          throw new Error(`Failed to fetch rotation: ${rotationRes.status}`);
        }

        const rotationData = await rotationRes.json();
        if (!rotationData || typeof rotationData !== "object") {
          throw new Error("Invalid rotation response");
        }

        if (rotationData.is_hoepfinger) {
          setIsHoepfinger(true);
          setGoatId(rotationData.goat_id);
          setPhase("hoepfinger");
          // Don't set rotation yet - Goat will select position
        } else {
          setIsHoepfinger(false);
          // Validate rotation_order is an array
          if (!Array.isArray(rotationData.rotation_order)) {
            throw new Error("Invalid rotation_order: expected array");
          }
          setRotationOrder(rotationData.rotation_order);
          setCaptainIndex(
            typeof rotationData.captain_index === "number"
              ? rotationData.captain_index
              : 0,
          );
          setPhase("normal");
          setGoatId(null);
          setJoesSpecialWager(null);
        }

        // Fetch next hole wager
        const wagerRes = await fetch(
          `${API_URL}/games/${gameId}/next-hole-wager`,
        );
        if (!wagerRes.ok) {
          throw new Error(`Failed to fetch wager: ${wagerRes.status}`);
        }

        const wagerData = await wagerRes.json();
        if (!wagerData || typeof wagerData !== "object") {
          throw new Error("Invalid wager response");
        }

        // Validate and set wager data with safe defaults
        const baseWagerValue =
          typeof wagerData.base_wager === "number"
            ? wagerData.base_wager
            : baseWager;
        setNextHoleWager(baseWagerValue);
        setCurrentWager(baseWagerValue);
        setCarryOver(wagerData.carry_over || false);
        setVinniesVariation(wagerData.vinnies_variation || false);
        setOptionActive(wagerData.option_active || false);
        if (wagerData.option_active) {
          setGoatId(wagerData.goat_id);
        }
      } catch (err) {
        console.error("Error fetching rotation/wager:", err);
        setRotationError(err.message);
        // Set safe defaults on error
        setCurrentWager(baseWager);
        setNextHoleWager(baseWager);
      }
    };

    if (gameId) {
      fetchRotationAndWager();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- setters are stable (useCallback), only trigger on data changes
  }, [gameId, currentHole, holeHistory, baseWager]);

  return { courseDataLoading, courseDataError, rotationError };
};

export default useScorekeeperSync;
