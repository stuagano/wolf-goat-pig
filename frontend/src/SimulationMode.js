import React, { useState, useEffect } from "react";

const API_URL = process.env.REACT_APP_API_URL || "";

const COLORS = {
  primary: "#1976d2",
  accent: "#00bcd4",
  warning: "#ff9800",
  error: "#d32f2f",
  success: "#388e3c",
  bg: "#f9fafe",
  card: "#fff",
  border: "#e0e0e0",
  text: "#222",
  muted: "#888",
};

const cardStyle = {
  background: COLORS.card,
  borderRadius: 12,
  boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
  padding: 16,
  marginBottom: 18,
  border: `1px solid ${COLORS.border}`,
};

const buttonStyle = {
  background: COLORS.primary,
  color: "#fff",
  border: "none",
  borderRadius: 8,
  padding: "14px 24px",
  fontWeight: 600,
  fontSize: 16,
  margin: "8px 8px 8px 0",
  cursor: "pointer",
  transition: "background 0.2s",
};

const inputStyle = {
  border: `1px solid ${COLORS.border}`,
  borderRadius: 6,
  padding: "12px 16px",
  fontSize: 16,
  width: "100%",
  margin: "4px 0",
};

const selectStyle = {
  ...inputStyle,
  width: "100%",
};

function SimulationMode() {
  const [gameState, setGameState] = useState(null);
  const [isGameActive, setIsGameActive] = useState(false);
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Setup state
  const [humanPlayer, setHumanPlayer] = useState({
    id: "human",
    name: "",
    handicap: 18,
    strength: "Average"
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
  
  // GHIN lookup state for all slots
  const [ghinSearch, setGhinSearch] = useState({}); // {human: {first_name, last_name}, comp1: {...}, ...}
  const [ghinResults, setGhinResults] = useState({});
  const [ghinLoading, setGhinLoading] = useState({});
  const [ghinError, setGhinError] = useState({});

  // Add state for interactive decisions
  const [interactionNeeded, setInteractionNeeded] = useState(null);
  const [pendingDecision, setPendingDecision] = useState({});

  // New state for shot-by-shot simulation
  const [shotProbabilities, setShotProbabilities] = useState(null);
  const [shotState, setShotState] = useState(null);
  const [hasNextShot, setHasNextShot] = useState(true);

  // Add GHIN lookup modal/inline UI state
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
      setHumanPlayer(h => ({ ...h, name: golfer.name, handicap: golfer.handicap || "" }));
    } else {
      setComputerPlayers(players => players.map((p, i) => {
        const slotId = `comp${i+1}`;
        return slotId === ghinLookupSlot ? { ...p, name: golfer.name, handicap: golfer.handicap || "" } : p;
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
          { id: "comp1", ...opponentsData.opponents[0] },
          { id: "comp2", ...opponentsData.opponents[1] },
          { id: "comp3", ...opponentsData.opponents[2] }
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
      // Optionally reset GHIN lookup state
      setGhinSearch({});
      setGhinResults({});
      setGhinLoading({});
      setGhinError({});
      
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

  // Enhanced playNextShot with better error handling
  const playNextShot = async () => {
    if (loading || interactionNeeded) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/simulation/next-shot`, {
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
        setHasNextShot(data.next_shot_available);
        
        // Add shot result to feedback
        if (data.shot_result) {
          const shotDesc = data.shot_result.shot_description || "Shot completed";
          setFeedback(prev => [...prev, `🏌️ ${shotDesc}`]);
        }
        
        // Handle interaction needed
        if (data.interaction_needed) {
          setInteractionNeeded(data.interaction_needed);
          setPendingDecision({});
        } else {
          setInteractionNeeded(null);
          setPendingDecision({});
        }
        
        // Show probabilities if available
        if (data.probabilities) {
          setShotProbabilities(data.probabilities);
        }
        
        // Show betting opportunity if available
        if (data.betting_opportunity) {
          setInteractionNeeded({
            type: "betting_opportunity",
            message: "A betting opportunity has arisen!",
            opportunity: data.betting_opportunity
          });
        }
        
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

  // GHIN lookup handlers
  const handleGhinSearchChange = (slot, field, value) => {
    setGhinSearch(s => ({ ...s, [slot]: { ...s[slot], [field]: value } }));
  };
  const handleGhinLookup = async (slot) => {
    const search = ghinSearch[slot] || {};
    if (!search.last_name || !search.last_name.trim()) return;
    setGhinLoading(l => ({ ...l, [slot]: true }));
    setGhinError(e => ({ ...e, [slot]: '' }));
    setGhinResults(r => ({ ...r, [slot]: [] }));
    try {
      const params = new URLSearchParams({
        last_name: search.last_name,
        ...(search.first_name ? { first_name: search.first_name } : {})
      });
      const res = await fetch(`${API_URL}/ghin/lookup?${params.toString()}`);
      if (!res.ok) throw new Error('Lookup failed');
      const data = await res.json();
      setGhinResults(r => ({ ...r, [slot]: data }));
    } catch (err) {
      setGhinError(e => ({ ...e, [slot]: err.message }));
    } finally {
      setGhinLoading(l => ({ ...l, [slot]: false }));
    }
  };
  const handleGhinSelect = (slot, golfer) => {
    if (slot === 'human') {
      setHumanPlayer(h => ({ ...h, name: golfer.name, handicap: golfer.handicap || '' }));
    } else {
      setComputerPlayers(players => players.map((p, i) => {
        const slotId = `comp${i+1}`;
        return slotId === slot ? { ...p, name: golfer.name, handicap: golfer.handicap || '' } : p;
      }));
    }
    setGhinResults(r => ({ ...r, [slot]: [] }));
    setGhinSearch(s => ({ ...s, [slot]: '' }));
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
      <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
        <div style={cardStyle}>
          <h2 style={{ color: COLORS.primary, marginBottom: 20 }}>🎮 Wolf Goat Pig Simulation Mode</h2>
          <p style={{ marginBottom: 20 }}>
            Practice Wolf Goat Pig against computer opponents! This mode helps you learn the betting strategies
            and get comfortable with the game mechanics. After each hole, you'll receive educational feedback
            about your decisions.
          </p>
          
          {/* Human Player Setup */}
          <div style={cardStyle}>
            <h3>Your Details</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <label>Your Name:</label>
                <input
                  style={inputStyle}
                  value={humanPlayer.name}
                  onChange={(e) => setHumanPlayer({...humanPlayer, name: e.target.value})}
                  placeholder="Enter your name"
                />
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <label>Your Handicap:</label>
                <input
                  style={inputStyle}
                  type="number"
                  step="0.1"
                  value={humanPlayer.handicap}
                  onChange={(e) => setHumanPlayer({...humanPlayer, handicap: parseFloat(e.target.value) || 18})}
                />
                <button style={{ ...buttonStyle, padding: "8px 12px", fontSize: 14 }} onClick={() => openGhinLookup("human")}>Lookup GHIN Handicap</button>
              </div>
              {ghinLookupSlot === "human" && (
                <div style={{ margin: "8px 0", padding: 12, background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <input style={inputStyle} placeholder="First Name (optional)" value={ghinLookupFirstName} onChange={e => setGhinLookupFirstName(e.target.value)} />
                    <input style={inputStyle} placeholder="Last Name (required)" value={ghinLookupLastName} onChange={e => setGhinLookupLastName(e.target.value)} />
                    <button style={{ ...buttonStyle, padding: "8px 12px", fontSize: 14 }} onClick={doGhinLookup} disabled={ghinLookupLoading}>Search</button>
                    <button style={{ ...buttonStyle, background: COLORS.error, padding: "8px 12px", fontSize: 14 }} onClick={closeGhinLookup}>Cancel</button>
                  </div>
                  {ghinLookupLoading && <div style={{ color: COLORS.muted, marginTop: 8 }}>Searching...</div>}
                  {ghinLookupError && <div style={{ color: COLORS.error, marginTop: 8 }}>{ghinLookupError}</div>}
                  {ghinLookupResults.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      {ghinLookupResults.map((g, idx) => (
                        <div key={idx} style={{ padding: 8, border: `1px solid ${COLORS.border}`, borderRadius: 6, marginBottom: 4, cursor: "pointer", background: "#fff" }} onClick={() => selectGhinGolfer(g)}>
                          <strong>{g.name}</strong> (H: {g.handicap}) {g.club && <span style={{ color: COLORS.muted }}>@ {g.club}</span>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              <div>
                <label>Your GHIN Name:</label>
                <input
                  type="text"
                  placeholder="First Name (optional)"
                  value={ghinSearch.human?.first_name || ''}
                  onChange={e => handleGhinSearchChange('human', 'first_name', e.target.value)}
                  style={inputStyle}
                />
                <input
                  type="text"
                  placeholder="Last Name (required)"
                  value={ghinSearch.human?.last_name || ''}
                  onChange={e => handleGhinSearchChange('human', 'last_name', e.target.value)}
                  required
                  style={inputStyle}
                />
                {ghinLoading.human && <span style={{ marginLeft: 8, fontSize: 14, color: COLORS.muted }}>Searching...</span>}
                {ghinError.human && <span style={{ marginLeft: 8, fontSize: 14, color: COLORS.error }}>{ghinError.human}</span>}
                {ghinResults.human?.length > 0 && (
                  <div style={{ marginTop: 8, padding: 8, border: `1px solid ${COLORS.border}`, borderRadius: 6, background: COLORS.bg }}>
                    <h5 style={{ margin: 0, fontSize: 14 }}>GHIN Results:</h5>
                    {ghinResults.human.map(golfer => (
                      <div key={golfer.id} style={{ cursor: "pointer", padding: "4px 8px", borderRadius: 4, marginBottom: 4, background: COLORS.bg, border: `1px solid ${COLORS.border}` }} onClick={() => handleGhinSelect('human', golfer)}>
                        {golfer.name} (H: {golfer.handicap})
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Computer Players Setup */}
          <div style={cardStyle}>
            <h3>Computer Opponents</h3>
            {computerPlayers.map((comp, index) => (
              <div key={index} style={{ marginBottom: 16, padding: 12, border: `1px solid ${COLORS.border}`, borderRadius: 8 }}>
                <h4>Opponent {index + 1}</h4>
                <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 12, marginBottom: 8 }}>
                  <div>
                    <label>Name:</label>
                    <input
                      style={inputStyle}
                      value={comp.name || ""}
                      onChange={(e) => updateComputerPlayer(index, "name", e.target.value)}
                    />
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <label>Handicap:</label>
                    <input
                      style={inputStyle}
                      type="number"
                      step="0.1"
                      value={comp.handicap || 18}
                      onChange={(e) => updateComputerPlayer(index, "handicap", parseFloat(e.target.value) || 18)}
                    />
                    <button style={{ ...buttonStyle, padding: "8px 12px", fontSize: 14 }} onClick={() => openGhinLookup(`comp${index+1}`)}>Lookup GHIN Handicap</button>
                  </div>
                  {ghinLookupSlot === `comp${index+1}` && (
                    <div style={{ margin: "8px 0", padding: 12, background: COLORS.bg, border: `1px solid ${COLORS.border}`, borderRadius: 8 }}>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <input style={inputStyle} placeholder="First Name (optional)" value={ghinLookupFirstName} onChange={e => setGhinLookupFirstName(e.target.value)} />
                        <input style={inputStyle} placeholder="Last Name (required)" value={ghinLookupLastName} onChange={e => setGhinLookupLastName(e.target.value)} />
                        <button style={{ ...buttonStyle, padding: "8px 12px", fontSize: 14 }} onClick={doGhinLookup} disabled={ghinLookupLoading}>Search</button>
                        <button style={{ ...buttonStyle, background: COLORS.error, padding: "8px 12px", fontSize: 14 }} onClick={closeGhinLookup}>Cancel</button>
                      </div>
                      {ghinLookupLoading && <div style={{ color: COLORS.muted, marginTop: 8 }}>Searching...</div>}
                      {ghinLookupError && <div style={{ color: COLORS.error, marginTop: 8 }}>{ghinLookupError}</div>}
                      {ghinLookupResults.length > 0 && (
                        <div style={{ marginTop: 8 }}>
                          {ghinLookupResults.map((g, idx) => (
                            <div key={idx} style={{ padding: 8, border: `1px solid ${COLORS.border}`, borderRadius: 6, marginBottom: 4, cursor: "pointer", background: "#fff" }} onClick={() => selectGhinGolfer(g)}>
                              <strong>{g.name}</strong> (H: {g.handicap}) {g.club && <span style={{ color: COLORS.muted }}>@ {g.club}</span>}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  <div>
                    <label>Personality:</label>
                    <select
                      style={selectStyle}
                      value={comp.personality || "balanced"}
                      onChange={(e) => updateComputerPlayer(index, "personality", e.target.value)}
                    >
                      {personalities.map(p => (
                        <option key={p.name} value={p.name}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 14, color: COLORS.muted }}>Quick select:</span>
                  {suggestedOpponents.slice(0, 3).map((opp, oppIndex) => (
                    <button
                      key={oppIndex}
                      style={{ ...buttonStyle, fontSize: 12, padding: "6px 12px" }}
                      onClick={() => selectSuggestedOpponent(index, oppIndex)}
                    >
                      {opp.name} ({opp.handicap})
                    </button>
                  ))}
                </div>
                <div style={{ marginTop: 12 }}>
                  <label>Opponent GHIN Name:</label>
                  <input
                    type="text"
                    placeholder="First Name (optional)"
                    value={ghinSearch[`comp${index + 1}`]?.first_name || ''}
                    onChange={e => handleGhinSearchChange(`comp${index + 1}`, 'first_name', e.target.value)}
                    style={inputStyle}
                  />
                  <input
                    type="text"
                    placeholder="Last Name (required)"
                    value={ghinSearch[`comp${index + 1}`]?.last_name || ''}
                    onChange={e => handleGhinSearchChange(`comp${index + 1}`, 'last_name', e.target.value)}
                    required
                    style={inputStyle}
                  />
                  {ghinLoading[`comp${index + 1}`] && <span style={{ marginLeft: 8, fontSize: 14, color: COLORS.muted }}>Searching...</span>}
                  {ghinError[`comp${index + 1}`] && <span style={{ marginLeft: 8, fontSize: 14, color: COLORS.error }}>{ghinError[`comp${index + 1}`]}</span>}
                  {ghinResults[`comp${index + 1}`]?.length > 0 && (
                    <div style={{ marginTop: 8, padding: 8, border: `1px solid ${COLORS.border}`, borderRadius: 6, background: COLORS.bg }}>
                      <h5 style={{ margin: 0, fontSize: 14 }}>GHIN Results:</h5>
                      {ghinResults[`comp${index + 1}`].map(golfer => (
                        <div key={golfer.id} style={{ cursor: "pointer", padding: "4px 8px", borderRadius: 4, marginBottom: 4, background: COLORS.bg, border: `1px solid ${COLORS.border}` }} onClick={() => handleGhinSelect(`comp${index + 1}`, golfer)}>
                          {golfer.name} (H: {golfer.handicap})
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          {/* Course Selection */}
          <div style={cardStyle}>
            <h3>Course Selection (Optional)</h3>
            <select
              style={selectStyle}
              value={selectedCourse}
              onChange={(e) => setSelectedCourse(e.target.value)}
            >
              <option value="">Default Course</option>
              {Object.keys(courses).map(courseName => (
                <option key={courseName} value={courseName}>{courseName}</option>
              ))}
            </select>
          </div>
          
          <button
            style={buttonStyle}
            onClick={startSimulation}
            disabled={loading}
          >
            {loading ? "Setting up..." : "🚀 Start Simulation"}
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: 20 }}>
      {/* Game Header */}
      <div style={cardStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ color: COLORS.primary, margin: 0 }}>
              🎮 Simulation - Hole {gameState?.current_hole || 1}
            </h2>
            {gameState?.selected_course && (
              <p style={{ margin: "4px 0 0 0", color: COLORS.muted, fontSize: 14 }}>
                Playing on: <strong>{gameState.selected_course}</strong>
              </p>
            )}
          </div>
          <button
            style={{ ...buttonStyle, background: COLORS.error }}
            onClick={resetSimulation}
          >
            End Simulation
          </button>
        </div>
        <p style={{ margin: "8px 0 0 0", color: COLORS.muted }}>
          {gameState?.game_status_message || ""}
        </p>
      </div>
      
      {/* Player Scores */}
      <div style={cardStyle}>
        <h3>Current Standings</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
          {gameState?.players?.map(player => (
            <div 
              key={player.id} 
              style={{ 
                padding: 12, 
                border: `2px solid ${player.id === "human" ? COLORS.primary : COLORS.border}`, 
                borderRadius: 8,
                background: player.id === "human" ? "#f0f8ff" : COLORS.bg
              }}
            >
              <div style={{ fontWeight: "bold" }}>
                {player.id === "human" ? "🧑 " : "💻 "}{player.name}
              </div>
              <div>Handicap: {player.handicap}</div>
              <div style={{ 
                fontSize: 18, 
                fontWeight: "bold", 
                color: player.points >= 0 ? COLORS.success : COLORS.error 
              }}>
                {player.points >= 0 ? "+" : ""}{player.points} points
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Interactive Decision UI */}
      {interactionNeeded && (
        <div style={{
          ...cardStyle,
          border: `3px solid ${COLORS.primary}`,
          background: "#f0f8ff",
          position: "relative"
        }}>
          <div style={{
            position: "absolute",
            top: -10,
            left: 20,
            background: COLORS.primary,
            color: "white",
            padding: "4px 12px",
            borderRadius: 12,
            fontSize: 12,
            fontWeight: "bold"
          }}>
            🤔 DECISION REQUIRED
          </div>
          
          <h3 style={{ color: COLORS.primary, marginBottom: 16 }}>
            {interactionNeeded.type === "captain_decision" && "👑 Captain's Decision"}
            {interactionNeeded.type === "captain_decision_mid_tee" && "🎯 Mid-Tee Decision"}
            {interactionNeeded.type === "partnership_response" && "🤝 Partnership Response"}
            {interactionNeeded.type === "doubling_decision" && "💰 Doubling Decision"}
            {interactionNeeded.type === "double_response" && "💸 Double Response"}
            {interactionNeeded.type === "betting_opportunity" && "🎲 Betting Opportunity"}
          </h3>
          
          <p style={{ marginBottom: 20, fontWeight: "bold", fontSize: 16 }}>
            {interactionNeeded.message}
          </p>
          
          {/* Captain Decision with Tee Results */}
          {(interactionNeeded.type === "captain_decision" || interactionNeeded.type === "captain_decision_mid_tee") && (
            <div>
              {/* Show tee shot results if available */}
              {interactionNeeded.type === "captain_decision" && interactionNeeded.tee_results && (
                <div style={{ background: "#f8f9fa", padding: 12, borderRadius: 8, marginBottom: 16, border: "1px solid #dee2e6" }}>
                  <h4 style={{ margin: "0 0 8px 0", color: "#495057" }}>📊 Tee Shot Results:</h4>
                  {Object.entries(interactionNeeded.tee_results || {}).map(([playerId, result]) => {
                    const isCaptain = playerId === gameState?.captain_id;
                    const isHuman = playerId === "human";
                    return (
                      <div key={playerId} style={{
                        padding: 8,
                        marginBottom: 4,
                        borderRadius: 6,
                        background: isCaptain ? "#e3f2fd" : "#f5f5f5",
                        border: isCaptain ? "2px solid #2196f3" : "1px solid #ddd"
                      }}>
                        <div style={{ fontWeight: "bold", color: isCaptain ? "#1976d2" : "#333" }}>
                          {isCaptain ? "👑 " : ""}{isHuman ? "🧑 " : "💻 "}{result.name}
                          {isCaptain && " (Captain)"}
                        </div>
                        <div style={{ fontSize: 14, color: "#666" }}>{result.shot_description}</div>
                        {result.partnership_advantage !== undefined && (
                          <div style={{ 
                            fontSize: 12, 
                            color: result.partnership_advantage > 0 ? "#2e7d32" : "#d32f2f",
                            fontWeight: "bold"
                          }}>
                            Partnership Advantage: {result.partnership_advantage > 0 ? "+" : ""}{result.partnership_advantage.toFixed(1)} strokes
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
              
              {/* Show current shot context for mid-tee decisions */}
              {interactionNeeded.type === "captain_decision_mid_tee" && interactionNeeded.shot_context && (
                <div style={{ background: "#fff3cd", padding: 12, borderRadius: 8, marginBottom: 16, border: "2px solid #ffc107" }}>
                  <h4 style={{ margin: "0 0 8px 0", color: "#856404" }}>🎯 Current Shot:</h4>
                  <div style={{ fontSize: 16, fontWeight: "bold" }}>{interactionNeeded.shot_context}</div>
                  {interactionNeeded.partnership_advantage !== undefined && (
                    <div style={{ 
                      marginTop: 8,
                      fontSize: 14, 
                      color: interactionNeeded.partnership_advantage > 0 ? "#2e7d32" : "#d32f2f",
                      fontWeight: "bold"
                    }}>
                      Partnership Advantage: {interactionNeeded.partnership_advantage > 0 ? "+" : ""}{interactionNeeded.partnership_advantage.toFixed(1)} strokes
                    </div>
                  )}
                </div>
              )}
              
              {/* Decision Options */}
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                {interactionNeeded.type === "captain_decision_mid_tee" ? (
                  <>
                    {interactionNeeded.options?.map((option, index) => {
                      const isRequestPartner = option.action === "request_partner";
                      return (
                        <button
                          key={index}
                          style={{
                            ...buttonStyle,
                            background: isRequestPartner ? "#10b981" : "#6366f1",
                            flex: 1,
                            minWidth: 200,
                            position: "relative"
                          }}
                          onClick={() => makeDecision({ action: "request_partner", requested_partner: option.partner_id })}
                          disabled={loading}
                        >
                          {isRequestPartner && (
                            <div style={{ position: "absolute", top: -8, right: -8, background: "#059669", color: "white", borderRadius: "50%", width: 24, height: 24, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12 }}>
                              ⭐
                            </div>
                          )}
                          🤝 Ask {option.partner_name} to Partner
                          {isRequestPartner && option.partnership_advantage > 0 && (
                            <div style={{ fontSize: 12, marginTop: 4 }}>
                              +{option.partnership_advantage.toFixed(1)} advantage
                            </div>
                          )}
                        </button>
                      );
                    })}
                    
                    <button
                      style={{
                        ...buttonStyle,
                        background: "#f59e0b",
                        flex: 1,
                        minWidth: 200
                      }}
                      onClick={() => makeDecision({ action: "keep_watching" })}
                      disabled={loading}
                    >
                      👀 Keep Watching ({interactionNeeded.options?.find(o => o.action === "keep_watching")?.remaining_players || 0} more players)
                    </button>
                    
                    {interactionNeeded.can_go_solo && (
                      <button
                        style={{
                          ...buttonStyle,
                          background: "#ef4444",
                          flex: 1,
                          minWidth: 200
                        }}
                        onClick={() => makeDecision({ action: "go_solo" })}
                        disabled={loading}
                      >
                        🏌️ Go Solo (2x wager)
                      </button>
                    )}
                  </>
                ) : (
                  <>
                    <button
                      style={{
                        ...buttonStyle,
                        background: "#10b981",
                        flex: 1
                      }}
                      onClick={() => makeDecision({ action: "request_partner" })}
                      disabled={loading}
                    >
                      🤝 Request Partner
                    </button>
                    
                    <button
                      style={{
                        ...buttonStyle,
                        background: "#ef4444",
                        flex: 1
                      }}
                      onClick={() => makeDecision({ action: "go_solo" })}
                      disabled={loading}
                    >
                      🏌️ Go Solo (2x wager)
                    </button>
                  </>
                )}
              </div>
              
              {/* Strategic Tips */}
              <div style={{ marginTop: 16, padding: 12, background: "#e8f5e8", borderRadius: 8, border: "1px solid #4caf50" }}>
                <h4 style={{ margin: "0 0 8px 0", color: "#2e7d32" }}>💡 Strategic Tips:</h4>
                <ul style={{ margin: 0, paddingLeft: 20, fontSize: 14, color: "#2e7d32" }}>
                  <li>Consider stroke index - harder holes favor partnerships</li>
                  <li>Look at partnership advantages - positive numbers are good</li>
                  <li>Your game position affects risk tolerance</li>
                  <li>Going solo doubles the wager but you must beat the best ball</li>
                </ul>
              </div>
            </div>
          )}
          
          {/* Partnership Response */}
          {interactionNeeded.type === "partnership_response" && (
            <div>
              <div style={{ background: "#fff3cd", padding: 12, borderRadius: 8, marginBottom: 16, border: "2px solid #ffc107" }}>
                <h4 style={{ margin: "0 0 8px 0", color: "#856404" }}>🤝 Partnership Request:</h4>
                <div style={{ fontSize: 16, fontWeight: "bold" }}>{interactionNeeded.shot_context}</div>
                {interactionNeeded.partnership_advantage !== undefined && (
                  <div style={{ 
                    marginTop: 8,
                    fontSize: 14, 
                    color: interactionNeeded.partnership_advantage > 0 ? "#2e7d32" : "#d32f2f",
                    fontWeight: "bold"
                  }}>
                    Team Advantage: {interactionNeeded.partnership_advantage > 0 ? "+" : ""}{interactionNeeded.partnership_advantage.toFixed(1)} strokes
                  </div>
                )}
              </div>
              
              <div style={{ display: "flex", gap: 12 }}>
                <button
                  style={{
                    ...buttonStyle,
                    background: "#10b981",
                    flex: 1
                  }}
                  onClick={() => makeDecision({ accept_partnership: true })}
                  disabled={loading}
                >
                  ✅ Accept Partnership
                </button>
                
                <button
                  style={{
                    ...buttonStyle,
                    background: "#ef4444",
                    flex: 1
                  }}
                  onClick={() => makeDecision({ accept_partnership: false })}
                  disabled={loading}
                >
                  ❌ Decline Partnership
                </button>
              </div>
              
              <p style={{ marginTop: 12, fontSize: 14, color: COLORS.muted, textAlign: "center" }}>
                💡 Consider the team advantage and your current game position!
              </p>
            </div>
          )}
          
          {/* Doubling Decision */}
          {interactionNeeded.type === "doubling_decision" && (
            <div>
              <div style={{ background: "#f0f8ff", padding: 12, borderRadius: 8, marginBottom: 16, border: "2px solid #4169E1" }}>
                <h4 style={{ margin: "0 0 8px 0", color: "#4169E1" }}>💰 Doubling Opportunity:</h4>
                <div><strong>Current wager:</strong> {interactionNeeded.current_wager} quarters</div>
                <div><strong>If doubled:</strong> {interactionNeeded.doubled_wager} quarters</div>
                <div><strong>Your position:</strong> {interactionNeeded.current_position >= 0 ? "+" : ""}{interactionNeeded.current_position} points</div>
                {interactionNeeded.context && (
                  <div style={{ marginTop: 8, fontSize: 14, color: "#666" }}>{interactionNeeded.context}</div>
                )}
              </div>
              
              <div style={{ display: "flex", gap: 12 }}>
                <button
                  style={{
                    ...buttonStyle,
                    background: "#10b981",
                    flex: 1
                  }}
                  onClick={() => makeDecision({ offer_double: true })}
                  disabled={loading}
                >
                  💰 Offer Double
                </button>
                
                <button
                  style={{
                    ...buttonStyle,
                    background: "#f59e0b",
                    flex: 1
                  }}
                  onClick={() => makeDecision({ offer_double: false })}
                  disabled={loading}
                >
                  🚫 Don't Double
                </button>
              </div>
              
              <p style={{ marginTop: 12, fontSize: 14, color: COLORS.muted, textAlign: "center" }}>
                Think carefully - doubling increases both risk and reward!
              </p>
            </div>
          )}
          
          {/* Double Response */}
          {interactionNeeded.type === "double_response" && (
            <div>
              <div style={{ background: "#fff3cd", padding: 12, borderRadius: 8, marginBottom: 16, border: "2px solid #ffc107" }}>
                <h4 style={{ margin: "0 0 8px 0", color: "#856404" }}>💸 Double Offered:</h4>
                <div><strong>Offering player:</strong> {interactionNeeded.offering_player}</div>
                <div><strong>Current wager:</strong> {interactionNeeded.current_wager} quarters</div>
                <div><strong>If accepted:</strong> {interactionNeeded.doubled_wager} quarters</div>
                <div><strong>Your position:</strong> {interactionNeeded.current_position >= 0 ? "+" : ""}{interactionNeeded.current_position} points</div>
                {interactionNeeded.context && (
                  <div style={{ marginTop: 8, fontSize: 14, color: "#666" }}>{interactionNeeded.context}</div>
                )}
              </div>
              
              <div style={{ display: "flex", gap: 12 }}>
                <button
                  style={{
                    ...buttonStyle,
                    background: "#10b981",
                    flex: 1
                  }}
                  onClick={() => makeDecision({ accept_double: true })}
                  disabled={loading}
                >
                  ✅ Accept Double
                </button>
                
                <button
                  style={{
                    ...buttonStyle,
                    background: "#ef4444",
                    flex: 1
                  }}
                  onClick={() => makeDecision({ accept_double: false })}
                  disabled={loading}
                >
                  ❌ Decline Double
                </button>
              </div>
              
              <p style={{ marginTop: 12, fontSize: 14, color: COLORS.muted, textAlign: "center" }}>
                Think carefully - declining means they win at current stakes!
              </p>
            </div>
          )}
          
          {/* Betting Opportunity */}
          {interactionNeeded.type === "betting_opportunity" && (
            <div>
              <p style={{ marginBottom: 20, fontWeight: "bold", fontSize: 16 }}>
                {interactionNeeded.message}
              </p>
              
              {/* Show shot context */}
              <div style={{ background: "#f0fff0", padding: 12, borderRadius: 8, marginBottom: 16, border: "2px solid #10b981" }}>
                <h4 style={{ margin: "0 0 8px 0", color: "#10b981" }}>🎯 Shot Analysis:</h4>
                <div style={{ fontSize: 16, fontWeight: "bold", marginBottom: 8 }}>
                  {interactionNeeded.opportunity.target_player.name}: {interactionNeeded.opportunity.shot_context.shot_description}
                </div>
                
                {/* Show betting probabilities */}
                {interactionNeeded.opportunity.betting_probabilities && (
                  <div style={{ fontSize: 14 }}>
                    <div><strong>Partnership Win Probability:</strong> {interactionNeeded.opportunity.betting_probabilities.win_probability}%</div>
                    <div><strong>Team Strength:</strong> {interactionNeeded.opportunity.betting_probabilities.team_strength} avg handicap</div>
                    <div><strong>Expected Points:</strong> {interactionNeeded.opportunity.betting_probabilities.expected_points >= 0 ? "+" : ""}{interactionNeeded.opportunity.betting_probabilities.expected_points}</div>
                    <div><strong>Risk Level:</strong> {interactionNeeded.opportunity.betting_probabilities.risk_level}</div>
                  </div>
                )}
              </div>
              
              <div style={{ display: "flex", gap: 12 }}>
                <button
                  style={{
                    ...buttonStyle,
                    background: "#10b981",
                    flex: 1
                  }}
                  onClick={() => makeBettingDecision({ 
                    action: "request_partner", 
                    partner_id: interactionNeeded.opportunity.target_player.id 
                  })}
                  disabled={loading}
                >
                  🤝 Request Partnership
                </button>
                
                <button
                  style={{
                    ...buttonStyle,
                    background: "#f59e0b",
                    flex: 1
                  }}
                  onClick={() => makeBettingDecision({ action: "keep_watching" })}
                  disabled={loading}
                >
                  👀 Keep Watching
                </button>
                
                <button
                  style={{
                    ...buttonStyle,
                    background: "#ef4444",
                    flex: 1
                  }}
                  onClick={() => makeBettingDecision({ action: "go_solo" })}
                  disabled={loading}
                >
                  🏌️ Go Solo
                </button>
              </div>
              
              <p style={{ marginTop: 12, fontSize: 14, color: COLORS.muted, textAlign: "center" }}>
                💡 Analyze the probabilities above to make the optimal betting decision!
              </p>
            </div>
          )}
          
          {/* Loading State */}
          {loading && (
            <div style={{ 
              position: "absolute", 
              top: 0, 
              left: 0, 
              right: 0, 
              bottom: 0, 
              background: "rgba(255,255,255,0.8)", 
              display: "flex", 
              alignItems: "center", 
              justifyContent: "center",
              borderRadius: 12
            }}>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 24, marginBottom: 8 }}>⏳</div>
                <div>Processing decision...</div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Play Hole Button - All decisions happen chronologically during play */}
      <div style={cardStyle}>
        <h3>🏌️ Ready to Play Hole {gameState?.current_hole}?</h3>
        <p style={{ marginBottom: 16, color: COLORS.muted }}>
          Click below to watch the hole unfold chronologically - tee shots, captain decisions, 
          partnerships, and betting all happen in real time just like actual Wolf Goat Pig!
        </p>
        
        {/* Show hole info for context */}
        {gameState?.hole_pars && gameState?.hole_stroke_indexes && (
          <div style={{ 
            background: "#f0f8ff", 
            padding: 12, 
            borderRadius: 8, 
            marginBottom: 16,
            border: "1px solid #4169E1"
          }}>
            <h4 style={{ margin: "0 0 8px 0", color: "#4169E1" }}>📊 Hole {gameState.current_hole} Preview:</h4>
            <div style={{ display: "flex", gap: 20, fontSize: 14, flexWrap: "wrap" }}>
              <span>Par: {gameState.hole_pars[gameState.current_hole - 1]}</span>
              <span>Yards: {gameState.hole_yards?.[gameState.current_hole - 1] || "N/A"}</span>
              <span>Stroke Index: {gameState.hole_stroke_indexes[gameState.current_hole - 1]} (1=hardest, 18=easiest)</span>
              {gameState.hole_stroke_indexes[gameState.current_hole - 1] <= 6 && 
                <span style={{ color: COLORS.error, fontWeight: "bold" }}>⚠️ Difficult Hole</span>
              }
              {gameState.hole_stroke_indexes[gameState.current_hole - 1] >= 13 && 
                <span style={{ color: COLORS.success, fontWeight: "bold" }}>✅ Scoring Opportunity</span>
              }
            </div>
            {gameState.hole_descriptions?.[gameState.current_hole - 1] && (
              <div style={{ marginTop: 8, fontSize: 13, color: COLORS.muted, fontStyle: "italic" }}>
                {gameState.hole_descriptions[gameState.current_hole - 1]}
              </div>
            )}
          </div>
        )}
        
        {/* Event-Driven Shot-by-Shot Simulation */}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <button
            style={{
              ...buttonStyle,
              background: COLORS.primary,
              fontSize: 18,
              padding: "16px 32px",
              flex: 1
            }}
            onClick={playNextShot}
            disabled={loading || interactionNeeded || !hasNextShot}
          >
            {loading ? "Playing Shot..." : hasNextShot ? "🏌️ Play Next Shot" : "🏁 All Shots Complete"}
          </button>
          
          {/* Probability View Toggle */}
          <button
            style={{...buttonStyle, background: "#6366f1"}}
            onClick={fetchShotProbabilities}
            disabled={loading}
          >
            📊 View Probabilities
          </button>
          
          {/* Shot State Info */}
          <button
            style={{...buttonStyle, background: "#6b7280"}}
            onClick={fetchShotState}
            disabled={loading}
          >
            ℹ️ Shot State
          </button>
        </div>
        
        {/* Shot Probabilities Display */}
        {shotProbabilities && (
          <div style={{
            background: "#f0f8ff",
            border: "2px solid #4169E1",
            borderRadius: 12,
            padding: 16,
            marginTop: 16
          }}>
            <h4 style={{ margin: "0 0 12px 0", color: "#4169E1" }}>📊 Shot Probabilities</h4>
            
            {shotProbabilities.pre_shot && (
              <div style={{ marginBottom: 16 }}>
                <h5 style={{ margin: "0 0 8px 0" }}>Pre-Shot Expectations:</h5>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 8 }}>
                  <div>🎯 Excellent: {shotProbabilities.pre_shot.excellent}%</div>
                  <div>👍 Good: {shotProbabilities.pre_shot.good}%</div>
                  <div>😐 Average: {shotProbabilities.pre_shot.average}%</div>
                  <div>👎 Poor: {shotProbabilities.pre_shot.poor}%</div>
                  <div>💥 Terrible: {shotProbabilities.pre_shot.terrible}%</div>
                </div>
                <div style={{ marginTop: 8, fontSize: 14, color: COLORS.muted }}>
                  <div>{shotProbabilities.pre_shot.handicap_factor}</div>
                  <div>{shotProbabilities.pre_shot.hole_difficulty}</div>
                  <div>Expected Distance: {shotProbabilities.pre_shot.expected_distance?.expected} yards 
                    ({shotProbabilities.pre_shot.expected_distance?.range})</div>
                </div>
              </div>
            )}
            
            {shotProbabilities.outcome && (
              <div style={{ marginBottom: 16 }}>
                <h5 style={{ margin: "0 0 8px 0" }}>Scoring Probabilities from Position:</h5>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))", gap: 8 }}>
                  <div>🦅 Birdie: {shotProbabilities.outcome.scoring_probabilities?.birdie}%</div>
                  <div>📌 Par: {shotProbabilities.outcome.scoring_probabilities?.par}%</div>
                  <div>☁️ Bogey: {shotProbabilities.outcome.scoring_probabilities?.bogey}%</div>
                  <div>⛈️ Double+: {shotProbabilities.outcome.scoring_probabilities?.double_bogey_or_worse}%</div>
                </div>
                <div style={{ marginTop: 8, fontSize: 14, fontWeight: "bold" }}>
                  Expected Score: {shotProbabilities.outcome.scoring_probabilities?.expected_score}
                </div>
              </div>
            )}
            
            {shotProbabilities.betting_implications && (
              <div>
                <h5 style={{ margin: "0 0 8px 0" }}>💰 Betting Implications:</h5>
                <div style={{ 
                  background: shotProbabilities.betting_implications.partnership_appeal >= 70 ? "#f0fff0" : 
                             shotProbabilities.betting_implications.partnership_appeal >= 50 ? "#fff8f0" : "#fff0f0",
                  padding: 12,
                  borderRadius: 8,
                  border: "1px solid " + (shotProbabilities.betting_implications.partnership_appeal >= 70 ? "#10b981" : 
                                         shotProbabilities.betting_implications.partnership_appeal >= 50 ? "#f59e0b" : "#ef4444")
                }}>
                  <div style={{ fontWeight: "bold" }}>
                    Partnership Appeal: {shotProbabilities.betting_implications.partnership_appeal}%
                  </div>
                  <div style={{ fontSize: 14, marginTop: 4 }}>
                    {shotProbabilities.betting_implications.recommendation}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Current Shot State Display */}
        {shotState && (
          <div style={{
            background: "#f9fafb",
            border: "1px solid #d1d5db",
            borderRadius: 8,
            padding: 16,
            marginTop: 16
          }}>
            <h4 style={{ margin: "0 0 12px 0" }}>📋 Current Shot State</h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
              <div>
                <strong>Phase:</strong> {shotState.phase}
              </div>
              <div>
                <strong>Shots Completed:</strong> {shotState.shots_completed}/{shotState.shots_completed + shotState.shots_remaining}
              </div>
              <div>
                <strong>Next Player:</strong> {shotState.next_player ? 
                  gameState?.players?.find(p => p.id === shotState.next_player)?.name || shotState.next_player 
                  : "None"}
              </div>
              <div>
                <strong>Captain:</strong> {gameState?.players?.find(p => p.id === shotState.captain_id)?.name || "Unknown"}
              </div>
              <div>
                <strong>Teams Formed:</strong> {shotState.teams_formed ? "Yes" : "No"}
              </div>
            </div>
          </div>
        )}
        
        <p style={{ fontSize: 14, color: COLORS.muted, marginTop: 8, textAlign: "center" }}>
          ⚡ <strong>Event-Driven Architecture:</strong> Each shot shows detailed probabilities and betting implications!
          {interactionNeeded && <><br/>🔄 <strong>Decision needed above - analyze the probabilities!</strong></>}
        </p>
        
        {loading && (
          <p style={{ color: COLORS.muted, marginTop: 8 }}>
            Processing...
          </p>
        )}
      </div>
      
      {/* Feedback */}
      {feedback.length > 0 && (
        <div style={cardStyle}>
          <h3>📋 Hole Analysis & Learning</h3>
          <div style={{ maxHeight: 600, overflowY: "auto", border: `1px solid ${COLORS.border}`, borderRadius: 8, padding: 16 }}>
            {feedback.map((message, index) => {
              // Parse different types of feedback for better styling
              const isHeader = message.includes("**") && message.includes(":**");
              const isSuccess = message.includes("✅");
              const isError = message.includes("❌");
              const isTip = message.includes("💡");
              const isInfo = message.includes("ℹ️") || message.includes("•");
              const isCourseManagement = message.includes("🏌️");
              const isPartnership = message.includes("🤝");
              const isSolo = message.includes("🎯");
              const isBetting = message.includes("💰");
              const isPsychology = message.includes("🧠");
              const isOpponent = message.includes("🤖");
              
              let backgroundColor = COLORS.bg;
              let borderColor = COLORS.border;
              let textColor = COLORS.text;
              
              if (isHeader) {
                backgroundColor = COLORS.primary;
                textColor = "white";
                borderColor = COLORS.primary;
              } else if (isSuccess) {
                backgroundColor = "#f0f9f0";
                borderColor = COLORS.success;
              } else if (isError) {
                backgroundColor = "#fdf2f2";
                borderColor = COLORS.error;
              } else if (isTip) {
                backgroundColor = "#fefce8";
                borderColor = COLORS.warning;
              } else if (isCourseManagement) {
                backgroundColor = "#f0f8ff";
                borderColor = "#4169E1";
              } else if (isPartnership || isSolo) {
                backgroundColor = "#f5f0ff";
                borderColor = "#8b5cf6";
              } else if (isBetting) {
                backgroundColor = "#ecfdf5";
                borderColor = "#10b981";
              } else if (isPsychology) {
                backgroundColor = "#fef3c7";
                borderColor = "#f59e0b";
              } else if (isOpponent) {
                backgroundColor = "#f3f4f6";
                borderColor = "#6b7280";
              }
              
              return (
                <div 
                  key={index} 
                  style={{ 
                    padding: isHeader ? 12 : 8, 
                    marginBottom: 8, 
                    background: backgroundColor,
                    color: textColor,
                    borderRadius: 6,
                    borderLeft: `4px solid ${borderColor}`,
                    fontSize: isHeader ? 16 : 14,
                    fontWeight: isHeader ? "bold" : "normal",
                    lineHeight: 1.4
                  }}
                >
                  {message}
                </div>
              );
            })}
          </div>
          
          {/* Quick Tips Summary */}
          <div style={{ marginTop: 16, padding: 12, background: "#fff7ed", borderRadius: 8, border: `1px solid ${COLORS.warning}` }}>
            <h4 style={{ margin: "0 0 8px 0", color: COLORS.warning }}>🎯 Key Takeaways:</h4>
            <ul style={{ margin: 0, paddingLeft: 20, fontSize: 14 }}>
              <li>Pay attention to stroke index - it affects betting confidence</li>
              <li>Consider opponent personalities when making decisions</li>
              <li>Your handicap determines realistic distance expectations</li>
              <li>Game position (ahead/behind) should influence risk-taking</li>
              <li>Use stroke advantages for more aggressive betting</li>
            </ul>
          </div>
        </div>
      )}
      
      {/* Game Over */}
      {gameState?.current_hole > 18 && (
        <div style={{ ...cardStyle, background: COLORS.success, color: "white" }}>
          <h2>🏆 Simulation Complete!</h2>
          <p>Great job completing the round! Review the feedback above to improve your Wolf Goat Pig strategy.</p>
          <button
            style={{ ...buttonStyle, background: "white", color: COLORS.success }}
            onClick={resetSimulation}
          >
            Start New Simulation
          </button>
        </div>
      )}
    </div>
  );
}

export default SimulationMode;