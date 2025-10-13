import React, { useState, useEffect } from "react";
import { useGame } from "../../context";
import { simulationConfig } from "../../config/environment";
import { getSimulationMock } from "./__fixtures__";
import { GameSetup, GamePlay, EnhancedSimulationLayout } from "./";
import TurnBasedInterface from "./TurnBasedInterface";
// import { Timeline, PokerBettingPanel } from "./"; // Removed - not currently used
// import TVPokerLayout from "../game/TVPokerLayout"; // Removed - not currently used

const {
  apiUrl: SIMULATION_API_URL,
  useMocks: USE_SIMULATION_MOCKS,
  mockPreset: SIMULATION_MOCK_PRESET,
} = simulationConfig;

// Helper function to safely serialize error details
const formatErrorDetail = (detail) => {
  if (typeof detail === 'object' && detail !== null) {
    return JSON.stringify(detail);
  }
  return detail;
};

function SimulationMode() {
  // const theme = useTheme(); // Unused for now
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

  // Timeline and Poker state
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [pokerState, setPokerState] = useState({});
  const [bettingOptions, setBettingOptions] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [mockStep, setMockStep] = useState(0);
  
  // Turn-based mode state
  const [useTurnBasedMode, setUseTurnBasedMode] = useState(true);
  const [turnBasedState, setTurnBasedState] = useState(null);

  // Setup state
  const [humanPlayer, setHumanPlayer] = useState({
    id: "human",
    name: "",
    handicap: 18,
    strength: "Average",
    is_human: true
  });
  const [computerPlayers, setComputerPlayers] = useState([]);
  const [suggestedOpponents, setSuggestedOpponents] = useState([]);
  const [personalities, setPersonalities] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [courses, setCourses] = useState({});
  
  // Hole decisions - setHoleDecisions used for resetting state between simulations
  const [, setHoleDecisions] = useState({
    action: null,
    requested_partner: null,
    offer_double: false,
    accept_double: false
  });
  
  // Note: interactionNeeded and setInteractionNeeded come from useGame() context above
  // const [pendingDecision, setPendingDecision] = useState({}); // Also from context

  // New state for shot-by-shot simulation
  // Note: All simulation state (shotProbabilities, shotState, hasNextShot, etc.) comes from useGame() context above

  // GHIN lookup functionality removed - was not being used in current UI

  // GHIN lookup functions removed - functionality not currently exposed in UI

  const isMockSessionEnabled = USE_SIMULATION_MOCKS;

  const resolveMockPreset = () => getSimulationMock(SIMULATION_MOCK_PRESET);

  const pushMockTimelineEvent = (partialEvent) => {
    setTimelineEvents((previous) => [
      {
        id: partialEvent.id || `mock-event-${Date.now()}`,
        timestamp: partialEvent.timestamp || new Date().toISOString(),
        ...partialEvent,
      },
      ...previous,
    ]);
  };

  const hydrateMockSetup = () => {
    if (!isMockSessionEnabled) {
      return;
    }

    const preset = resolveMockPreset();
    if (!preset) {
      return;
    }

    const { setup, gameState: presetGameState } = preset;

    if (setup) {
      setPersonalities(setup.personalities || []);
      setSuggestedOpponents(setup.opponents || []);
      setCourses(setup.courses || {});

      if (Array.isArray(setup.opponents) && setup.opponents.length > 0) {
        setComputerPlayers(
          setup.opponents.slice(0, 3).map((opponent, index) => ({
            id: opponent.id || `mock-opponent-${index + 1}`,
            name: opponent.name,
            handicap: opponent.handicap,
            personality: opponent.personality,
            is_human: false,
          }))
        );
      }
    }

    if (presetGameState?.players) {
      const humanPlayerFromPreset = presetGameState.players.find(
        (player) => player?.is_human || player?.id === "human"
      );

      if (humanPlayerFromPreset) {
        setHumanPlayer((prev) => ({
          ...prev,
          ...humanPlayerFromPreset,
        }));
      }
    }
  };

  const runMockSimulation = () => {
    const preset = resolveMockPreset();
    if (!preset) {
      return;
    }

    setGameState(preset.gameState);
    startGame(preset.gameState);
    setShotState(preset.shotState || null);
    setShotProbabilities(preset.shotProbabilities || null);
    setHasNextShot(
      preset.hasNextShot !== undefined ? Boolean(preset.hasNextShot) : true
    );
    setInteractionNeeded(preset.interactionNeeded || null);

    clearFeedback();
    (preset.feedback || []).forEach((entry) => addFeedback(entry));

    setTimelineEvents(preset.timelineEvents || []);
    setPokerState(preset.pokerState || {});
    setBettingOptions(preset.bettingOptions || []);
    setMockStep(0);
  };

  const handleMockDecision = (decision) => {
    if (!isMockSessionEnabled) {
      return;
    }

    if (decision.offer_double !== undefined) {
      handleBettingAction(
        decision.offer_double ? 'offer_double' : 'decline_double',
        {
          label: decision.offer_double ? 'Offer Double' : 'Decline Double',
        }
      );
      setInteractionNeeded(null);
      setPendingDecision({});
      return;
    }

    if (decision.accept_double !== undefined) {
      handleBettingAction(
        decision.accept_double ? 'accept_double' : 'decline_double',
        {
          label: decision.accept_double ? 'Accept Double' : 'Decline Double',
        }
      );
      setInteractionNeeded(null);
      setPendingDecision({});
      return;
    }

    if (decision.accept_partnership !== undefined) {
      const accepted = Boolean(decision.accept_partnership);
      pushMockTimelineEvent({
        type: accepted ? 'partnership' : 'solo',
        description: accepted
          ? 'Mock: Partnership accepted. Robots brace for teamwork.'
          : 'Mock: Partnership declined. Captain must go solo.',
      });
      addFeedback(
        accepted
          ? '✅ Mock confirmation: partnership locked in.'
          : '⚠️ Mock decline: prepare for solo play.'
      );

      if (!accepted) {
        handleBettingAction('offer_double', { label: 'Forced Solo Double' });
      }

      setInteractionNeeded(null);
      setPendingDecision({});
      return;
    }

    if (decision.action === 'request_partner') {
      const partnerId = decision.requested_partner;
      const partnerName =
        gameState?.players?.find((player) => player.id === partnerId)?.name || partnerId || 'selected partner';

      pushMockTimelineEvent({
        type: 'partnership',
        description: `Mock: You selected ${partnerName} as your partner.`,
      });

      addFeedback(`🤝 Mock partner secured: ${partnerName}`);

      const pressurePreset = getSimulationMock('pressureDouble');
      setInteractionNeeded(pressurePreset.interactionNeeded || null);
      setShotState(pressurePreset.shotState || shotState);
      setShotProbabilities(pressurePreset.shotProbabilities || shotProbabilities);
      setBettingOptions(pressurePreset.bettingOptions || bettingOptions);
      setPokerState((previous) => ({
        ...previous,
        ...pressurePreset.pokerState,
      }));
      setMockStep((previous) => previous + 1);
      setPendingDecision({});
      return;
    }

    if (decision.action === 'go_solo') {
      pushMockTimelineEvent({
        type: 'solo',
        description: 'Mock: Captain elects to go solo and press the wager.',
      });
      addFeedback('🚀 Mock solo play engaged. The wager has been doubled.');
      handleBettingAction('offer_double', { label: 'Mock Solo Double' });
      setInteractionNeeded(null);
      setPendingDecision({});
      return;
    }

    if (decision.action === 'keep_watching') {
      pushMockTimelineEvent({
        type: 'captain',
        description: 'Mock: Captain keeps observing robot tee shots.',
      });
      addFeedback('👀 Mock mode: continuing to observe tee shots.');
      setInteractionNeeded(null);
      setPendingDecision({});
      return;
    }

    pushMockTimelineEvent({
      type: 'info',
      description: `Mock decision recorded: ${JSON.stringify(decision)}`,
    });
    addFeedback('ℹ️ Mock decision logged. No backend action triggered.');
    setInteractionNeeded(null);
    setPendingDecision({});
  };

  useEffect(() => {
    if (isMockSessionEnabled) {
      hydrateMockSetup();
      return;
    }

    fetchInitialData();
  }, []);
  
  // Fetch turn-based state when game is active
  useEffect(() => {
    if (isGameActive && useTurnBasedMode && !isMockSessionEnabled) {
      fetchTurnBasedState();
      const interval = setInterval(fetchTurnBasedState, 2000); // Poll every 2 seconds
      return () => clearInterval(interval);
    }
  }, [isGameActive, useTurnBasedMode]);
  
  const fetchInitialData = async () => {
    if (isMockSessionEnabled) {
      return;
    }

    try {
      const [personalitiesRes, opponentsRes, coursesRes] = await Promise.all([
        fetch(`${SIMULATION_API_URL}/simulation/available-personalities`),
        fetch(`${SIMULATION_API_URL}/simulation/suggested-opponents`),
        fetch(`${SIMULATION_API_URL}/courses`)
      ]);
      
      const personalitiesData = await personalitiesRes.json();
      const opponentsData = await opponentsRes.json();
      const coursesData = await coursesRes.json();
      
      setPersonalities(personalitiesData.personalities || []);
      setSuggestedOpponents(opponentsData.opponents || []);
      setCourses(coursesData || {});
      
      // Set default computer players
      if (opponentsData.opponents && opponentsData.opponents.length >= 3) {
        setComputerPlayers([
          { id: "comp1", ...opponentsData.opponents[0], is_human: false },
          { id: "comp2", ...opponentsData.opponents[1], is_human: false },
          { id: "comp3", ...opponentsData.opponents[2], is_human: false }
        ]);
      }
    } catch (error) {
      console.error("Error fetching initial data:", error);
    }
  };
  
  const startSimulation = async () => {
    if (!isMockSessionEnabled && !humanPlayer.name.trim()) {
      alert("Please enter your name");
      return;
    }

    setLoading(true);
    try {
      // Reset all local state for new simulation
      setGameState(null);
      endGame();  // Use endGame directly instead of setIsGameActive
      clearFeedback();
      setShotProbabilities(null);
      setShotState(null);
      setHasNextShot(true);
      setInteractionNeeded(null);
      setPendingDecision({});
      setHoleDecisions({
        action: null,
        requested_partner: null,
        offer_double: false,
        accept_double: false
      });
      // GHIN lookup state reset removed - functionality not currently used

      setMockStep(0);

      if (isMockSessionEnabled) {
        runMockSimulation();
        setLoading(false);
        return;
      }

      const response = await fetch(`${SIMULATION_API_URL}/simulation/setup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          human_player: humanPlayer,
          computer_players: computerPlayers,
          course_name: selectedCourse || null
        })
      });
      
      const data = await response.json();
      if (data.status === "ok") {
        // First set the game state
        setGameState(data.game_state);
        
        // Then start the game with the new state
        startGame(data.game_state);
        
        // Set initial feedback
        clearFeedback();
        if (data.feedback && Array.isArray(data.feedback)) {
          data.feedback.forEach((msg) => addFeedback(msg));
        } else {
          addFeedback(data.message || "Simulation started!");
        }
        
        // Set next shot availability from the response
        if (data.next_shot_available !== undefined) {
          setHasNextShot(data.next_shot_available);
        } else {
          setHasNextShot(true);  // Default to true after setup
        }
        
        // Don't immediately play next shot - let the user initiate
        // This prevents race conditions and gives user control
      } else {
        alert("Error starting simulation: " + (formatErrorDetail(data.detail) || "Unknown error"));
      }
    } catch (error) {
      console.error("Error starting simulation:", error);
      alert("Error starting simulation");
    } finally {
      if (!isMockSessionEnabled) {
        setLoading(false);
      }
    }
  };

  // Fetch timeline events from backend
  const fetchTimelineEvents = async () => {
    if (!isGameActive || isMockSessionEnabled) return;
    
    try {
      setTimelineLoading(true);
      const response = await fetch(`${SIMULATION_API_URL}/simulation/timeline`);
      if (response.ok) {
        const data = await response.json();
        setTimelineEvents(data.events || []);
      }
    } catch (error) {
      console.error("Error fetching timeline:", error);
    } finally {
      setTimelineLoading(false);
    }
  };

  // Fetch poker-style betting state
  const fetchPokerState = async () => {
    if (!isGameActive || isMockSessionEnabled) return;
    
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
        setBettingOptions(data.betting_options || []);
      }
    } catch (error) {
      console.error("Error fetching poker state:", error);
    }
  };

  // Handle poker-style betting actions
  const handleBettingAction = async (action, option) => {
    if (isMockSessionEnabled) {
      const label = option?.label || action;
      const currentWager = gameState?.betting?.current_wager ?? gameState?.base_wager ?? 1;
      const updatedWager = action === 'offer_double' ? currentWager * 2 : currentWager;

      setGameState((previous) => {
        if (!previous) {
          return previous;
        }

        return {
          ...previous,
          betting: {
            ...(previous.betting || {}),
            current_wager: updatedWager,
          },
        };
      });

      setPokerState((previous) => ({
        ...previous,
        current_wager:
          action === 'offer_double'
            ? (previous?.current_wager ?? currentWager) * 2
            : previous?.current_wager ?? updatedWager,
        pending_actions: [],
        last_mock_action: action,
      }));

      pushMockTimelineEvent({
        type: action?.includes('double') ? 'double' : 'bet',
        description: `Mock: ${label}`,
      });

      addFeedback(`🃏 Mock betting action captured: ${label}`);
      return;
    }

    try {
      setLoading(true);

      const decision = {
        decision_type: action,
        player_id: 'human',
        amount: option.amount || 0,
        ...option
      };

      const response = await fetch(`${SIMULATION_API_URL}/simulation/betting-decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(decision)
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          // Update game state if provided
          if (result.game_state) {
            setGameState(result.game_state);
          }

          // Refresh timeline and poker state
          await Promise.all([fetchTimelineEvents(), fetchPokerState()]);
        }
      }
    } catch (error) {
      console.error("Error handling betting action:", error);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh timeline and poker state when game is active
  useEffect(() => {
    if (isGameActive && !isMockSessionEnabled) {
      // Initial fetch
      fetchTimelineEvents();
      fetchPokerState();

      // Set up polling for real-time updates
      const interval = setInterval(() => {
        fetchTimelineEvents();
        fetchPokerState();
      }, 3000); // Update every 3 seconds

      return () => clearInterval(interval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isGameActive, gameState?.current_hole, gameState?.hole_state?.current_shot_number]); // fetchTimelineEvents and fetchPokerState are stable
  
  // Removed unused testNewEndpoints function

  // Add the missing makeDecision function and improve interactive flow
  const makeDecision = async (decision) => {
    if (isMockSessionEnabled) {
      handleMockDecision(decision);
      return;
    }

    setLoading(true);
    try {
      // Determine which endpoint to use based on decision type
      let endpoint = '/simulation/play-hole';
      let payload = { ...decision };
      
      // Handle different decision types
      if (decision.action === 'request_partner' || decision.action === 'go_solo' || decision.action === 'keep_watching') {
        // Captain decisions during tee shots
        endpoint = '/simulation/play-hole';
        payload = {
          action: decision.action,
          requested_partner: decision.requested_partner || decision.partner_id
        };
      } else if (decision.accept_partnership !== undefined) {
        // Partnership response
        endpoint = '/simulation/play-hole';
        payload = {
          accept_partnership: decision.accept_partnership
        };
      } else if (decision.offer_double !== undefined) {
        // Doubling decisions
        endpoint = '/simulation/betting-decision';
        payload = {
          action: decision.offer_double ? 'offer_double' : 'decline_double'
        };
      } else if (decision.accept_double !== undefined) {
        // Double response
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
        // Update game state
        setGameState(data.game_state);
        
        // Add feedback messages
        if (data.feedback && Array.isArray(data.feedback)) {
          data.feedback.forEach(msg => addFeedback(msg));
        } else if (data.decision_result?.message) {
          addFeedback(`💰 ${data.decision_result.message}`);
        }
        
        // Handle interaction needed
        if (data.interaction_needed) {
          setInteractionNeeded(data.interaction_needed);
        } else {
          setInteractionNeeded(null);
          setPendingDecision({});
        }
        
        // Update shot state if available
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
        
        // Auto-continue if no interaction needed and shots available
        if (!data.interaction_needed && data.next_shot_available) {
          // Small delay to let user see the feedback
          setTimeout(() => {
            if (!loading && !interactionNeeded) {
              playNextShot();
            }
          }, 1500);
        }
        
      } else {
        throw new Error(data.message || 'Unknown error occurred');
      }
      
    } catch (error) {
      console.error("Error making decision:", error);
      
      // Provide user-friendly error messages
      let errorMessage = "Error making decision: ";
      if (error.message.includes("Backend error: 500")) {
        errorMessage += "Server error - please try again";
      } else if (error.message.includes("Backend error: 400")) {
        errorMessage += "Invalid decision - please check your choice";
      } else if (error.message.includes("fetch")) {
        errorMessage += "Network error - check your connection";
      } else {
        errorMessage += error.message;
      }
      
      // Add error to feedback instead of alert
      addFeedback(`❌ ${errorMessage}`);
      
      // Clear interaction needed to prevent stuck state
      setInteractionNeeded(null);
    } finally {
      setLoading(false);
    }
  };
  
  const playNextShot = async () => {
    if (loading || interactionNeeded) {
      console.log("Cannot play shot:", { loading, interactionNeeded });
      return;
    }

    if (isMockSessionEnabled) {
      const presetName = mockStep % 2 === 0 ? 'pressureDouble' : SIMULATION_MOCK_PRESET;
      const nextPreset = getSimulationMock(presetName);

      pushMockTimelineEvent({
        type: 'shot',
        description:
          nextPreset.shotState?.recommended_shot ||
          `Mock shot progression ${mockStep + 1}.`,
      });

      addFeedback(`🎯 Mock shot advanced (step ${mockStep + 1}).`);

      setGameState((previous) => {
        if (!previous) {
          return nextPreset.gameState || previous;
        }

        const nextHoleState = {
          ...(previous.hole_state || {}),
          ...((nextPreset.gameState && nextPreset.gameState.hole_state) || {}),
          current_shot_number:
            (previous.hole_state?.current_shot_number || 0) + 1,
        };

        return {
          ...previous,
          ...(nextPreset.gameState || {}),
          hole_state: nextHoleState,
        };
      });

      setShotState(nextPreset.shotState || null);
      setShotProbabilities(nextPreset.shotProbabilities || null);
      setInteractionNeeded(nextPreset.interactionNeeded || null);
      setBettingOptions(nextPreset.bettingOptions || bettingOptions);
      setPokerState((previous) => ({
        ...previous,
        ...nextPreset.pokerState,
      }));
      setHasNextShot(
        nextPreset.hasNextShot !== undefined
          ? Boolean(nextPreset.hasNextShot)
          : false
      );
      setMockStep((previous) => previous + 1);
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
        
        // Add feedback from the shot simulation
        if (data.feedback && data.feedback.length > 0) {
          data.feedback.forEach(msg => addFeedback(msg));
        }
        
        // Handle shot result
        if (data.shot_result) {
          addFeedback(`🎯 Shot Result: ${JSON.stringify(data.shot_result)}`);
        }
        
        // Handle interaction needed
        if (data.interaction_needed) {
          setInteractionNeeded(data.interaction_needed);
          setPendingDecision({});
        } else {
          setInteractionNeeded(null);
          setPendingDecision({});
        }
        
        // Update next shot availability
        setHasNextShot(data.next_shot_available);
        
        // Refresh timeline and poker state after shot
        await Promise.all([fetchTimelineEvents(), fetchPokerState()]);
        
      } else {
        throw new Error(data.message || 'Unknown error occurred');
      }
      
    } catch (error) {
      console.error("Error playing next shot:", error);
      
      let errorMessage = "Error playing shot: ";
      if (error.message.includes("Backend error: 500")) {
        errorMessage += "Server error - please try again";
      } else if (error.message.includes("fetch")) {
        errorMessage += "Network error - check your connection";
      } else {
        errorMessage += error.message;
      }
      
      addFeedback(`❌ ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchTurnBasedState = async () => {
    if (isMockSessionEnabled) {
      return;
    }

    try {
      const response = await fetch(`${SIMULATION_API_URL}/simulation/turn-based-state`);
      const data = await response.json();
      
      if (data.success) {
        setTurnBasedState(data.turn_based_state);
      }
    } catch (error) {
      console.error('Error fetching turn-based state:', error);
    }
  };
  
  const resetSimulation = () => {
    setGameState(null);
    endGame();  // Use endGame directly instead of setIsGameActive
    clearFeedback();
    setHoleDecisions({
      action: null,
      requested_partner: null,
      offer_double: false,
      accept_double: false
    });
    setMockStep(0);
  };
  
  if (!isGameActive) {
    return (
      <GameSetup
        humanPlayer={humanPlayer}
        setHumanPlayer={setHumanPlayer}
        computerPlayers={computerPlayers}
        setComputerPlayers={setComputerPlayers}
        selectedCourse={selectedCourse}
        setSelectedCourse={setSelectedCourse}
        courses={courses}
        setCourses={setCourses}
        personalities={personalities}
        setPersonalities={setPersonalities}
        suggestedOpponents={suggestedOpponents}
        setSuggestedOpponents={setSuggestedOpponents}
        onStartGame={startSimulation}
      />
    );
  }

  // Choose interface based on mode preference
  if (useTurnBasedMode && turnBasedState) {
    return (
      <TurnBasedInterface
        gameState={{
          ...gameState,
          ...(turnBasedState.turn_based_state || turnBasedState),
          interactionNeeded,
          hasNextShot,
          feedback
        }}
        onMakeDecision={makeDecision}
        interactionNeeded={interactionNeeded}
        feedback={feedback}
        shotState={shotState}
        onNextShot={playNextShot}
        hasNextShot={hasNextShot}
      />
    );
  }
  
  // Use Enhanced Simulation Layout with Timeline and Poker Betting
  const useEnhancedLayout = true; // TODO: Make this a user preference

  if (useEnhancedLayout) {
    return (
      <EnhancedSimulationLayout
        gameState={gameState}
        shotState={shotState}
        probabilities={shotProbabilities}
        onDecision={makeDecision}
        onPlayNextShot={playNextShot}
        timelineEvents={timelineEvents}
        timelineLoading={timelineLoading}
        pokerState={pokerState}
        bettingOptions={bettingOptions}
        onBettingAction={handleBettingAction}
        currentPlayer="human"
        interactionNeeded={interactionNeeded}
        hasNextShot={hasNextShot}
        feedback={feedback}
      />
    );
  }

  return (
    <GamePlay
      gameState={gameState}
      onEndSimulation={resetSimulation}
      interactionNeeded={interactionNeeded}
      onMakeDecision={makeDecision}
      feedback={feedback}
      shotState={shotState}
      shotProbabilities={shotProbabilities}
      onNextShot={playNextShot}
      hasNextShot={hasNextShot}
    />
  );
}

export default SimulationMode;
