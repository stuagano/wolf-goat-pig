// frontend/src/hooks/useHoleSubmission.js
// Hole submission/edit lifecycle for SimpleScorekeeper — moved verbatim:
// resetHole, getEffectiveQuarters (auto-balance), handleSubmitHole,
// handleEditModalSave, handleEditHoleFromScorecard.
//
// Takes one ctx object (the closure surface is ~50 identifiers); destructured
// immediately so every function body is byte-identical to the original.

import { apiConfig } from "../config/api.config";
import { fetchJson } from "../services/fetchJson";
import { upsertHole } from "../utils/holeHistory";

const API_URL = apiConfig.baseUrl;

const createPlayerMap = (players, getValue) =>
  Object.fromEntries(players.map((p) => [p.id, getValue(p)]));

const useHoleSubmission = (ctx) => {
  const {
    gameId,
    baseWager,
    players,
    localPlayers,
    quarters,
    scores,
    teamMode,
    team1,
    team2,
    captain,
    opponents,
    currentHole,
    currentWager,
    phase,
    rotationOrder,
    captainIndex,
    holeNotes,
    winner,
    editingHole,
    holeHistory,
    playerStandings,
    syncHole,
    logBettingAction,
    checkAchievements,
    setQuarters,
    setScores,
    setError,
    setSubmitting,
    setCurrentHole,
    setHoleHistory,
    setPlayerStandings,
    setHoleNotes,
    setWinner,
    setEditingHole,
    setLocalPlayers,
    setCurrentWager,
    setTeam1,
    setTeam2,
    setCaptain,
    setOpponents,
    setFloatInvokedBy,
    setOptionInvokedBy,
    setJoesSpecialWager,
    setOptionTurnedOff,
    setDuncanInvoked,
    setAardvarkRequestedTeam,
    setAardvarkTossed,
    setAardvarkSolo,
    setInvisibleAardvarkTossed,
    setPendingOffer,
    setCurrentHoleBettingEvents,
    setRotationOrder,
    setAchievementCheckFailed,
  } = ctx;

  // Reset hole state for new hole
  const resetHole = () => {
    setTeam1([]);
    setTeam2([]);
    setCaptain(null);
    setOpponents([]);
    setCurrentWager(baseWager);
    setScores({});
    setQuarters({});
    setHoleNotes("");
    setWinner(null);
    setFloatInvokedBy(null);
    setOptionInvokedBy(null);
    setError(null);
    setEditingHole(null);
    // carryOverApplied state removed (was unused)
    setJoesSpecialWager(null); // Reset Joe's Special for next hole
    setOptionTurnedOff(false); // Reset Option for next hole
    setDuncanInvoked(false); // Reset Duncan for next hole
    // Reset Aardvark state
    setAardvarkRequestedTeam(null);
    setAardvarkTossed(false);
    setAardvarkSolo(false);
    setInvisibleAardvarkTossed(false);
    // Reset interactive betting state
    setPendingOffer(null);
    setCurrentHoleBettingEvents([]);
  };

  // Compute effective quarters with auto-balance applied
  const getEffectiveQuarters = () => {
    const effective = { ...quarters };
    const entered = [];
    const empty = [];
    players.forEach((p) => {
      const val = effective[p.id];
      if (val !== undefined && val !== "" && val !== null) {
        entered.push({ id: p.id, value: parseFloat(val) || 0 });
      } else {
        empty.push(p.id);
      }
    });
    if (empty.length === 1 && entered.length >= 1) {
      const sum = entered.reduce((acc, e) => acc + e.value, 0);
      effective[empty[0]] = (-sum).toString();
    }
    return effective;
  };

  // Submit hole to backend
  const handleSubmitHole = async () => {
    // A round is 18 holes — there is no hole 19+. Without this guard,
    // edit-complete mode (which parks currentHole at 19) lets the "Complete
    // Hole" button keep advancing and record phantom holes 19, 20, 21…
    // Editing an existing hole (editingHole set) is always allowed.
    if (!editingHole && currentHole > 18) {
      return;
    }

    // Apply auto-balance before validation
    const effectiveQuarters = getEffectiveQuarters();
    setQuarters(effectiveQuarters);

    // Validate with effective quarters
    const allPlayers = players.map((p) => p.id);
    const quartersEntered = Object.keys(effectiveQuarters).length > 0;
    let validationError = null;
    if (!quartersEntered) {
      validationError = "Please enter quarters for all players";
    } else {
      for (const playerId of allPlayers) {
        if (effectiveQuarters[playerId] === undefined || effectiveQuarters[playerId] === "") {
          validationError = "Please enter quarters for all players";
          break;
        }
      }
      if (!validationError) {
        const quartersSum = allPlayers.reduce((sum, playerId) => {
          return sum + (parseFloat(effectiveQuarters[playerId]) || 0);
        }, 0);
        if (Math.abs(quartersSum) > 0.001) {
          validationError = `Quarters must sum to zero. Current sum: ${quartersSum > 0 ? "+" : ""}${quartersSum.toFixed(2)}`;
        }
      }
    }
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      // For partners mode, Team 2 is always calculated as players not in Team 1
      const teams =
        teamMode === "partners"
          ? {
              type: "partners",
              team1: team1,
              team2: players
                .filter((p) => !team1.includes(p.id))
                .map((p) => p.id),
            }
          : {
              type: "solo",
              captain: captain,
              opponents: opponents,
            };

      // QUARTERS-ONLY MODE: Use manually-entered quarters
      // Build pointsDelta from user-entered quarters (supports decimals for split scoring)
      const pointsDelta = createPlayerMap(
        players,
        (p) => parseFloat(effectiveQuarters[p.id]) || 0,
      );

      // Zero-sum validated earlier in this handler

      // Build hole result object (local, no server needed for calculation)
      const holeResult = {
        hole: currentHole,
        points_delta: pointsDelta,
        gross_scores: scores,
        teams: teams,
        winner: null, // Winner not used - quarters entered manually
        wager: currentWager,
        phase: phase,
        rotation_order: rotationOrder,
        captain_index: captainIndex,
        quarters_only: true,
        notes: holeNotes || null,
      };

      // Log hole completion to betting history
      logBettingAction("Hole Completed", {
        actor: "Quarters entered manually",
        wager: currentWager,
        winner: null,
        scores: scores,
      });

      // Update local state first (optimistic update). upsertHole replaces any
      // existing entry for this hole (offline replay / re-submit) instead of
      // appending — duplicates inflate standings (money) and break the
      // 18-distinct-holes completion check. Mirrors the backend dedupe.
      let updatedHistory;
      if (editingHole) {
        // Editing an existing hole whose number may be changing — key off the
        // hole being edited, not the result's hole number.
        updatedHistory = holeHistory.map((h) =>
          h.hole === editingHole ? holeResult : h,
        );
      } else {
        updatedHistory = upsertHole(holeHistory, holeResult);
      }
      setHoleHistory(updatedHistory);

      // Recalculate all player standings from the updated history
      const newStandings = createPlayerMap(players, (p) => ({
        quarters: 0,
        name: p.name,
        soloCount: 0,
        floatCount: 0,
        optionCount: 0,
      }));

      updatedHistory.forEach((hole) => {
        const delta = hole.points_delta || {};
        Object.entries(delta).forEach(([playerId, points]) => {
          if (newStandings[playerId]) {
            newStandings[playerId].quarters +=
              typeof points === "number" ? points : 0;
          }
        });
        // Track solo usage
        if (hole.teams?.type === "solo" && hole.teams?.captain) {
          if (newStandings[hole.teams.captain]) {
            newStandings[hole.teams.captain].soloCount += 1;
          }
        }
      });
      setPlayerStandings(newStandings);

      // Build scores payload for POST /scores
      const holeQuarters = {};
      updatedHistory.forEach((hole) => {
        if (hole.points_delta) {
          holeQuarters[String(hole.hole)] = hole.points_delta;
        }
      });

      const optionalDetails = {};
      updatedHistory.forEach((hole) => {
        optionalDetails[String(hole.hole)] = {
          teams: hole.teams,
          winner: hole.winner,
          wager: hole.wager,
          gross_scores: hole.gross_scores,
          phase: hole.phase,
          notes: hole.notes || null,
        };
      });

      // Sync to backend using offline-first approach
      // This will queue the sync if offline or on slow connection
      const syncResult = await syncHole(
        holeQuarters,
        optionalDetails,
        editingHole ? currentHole : currentHole + 1,
      );

      // Handle permanent errors (like validation failures)
      if (!syncResult.success && syncResult.permanent) {
        const rawError = syncResult.error || "Failed to save quarters";

        // Handle zero-sum validation error from backend
        if (rawError.includes("Zero-sum validation failed")) {
          throw new Error(
            `Quarters don't balance!\n\n${rawError}\n\n💡 Each hole must sum to zero. Check the wager and winner settings.`,
          );
        }

        throw new Error(rawError);
      }

      // If queued for later sync, that's still a success - data is saved locally
      // The UI will show pending sync indicator

      // Move to next hole or return from editing
      if (editingHole) {
        const maxHole =
          updatedHistory.length > 0
            ? Math.max(...updatedHistory.map((h) => h.hole))
            : 0;
        setCurrentHole(maxHole + 1);
        resetHole();
      } else {
        setCurrentHole(currentHole + 1);
        resetHole();
      }

      // Check for achievement unlocks for all players
      await checkAchievements();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Save edits from the edit-hole modal without touching current hole state
  const handleEditModalSave = async (updatedHole) => {
    const updatedHistory = holeHistory.map((h) =>
      h.hole === updatedHole.hole ? updatedHole : h,
    );
    setHoleHistory(updatedHistory);

    // Recalculate standings
    const newStandings = createPlayerMap(players, (p) => ({
      quarters: 0, name: p.name, soloCount: 0, floatCount: 0, optionCount: 0,
    }));
    updatedHistory.forEach((hole) => {
      const delta = hole.points_delta || {};
      Object.entries(delta).forEach(([playerId, points]) => {
        if (newStandings[playerId]) {
          newStandings[playerId].quarters += typeof points === "number" ? points : 0;
        }
      });
      if (hole.teams?.type === "solo" && hole.teams?.captain) {
        if (newStandings[hole.teams.captain]) {
          newStandings[hole.teams.captain].soloCount += 1;
        }
      }
    });
    setPlayerStandings(newStandings);

    // Sync to backend
    const holeQuarters = {};
    const optionalDetails = {};
    updatedHistory.forEach((hole) => {
      if (hole.points_delta) holeQuarters[String(hole.hole)] = hole.points_delta;
      optionalDetails[String(hole.hole)] = {
        teams: hole.teams, winner: hole.winner, wager: hole.wager,
        gross_scores: hole.gross_scores, phase: hole.phase, notes: hole.notes || null,
      };
    });
    await syncHole(holeQuarters, optionalDetails, currentHole);
  };

  // Handler for editing a hole from the scorecard
  // This is called when user clicks a cell and saves in the Scorecard modal
  const handleEditHoleFromScorecard = ({
    hole,
    playerId,
    strokes,
    quarters: quartersOverride,
  }) => {
    const holeData = holeHistory.find((h) => h.hole === hole);
    if (!holeData) return;

    const updatedScores = { ...holeData.gross_scores };
    if (strokes !== null) updatedScores[playerId] = strokes;

    const updatedPointsDelta = { ...holeData.points_delta };
    if (quartersOverride !== null && quartersOverride !== undefined) {
      updatedPointsDelta[playerId] = quartersOverride;
    }

    handleEditModalSave({
      ...holeData,
      gross_scores: updatedScores,
      points_delta: updatedPointsDelta,
    });
  };

  return {
    resetHole,
    getEffectiveQuarters,
    handleSubmitHole,
    handleEditModalSave,
    handleEditHoleFromScorecard,
  };
};

export default useHoleSubmission;
