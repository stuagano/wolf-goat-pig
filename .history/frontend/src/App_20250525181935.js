import React, { useEffect, useState } from "react";

const API_URL = process.env.REACT_APP_API_URL || "";

const PLAYER_NAMES = {
  p1: "Bob",
  p2: "Scott",
  p3: "Vince",
  p4: "Mike",
};

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
  ...COLORS,
  background: COLORS.primary,
  color: "#fff",
  border: "none",
  borderRadius: 8,
  padding: "14px 24px",
  fontWeight: 600,
  fontSize: 18,
  minHeight: 44,
  margin: "8px 0",
  boxShadow: "0 1px 4px rgba(25, 118, 210, 0.08)",
  cursor: "pointer",
  transition: "background 0.2s",
};

const inputStyle = {
  border: `1px solid ${COLORS.border}`,
  borderRadius: 6,
  padding: "12px 16px",
  fontSize: 18,
  minHeight: 44,
  width: 60,
  margin: "4px 0",
};

const tableContainerStyle = {
  overflowX: "auto",
  WebkitOverflowScrolling: "touch",
  marginBottom: 16,
  maxWidth: "100vw",
};

const tableStyle = {
  width: "100%",
  minWidth: 400,
  borderCollapse: "collapse",
  fontSize: 15,
};

const thStyle = {
  background: COLORS.bg,
  color: COLORS.text,
  fontWeight: 700,
  padding: "8px 6px",
  borderBottom: `1px solid ${COLORS.border}`,
  textAlign: "left",
};

const tdStyle = {
  padding: "8px 6px",
  borderBottom: `1px solid ${COLORS.border}`,
  background: COLORS.card,
};

const stickyHeaderStyle = {
  position: "sticky",
  top: 0,
  zIndex: 10,
  background: COLORS.primary,
  color: "#fff",
  padding: "16px 0 8px 0",
  textAlign: "center",
  fontWeight: 800,
  fontSize: 22,
  letterSpacing: 1,
  boxShadow: "0 2px 8px rgba(25, 118, 210, 0.08)",
};

const mobileNavStyle = {
  position: "fixed",
  left: 0,
  right: 0,
  bottom: 0,
  background: COLORS.card,
  borderTop: `1px solid ${COLORS.border}`,
  display: "flex",
  justifyContent: "space-around",
  alignItems: "center",
  padding: "8px 0 4px 0",
  zIndex: 100,
};

const navBtnStyle = {
  ...buttonStyle,
  background: COLORS.primary,
  borderRadius: 24,
  fontSize: 14,
  padding: "10px 16px",
  margin: 0,
  minWidth: 0,
};

function CourseManager({ onClose, onCoursesChanged }) {
  const [courses, setCourses] = useState([]);
  const [newName, setNewName] = useState("");
  const [newHoles, setNewHoles] = useState(Array(18).fill({ stroke_index: "", par: "" }));
  const [error, setError] = useState("");
  useEffect(() => {
    fetch(`${API_URL}/courses`).then(res => res.json()).then(data => setCourses(Object.entries(data)));
  }, []);
  const handleAdd = async e => {
    e.preventDefault();
    if (!newName.trim() || newHoles.some(x => !x.stroke_index || !x.par)) {
      setError("Name and all 18 holes (stroke index and par) required.");
      return;
    }
    const holes = newHoles.map(h => ({ stroke_index: Number(h.stroke_index), par: Number(h.par) }));
    if (holes.some(h => isNaN(h.stroke_index) || h.stroke_index < 1 || h.stroke_index > 18 || isNaN(h.par) || h.par < 3 || h.par > 5)) {
      setError("Stroke indexes 1-18, pars 3-5.");
      return;
    }
    const res = await fetch(`${API_URL}/courses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newName, holes }),
    });
    if (res.ok) {
      const data = await res.json();
      setCourses(Object.entries(data));
      setNewName("");
      setNewHoles(Array(18).fill({ stroke_index: "", par: "" }));
      setError("");
      onCoursesChanged && onCoursesChanged();
    } else {
      const data = await res.json();
      setError(data.detail || "Add failed");
    }
  };
  const handleDelete = async name => {
    if (!window.confirm(`Delete course '${name}'?`)) return;
    const res = await fetch(`${API_URL}/courses/${encodeURIComponent(name)}`, { method: "DELETE" });
    if (res.ok) {
      const data = await res.json();
      setCourses(Object.entries(data));
      onCoursesChanged && onCoursesChanged();
    }
  };
  return (
    <div style={{ ...cardStyle, maxWidth: 600, margin: "40px auto", background: COLORS.bg }}>
      <h2 style={{ color: COLORS.primary, marginBottom: 12 }}>Course Management</h2>
      <button style={{ ...buttonStyle, float: "right", marginTop: -36 }} onClick={onClose}>Close</button>
      <h3 style={{ marginTop: 0 }}>Existing Courses</h3>
      <ul style={{ paddingLeft: 18 }}>
        {courses.map(([name, holes]) => (
          <li key={name} style={{ marginBottom: 6 }}>
            <b>{name}</b> &nbsp;
            <span style={{ fontSize: 13, color: COLORS.muted }}>Stroke Indexes: {holes.map(h => h.stroke_index).join(", ")}</span>
            <span style={{ fontSize: 13, color: COLORS.muted, marginLeft: 8 }}>Pars: {holes.map(h => h.par).join(", ")}</span>
            <button style={{ ...buttonStyle, background: COLORS.error, marginLeft: 10, fontSize: 13, padding: "4px 10px" }} onClick={() => handleDelete(name)}>Delete</button>
          </li>
        ))}
      </ul>
      <h3>Add New Course</h3>
      <form onSubmit={handleAdd} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <input style={{ ...inputStyle, width: 220 }} placeholder="Course Name" value={newName} onChange={e => setNewName(e.target.value)} />
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {Array(18).fill(0).map((_, i) => (
            <span key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", marginRight: 8 }}>
              <input
                style={{ ...inputStyle, width: 36, marginBottom: 2 }}
                placeholder={`SI ${i + 1}`}
                value={newHoles[i]?.stroke_index || ""}
                onChange={e => setNewHoles(newHoles.map((h, idx) => idx === i ? { ...h, stroke_index: e.target.value } : h))}
                maxLength={2}
              />
              <input
                style={{ ...inputStyle, width: 36 }}
                placeholder="Par"
                value={newHoles[i]?.par || ""}
                onChange={e => setNewHoles(newHoles.map((h, idx) => idx === i ? { ...h, par: e.target.value } : h))}
                maxLength={1}
              />
            </span>
          ))}
        </div>
        {error && <div style={{ color: COLORS.error }}>{error}</div>}
        <button type="submit" style={{ ...buttonStyle, width: 180 }}>Add Course</button>
      </form>
    </div>
  );
}

function GameSetupForm({ onSetup }) {
  const [players, setPlayers] = useState([
    { id: 'p1', name: '', handicap: '', strength: '' },
    { id: 'p2', name: '', handicap: '', strength: '' },
    { id: 'p3', name: '', handicap: '', strength: '' },
    { id: 'p4', name: '', handicap: '', strength: '' },
  ]);
  const [courses, setCourses] = useState([]);
  const [courseName, setCourseName] = useState('');
  const [error, setError] = useState('');
  const [showCourseManager, setShowCourseManager] = useState(false);
  useEffect(() => {
    fetch(`${API_URL}/courses`).then(res => res.json()).then(data => {
      setCourses(Object.keys(data));
      if (Object.keys(data).length > 0) setCourseName(Object.keys(data)[0]);
    });
  }, []);
  const handleChange = (idx, field, value) => {
    setPlayers(players => players.map((p, i) => i === idx ? { ...p, [field]: value } : p));
  };
  const handleSubmit = async e => {
    e.preventDefault();
    if (players.some(p => !p.name || p.handicap === '' || !p.strength)) {
      setError('All names, handicaps, and strengths are required.');
      return;
    }
    setError('');
    const res = await fetch(`${API_URL}/game/setup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ players, course_name: courseName }),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      onSetup(data.game_state);
    } else {
      setError(data.detail || 'Setup failed');
    }
  };
  return (
    <>
      {showCourseManager && <CourseManager onClose={() => setShowCourseManager(false)} onCoursesChanged={() => {
        fetch(`${API_URL}/courses`).then(res => res.json()).then(data => setCourses(Object.keys(data)));
      }} />}
      <form onSubmit={handleSubmit} style={{ ...cardStyle, maxWidth: 420, margin: '40px auto', background: COLORS.bg }}>
        <h2 style={{ color: COLORS.primary, marginBottom: 12 }}>Setup Players & Course</h2>
        <div style={{ marginBottom: 12, display: 'flex', flexWrap: 'wrap', gap: 8, flexDirection: window.innerWidth < 600 ? 'column' : 'row' }}>
          <label style={{ fontWeight: 600, marginRight: 8 }}>Course:</label>
          <select style={{ ...inputStyle, width: 180 }} value={courseName} onChange={e => setCourseName(e.target.value)}>
            {courses.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <button type="button" style={{ ...buttonStyle, background: COLORS.accent, marginLeft: 10, fontSize: 16, padding: "10px 18px" }} onClick={() => setShowCourseManager(true)}>Manage Courses</button>
        </div>
        {players.map((p, i) => (
          <div key={p.id} style={{ display: 'flex', gap: 8, marginBottom: 8, flexDirection: window.innerWidth < 600 ? 'column' : 'row' }}>
            <input
              style={{ ...inputStyle, flex: 2 }}
              placeholder={`Player ${i + 1} Name`}
              value={p.name}
              onChange={e => handleChange(i, 'name', e.target.value)}
              required
            />
            <input
              style={{ ...inputStyle, flex: 1 }}
              placeholder="Handicap"
              type="number"
              min="0"
              step="0.5"
              value={p.handicap}
              onChange={e => handleChange(i, 'handicap', e.target.value)}
              required
            />
            <select
              style={{ ...inputStyle, flex: 1 }}
              value={p.strength || ''}
              onChange={e => handleChange(i, 'strength', e.target.value)}
              required
            >
              <option value="">Strength</option>
              <option value="Beginner">Beginner</option>
              <option value="Average">Average</option>
              <option value="Strong">Strong</option>
              <option value="Expert">Expert</option>
            </select>
          </div>
        ))}
        {error && <div style={{ color: COLORS.error, marginBottom: 8 }}>{error}</div>}
        <button type="submit" style={{ ...buttonStyle, width: '100%' }}>Start Game</button>
      </form>
    </>
  );
}

function App() {
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scoreInputs, setScoreInputs] = useState({});
  const [partnerSelect, setPartnerSelect] = useState("");
  const [showDebug, setShowDebug] = useState(false);
  const [bettingTips, setBettingTips] = useState([]);
  const [playerStrokes, setPlayerStrokes] = useState({});
  const [showSplash, setShowSplash] = useState(true);

  // Fetch current game state and player strokes on mount
  useEffect(() => {
    fetch(`${API_URL}/game/state`)
      .then(res => res.json())
      .then(data => {
        setGameState(data);
        setLoading(false);
      });
    fetch(`${API_URL}/game/tips`).then(res => res.json()).then(data => setBettingTips(data.tips || []));
    fetch(`${API_URL}/game/player_strokes`).then(res => res.json()).then(data => setPlayerStrokes(data));
  }, []);

  const refreshState = () => {
    setLoading(true);
    fetch(`${API_URL}/game/state`)
      .then(res => res.json())
      .then(data => {
        setGameState(data);
        setLoading(false);
        fetch(`${API_URL}/game/tips`).then(res => res.json()).then(data => setBettingTips(data.tips || []));
        fetch(`${API_URL}/game/player_strokes`).then(res => res.json()).then(data => setPlayerStrokes(data));
      });
  };

  const doAction = async (action, payload = {}) => {
    setLoading(true);
    const res = await fetch(`${API_URL}/game/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, payload }),
    });
    const data = await res.json();
    setGameState(data.game_state);
    setLoading(false);
    setScoreInputs({});
    setPartnerSelect("");
  };

  const startGame = () => doAction("next_hole"); // Actually, restart is handled by /game/start
  const restartGame = () => {
    if (!window.confirm("Are you sure you want to restart the game? All progress will be lost.")) return;
    setLoading(true);
    fetch(`${API_URL}/game/start`, { method: "POST" })
      .then(res => res.json())
      .then(data => {
        setGameState(data.game_state);
        setLoading(false);
        setScoreInputs({});
        setPartnerSelect("");
      });
  };

  // Add handler for setup
  const handleSetup = (state) => {
    setGameState(state);
    setLoading(false);
  };

  // Splash screen logic
  if (showSplash) {
    return (
      <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',height:'100vh',background:COLORS.bg}}>
        <div style={{...cardStyle, textAlign:'center', maxWidth: 400, marginTop: -80}}>
          <h1 style={{color:COLORS.primary, fontSize:32, marginBottom:16}}>Wolf Goat Pig</h1>
          <p style={{fontSize:18, color:COLORS.text, marginBottom:24}}>Golf Game Tracker</p>
          <button style={{...buttonStyle, fontSize:22, width:220, margin:'0 auto'}} onClick={() => setShowSplash(false)}>
            Start New Game
          </button>
        </div>
      </div>
    );
  }

  if (loading) return <div>Loading...</div>;
  if (!gameState) return <GameSetupForm onSetup={handleSetup} />;

  // Team helpers
  const team1 = gameState.teams?.team1 || [];
  const team2 = gameState.teams?.team2 || [];
  const isCaptain = pid => pid === gameState.captain_id;
  const teamColor = pid => team1.includes(pid) ? "#e0f7fa" : team2.includes(pid) ? "#ffe0b2" : "#fff";
  const teamBadge = pid => team1.includes(pid) ? <span style={{background:'#00bcd4',color:'#fff',borderRadius:4,padding:'2px 6px',marginLeft:4,fontSize:12}}>Team 1</span> : team2.includes(pid) ? <span style={{background:'#ff9800',color:'#fff',borderRadius:4,padding:'2px 6px',marginLeft:4,fontSize:12}}>Team 2</span> : null;

  // Team status
  let teamStatus = null;
  if (gameState.teams?.type === "pending") {
    teamStatus = <div>Captain requests <b>{PLAYER_NAMES[gameState.teams.requested]}</b> as partner. Awaiting response.</div>;
  } else if (gameState.teams?.type === "partners") {
    teamStatus = <div><span style={{background:'#00bcd4',color:'#fff',borderRadius:4,padding:'2px 6px'}}>Team 1</span>: <b>{PLAYER_NAMES[gameState.teams.team1[0]]} & {PLAYER_NAMES[gameState.teams.team1[1]]}</b> vs <span style={{background:'#ff9800',color:'#fff',borderRadius:4,padding:'2px 6px'}}>Team 2</span>: <b>{PLAYER_NAMES[gameState.teams.team2[0]]} & {PLAYER_NAMES[gameState.teams.team2[1]]}</b></div>;
  } else if (gameState.teams?.type === "solo") {
    teamStatus = <div><b>Captain {PLAYER_NAMES[gameState.teams.captain]}</b> (Solo) vs {gameState.teams.opponents.map(pid => PLAYER_NAMES[pid]).join(", ")}</div>;
  }

  // Players table
  const playersTable = (
    <div style={tableContainerStyle}>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>Name</th>
            <th style={thStyle}>Handicap</th>
            <th style={thStyle}>Strength</th>
            <th style={thStyle}>Points</th>
            <th style={thStyle}>Role</th>
            <th style={thStyle}>Team</th>
          </tr>
        </thead>
        <tbody>
          {gameState.players.map(player => (
            <tr key={player.id}>
              <td style={{...tdStyle, fontWeight: isCaptain(player.id) ? 700 : 400}}>
                {player.name} {isCaptain(player.id) && <span style={{color:COLORS.success,fontWeight:700,marginLeft:4}}>(Captain)</span>}
              </td>
              <td style={tdStyle}>{player.handicap}</td>
              <td style={tdStyle}>{player.strength || '-'}</td>
              <td style={tdStyle}>{player.points}</td>
              <td style={tdStyle}>{isCaptain(player.id) ? 'Captain' : ''}</td>
              <td style={tdStyle}>{teamBadge(player.id)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  // Score entry table
  const scoreEntryTable = (
    <div style={tableContainerStyle}>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>Player</th>
            <th style={thStyle}>Net Score</th>
          </tr>
        </thead>
        <tbody>
          {gameState.players.map(player => (
            <tr key={player.id}>
              <td style={tdStyle}>{player.name}</td>
              <td style={tdStyle}>
                <input
                  type="number"
                  value={scoreInputs[player.id] ?? gameState.hole_scores[player.id] ?? ""}
                  onChange={e => setScoreInputs({ ...scoreInputs, [player.id]: e.target.value })}
                  style={inputStyle}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  // Can calculate points if all scores are entered and teams are set
  const canCalculate = Object.values({ ...gameState.hole_scores, ...scoreInputs }).every(v => v !== null && v !== "") && ["partners", "solo"].includes(gameState.teams?.type);

  // Notification/status area
  const statusColor = gameState.game_status_message?.toLowerCase().includes("win") ? COLORS.success : gameState.game_status_message?.toLowerCase().includes("error") ? COLORS.error : COLORS.primary;
  const statusBox = (
    <div style={{background:statusColor,color:'#fff',padding:12,borderRadius:8,marginBottom:18,fontWeight:500,boxShadow:'0 1px 4px rgba(0,0,0,0.06)'}}>
      {gameState.game_status_message}
    </div>
  );

  // Helper: get available partners for captain
  const availablePartners = () => {
    if (!gameState) return [];
    return gameState.players
      .filter(p => p.id !== gameState.captain_id)
      .map(p => ({ id: p.id, name: p.name }));
  };

  // Helper: is this player the requested partner?
  const requestedPartnerId = gameState.teams?.requested;

  // Detect if a double is pending (doubled_status true and teams set)
  const doublePending = gameState.doubled_status && (["partners", "solo"].includes(gameState.teams?.type));

  // Prominent double offer alert
  const doubleAlert = doublePending && (
    <div style={{background:'#fff3cd',color:'#856404',border:'2px solid #ffe082',padding:20,borderRadius:8,marginBottom:20,boxShadow:'0 2px 8px #ffe082'}}>
      <div style={{fontWeight:700,fontSize:18,marginBottom:10}}>Double Offered!</div>
      <div style={{marginBottom:12}}>A double has been offered. Do you accept or decline?</div>
      <button style={{background:'#388e3c',color:'#fff',fontWeight:600,padding:'8px 18px',marginRight:10,border:'none',borderRadius:4,fontSize:16}} onClick={() => doAction("accept_double", { team_id: "team2" })}>Accept Double</button>
      <button style={{background:'#d32f2f',color:'#fff',fontWeight:600,padding:'8px 18px',border:'none',borderRadius:4,fontSize:16}} onClick={() => doAction("decline_double", { team_id: "team2" })}>Decline Double</button>
    </div>
  );

  // Per-hole history table
  const holeHistoryTable = gameState.hole_history && gameState.hole_history.length > 0 && (
    <div style={{marginTop:24}}>
      <h3 style={{marginBottom:8, fontSize:18, color:COLORS.primary}}>Per-Hole History</h3>
      <div style={tableContainerStyle}>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Hole</th>
              <th style={thStyle}>Hitting Order</th>
              {gameState.players.map(p => (
                <th key={p.id} style={thStyle}>Net {p.name}</th>
              ))}
              {gameState.players.map(p => (
                <th key={p.id+"_pts"} style={thStyle}>ΔPts {p.name}</th>
              ))}
              <th style={thStyle}>Teams</th>
            </tr>
          </thead>
          <tbody>
            {gameState.hole_history.map(h => (
              <tr key={h.hole} style={{background: h.hole === gameState.current_hole ? '#e3f2fd' : undefined}}>
                <td style={tdStyle}>{h.hole}</td>
                <td style={tdStyle}>{h.hole <= 16 ? h.hitting_order.map(pid => PLAYER_NAMES[pid]).join(", ") : "(Hoepfinger phase)"}</td>
                {gameState.players.map(p => {
                  const stroke = playerStrokes?.[p.id]?.[h.hole] || 0;
                  return (
                    <td key={p.id} style={tdStyle}>
                      {h.net_scores[p.id] ?? ""}
                      {stroke === 1 && <span title="Gets a stroke" style={{color:COLORS.accent,marginLeft:4,fontWeight:700}}>●</span>}
                      {stroke === 0.5 && <span title="Gets a half-stroke" style={{color:COLORS.warning,marginLeft:4,fontWeight:700}}>◐</span>}
                      {stroke > 1 && <span title={`Gets ${stroke} strokes`} style={{color:COLORS.accent,marginLeft:4,fontWeight:700}}>●x{stroke}</span>}
                    </td>
                  );
                })}
                {gameState.players.map(p => (
                  <td key={p.id+"_pts"} style={tdStyle}>{h.points_delta[p.id] > 0 ? "+" : ""}{h.points_delta[p.id]}</td>
                ))}
                <td style={tdStyle}>
                  {h.teams.type === "partners" &&
                    `T1: ${h.teams.team1.map(pid => PLAYER_NAMES[pid]).join(" & ")}, T2: ${h.teams.team2.map(pid => PLAYER_NAMES[pid]).join(" & ")}`}
                  {h.teams.type === "solo" &&
                    `Solo: ${PLAYER_NAMES[h.teams.captain]} vs ${h.teams.opponents.map(pid => PLAYER_NAMES[pid]).join(", ")}`}
                  {h.teams.type === "pending" && "Pending"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{fontSize:13, color:COLORS.muted, marginTop:4}}>
          <span style={{color:COLORS.accent, fontWeight:700}}>●</span> = player received a stroke on this hole &nbsp; <span style={{color:COLORS.warning, fontWeight:700}}>◐</span> = player received a half-stroke
        </div>
      </div>
    </div>
  );

  // Mobile nav bar
  const mobileNav = (
    <nav style={mobileNavStyle}>
      <button style={navBtnStyle} onClick={restartGame}>
        Restart
      </button>
      <button style={navBtnStyle} onClick={() => doAction("next_hole")}>Next Hole</button>
      <button style={navBtnStyle} onClick={() => setShowDebug(v => !v)}>{showDebug ? "Hide" : "Show"} Debug</button>
    </nav>
  );

  // Betting Tips Card
  const bettingTipsCard = bettingTips.length > 0 && (
    <div style={{ ...cardStyle, background: COLORS.bg, borderLeft: `4px solid ${COLORS.accent}` }}>
      <div style={{ fontWeight: 700, color: COLORS.accent, marginBottom: 6, fontSize: 16 }}>Betting Tips</div>
      <ul style={{ margin: 0, paddingLeft: 18 }}>
        {bettingTips.map((tip, i) => (
          <li key={i} style={{ marginBottom: 4, color: COLORS.text, fontSize: 14 }}>{tip}</li>
        ))}
      </ul>
    </div>
  );

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", fontFamily: "Inter, system-ui, sans-serif", background: COLORS.bg, minHeight: "100vh", paddingBottom: 70 }}>
      <header style={stickyHeaderStyle}>
        Wolf Goat Pig MVP
      </header>
      <main style={{padding: "12px 8px 0 8px"}}>
        {gameState.selected_course && <div style={{marginBottom:8, fontWeight:600, color:COLORS.primary}}>Course: {gameState.selected_course}</div>}
        {bettingTipsCard}
        {doubleAlert}
        <div style={{display:'flex',flexDirection:'row',alignItems:'center',justifyContent:'space-between',marginBottom:8}}>
          <h2 style={{margin:0,fontSize:22,color:COLORS.primary}}>Hole {gameState.current_hole} (Par {gameState.hole_par})</h2>
          <span style={{fontSize:15,color:COLORS.muted}}><strong>Wager:</strong> {gameState.base_wager}q</span>
        </div>
        <div style={{marginBottom:8,fontSize:15,color:COLORS.muted}}><strong>Game Phase:</strong> {gameState.game_phase}</div>
        {statusBox}
        {teamStatus && <div style={{ margin: "10px 0", ...cardStyle }}>{teamStatus}</div>}
        <div style={cardStyle}>
          <h3 style={{marginTop:0,marginBottom:8,fontSize:17,color:COLORS.primary}}>Players</h3>
          {playersTable}
        </div>
        <div style={cardStyle}>
          <h3 style={{marginTop:0,marginBottom:8,fontSize:17,color:COLORS.primary}}>Hitting Order</h3>
          <ol style={{paddingLeft:18,margin:0,display:'flex',flexWrap:'wrap',gap:8}}>
            {gameState.hitting_order.map(pid => (
              <li key={pid} style={{fontSize:15,margin:0}}>{gameState.players.find(p => p.id === pid)?.name}</li>
            ))}
          </ol>
        </div>
        {holeHistoryTable}
        {/* Captain's actions */}
        {gameState.teams?.type === undefined && !doublePending && (
          <div style={{ ...cardStyle, opacity: doublePending ? 0.5 : 1, pointerEvents: doublePending ? 'none' : 'auto' }}>
            <div style={{marginBottom:8}}><strong>Captain's Actions:</strong></div>
            <select value={partnerSelect} onChange={e => setPartnerSelect(e.target.value)} style={{...inputStyle, width:'100%',marginBottom:8}}>
              <option value="">Select Partner</option>
              {availablePartners().map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <button style={{...buttonStyle, width:'100%',marginBottom:6}} disabled={!partnerSelect} onClick={() => doAction("request_partner", { captain_id: gameState.captain_id, partner_id: partnerSelect })}>Request Partner</button>
            <button style={{...buttonStyle, width:'100%'}} onClick={() => doAction("go_solo", { captain_id: gameState.captain_id })}>Go Solo</button>
          </div>
        )}
        {/* Partner's response */}
        {gameState.teams?.type === "pending" && requestedPartnerId && !doublePending && (
          <div style={{ ...cardStyle, opacity: doublePending ? 0.5 : 1, pointerEvents: doublePending ? 'none' : 'auto' }}>
            <div style={{marginBottom:8}}><strong>{PLAYER_NAMES[requestedPartnerId]}'s Response:</strong></div>
            <button style={{...buttonStyle, width:'100%',marginBottom:6}} onClick={() => doAction("accept_partner", { partner_id: requestedPartnerId })}>Accept</button>
            <button style={{...buttonStyle, width:'100%'}} onClick={() => doAction("decline_partner", { partner_id: requestedPartnerId })}>Decline</button>
          </div>
        )}
        {/* Score input and calculate points */}
        {(["partners", "solo"].includes(gameState.teams?.type)) && !doublePending && (
          <div style={{ ...cardStyle, opacity: doublePending ? 0.5 : 1, pointerEvents: doublePending ? 'none' : 'auto' }}>
            <div style={{marginBottom:8}}><strong>Enter Net Scores:</strong></div>
            {scoreEntryTable}
            <button
              style={{...buttonStyle, width:'100%'}}
              disabled={!canCalculate}
              onClick={async () => {
                for (const pid of Object.keys(scoreInputs)) {
                  await doAction("record_net_score", { player_id: pid, score: Number(scoreInputs[pid]) });
                }
                await doAction("calculate_hole_points");
              }}
            >Calculate Points</button>
          </div>
        )}
        {/* Betting actions */}
        {(["partners", "solo"].includes(gameState.teams?.type)) && !doublePending && (
          <div style={{ ...cardStyle, opacity: doublePending ? 0.5 : 1, pointerEvents: doublePending ? 'none' : 'auto' }}>
            <div style={{marginBottom:8}}><strong>Betting Actions:</strong></div>
            {!gameState.doubled_status && (
              <button style={{...buttonStyle, width:'100%',marginBottom:6}} onClick={() => doAction("offer_double", { offering_team_id: "team1", target_team_id: "team2" })}>
                Offer Double
              </button>
            )}
            {/* Float (only if captain hasn't used it) */}
            {!gameState.player_float_used[gameState.captain_id] && (
              <button style={{...buttonStyle, width:'100%',marginBottom:6}} onClick={() => doAction("invoke_float", { captain_id: gameState.captain_id })}>
                Invoke Float
              </button>
            )}
            {/* Option (always available for MVP) */}
            <button style={{...buttonStyle, width:'100%'}} onClick={() => doAction("toggle_option", { captain_id: gameState.captain_id })}>
              Toggle Option
            </button>
          </div>
        )}
        {/* Next hole */}
        <div style={{ ...cardStyle, opacity: doublePending ? 0.5 : 1, pointerEvents: doublePending ? 'none' : 'auto', textAlign:'center' }}>
          <button style={{...buttonStyle, width:'100%'}} onClick={() => doAction("next_hole")}>Next Hole</button>
        </div>
        {/* Collapsible debug state */}
        {showDebug && (
          <div style={{ ...cardStyle, background: COLORS.bg, fontSize: 12, overflowX: "auto" }}>
            <pre>{JSON.stringify(gameState, null, 2)}</pre>
          </div>
        )}
      </main>
      {mobileNav}
    </div>
  );
}

export default App; 