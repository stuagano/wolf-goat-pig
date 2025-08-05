import React, { useState, useEffect } from "react";
import { useTheme } from "../../theme/Provider";
import { useGame } from "../../context";
import { GameSetup, GamePlay } from "./";

const API_URL = process.env.REACT_APP_API_URL || "";

function SimulationMode() {
  const theme = useTheme();
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
    createGame,
    makeGameAction
  } = useGame();

  // Helper functions for missing setters
  const setIsGameActive = (active) => active ? startGame(gameState) : endGame();
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
  
  // Hole decisions
  const [holeDecisions, setHoleDecisions] = useState({
    action: null,
    requested_partner: null,
    offer_double: false,
    accept_double: false
  });
  
  // Note: interactionNeeded and setInteractionNeeded come from useGame() context above
  // const [pendingDecision, setPendingDecision] = useState({}); // Also from context

  // New state for shot-by-shot simulation
  // Note: All simulation state (shotProbabilities, shotState, hasNextShot, etc.) comes from useGame() context above

  // GHIN lookup modal state
  const [ghinLookupSlot, setGhinLookupSlot] = useState(null); // 'human' or 'comp1', 'comp2', 'comp3'
  const [ghinLookupFirstName, setGhinLookupFirstName] = useState("");
  const [ghinLookupLastName, setGhinLookupLastName] = useState("");
  const [ghinLookupResults, setGhinLookupResults] = useState([]);
  const [ghinLookupLoading, setGhinLookupLoading] = useState(false);
  const [ghinLookupError, setGhinLookupError] = useState("");

  const openGhinLookup = (slot) => {
    setGhinLookupSlot(slot);
    setGhinLookupFirstName("");
    setGhinLookupLastName("");
    setGhinLookupResults([]);
    setGhinLookupLoading(false);
    setGhinLookupError("");
  };
  const closeGhinLookup = () => {
    setGhinLookupSlot(null);
  };
  const doGhinLookup = async () => {
    if (!ghinLookupLastName.trim()) {
      setGhinLookupError("Last name required");
      return;
    }
    setGhinLookupLoading(true);
    setGhinLookupError("");
    setGhinLookupResults([]);
    try {
      const params = new URLSearchParams({ last_name: ghinLookupLastName, first_name: ghinLookupFirstName });
      const res = await fetch(`${API_URL}/ghin/lookup?${params.toString()}`);
      if (!res.ok) throw new Error("Lookup failed");
      const data = await res.json();
      setGhinLookupResults(data);
      if (data.length === 0) setGhinLookupError("No golfers found");
    } catch (err) {
      setGhinLookupError("Lookup failed");
    } finally {
      setGhinLookupLoading(false);
    }
  };
  const selectGhinGolfer = (golfer) => {
    if (ghinLookupSlot === "human") {
      setHumanPlayer(h => ({ ...h, name: golfer.name, handicap: golfer.handicap || "", is_human: true }));
    } else {
      setComputerPlayers(players => players.map((p, i) => {
        const slotId = `comp${i+1}`;
        return slotId === ghinLookupSlot ? { ...p, name: golfer.name, handicap: golfer.handicap || "", is_human: false } : p;
      }));
    }
    closeGhinLookup();
  };

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
      setIsGameActive(false);
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
      // Reset GHIN lookup state
      setGhinLookupSlot(null);
      setGhinLookupFirstName("");
      setGhinLookupLastName("");
      setGhinLookupResults([]);
      setGhinLookupLoading(false);
      setGhinLookupError("");
      
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
        setGameState(data.game_state);
        setIsGameActive(true);
        setFeedback([data.message || "Simulation started!"]);
        // Immediately trigger the first shot event
        await playNextShot();
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
  
  const testNewEndpoints = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/simulation/test-new-endpoints`);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend error: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      alert(`✅ New endpoints working! ${data.message}`);
    } catch (error) {
      console.error("Error testing endpoints:", error);
      alert("❌ New endpoints not working: " + error.message);
    } finally {
      setLoading(false);
    }
  };

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
          setFeedback(prev => [...prev, ...data.feedback]);
        } else if (data.decision_result?.message) {
          setFeedback(prev => [...prev, `💰 ${data.decision_result.message}`]);
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
      setFeedback(prev => [...prev, `❌ ${errorMessage}`]);
      
      // Clear interaction needed to prevent stuck state
      setInteractionNeeded(null);
    } finally {
      setLoading(false);
    }
  };

  // Enhanced playNextShot with better error handling - using shot-by-shot approach
  const playNextShot = async () => {
    if (loading || interactionNeeded) return;
    
    setLoading(true);
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
      
      if (data.status === "ok") {
        setGameState(data.game_state);
        
        // Add feedback from the shot simulation
        if (data.feedback && data.feedback.length > 0) {
          setFeedback(prev => [...prev, ...data.feedback]);
        }
        
        // Handle shot result
        if (data.shot_result) {
          setFeedback(prev => [...prev, `🎯 Shot Result: ${JSON.stringify(data.shot_result)}`]);
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
  
  const fetchShotProbabilities = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/simulation/shot-probabilities`);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend error: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      if (data.status === "ok") {
        setShotProbabilities(data.probabilities);
      }
    } catch (error) {
      console.error("Error fetching probabilities:", error);
      alert("Error fetching probabilities: " + error.message);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchShotState = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/simulation/current-shot-state`);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend error: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      if (data.status === "ok") {
        setShotState(data.shot_state);
      }
    } catch (error) {
      console.error("Error fetching shot state:", error);
      alert("Error fetching shot state: " + error.message);
    } finally {
      setLoading(false);
    }
  };
  
  const makeBettingDecision = async (decision) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/simulation/betting-decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(decision)
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend error: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      if (data.status === "ok") {
        setGameState(data.game_state);
        setFeedback([...feedback, `💰 ${data.decision_result.message}`]);
        setInteractionNeeded(null);
        
        // Show betting probabilities in feedback
        if (data.betting_probabilities) {
          setShotProbabilities({
            betting_analysis: data.betting_probabilities
          });
        }
      }
    } catch (error) {
      console.error("Error making betting decision:", error);
      alert("Error making betting decision: " + error.message);
    } finally {
      setLoading(false);
    }
  };
  
  const resetSimulation = () => {
    setGameState(null);
    setIsGameActive(false);
    setFeedback([]);
    setHoleDecisions({
      action: null,
      requested_partner: null,
      offer_double: false,
      accept_double: false
    });
  };
  
  const updateComputerPlayer = (index, field, value) => {
    const updated = [...computerPlayers];
    updated[index] = { ...updated[index], [field]: value };
    setComputerPlayers(updated);
  };
  
  const selectSuggestedOpponent = (index, opponentIndex) => {
    const opponent = suggestedOpponents[opponentIndex];
    updateComputerPlayer(index, "name", opponent.name);
    updateComputerPlayer(index, "handicap", opponent.handicap);
    updateComputerPlayer(index, "personality", opponent.personality);
  };


  
  // Check if human is captain
  const isHumanCaptain = gameState?.captain_id === "human";
  
  // Get other players for partnership selection
  const getPartnerOptions = () => {
    if (!gameState) return [];
    return gameState.players.filter(p => p.id !== "human" && p.id !== gameState.captain_id);
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
