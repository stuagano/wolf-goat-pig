// frontend/src/components/game/useGameActions.js
// The gameReducer dispatch wrappers — moved verbatim from SimpleScorekeeper.
// Stable identities (empty dep arrays) are preserved: dispatch from useReducer
// is stable, so these never re-create.

import { useCallback } from "react";
import { gameActions } from "./gameReducer";

const useGameActions = (dispatch) => {
  // ============================================================
  // ACTION DISPATCHERS - Maintain existing setter function names
  // ============================================================

  // Hole actions
  const setCurrentHole = useCallback(
    (h) => dispatch(gameActions.setCurrentHole(h)),
    [],
  );
  const setScores = useCallback((s) => dispatch(gameActions.setScores(s)), []);
  const setQuarters = useCallback(
    (q) => dispatch(gameActions.setQuarters(q)),
    [],
  );
  const setHoleNotes = useCallback(
    (n) => dispatch(gameActions.setHoleNotes(n)),
    [],
  );
  const setWinner = useCallback((w) => dispatch(gameActions.setWinner(w)), []);

  // Team actions
  const setTeamMode = useCallback(
    (m) => dispatch(gameActions.setTeamMode(m)),
    [],
  );
  const setTeam1 = useCallback((t) => dispatch(gameActions.setTeam1(t)), []);
  const setTeam2 = useCallback((t) => dispatch(gameActions.setTeam2(t)), []);
  const setCaptain = useCallback(
    (c) => dispatch(gameActions.setCaptain(c)),
    [],
  );
  const setOpponents = useCallback(
    (o) => dispatch(gameActions.setOpponents(o)),
    [],
  );

  // Betting actions
  const setCurrentWager = useCallback(
    (w) => dispatch(gameActions.setCurrentWager(w)),
    [],
  );
  const setNextHoleWager = useCallback(
    (w) => dispatch(gameActions.setNextHoleWager(w)),
    [],
  );
  const setFloatInvokedBy = useCallback(
    (p) => dispatch(gameActions.setFloatInvokedBy(p)),
    [],
  );
  const setOptionInvokedBy = useCallback(
    (p) => dispatch(gameActions.setOptionInvokedBy(p)),
    [],
  );
  const setOptionActive = useCallback(
    (a) => dispatch(gameActions.setOptionActive(a)),
    [],
  );
  const setOptionTurnedOff = useCallback(
    (o) => dispatch(gameActions.setOptionTurnedOff(o)),
    [],
  );
  const setDuncanInvoked = useCallback(
    (d) => dispatch(gameActions.setDuncanInvoked(d)),
    [],
  );
  const setCarryOver = useCallback(
    (c) => dispatch(gameActions.setCarryOver(c)),
    [],
  );
  const setVinniesVariation = useCallback(
    (v) => dispatch(gameActions.setVinniesVariation(v)),
    [],
  );
  const setJoesSpecialWager = useCallback(
    (w) => dispatch(gameActions.setJoesSpecialWager(w)),
    [],
  );

  // Rotation actions
  const setRotationOrder = useCallback(
    (o) => dispatch(gameActions.setRotationOrder(o)),
    [],
  );
  const setCaptainIndex = useCallback(
    (i) => dispatch(gameActions.setCaptainIndex(i)),
    [],
  );
  const setIsHoepfinger = useCallback(
    (h) => dispatch(gameActions.setIsHoepfinger(h)),
    [],
  );
  const setGoatId = useCallback(
    (id) => dispatch(gameActions.setGoatId(id)),
    [],
  );
  const setPhase = useCallback((p) => dispatch(gameActions.setPhase(p)), []);

  // Aardvark actions
  const setAardvarkRequestedTeam = useCallback(
    (t) => dispatch(gameActions.setAardvarkRequestedTeam(t)),
    [],
  );
  const setAardvarkTossed = useCallback(
    (t) => dispatch(gameActions.setAardvarkTossed(t)),
    [],
  );
  const setAardvarkSolo = useCallback(
    (s) => dispatch(gameActions.setAardvarkSolo(s)),
    [],
  );
  const setInvisibleAardvarkTossed = useCallback(
    (t) => dispatch(gameActions.setInvisibleAardvarkTossed(t)),
    [],
  );

  // History actions
  const setHoleHistory = useCallback(
    (h) => dispatch(gameActions.setHoleHistory(h)),
    [],
  );
  const setPlayerStandings = useCallback(
    (s) => dispatch(gameActions.setPlayerStandings(s)),
    [],
  );

  return {
    setCurrentHole,
    setScores,
    setQuarters,
    setHoleNotes,
    setWinner,
    setTeamMode,
    setTeam1,
    setTeam2,
    setCaptain,
    setOpponents,
    setCurrentWager,
    setNextHoleWager,
    setFloatInvokedBy,
    setOptionInvokedBy,
    setOptionActive,
    setOptionTurnedOff,
    setDuncanInvoked,
    setCarryOver,
    setVinniesVariation,
    setJoesSpecialWager,
    setRotationOrder,
    setCaptainIndex,
    setIsHoepfinger,
    setGoatId,
    setPhase,
    setAardvarkRequestedTeam,
    setAardvarkTossed,
    setAardvarkSolo,
    setInvisibleAardvarkTossed,
    setHoleHistory,
    setPlayerStandings,
  };
};

export default useGameActions;
