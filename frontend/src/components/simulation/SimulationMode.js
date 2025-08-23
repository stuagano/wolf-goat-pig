import React, { useState, useEffect } from "react";
import { useGame } from "../../context";
import { GameSetup, GamePlay } from "./";
import TVPokerLayout from "../game/TVPokerLayout";

const API_URL = process.env.REACT_APP_API_URL || "";

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

  // Helper functions for missing setters
  const setFeedback = (message) => {
    clearFeedback();
    if (message) addFeedback(message);
  };
  
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

  useEffect(() => {
    fetchInitialData();
  }, []);
  
  const fetchInitialData = async () => {
    try {
      const [personalitiesRes, opponentsRes, coursesRes] = await Promise.all([
        fetch(`${API_URL}/simulation/available-personalities`),
        fetch(`${API_URL}/simulation/suggested-opponents`),
        fetch(`${API_URL}/courses`)
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
    if (!humanPlayer.name.trim()) {
      alert("Please enter your name");
      return;
    }
    
    setLoading(true);
    try {
      // Reset all local state for new simulation
      setGameState(null);
      endGame();  // Use endGame directly instead of setIsGameActive
      setFeedback([]);
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
      
      const response = await fetch(`${API_URL}/simulation/setup`, {
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
        if (data.feedback && Array.isArray(data.feedback)) {
          setFeedback(data.feedback);
        } else {
          setFeedback([data.message || "Simulation started!"]);
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
        alert("Error starting simulation: " + (data.detail || "Unknown error"));
      }
    } catch (error) {
      console.error("Error starting simulation:", error);
      alert("Error starting simulation");
    } finally {
      setLoading(false);
    }
  };
  
  // Removed unused testNewEndpoints function

  // Add the missing makeDecision function and improve interactive flow
  const makeDecision = async (decision) => {
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

      const response = await fetch(`${API_URL}${endpoint}`, {
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
        
        // Show probabilities if available
        if (data.probabilities) {
          setShotProbabilities(data.probabilities);
        }
        
        // Show betting probabilities if available
        if (data.betting_probabilities) {
          setShotProbabilities(prev => ({
            ...prev,
            betting_analysis: data.betting_probabilities
          }));
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
    console.log("playNextShot called", { loading, interactionNeeded, API_URL });
    if (loading || interactionNeeded) return;
    
    setLoading(true);
    console.log("Calling API:", `${API_URL}/simulation/play-next-shot`);
    try {
      const response = await fetch(`${API_URL}/simulation/play-next-shot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pendingDecision)
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend error: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      console.log("API Response:", data);
      
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
      
      setFeedback(prev => [...prev, `❌ ${errorMessage}`]);
    } finally {
      setLoading(false);
    }
  };
  
  const resetSimulation = () => {
    setGameState(null);
    endGame();  // Use endGame directly instead of setIsGameActive
    setFeedback([]);
    setHoleDecisions({
      action: null,
      requested_partner: null,
      offer_double: false,
      accept_double: false
    });
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

  // Use TV Poker Layout if enabled (you can toggle this with a setting)
  const useTVLayout = true; // TODO: Make this a user preference

  if (useTVLayout) {
    return (
      <TVPokerLayout
        gameState={{
          ...gameState,
          interactionNeeded,
          hasNextShot,
          feedback
        }}
        shotState={shotState}
        probabilities={shotProbabilities}
        onDecision={makeDecision}
        autoPlayEnabled={true}
        playSpeed="normal"
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
