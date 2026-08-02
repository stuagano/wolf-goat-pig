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
import { parseQuarter } from "../utils/quarters";
import {
  blocksHole18Push,
  isHolePush,
  resolveCarryOverForHole,
} from "../utils/carryOver";

const API_URL = apiConfig.baseUrl;

const createPlayerMap = (players, getValue) =>
  Object.fromEntries(players.map((p) => [p.id, getValue(p)]));

/** Rebuild standings from hole history — quarters plus usage counters. */
export const standingsFromHistory = (players, history) => {
  const standings = createPlayerMap(players, (p) => ({
    quarters: 0,
    name: p.name,
    soloCount: 0,
    floatCount: 0,
    optionCount: 0,
  }));

  history.forEach((hole) => {
    const delta = hole.points_delta || {};
    Object.entries(delta).forEach(([playerId, points]) => {
      if (standings[playerId]) {
        standings[playerId].quarters += typeof points === "number" ? points : 0;
      }
    });
    if (hole.teams?.type === "solo" && hole.teams?.captain) {
      if (standings[hole.teams.captain]) {
        standings[hole.teams.captain].soloCount += 1;
      }
    }
    if (hole.float_invoked_by && standings[hole.float_invoked_by]) {
      standings[hole.float_invoked_by].floatCount += 1;
    }
    if (hole.option_invoked_by && standings[hole.option_invoked_by]) {
      standings[hole.option_invoked_by].optionCount += 1;
    }
  });

  return standings;
};

/** Build the hole result + /scores optional_details payload for one hole. */
export const buildHoleSubmitPayload = ({
  players,
  teamMode,
  team1,
  captain,
  opponents,
  currentHole,
  currentWager,
  phase,
  rotationOrder,
  captainIndex,
  scores,
  holeNotes,
  effectiveQuarters,
  floatInvokedBy = null,
  optionInvokedBy = null,
  duncanInvoked = false,
  joesSpecialWager = null,
  aardvarkRequestedTeam = null,
  aardvarkTossed = false,
  aardvarkSolo = false,
  invisibleAardvarkTossed = false,
  carryOverApplied = false,
}) => {
  const teams =
    teamMode === "partners"
      ? {
          type: "partners",
          team1,
          team2: players.filter((p) => !team1.includes(p.id)).map((p) => p.id),
        }
      : {
          type: "solo",
          captain,
          opponents,
        };

  const pointsDelta = createPlayerMap(
    players,
    (p) => parseQuarter(effectiveQuarters[p.id]) ?? 0,
  );

  const push = isHolePush({ points_delta: pointsDelta });

  const holeResult = {
    hole: currentHole,
    points_delta: pointsDelta,
    gross_scores: scores,
    teams,
    winner: push ? "push" : null,
    wager: currentWager,
    phase,
    rotation_order: rotationOrder,
    captain_index: captainIndex,
    quarters_only: true,
    notes: holeNotes || null,
    float_invoked_by: floatInvokedBy || null,
    option_invoked_by: optionInvokedBy || null,
    duncan_invoked: Boolean(duncanInvoked),
    joes_special_wager: joesSpecialWager ?? null,
    aardvark_requested_team: aardvarkRequestedTeam || null,
    aardvark_tossed: Boolean(aardvarkTossed),
    aardvark_solo: Boolean(aardvarkSolo),
    invisible_aardvark_tossed: Boolean(invisibleAardvarkTossed),
    carry_over_applied: Boolean(carryOverApplied),
  };

  const optionalDetails = {
    teams: holeResult.teams,
    winner: holeResult.winner,
    wager: holeResult.wager,
    gross_scores: holeResult.gross_scores,
    phase: holeResult.phase,
    notes: holeResult.notes,
    float_invoked_by: holeResult.float_invoked_by,
    option_invoked_by: holeResult.option_invoked_by,
    duncan_invoked: holeResult.duncan_invoked,
    joes_special_wager: holeResult.joes_special_wager,
    aardvark_requested_team: holeResult.aardvark_requested_team,
    aardvark_tossed: holeResult.aardvark_tossed,
    aardvark_solo: holeResult.aardvark_solo,
    carry_over_applied: holeResult.carry_over_applied,
  };

  return { holeResult, optionalDetails, teams, pointsDelta };
};

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
    floatInvokedBy,
    optionInvokedBy,
    duncanInvoked,
    joesSpecialWager,
    aardvarkRequestedTeam,
    aardvarkTossed,
    aardvarkSolo,
    invisibleAardvarkTossed,
    carryOver,
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
    setNextHoleWager,
    setTeam1,
    setTeam2,
    setCaptain,
    setOpponents,
    setFloatInvokedBy,
    setOptionInvokedBy,
    setJoesSpecialWager,
    setOptionTurnedOff,
    setDuncanInvoked,
    setCarryOver,
    setAardvarkRequestedTeam,
    setAardvarkTossed,
    setAardvarkSolo,
    setInvisibleAardvarkTossed,
    setPendingOffer,
    setCurrentHoleBettingEvents,
    setRotationOrder,
    setAchievementCheckFailed,
  } = ctx;

  const applyStartingWager = (holeNumber, history) => {
    const resolved = resolveCarryOverForHole({
      holeHistory: history,
      baseWager,
      holeNumber,
    });
    setCurrentWager(resolved.wager);
    if (typeof setNextHoleWager === "function") {
      setNextHoleWager(resolved.wager);
    }
    if (typeof setCarryOver === "function") {
      setCarryOver(resolved.carryOver);
    }
  };

  // Reset hole state for new hole
  const resetHole = (opts = {}) => {
    setTeam1([]);
    setTeam2([]);
    setCaptain(null);
    setOpponents([]);
    applyStartingWager(
      opts.holeNumber ?? currentHole,
      opts.holeHistory ?? holeHistory,
    );
    setScores({});
    setQuarters({});
    setHoleNotes("");
    setWinner(null);
    setFloatInvokedBy(null);
    setOptionInvokedBy(null);
    setError(null);
    setEditingHole(null);
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
      // A half-typed "-"/"." parses to null and counts as empty (not 0), so
      // auto-balance can fill it and a partial entry never silently zeroes.
      const val = parseQuarter(effective[p.id]);
      if (val === null) {
        empty.push(p.id);
      } else {
        entered.push({ id: p.id, value: val });
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
    let validationError = null;
    // Flag a half-typed / malformed entry explicitly instead of silently
    // treating it as 0 and reporting a confusing "must sum to zero" error.
    const malformed = players.find(
      (p) =>
        effectiveQuarters[p.id] !== undefined &&
        effectiveQuarters[p.id] !== "" &&
        effectiveQuarters[p.id] !== null &&
        parseQuarter(effectiveQuarters[p.id]) === null,
    );
    const missing = allPlayers.some(
      (id) =>
        effectiveQuarters[id] === undefined ||
        effectiveQuarters[id] === "" ||
        effectiveQuarters[id] === null,
    );
    if (malformed) {
      validationError = `Enter a valid number for ${malformed.name} (use the +/- or ± buttons for negatives).`;
    } else if (missing) {
      validationError = "Please enter quarters for all players";
    } else {
      const quartersSum = allPlayers.reduce(
        (sum, playerId) => sum + (parseQuarter(effectiveQuarters[playerId]) ?? 0),
        0,
      );
      if (Math.abs(quartersSum) > 0.001) {
        validationError = `Quarters must sum to zero. Current sum: ${quartersSum > 0 ? "+" : ""}${quartersSum.toFixed(2)}`;
      }
    }
    if (validationError) {
      setError(validationError);
      return;
    }

    const pushCheck = isHolePush({
      points_delta: createPlayerMap(
        players,
        (p) => parseQuarter(effectiveQuarters[p.id]) ?? 0,
      ),
    });
    if (
      blocksHole18Push({
        holeHistory,
        holeNumber: currentHole,
        isPush: pushCheck,
      })
    ) {
      setError(
        "Cannot push on hole 18 with a carry-over wager — someone must win this hole.",
      );
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const { holeResult, optionalDetails: holeOptional } = buildHoleSubmitPayload({
        players,
        teamMode,
        team1,
        captain,
        opponents,
        currentHole,
        currentWager,
        phase,
        rotationOrder,
        captainIndex,
        scores,
        holeNotes,
        effectiveQuarters,
        floatInvokedBy,
        optionInvokedBy,
        duncanInvoked,
        joesSpecialWager,
        aardvarkRequestedTeam,
        aardvarkTossed,
        aardvarkSolo,
        invisibleAardvarkTossed,
        carryOverApplied: Boolean(carryOver),
      });

      // Log hole completion to betting history
      logBettingAction("Hole Completed", {
        actor: "Quarters entered manually",
        wager: currentWager,
        winner: null,
        scores: scores,
        float_invoked_by: floatInvokedBy || null,
        duncan_invoked: Boolean(duncanInvoked),
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

      const newStandings = standingsFromHistory(players, updatedHistory);
      setPlayerStandings(newStandings);

      // Build scores payload for POST /scores
      const holeQuarters = {};
      const optionalDetails = {};
      updatedHistory.forEach((hole) => {
        if (hole.points_delta) {
          holeQuarters[String(hole.hole)] = hole.points_delta;
        }
        optionalDetails[String(hole.hole)] = {
          teams: hole.teams,
          winner: hole.winner,
          wager: hole.wager,
          gross_scores: hole.gross_scores,
          phase: hole.phase,
          notes: hole.notes || null,
          float_invoked_by: hole.float_invoked_by || null,
          option_invoked_by: hole.option_invoked_by || null,
          duncan_invoked: hole.duncan_invoked || false,
          joes_special_wager: hole.joes_special_wager ?? null,
          aardvark_requested_team: hole.aardvark_requested_team || null,
          aardvark_tossed: hole.aardvark_tossed || false,
          aardvark_solo: hole.aardvark_solo || false,
          carry_over_applied: hole.carry_over_applied || false,
        };
      });
      // Ensure the hole we just built is present even if history was empty.
      optionalDetails[String(holeResult.hole)] = {
        ...optionalDetails[String(holeResult.hole)],
        ...holeOptional,
      };

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
        const nextHole = maxHole + 1;
        setCurrentHole(nextHole);
        resetHole({ holeNumber: nextHole, holeHistory: updatedHistory });
      } else {
        const nextHole = currentHole + 1;
        setCurrentHole(nextHole);
        resetHole({ holeNumber: nextHole, holeHistory: updatedHistory });
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

    const newStandings = standingsFromHistory(players, updatedHistory);
    setPlayerStandings(newStandings);

    // Sync to backend
    const holeQuarters = {};
    const optionalDetails = {};
    updatedHistory.forEach((hole) => {
      if (hole.points_delta) holeQuarters[String(hole.hole)] = hole.points_delta;
      optionalDetails[String(hole.hole)] = {
        teams: hole.teams,
        winner: hole.winner,
        wager: hole.wager,
        gross_scores: hole.gross_scores,
        phase: hole.phase,
        notes: hole.notes || null,
        float_invoked_by: hole.float_invoked_by || null,
        option_invoked_by: hole.option_invoked_by || null,
        duncan_invoked: hole.duncan_invoked || false,
        joes_special_wager: hole.joes_special_wager ?? null,
        aardvark_requested_team: hole.aardvark_requested_team || null,
        aardvark_tossed: hole.aardvark_tossed || false,
        aardvark_solo: hole.aardvark_solo || false,
        carry_over_applied: hole.carry_over_applied || false,
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
