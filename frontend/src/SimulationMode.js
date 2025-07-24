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

  // NEW EVENT-DRIVEN SHOT FUNCTIONS
  
  const playNextShot = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/simulation/next-shot`, {
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
        setShotProbabilities(data.probabilities);
        setHasNextShot(data.next_shot_available);
        
        // Add shot result to feedback
        const newFeedback = [...feedback, data.shot_result.shot_description];
        if (data.shot_result.reactions) {
          newFeedback.push(...data.shot_result.reactions);
        }
        setFeedback(newFeedback);
        
        // Check for betting opportunity
        if (data.betting_opportunity) {
          setInteractionNeeded({
            type: "betting_opportunity",
            message: "Betting opportunity available!",
            opportunity: data.betting_opportunity
          });
        }
      }
    } catch (error) {
      console.error("Error playing next shot:", error);
      alert("Error playing shot: " + error.message);
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
              <div>
                <label>Your Handicap:</label>
                <input
                  style={inputStyle}
                  type="number"
                  step="0.1"
                  value={humanPlayer.handicap}
                  onChange={(e) => setHumanPlayer({...humanPlayer, handicap: parseFloat(e.target.value) || 18})}
                />
              </div>
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
                  <div>
                    <label>Handicap:</label>
                    <input
                      style={inputStyle}
                      type="number"
                      step="0.1"
                      value={comp.handicap || 18}
                      onChange={(e) => updateComputerPlayer(index, "handicap", parseFloat(e.target.value) || 18)}
                    />
                  </div>
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
        <div style={{...cardStyle, background: "#fff7ed", border: "2px solid #f59e0b"}}>
          <h3 style={{ color: "#f59e0b", marginBottom: 16 }}>🤔 Decision Required!</h3>
          
          {(interactionNeeded.type === "captain_decision" || interactionNeeded.type === "captain_decision_mid_tee") && (
            <div>
              <p style={{ marginBottom: 20, fontWeight: "bold" }}>
                {interactionNeeded.message}
              </p>
              
              {/* Show context based on interaction type */}
              {interactionNeeded.type === "captain_decision" && interactionNeeded.tee_results && (
                <div style={{ background: "#f0f8ff", padding: 12, borderRadius: 8, marginBottom: 16 }}>
                  <h4 style={{ margin: "0 0 8px 0", color: "#4169E1" }}>📊 Tee Shot Results:</h4>
                  {Object.entries(interactionNeeded.tee_results || {}).map(([playerId, result]) => {
                    const playerName = gameState?.players?.find(p => p.id === playerId)?.name || playerId;
                    return (
                      <div key={playerId} style={{ fontSize: 14, marginBottom: 4 }}>
                        <strong>{playerName}:</strong> {result.drive} yards, {result.lie}, {result.remaining} to pin
                      </div>
                    );
                  })}
                </div>
              )}
              
              {/* Show shot context for mid-tee decisions */}
              {interactionNeeded.type === "captain_decision_mid_tee" && interactionNeeded.shot_context && (
                <div style={{ background: "#f0fff0", padding: 12, borderRadius: 8, marginBottom: 16, border: "2px solid #10b981" }}>
                  <h4 style={{ margin: "0 0 8px 0", color: "#10b981" }}>🎯 Just Happened:</h4>
                  <div style={{ fontSize: 16, fontWeight: "bold" }}>{interactionNeeded.shot_context}</div>
                </div>
              )}
              
              {/* Handle mid-tee decision options */}
              {interactionNeeded.type === "captain_decision_mid_tee" ? (
                <div>
                  {/* Show options from the backend */}
                  {interactionNeeded.options?.map((option, index) => {
                    if (option.action === "request_partner") {
                      return (
                        <div
                          key={option.partner_id}
                          style={{
                            border: "2px solid #10b981",
                            borderRadius: 8,
                            padding: 16,
                            marginBottom: 12,
                            background: "#f0fff0",
                            cursor: "pointer"
                          }}
                          onClick={() => makeDecision({ action: "request_partner", requested_partner: option.partner_id })}
                        >
                          <h4 style={{ margin: "0 0 8px 0", color: "#10b981" }}>🤝 Partner with {option.partner_name}</h4>
                          <p style={{ margin: 0, fontSize: 14, color: "#666" }}>
                            Great shot! Ask them to be your partner for this hole.
                          </p>
                        </div>
                      );
                    } else if (option.action === "keep_watching") {
                      return (
                        <div
                          key="keep_watching"
                          style={{
                            border: "1px solid #f59e0b",
                            borderRadius: 8,
                            padding: 16,
                            marginBottom: 12,
                            background: "#fff8e1",
                            cursor: "pointer"
                          }}
                          onClick={() => makeDecision({ action: "keep_watching" })}
                        >
                          <h4 style={{ margin: "0 0 8px 0", color: "#f59e0b" }}>👀 Keep Watching</h4>
                          <p style={{ margin: 0, fontSize: 14, color: "#666" }}>
                            Wait to see more shots ({option.remaining_players} players left)
                          </p>
                        </div>
                      );
                    }
                    return null;
                  })}
                  
                  {/* Go Solo option if this is the last shot */}
                  {interactionNeeded.can_go_solo && (
                    <div style={{
                      border: "2px solid #ef4444",
                      borderRadius: 8,
                      padding: 16,
                      marginBottom: 12,
                      background: "#fef2f2",
                      cursor: "pointer"
                    }}
                    onClick={() => makeDecision({ action: "go_solo" })}
                    >
                      <h4 style={{ margin: "0 0 8px 0", color: "#ef4444" }}>🏌️ Go Solo (Triple Points!)</h4>
                      <p style={{ margin: 0, fontSize: 14, color: "#666" }}>
                        Last shot - go it alone for maximum risk/reward!
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  {/* Traditional captain decision after all tee shots */}
                  <div style={{
                    border: "2px solid #10b981",
                    borderRadius: 8,
                    padding: 16,
                    marginBottom: 12,
                    background: "#f0f9f0",
                    cursor: "pointer"
                  }}
                  onClick={() => makeDecision({ action: "go_solo" })}
                  >
                    <h4 style={{ margin: "0 0 8px 0", color: "#10b981" }}>🏌️ Go Solo (Triple Points!)</h4>
                    <p style={{ margin: 0, fontSize: 14, color: "#666" }}>
                      <strong>Risk:</strong> High - you vs everyone else<br/>
                      <strong>Reward:</strong> Win 3 points from each opponent if successful
                    </p>
                  </div>
                  
                  {/* Partner Options */}
                  <h4 style={{ marginBottom: 12 }}>Or Request a Partner:</h4>
                  {interactionNeeded.options?.map(player => {
                    const handicapDiff = Math.abs(player.handicap - (gameState?.players?.find(p => p.id === "human")?.handicap || 18));
                    const isGoodMatch = handicapDiff <= 6;
                    
                    return (
                      <div
                        key={player.id}
                        style={{
                          border: "1px solid #d1d5db",
                          borderRadius: 8,
                          padding: 12,
                          marginBottom: 8,
                          background: "#fff",
                          cursor: "pointer"
                        }}
                        onClick={() => makeDecision({ action: "request_partner", requested_partner: player.id })}
                      >
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                          <div>
                            <div style={{ fontWeight: "bold" }}>💻 {player.name}</div>
                            <div style={{ fontSize: 12, color: COLORS.muted }}>
                              Handicap: {player.handicap} | Points: {player.points >= 0 ? "+" : ""}{player.points}
                            </div>
                          </div>
                          <div style={{ textAlign: "right", fontSize: 12 }}>
                            {isGoodMatch ? (
                              <span style={{ color: COLORS.success, fontWeight: "bold" }}>✅ Good Match</span>
                            ) : (
                              <span style={{ color: COLORS.warning }}>⚠️ Handicap Gap: {handicapDiff.toFixed(1)}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
          
          {interactionNeeded.type === "partnership_response" && (
            <div>
              <p style={{ marginBottom: 20, fontWeight: "bold", fontSize: 16 }}>
                {interactionNeeded.message}
              </p>
              
              <div style={{ display: "flex", gap: 12 }}>
                <button
                  style={{
                    ...buttonStyle,
                    background: "#10b981",
                    flex: 1
                  }}
                  onClick={() => makeDecision({ accept_partnership: true })}
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
                >
                  ❌ Decline Partnership
                </button>
              </div>
              
              <p style={{ marginTop: 12, fontSize: 14, color: COLORS.muted, textAlign: "center" }}>
                Choose wisely - this affects the entire hole outcome!
              </p>
            </div>
          )}
          
          {interactionNeeded.type === "doubling_decision" && (
            <div>
              <p style={{ marginBottom: 20, fontWeight: "bold", fontSize: 16 }}>
                {interactionNeeded.message}
              </p>
              
              {/* Show betting context */}
              <div style={{ background: "#f0f8ff", padding: 12, borderRadius: 8, marginBottom: 16 }}>
                <h4 style={{ margin: "0 0 8px 0", color: "#4169E1" }}>💰 Betting Situation:</h4>
                <div style={{ fontSize: 14 }}>
                  <div><strong>Current wager:</strong> {interactionNeeded.current_wager} quarters</div>
                  <div><strong>If doubled:</strong> {interactionNeeded.doubled_wager} quarters</div>
                  <div><strong>Your position:</strong> {interactionNeeded.current_position >= 0 ? "+" : ""}{interactionNeeded.current_position} points</div>
                  <div style={{ marginTop: 8, fontStyle: "italic", color: "#666" }}>
                    {interactionNeeded.context}
                  </div>
                </div>
              </div>
              
              <div style={{ display: "flex", gap: 12 }}>
                <button
                  style={{
                    ...buttonStyle,
                    background: "#f59e0b",
                    flex: 1
                  }}
                  onClick={() => makeDecision({ offer_double: true })}
                >
                  💰 Offer Double
                </button>
                
                <button
                  style={{
                    ...buttonStyle,
                    background: "#6b7280",
                    flex: 1
                  }}
                  onClick={() => makeDecision({ offer_double: false })}
                >
                  ↪️ Continue Current Stakes
                </button>
              </div>
              
              <p style={{ marginTop: 12, fontSize: 14, color: COLORS.muted, textAlign: "center" }}>
                Doubling increases risk and reward - consider your position and hole difficulty!
              </p>
            </div>
          )}
          
          {interactionNeeded.type === "double_response" && (
            <div>
              <p style={{ marginBottom: 20, fontWeight: "bold", fontSize: 16 }}>
                {interactionNeeded.message}
              </p>
              
              {/* Show betting context */}
              <div style={{ background: "#fef3c7", padding: 12, borderRadius: 8, marginBottom: 16 }}>
                <h4 style={{ margin: "0 0 8px 0", color: "#f59e0b" }}>⚠️ Double Offered:</h4>
                <div style={{ fontSize: 14 }}>
                  <div><strong>Offering player:</strong> {interactionNeeded.offering_player}</div>
                  <div><strong>Current wager:</strong> {interactionNeeded.current_wager} quarters</div>
                  <div><strong>If accepted:</strong> {interactionNeeded.doubled_wager} quarters</div>
                  <div><strong>Your position:</strong> {interactionNeeded.current_position >= 0 ? "+" : ""}{interactionNeeded.current_position} points</div>
                  <div style={{ marginTop: 8, fontStyle: "italic", color: "#666" }}>
                    {interactionNeeded.context}
                  </div>
                </div>
              </div>
              
              <div style={{ display: "flex", gap: 12 }}>
                <button
                  style={{
                    ...buttonStyle,
                    background: "#10b981",
                    flex: 1
                  }}
                  onClick={() => makeDecision({ accept_double: true })}
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
                >
                  ❌ Decline Double
                </button>
              </div>
              
              <p style={{ marginTop: 12, fontSize: 14, color: COLORS.muted, textAlign: "center" }}>
                Think carefully - declining means they win at current stakes!
              </p>
            </div>
          )}
          
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
                >
                  🏌️ Go Solo
                </button>
              </div>
              
              <p style={{ marginTop: 12, fontSize: 14, color: COLORS.muted, textAlign: "center" }}>
                💡 Analyze the probabilities above to make the optimal betting decision!
              </p>
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