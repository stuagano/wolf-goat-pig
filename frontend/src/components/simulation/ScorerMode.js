// frontend/src/components/simulation/ScorerMode.js
import React, { useState, useEffect, useCallback } from "react";
import { useGame } from "../../context";
import { simulationConfig } from "../../config/environment";
import { SimulationVisualInterface } from "./visual";
import RoundSummary from "./RoundSummary";

const {
  apiUrl: SIMULATION_API_URL,
} = simulationConfig;

/**
 * ScorerMode - Simplified single-user mode for scoring without multiplayer setup
 * This bypasses player registration and allows direct access to scoring interface
 */
function ScorerMode() {
  const {
    gameState,
    setGameState,
    isGameActive,
    startGame,
    endGame,
    loading,
    setLoading,
    feedback,
    addFeedback,
    clearFeedback,
    shotState,
    setShotState,
    interactionNeeded,
    setInteractionNeeded,
    pendingDecision,
    setPendingDecision,
    shotProbabilities,
    setShotProbabilities,
    hasNextShot,
    setHasNextShot,
  } = useGame();

  const [pokerState, setPokerState] = useState({});
  const [roundFinished, setRoundFinished] = useState(false);

  // Auto-start a game with default players on mount
  useEffect(() => {
    const autoStartGame = async () => {
      if (isGameActive) return; // Don't restart if already active

      setLoading(true);
      try {
        // Create a quick game with default players for scoring
        const response = await fetch(`${SIMULATION_API_URL}/simulation/setup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            human_player: {
              id: "human",
              name: "Scorer",
              handicap: 18,
              is_human: true
            },
            computer_players: [
              { id: "comp1", name: "Player 2", handicap: 15, is_human: false },
              { id: "comp2", name: "Player 3", handicap: 12, is_human: false },
              { id: "comp3", name: "Player 4", handicap: 20, is_human: false }
            ],
            course_name: null
          })
        });

        const data = await response.json();
        if (data.status === "ok") {
          setGameState(data.game_state);
          startGame(data.game_state);
          clearFeedback();

          if (data.feedback && Array.isArray(data.feedback)) {
            data.feedback.forEach((msg) => addFeedback(msg));
          }

          if (data.interaction_needed) {
            setInteractionNeeded(data.interaction_needed);
          }

          setHasNextShot(data.next_shot_available !== undefined ? data.next_shot_available : true);
        }
      } catch (error) {
        console.error("Error auto-starting scorer mode:", error);
        addFeedback("❌ Error starting scorer mode");
      } finally {
        setLoading(false);
      }
    };

    autoStartGame();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount

  const fetchPokerState = async () => {
    if (!isGameActive) return;

    try {
      const response = await fetch(`${SIMULATION_API_URL}/simulation/poker-state`);
      if (response.ok) {
        const data = await response.json();
        setPokerState({
          pot_size: data.pot_size,
          base_bet: data.base_bet,
          current_bet: data.current_bet,
          betting_phase: data.betting_phase,
          doubled: data.doubled,
          players_in: data.players_in,
          wagering_closed: data.wagering_closed
        });
      }
    } catch (error) {
      console.error("Error fetching poker state:", error);
    }
  };

  useEffect(() => {
    if (isGameActive) {
      fetchPokerState();
      const interval = setInterval(() => {
        fetchPokerState();
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [isGameActive, gameState?.current_hole]);

  const makeDecision = async (decision) => {
    setLoading(true);
    try {
      let endpoint = '/simulation/play-hole';
      let payload = { ...decision };

      if (decision.action === 'request_partner' || decision.action === 'go_solo' || decision.action === 'keep_watching') {
        endpoint = '/simulation/play-hole';
        payload = {
          action: decision.action,
          requested_partner: decision.requested_partner || decision.partner_id
        };
      } else if (decision.accept_partnership !== undefined) {
        endpoint = '/simulation/play-hole';
        payload = {
          accept_partnership: decision.accept_partnership
        };
      } else if (decision.offer_double !== undefined) {
        endpoint = '/simulation/betting-decision';
        payload = {
          action: decision.offer_double ? 'offer_double' : 'decline_double'
        };
      } else if (decision.accept_double !== undefined) {
        endpoint = '/simulation/betting-decision';
        payload = {
          action: decision.accept_double ? 'accept_double' : 'decline_double'
        };
      }

      const response = await fetch(`${SIMULATION_API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();

      if (data.status === "ok") {
        setGameState(data.game_state);

        if (data.feedback && Array.isArray(data.feedback)) {
          data.feedback.forEach(msg => addFeedback(msg));
        } else if (data.decision_result?.message) {
          addFeedback(`💰 ${data.decision_result.message}`);
        }

        if (data.interaction_needed) {
          setInteractionNeeded(data.interaction_needed);
        } else {
          setInteractionNeeded(null);
          setPendingDecision({});
        }

        if (data.next_shot_available !== undefined) {
          setHasNextShot(data.next_shot_available);
        }

        const baseProbabilities =
          data.probabilities && typeof data.probabilities === "object" && !Array.isArray(data.probabilities)
            ? data.probabilities
            : null;

        const bettingAnalysis =
          data.betting_probabilities && typeof data.betting_probabilities === "object"
            ? data.betting_probabilities
            : null;

        if (baseProbabilities || bettingAnalysis) {
          const combinedProbabilities = {
            ...(baseProbabilities || {}),
            ...(bettingAnalysis ? { betting_analysis: bettingAnalysis } : {}),
          };
          setShotProbabilities(combinedProbabilities);
        }

      } else {
        throw new Error(data.message || 'Unknown error occurred');
      }

    } catch (error) {
      console.error("Error making decision:", error);
      addFeedback(`❌ Error making decision: ${error.message}`);
      setInteractionNeeded(null);
    } finally {
      setLoading(false);
    }
  };

  const playNextShot = async () => {
    if (loading) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${SIMULATION_API_URL}/simulation/play-next-shot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pendingDecision)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();

      if (data.status === "ok") {
        setGameState(data.game_state);

        if (data.feedback && data.feedback.length > 0) {
          data.feedback.forEach(msg => addFeedback(msg));
        }

        if (data.interaction_needed) {
          setInteractionNeeded(data.interaction_needed);
          setPendingDecision({});
        } else {
          setInteractionNeeded(null);
          setPendingDecision({});
        }

        setHasNextShot(data.next_shot_available);
        await fetchPokerState();

      } else {
        throw new Error(data.message || 'Unknown error occurred');
      }

    } catch (error) {
      console.error("Error playing next shot:", error);
      addFeedback(`❌ Error playing shot: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const advanceToNextHole = async () => {
    if (loading) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${SIMULATION_API_URL}/simulation/next-hole`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();

      if (data.status === "ok") {
        setGameState(data.game_state);

        if (data.feedback && Array.isArray(data.feedback)) {
          clearFeedback();
          data.feedback.forEach(msg => addFeedback(msg));
        }

        if (data.game_finished) {
          setRoundFinished(true);
          setHasNextShot(false);
          addFeedback("🏆 Round complete! Final results are shown.");
        } else {
          setHasNextShot(true);
          setInteractionNeeded(null);
          setPendingDecision({});
        }

        await fetchPokerState();

      } else {
        throw new Error(data.message || 'Unknown error occurred');
      }

    } catch (error) {
      console.error("Error advancing to next hole:", error);
      addFeedback(`❌ Error advancing hole: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleEditHole = async (editData) => {
    console.log('Editing hole:', editData);
    addFeedback(`📝 Updated Hole ${editData.hole} for player - ${editData.strokes} strokes, ${editData.quarters} quarters`);

    // In a real implementation, this would call a backend endpoint to update the hole data
    // For now, just provide feedback to the user
    // TODO: Implement backend endpoint for editing hole scores
  };

  // Show round summary if game is finished
  if (roundFinished && gameState) {
    return (
      <RoundSummary
        gameState={gameState}
        onPlayAgain={() => {
          setRoundFinished(false);
          endGame();
          // Will auto-restart on next render due to useEffect
        }}
        onExit={() => {
          setRoundFinished(false);
          endGame();
        }}
      />
    );
  }

  // Show loading state until game is ready
  if (!isGameActive || !gameState) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        fontSize: '24px'
      }}>
        🏌️ Loading Scorer Mode...
      </div>
    );
  }

  return (
    <SimulationVisualInterface
      gameState={gameState}
      shotState={shotState}
      shotProbabilities={shotProbabilities}
      interactionNeeded={interactionNeeded}
      hasNextShot={hasNextShot}
      loading={loading}
      pokerState={pokerState}
      feedback={feedback}
      onMakeDecision={makeDecision}
      onNextShot={playNextShot}
      onNextHole={advanceToNextHole}
      onEditHole={handleEditHole}
    />
  );
}

export default ScorerMode;
