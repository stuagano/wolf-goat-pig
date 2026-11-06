// frontend/src/components/game/scorekeeper/scorekeeperHandlers.js
// Per-render event handlers for SimpleScorekeeper (team/captain toggles,
// score entry, hitting-order edits, player rename, hole jump). Moved verbatim;
// no React hooks here — the handlers are rebuilt every render exactly as the
// inline closures were.

import { apiConfig } from "../../../config/api.config";
import { fetchJson } from "../../../services/fetchJson";
import { aiPartnerResponse } from "../../../utils/stuartModeAiDecisions";
import { nudgeHittingOrder } from "../../../utils/hittingOrder";

const API_URL = apiConfig.baseUrl;

const buildScorekeeperHandlers = ({
  gameId,
  players,
  localPlayers,
  setLocalPlayers,
  team1,
  setTeam1,
  captain,
  setCaptain,
  setOpponents,
  stuartMode,
  currentHole,
  setCurrentHole,
  strokeAllocation,
  playerStandings,
  setPlayerStandings,
  setAiMoves,
  addBettingEvent,
  scores,
  setScores,
  rotationOrder,
  reorderHittingOrder,
  setRotationOrder,
  setPendingOffer,
  setCurrentHoleBettingEvents,
  setShowTeamSelection,
  setShowTeeToss,
  setEditingOrder,
  editingPlayerName,
  editPlayerNameValue,
  handleCancelPlayerNameEdit,
  holeHistory,
  setEditModalHole,
  resetHole,
}) => {
  // Handle team selection for partners mode
  // Toggle players in/out of Team 1. Team 2 is automatically all other players.
  const togglePlayerTeam = (playerId) => {
    if (team1.includes(playerId)) {
      // Remove from team1 (they'll go to team2 automatically)
      setTeam1(team1.filter((id) => id !== playerId));
      return;
    }

    // Stuart Mode: when adding an AI player as partner, run their accept
    // /decline heuristic. Decline = don't add + log; accept = add + log.
    if (stuartMode) {
      const target = players.find((p) => p.id === playerId);
      if (target && !target.is_authenticated) {
        const result = aiPartnerResponse({
          aiPlayer: target,
          currentHole,
          strokeAllocation,
          playerStandings,
        });
        setAiMoves((prev) => [
          ...prev,
          {
            type: "partner",
            text:
              result.decision === "accept"
                ? `🤖 ${target.name} accepts partnership — ${result.reason}`
                : `🤖 ${target.name} declines partnership — ${result.reason}`,
            timestamp: Date.now(),
          },
        ]);
        if (result.decision === "decline") return; // don't add
      }
    }

    // Add to team1
    setTeam1([...team1, playerId]);
  };

  // Handle captain selection for solo mode
  const toggleCaptain = (playerId) => {
    if (captain === playerId) {
      setCaptain(null);
    } else {
      setCaptain(playerId);
      // Set all other players as opponents
      setOpponents(players.filter((p) => p.id !== playerId).map((p) => p.id));
    }
  };

  // Announce an action (Duncan, Option Off) - no accept needed
  const announceAction = (actionType, announcedBy) => {
    addBettingEvent({
      eventType: `${actionType.toUpperCase()}_ANNOUNCED`,
      announced_by: announcedBy,
      actor: announcedBy,
    });
  };

  // Handle score input
  const handleScoreChange = (playerId, value) => {
    setScores({
      ...scores,
      [playerId]: parseInt(value, 10) || 0,
    });
  };

  // Correct the hitting order after the game has started: first player becomes
  // captain, current-hole teams/specials clear, and the order sticks for the
  // rest of the round (tee_order is what a reload rebuilds rotation from).
  const applyHittingOrder = async (newOrder) => {
    const previousOrder = rotationOrder;
    reorderHittingOrder(newOrder);
    // Interactive betting lives outside the game reducer
    setPendingOffer(null);
    setCurrentHoleBettingEvents([]);
    setShowTeamSelection(true);

    try {
      await fetchJson(`${API_URL}/games/${gameId}/tee-order`, {
        method: "PATCH",
        body: JSON.stringify({ player_order: newOrder }),
      });
    } catch (error) {
      console.error("Error updating hitting order:", error);
      setRotationOrder(previousOrder);
    }
  };

  const movePlayerInOrder = async (fromIndex, direction) => {
    const newOrder = nudgeHittingOrder(rotationOrder, fromIndex, direction);
    if (newOrder === rotationOrder) return;

    await applyHittingOrder(newOrder);
  };

  const handleTeeTossComplete = async (orderedPlayers) => {
    const newOrder = orderedPlayers.map((p) => p.id);
    setShowTeeToss(false);
    setEditingOrder(false);
    await applyHittingOrder(newOrder);
  };

  const handleSavePlayerName = async () => {
    if (!editingPlayerName || !editPlayerNameValue.trim()) {
      return;
    }

    try {
      await fetchJson(
        `${API_URL}/games/${gameId}/players/${editingPlayerName}/name`,
        {
          method: "PATCH",
          body: JSON.stringify({ name: editPlayerNameValue.trim() }),
        },
      );

      // Update local players state immediately for better UX
      const updatedPlayers = localPlayers.map((p) =>
        p.id === editingPlayerName
          ? { ...p, name: editPlayerNameValue.trim() }
          : p,
      );
      setLocalPlayers(updatedPlayers);

      // Also update player standings
      if (playerStandings[editingPlayerName]) {
        setPlayerStandings({
          ...playerStandings,
          [editingPlayerName]: {
            ...playerStandings[editingPlayerName],
            name: editPlayerNameValue.trim(),
          },
        });
      }

      // Close the edit modal
      handleCancelPlayerNameEdit();
    } catch (err) {
      console.error("Failed to update player name:", err);
      alert("Failed to update player name. Please try again.");
    }
  };

  // Direct hole jump - open edit modal for completed holes
  const jumpToHole = (holeNumber) => {
    const holeData = holeHistory.find((h) => h.hole === holeNumber);
    if (holeData) {
      setEditModalHole(holeData);
    } else {
      setCurrentHole(holeNumber);
      resetHole({ holeNumber, holeHistory });
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return {
    togglePlayerTeam,
    toggleCaptain,
    announceAction,
    handleScoreChange,
    movePlayerInOrder,
    handleTeeTossComplete,
    handleSavePlayerName,
    jumpToHole,
  };
};

export default buildScorekeeperHandlers;
