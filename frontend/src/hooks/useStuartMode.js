// frontend/src/hooks/useStuartMode.js
// Stuart Mode orchestration for SimpleScorekeeper: the hidden toggle
// listeners, AI score pre-fill, per-hole reset, AI captain decisions at
// tee/after-tee, AI double offer/response, and the move log.
//
// All effects moved VERBATIM from SimpleScorekeeper.jsx. The single object
// parameter is destructured immediately so every dependency array below is
// byte-identical to the original. Call-order note: this hook must be invoked
// before the course-data/rotation effects in the parent (it was the first
// effect cluster in the original component).

import { useState, useEffect, useMemo, useRef } from "react";
import { prefillAiScores } from "../utils/stuartModeSimulation";
import {
  aiCaptainDecide,
  aiDoubleResponse,
  aiShouldOfferDouble,
} from "../utils/stuartModeAiDecisions";

const useStuartMode = ({
  stuartMode,
  toggleStuartMode,
  gameId,
  players,
  courseData,
  currentHole,
  scores,
  setScores,
  rotationOrder,
  captainIndex,
  teamMode,
  team1,
  captain,
  setTeamMode,
  setCaptain,
  setTeam1,
  strokeAllocation,
  playerStandings,
  currentWager,
  pendingOffer,
  respondToOffer,
  createOffer,
}) => {
  const [aiMoves, setAiMoves] = useState([]); // Stuart Mode: log of AI decisions for the current hole
  const [holePhase, setHolePhase] = useState("tee"); // 'tee' | 'after-tee' | 'green'

  // Hidden Stuart Mode toggle. Two activation paths so it works without a
  // keyboard on mobile, both leading to the same persisted state in
  // localStorage (wgp_stuart_mode via useUIState):
  //   - Desktop: Cmd/Ctrl+Shift+S
  //   - Touch / mouse: long-press (1.5s) anywhere on a non-interactive
  //     part of the page. Pointermove > 10px cancels so a scroll doesn't
  //     trigger it.
  useEffect(() => {
    const INTERACTIVE_SELECTOR =
      'button, input, select, textarea, a, label, [role="button"], [contenteditable="true"]';

    const handleKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === "S" || e.key === "s")) {
        e.preventDefault();
        toggleStuartMode();
      }
    };

    let pressTimer = null;
    let pressStart = null;
    const cancelPress = () => {
      if (pressTimer) {
        clearTimeout(pressTimer);
        pressTimer = null;
      }
      pressStart = null;
    };
    const handlePointerDown = (e) => {
      if (e.target?.closest?.(INTERACTIVE_SELECTOR)) return;
      pressStart = { x: e.clientX, y: e.clientY };
      pressTimer = setTimeout(() => {
        pressTimer = null;
        toggleStuartMode();
      }, 1500);
    };
    const handlePointerMove = (e) => {
      if (!pressStart) return;
      const dx = e.clientX - pressStart.x;
      const dy = e.clientY - pressStart.y;
      if (dx * dx + dy * dy > 100) cancelPress();
    };

    window.addEventListener("keydown", handleKey);
    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("pointerup", cancelPress);
    document.addEventListener("pointercancel", cancelPress);
    document.addEventListener("pointermove", handlePointerMove);
    return () => {
      cancelPress();
      window.removeEventListener("keydown", handleKey);
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("pointerup", cancelPress);
      document.removeEventListener("pointercancel", cancelPress);
      document.removeEventListener("pointermove", handlePointerMove);
    };
  }, [toggleStuartMode]);

  // Stuart Mode score pre-fill: when on, generate plausible gross scores for
  // any non-authenticated player who hasn't been scored yet on this hole.
  // Stuart can override any field — this only fills empties.
  useEffect(() => {
    if (!stuartMode || !players?.length) return;
    const hole = courseData?.holes?.find((h) => h.hole_number === currentHole);
    const updated = prefillAiScores({
      players,
      currentScores: scores,
      par: hole?.par || 4,
      strokeIndex: hole?.handicap || 9,
      gameId,
      hole: currentHole,
    });
    const changed = Object.keys(updated).some((k) => updated[k] !== scores[k]);
    if (changed) setScores(updated);
  }, [stuartMode, currentHole, players, courseData, gameId, scores, setScores]);

  // Stuart Mode: clear AI moves and reset hole phase when the hole changes.
  useEffect(() => {
    setAiMoves([]);
    setHolePhase("tee");
  }, [currentHole]);


  // Stuart Mode @ tee phase: AI captain decides whether to call solo
  // BEFORE seeing tee shots (Duncan-style). If it would partner, it
  // waits — partner pick happens after the tee phase.
  useEffect(() => {
    if (!stuartMode || holePhase !== "tee") return;
    if (!players?.length || !rotationOrder?.length) return;
    if (team1.length > 0 || captain) return;

    const aiCaptainId = rotationOrder[captainIndex];
    const aiCaptain = players.find((p) => p.id === aiCaptainId);
    if (!aiCaptain || aiCaptain.is_authenticated) return;

    const decision = aiCaptainDecide({
      captain: aiCaptain,
      players,
      currentHole,
      strokeAllocation,
      playerStandings,
    });

    const t = setTimeout(() => {
      if (decision.mode === "solo") {
        setTeamMode("solo");
        setCaptain(aiCaptain.id);
        setAiMoves((prev) => [
          ...prev,
          {
            type: "captain",
            text: `🤖 ${aiCaptain.name} calls solo before tee — ${decision.reason}`,
            timestamp: Date.now(),
          },
        ]);
      } else {
        setAiMoves((prev) => [
          ...prev,
          {
            type: "captain-wait",
            text: `🤖 ${aiCaptain.name} waits to see tee shots`,
            timestamp: Date.now(),
          },
        ]);
      }
    }, 800);
    return () => clearTimeout(t);
  }, [
    stuartMode,
    holePhase,
    currentHole,
    rotationOrder,
    captainIndex,
    players,
    team1.length,
    captain,
    strokeAllocation,
    playerStandings,
    setTeamMode,
    setCaptain,
  ]);

  // Stuart Mode @ after-tee phase: if the AI captain didn't go solo at
  // tee, they now pick their partner (having "seen" the tee shots).
  useEffect(() => {
    if (!stuartMode || holePhase !== "after-tee") return;
    if (!players?.length || !rotationOrder?.length) return;
    if (team1.length > 0 || captain) return;

    const aiCaptainId = rotationOrder[captainIndex];
    const aiCaptain = players.find((p) => p.id === aiCaptainId);
    if (!aiCaptain || aiCaptain.is_authenticated) return;

    const decision = aiCaptainDecide({
      captain: aiCaptain,
      players,
      currentHole,
      strokeAllocation,
      playerStandings,
    });
    if (decision.mode !== "partners" || !decision.partnerId) return;

    const t = setTimeout(() => {
      setTeamMode("partners");
      setTeam1([aiCaptain.id, decision.partnerId]);
      setAiMoves((prev) => [
        ...prev,
        {
          type: "captain",
          text: `🤖 ${decision.reason}`,
          timestamp: Date.now(),
        },
      ]);
    }, 800);
    return () => clearTimeout(t);
  }, [
    stuartMode,
    holePhase,
    currentHole,
    rotationOrder,
    captainIndex,
    players,
    team1.length,
    captain,
    strokeAllocation,
    playerStandings,
    setTeamMode,
    setTeam1,
  ]);

  // Stuart Mode: which side is each player on for this hole. In partners
  // mode, team1 vs team2; in solo mode, captain vs opponents.
  const stuartTeamInfo = useMemo(() => {
    const stuart = players?.find((p) => p.is_authenticated);
    if (!stuart) return null;
    const sideOf = (id) => {
      if (teamMode === "solo") return captain === id ? "captain" : "opponents";
      return team1.includes(id) ? "team1" : "team2";
    };
    const stuartSide = sideOf(stuart.id);
    const isStuartResponseTurn = pendingOffer
      ? sideOf(pendingOffer.offered_by) !== stuartSide
      : false;
    return { stuart, stuartSide, sideOf, isStuartResponseTurn };
  }, [players, teamMode, team1, captain, pendingOffer]);

  // Stuart Mode: AI auto-responds when it's the AI team's turn to answer.
  useEffect(() => {
    if (!stuartMode || !pendingOffer || !stuartTeamInfo) return;
    if (stuartTeamInfo.isStuartResponseTurn) return; // Stuart will click

    const { sideOf } = stuartTeamInfo;
    const offerSide = sideOf(pendingOffer.offered_by);
    const responders = players.filter((p) => sideOf(p.id) !== offerSide);
    const representative = responders[0];
    if (!representative) return;

    const result = aiDoubleResponse({
      aiPlayer: representative,
      currentHole,
      strokeAllocation,
      playerStandings,
      currentWager,
    });

    const timer = setTimeout(() => {
      respondToOffer(result.decision, representative.id);
      setAiMoves((prev) => [
        ...prev,
        {
          type: "double-response",
          text: `🤖 ${representative.name} ${result.decision === "accept" ? "accepts" : "declines"} the double — ${result.reason}`,
          timestamp: Date.now(),
        },
      ]);
    }, 700);
    return () => clearTimeout(timer);
  }, [
    stuartMode,
    pendingOffer,
    stuartTeamInfo,
    players,
    currentHole,
    strokeAllocation,
    playerStandings,
    currentWager,
    respondToOffer,
  ]);

  // Stuart Mode: at each phase entry, AI considers offering a double.
  // One attempt per (hole, phase). Phase is part of the hash gate inside
  // aiShouldOfferDouble so each phase rolls independently.
  const offerCheckedPhasesRef = useRef({});
  useEffect(() => {
    if (!stuartMode || !stuartTeamInfo) return;
    const key = `${currentHole}|${holePhase}`;
    if (offerCheckedPhasesRef.current[key]) return;

    const teamReady = teamMode === "solo" ? !!captain : team1.length >= 2;
    if (!teamReady) return;
    offerCheckedPhasesRef.current[key] = true;

    const { sideOf, stuartSide } = stuartTeamInfo;
    const aiTeamPlayers = players.filter(
      (p) => !p.is_authenticated && sideOf(p.id) !== stuartSide,
    );

    const result = aiShouldOfferDouble({
      aiTeamPlayers,
      currentHole,
      strokeAllocation,
      playerStandings,
      currentWager,
      phase: holePhase,
    });
    if (!result) return;

    const timer = setTimeout(() => {
      createOffer("double", result.player.id);
      setAiMoves((prev) => [
        ...prev,
        {
          type: "double-offer",
          text: `🤖 ${result.player.name} offers double @ ${holePhase} — ${result.reason}`,
          timestamp: Date.now(),
        },
      ]);
    }, 1200);
    return () => clearTimeout(timer);
  }, [
    stuartMode,
    currentHole,
    holePhase,
    teamMode,
    team1.length,
    captain,
    stuartTeamInfo,
    players,
    strokeAllocation,
    playerStandings,
    currentWager,
    createOffer,
  ]);

  return { aiMoves, setAiMoves, holePhase, setHolePhase, stuartTeamInfo };
};

export default useStuartMode;
