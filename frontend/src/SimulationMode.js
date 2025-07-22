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
  
  const playHole = async () => {
    setLoading(true);
    try {
      // Send current pending decision or defaults
      const decisions = {
        action: pendingDecision.action || null,
        requested_partner: pendingDecision.requested_partner || null,
        offer_double: pendingDecision.offer_double || false,
        accept_double: pendingDecision.accept_double || false,
        accept_partnership: pendingDecision.accept_partnership || false
      };
      
      const response = await fetch(`${API_URL}/simulation/play-hole`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(decisions)
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Backend error:", response.status, errorText);
        throw new Error(`Backend error: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      if (data.status === "ok") {
        setGameState(data.game_state);
        setFeedback(data.feedback || []);
        
        // Check if human interaction is needed
        if (data.interaction_needed) {
          setInteractionNeeded(data.interaction_needed);
          setLoading(false); // Stop loading to show decision UI
        } else {
          // Hole completed, reset for next hole
          setInteractionNeeded(null);
          setPendingDecision({});
          setHoleDecisions({
            action: null,
            requested_partner: null,
            offer_double: false,
            accept_double: false
          });
          setLoading(false);
        }
      } else {
        alert("Error playing hole: " + (data.detail || "Unknown error"));
        setLoading(false);
      }
    } catch (error) {
      console.error("Error playing hole:", error);
      alert("Error playing hole");
      setLoading(false);
    }
  };

  const makeDecision = (decision) => {
    setPendingDecision(decision);
    setInteractionNeeded(null);
    // Continue the hole with this decision
    playHole();
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
          
          {interactionNeeded.type === "captain_decision" && (
            <div>
              <p style={{ marginBottom: 20, fontWeight: "bold" }}>
                {interactionNeeded.message}
              </p>
              
              {/* Show tee shot results for context */}
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
              
              {/* Go Solo Option */}
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
        
        <button
          style={buttonStyle}
          onClick={playHole}
          disabled={loading}
        >
          {loading ? "Playing hole..." : "⛳ Play This Hole"}
        </button>
        
        {loading && (
          <p style={{ color: COLORS.muted, marginTop: 8 }}>
            Simulating hole and processing decisions...
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