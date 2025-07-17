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
      const response = await fetch(`${API_URL}/simulation/play-hole`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(holeDecisions)
      });
      
      const data = await response.json();
      if (data.status === "ok") {
        setGameState(data.game_state);
        setFeedback(data.feedback || []);
        // Reset decisions for next hole
        setHoleDecisions({
          action: null,
          requested_partner: null,
          offer_double: false,
          accept_double: false
        });
      } else {
        alert("Error playing hole: " + (data.detail || "Unknown error"));
      }
    } catch (error) {
      console.error("Error playing hole:", error);
      alert("Error playing hole");
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
          <h2 style={{ color: COLORS.primary, margin: 0 }}>
            🎮 Simulation - Hole {gameState?.current_hole || 1}
          </h2>
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
      
      {/* Captain Decision Interface */}
      {isHumanCaptain && !gameState?.teams?.type && (
        <div style={cardStyle}>
          <h3>🎯 You're the Captain! Make Your Decision</h3>
          <p style={{ marginBottom: 20 }}>
            As captain, you can either request a partner or go solo. Consider the hole difficulty, 
            your current position, and stroke advantages before deciding.
          </p>
          
          {/* Course Info Helper */}
          {gameState?.hole_pars && gameState?.hole_stroke_indexes && (
            <div style={{ 
              background: "#f0f8ff", 
              padding: 12, 
              borderRadius: 8, 
              marginBottom: 16,
              border: "1px solid #4169E1"
            }}>
              <h4 style={{ margin: "0 0 8px 0", color: "#4169E1" }}>📊 Hole Information:</h4>
              <div style={{ display: "flex", gap: 20, fontSize: 14 }}>
                <span>Par: {gameState.hole_pars[gameState.current_hole - 1]}</span>
                <span>Stroke Index: {gameState.hole_stroke_indexes[gameState.current_hole - 1]} (1=hardest, 18=easiest)</span>
                {gameState.hole_stroke_indexes[gameState.current_hole - 1] <= 6 && 
                  <span style={{ color: COLORS.error, fontWeight: "bold" }}>⚠️ Difficult Hole</span>
                }
                {gameState.hole_stroke_indexes[gameState.current_hole - 1] >= 13 && 
                  <span style={{ color: COLORS.success, fontWeight: "bold" }}>✅ Scoring Opportunity</span>
                }
              </div>
            </div>
          )}
          
          {/* Stroke Advantage Display */}
          {(() => {
            const strokes = gameState?.players?.find(p => p.id === "human");
            const strokesOnHole = strokes ? gameState.get_player_strokes?.()?.[strokes.id]?.[gameState.current_hole] || 0 : 0;
            
            return strokesOnHole > 0 && (
              <div style={{ 
                background: "#f0f9f0", 
                padding: 12, 
                borderRadius: 8, 
                marginBottom: 16,
                border: `1px solid ${COLORS.success}`
              }}>
                <h4 style={{ margin: "0 0 8px 0", color: COLORS.success }}>🎁 Stroke Advantage:</h4>
                <p style={{ margin: 0, fontSize: 14 }}>
                  You receive <strong>{strokesOnHole} stroke(s)</strong> on this hole! 
                  This is a significant advantage - consider being more aggressive with your betting.
                </p>
              </div>
            );
          })()}
          
          <div style={{ marginBottom: 20 }}>
            <div style={{ 
              border: holeDecisions.action === "go_solo" ? `2px solid ${COLORS.success}` : `1px solid ${COLORS.border}`,
              borderRadius: 8,
              padding: 16,
              marginBottom: 12,
              background: holeDecisions.action === "go_solo" ? "#f0f9f0" : COLORS.card,
              cursor: "pointer"
            }}
            onClick={() => setHoleDecisions({...holeDecisions, action: "go_solo", requested_partner: null})}
            >
              <div style={{ display: "flex", alignItems: "center", marginBottom: 8 }}>
                <input 
                  type="radio" 
                  checked={holeDecisions.action === "go_solo"}
                  onChange={() => {}}
                  style={{ marginRight: 12 }}
                />
                <h4 style={{ margin: 0, fontSize: 18 }}>🏌️ Go Solo (Triple Points!)</h4>
              </div>
              <p style={{ margin: 0, fontSize: 14, color: COLORS.muted }}>
                <strong>Risk:</strong> High - you vs everyone else<br/>
                <strong>Reward:</strong> Win 3 points from each opponent if successful<br/>
                <strong>When to choose:</strong> You have stroke advantage, feeling confident, or need to catch up
              </p>
            </div>
          </div>
          
          <div>
            <h4 style={{ marginBottom: 12 }}>Or Request a Partner:</h4>
            <p style={{ fontSize: 14, color: COLORS.muted, marginBottom: 12 }}>
              Choose someone whose skills complement yours. Consider their recent performance and handicap.
            </p>
            {getPartnerOptions().map(player => {
              const isSelected = holeDecisions.requested_partner === player.id;
              const handicapDiff = Math.abs(player.handicap - (gameState?.players?.find(p => p.id === "human")?.handicap || 18));
              const isGoodMatch = handicapDiff <= 6;
              
              return (
                <div
                  key={player.id}
                  style={{
                    border: isSelected ? `2px solid ${COLORS.success}` : `1px solid ${COLORS.border}`,
                    borderRadius: 8,
                    padding: 12,
                    marginBottom: 8,
                    background: isSelected ? "#f0f9f0" : COLORS.card,
                    cursor: "pointer"
                  }}
                  onClick={() => setHoleDecisions({...holeDecisions, action: null, requested_partner: player.id})}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div style={{ display: "flex", alignItems: "center" }}>
                      <input 
                        type="radio" 
                        checked={isSelected}
                        onChange={() => {}}
                        style={{ marginRight: 12 }}
                      />
                      <div>
                        <div style={{ fontWeight: "bold" }}>💻 {player.name}</div>
                        <div style={{ fontSize: 12, color: COLORS.muted }}>
                          Handicap: {player.handicap} | Points: {player.points >= 0 ? "+" : ""}{player.points}
                        </div>
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
        </div>
      )}
      
      {/* Doubling Interface */}
      {gameState?.teams?.type && !gameState?.doubled_status && (
        <div style={cardStyle}>
          <h3>💰 Doubling Opportunity</h3>
          <p>Current base wager: {gameState.base_wager} quarter(s)</p>
          
          <label style={{ display: "flex", alignItems: "center", marginBottom: 8 }}>
            <input
              type="checkbox"
              checked={holeDecisions.offer_double}
              onChange={(e) => setHoleDecisions({...holeDecisions, offer_double: e.target.checked})}
              style={{ marginRight: 8 }}
            />
            Offer to double the opposing team
          </label>
        </div>
      )}
      
      {/* Computer Double Offer Response */}
      {gameState?.doubled_status && (
        <div style={cardStyle}>
          <h3>🤔 Computer Team Offered a Double!</h3>
          <p style={{ color: COLORS.warning, fontWeight: "bold" }}>
            The computer team wants to double the stakes. Do you accept?
          </p>
          <p>Current wager: {gameState.base_wager} → Would become: {gameState.base_wager * 2}</p>
          
          <div>
            <label style={{ display: "flex", alignItems: "center", marginBottom: 8 }}>
              <input
                type="radio"
                name="double_response"
                checked={holeDecisions.accept_double === true}
                onChange={() => setHoleDecisions({...holeDecisions, accept_double: true})}
                style={{ marginRight: 8 }}
              />
              Accept the double (higher risk, higher reward)
            </label>
            <label style={{ display: "flex", alignItems: "center" }}>
              <input
                type="radio"
                name="double_response"
                checked={holeDecisions.accept_double === false}
                onChange={() => setHoleDecisions({...holeDecisions, accept_double: false})}
                style={{ marginRight: 8 }}
              />
              Decline the double (they win the hole at current stakes)
            </label>
          </div>
        </div>
      )}
      
      {/* Play Hole Button */}
      <div style={cardStyle}>
        <button
          style={buttonStyle}
          onClick={playHole}
          disabled={loading || (!isHumanCaptain && !gameState?.teams?.type)}
        >
          {loading ? "Playing hole..." : "⛳ Play This Hole"}
        </button>
        
        {!isHumanCaptain && !gameState?.teams?.type && (
          <p style={{ color: COLORS.muted, marginTop: 8 }}>
            Waiting for computer captain to make decisions...
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