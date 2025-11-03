import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useTheme } from '../theme/Provider';
import Scorecard from '../components/simulation/visual/Scorecard';
import LargeScoringButtons from '../components/game/LargeScoringButtons';
import GameStateWidget from '../components/GameStateWidget';
import GameBanner from '../components/GameBanner';

const API_URL = process.env.REACT_APP_API_URL || "";

const PLAYER_NAMES = {
  p1: "Bob",
  p2: "Scott", 
  p3: "Vince",
  p4: "Mike",
};

// Simple utility to check if game state is blank/empty
const isBlankGameState = (gameState) => {
  return !gameState || !gameState.players || gameState.players.length === 0;
};

function GamePage({ gameState, setGameState, loading, setLoading, ...rest }) {
  const theme = useTheme();
  const [partnerSelect, setPartnerSelect] = useState("");
  const [showDebug, setShowDebug] = useState(false);
  const [bettingTips, setBettingTips] = useState([]);
  const [playerStrokes, setPlayerStrokes] = useState({});
  const [rules, setRules] = useState([]);
  const [ruleIdx, setRuleIdx] = useState(0);

  // Derived styles from theme
  const tableContainerStyle = {
    overflowX: "auto",
    WebkitOverflowScrolling: "touch",
    marginBottom: theme.spacing[4],
  };

  const tableStyle = {
    width: "100%",
    minWidth: 400,
    borderCollapse: "collapse",
  };

  const thStyle = {
    background: theme.colors.background,
    color: theme.colors.textPrimary,
    fontWeight: theme.typography.bold,
    textAlign: "left",
    padding: `${theme.spacing[3]} ${theme.spacing[2]}`,
    borderBottom: `2px solid ${theme.colors.border}`,
  };

  const tdStyle = {
    padding: `${theme.spacing[2]} ${theme.spacing[1]}`,
    borderBottom: `1px solid ${theme.colors.border}`,
    background: theme.colors.paper,
  };

  const stickyHeaderStyle = {
    position: "sticky",
    top: 0,
    zIndex: 10,
  };

  const mobileNavStyle = {
    position: "fixed",
    left: 0,
    right: 0,
    bottom: 0,
    background: theme.colors.paper,
    borderTop: `2px solid ${theme.colors.border}`,
    padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
    display: "flex",
    justifyContent: "space-around",
    zIndex: 1000,
    boxShadow: theme.shadows.lg,
  };

  const navBtnStyle = {
    ...theme.buttonStyle,
    background: theme.colors.primary,
    borderRadius: theme.borderRadius.full,
    fontSize: theme.typography.xs,
    padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
    margin: 0,
    minWidth: 70,
    textAlign: "center",
  };

  useEffect(() => {
    fetch(`${API_URL}/rules`).then(res => res.json()).then(data => setRules(data));
  }, []);

  useEffect(() => {
    if (!loading || rules.length === 0) return;
    const interval = setInterval(() => {
      setRuleIdx(idx => (idx + 1) % rules.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [loading, rules]);

  const setupNewSimulation = async () => {
    setLoading(true);
    try {
      // Initialize with default players using the simulation system
      const setupData = {
        players: [
          { id: "p1", name: "Bob", handicap: 10.5 },
          { id: "p2", name: "Scott", handicap: 15 },
          { id: "p3", name: "Vince", handicap: 8 },
          { id: "p4", name: "Mike", handicap: 20.5 }
        ],
        course_name: "Wing Point Golf & Country Club"
      };

      const res = await fetch(`${API_URL}/simulation/setup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(setupData)
      });

      const data = await res.json();

      if (res.ok && data.game_state) {
        setGameState(data.game_state);
        return true;
      } else {
        console.error("Failed to setup game:", data);
        setGameState(null);
        return false;
      }
    } catch (error) {
      console.error("Error setting up simulation:", error);
      setGameState(null);
      return false;
    } finally {
      setLoading(false);
      setPartnerSelect("");
    }
  };

  useEffect(() => {
    const initializeGame = async () => {
      try {
        // Try to fetch existing game state
        const stateRes = await fetch(`${API_URL}/game/state`);
        const stateData = await stateRes.json();

        if (isBlankGameState(stateData)) {
          // No game exists, auto-initialize with simulation system
          console.log("No existing game, initializing new game with simulation system...");
          await setupNewSimulation();
        } else {
          setGameState(stateData);
          setLoading(false);
        }

        // Fetch tips and strokes
        fetch(`${API_URL}/game/tips`).then(res => res.json()).then(data => setBettingTips(data.tips || []));
        fetch(`${API_URL}/game/player_strokes`).then(res => res.json()).then(data => setPlayerStrokes(data));
      } catch (error) {
        console.error("Error initializing game:", error);
        setLoading(false);
      }
    };

    initializeGame();
  }, [setGameState, setLoading]);

  const fetchAndSetGameState = async () => {
    try {
      const res = await fetch(`${API_URL}/game/state`);
      if (!res.ok) return false;
      const stateData = await res.json();
      if (isBlankGameState(stateData)) {
        setGameState(null);
      } else {
        setGameState(stateData);
      }
      return true;
    } catch (error) {
      console.error('Failed to refresh game state:', error);
      return false;
    }
  };

  const applyGameStateFromResponse = async (data) => {
    if (!data) return false;

    const possibleState = data.game_state || data.gameState || data.state;
    if (possibleState) {
      if (isBlankGameState(possibleState)) {
        setGameState(null);
      } else {
        setGameState(possibleState);
      }
      return true;
    }

    if (data.status || data.message || data.available_actions || data.log_message) {
      return await fetchAndSetGameState();
    }

    return false;
  };

  const doAction = async (action, payload = {}) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/game/action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, payload }),
      });

      let data = null;
      try {
        data = await res.json();
      } catch (jsonError) {
        console.warn('Failed to parse action response', jsonError);
      }

      if (!res.ok) {
        console.error(`Action ${action} failed`, data);
      }

      const handled = await applyGameStateFromResponse(data);
      if (!handled) {
        await fetchAndSetGameState();
      }

      return data;
    } catch (error) {
      console.error('Failed to perform action:', error);
      await fetchAndSetGameState();
      return null;
    } finally {
      setLoading(false);
      setPartnerSelect("");
    }
  };

  const handleScoreSubmit = async (scores) => {
    // Submit all scores
    for (const pid of Object.keys(scores)) {
      await doAction("record_net_score", { player_id: pid, score: Number(scores[pid]) });
    }
    // Calculate points after all scores are recorded
    await doAction("calculate_hole_points");
  };

  const createNewGame = async () => {
    if (!window.confirm("Are you sure you want to start a new game? All progress will be lost.")) return;
    await setupNewSimulation();
  };

  if (loading) {
    return (
      <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',height:'100vh',background:theme.colors.background}}>
        <div style={{...theme.cardStyle, textAlign:'center', maxWidth: 420, marginTop: -80}}>
          <h1 style={{color:theme.colors.primary, fontSize:32, marginBottom:16}}>Wolf Goat Pig</h1>
          <p style={{fontSize:18, color:theme.colors.textPrimary, marginBottom:16}}>Warming up the backend... hang tight!</p>
          {rules.length > 0 && (
            <div style={{marginTop:16, fontSize:17, color:theme.colors.accent, minHeight: 80}}>
              <b>Rule:</b> <span style={{color:theme.colors.textPrimary}}>{rules[ruleIdx].title}</span>
              <div style={{fontSize:15, color:theme.colors.textSecondary, marginTop:6}}>{rules[ruleIdx].description}</div>
            </div>
          )}
          {rules.length === 0 && <div style={{marginTop:24, color:theme.colors.textSecondary}}>Loading rules...</div>}
        </div>
      </div>
    );
  }
  
  if (!gameState) return <Navigate to="/setup" />;

  const team1 = gameState.teams?.team1 || [];
  const team2 = gameState.teams?.team2 || [];
  const isCaptain = pid => pid === gameState.captain_id;
  const teamBadge = pid => team1.includes(pid) ? <span style={{background:'#00bcd4',color:'#fff',borderRadius:4,padding:'2px 6px',marginLeft:4,fontSize:12}}>Team 1</span> : team2.includes(pid) ? <span style={{background:'#ff9800',color:'#fff',borderRadius:4,padding:'2px 6px',marginLeft:4,fontSize:12}}>Team 2</span> : null;

  let teamStatus = null;
  if (gameState.teams?.type === "pending") {
    teamStatus = <div>Captain requests <b>{PLAYER_NAMES[gameState.teams.requested]}</b> as partner. Awaiting response.</div>;
  } else if (gameState.teams?.type === "partners") {
    teamStatus = <div><span style={{background:'#00bcd4',color:'#fff',borderRadius:4,padding:'2px 6px'}}>Team 1</span>: <b>{PLAYER_NAMES[gameState.teams.team1[0]]} & {PLAYER_NAMES[gameState.teams.team1[1]]}</b> vs <span style={{background:'#ff9800',color:'#fff',borderRadius:4,padding:'2px 6px'}}>Team 2</span>: <b>{PLAYER_NAMES[gameState.teams.team2[0]]} & {PLAYER_NAMES[gameState.teams.team2[1]]}</b></div>;
  } else if (gameState.teams?.type === "solo") {
    teamStatus = <div><b>Captain {PLAYER_NAMES[gameState.teams.captain]}</b> (Solo) vs {gameState.teams.opponents.map(pid => PLAYER_NAMES[pid]).join(", ")}</div>;
  }

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
                {player.name} {isCaptain(player.id) && <span style={{color:theme.colors.success,fontWeight:700,marginLeft:4}}>(Captain)</span>}
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


  const statusColor = gameState.game_status_message?.toLowerCase().includes("win") ? theme.colors.success : gameState.game_status_message?.toLowerCase().includes("error") ? theme.colors.error : theme.colors.primary;
  const statusBox = (
    <div style={{background:statusColor,color:'#fff',padding:12,borderRadius:8,marginBottom:18,fontWeight:500,boxShadow:'0 1px 4px rgba(0,0,0,0.06)'}}>
      {gameState.game_status_message}
    </div>
  );

  const availablePartners = () => {
    if (!gameState) return [];
    return gameState.players
      .filter(p => p.id !== gameState.captain_id)
      .map(p => ({ id: p.id, name: p.name }));
  };

  const requestedPartnerId = gameState.teams?.requested;
  const doublePending = gameState.doubled_status && (["partners", "solo"].includes(gameState.teams?.type));

  const doubleAlert = doublePending && (
    <div style={{background:'#fff3cd',color:'#856404',border:'2px solid #ffe082',padding:20,borderRadius:8,marginBottom:20,boxShadow:'0 2px 8px #ffe082'}}>
      <div style={{fontWeight:700,fontSize:18,marginBottom:10}}>Double Offered!</div>
      <div style={{marginBottom:12}}>A double has been offered. Do you accept or decline?</div>
      <button style={{background:'#388e3c',color:'#fff',fontWeight:600,padding:'8px 18px',marginRight:10,border:'none',borderRadius:4,fontSize:16}} onClick={() => doAction("accept_double", { team_id: "team2", accepted: true })}>Accept Double</button>
      <button style={{background:'#d32f2f',color:'#fff',fontWeight:600,padding:'8px 18px',border:'none',borderRadius:4,fontSize:16}} onClick={() => doAction("decline_double", { team_id: "team2", accepted: false })}>Decline Double</button>
    </div>
  );

  const holeHistoryTable = gameState.hole_history && gameState.hole_history.length > 0 && (
    <div style={{marginTop:24}}>
      <h3 style={{marginBottom:8, fontSize:18, color:theme.colors.primary}}>Per-Hole History</h3>
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
                      {stroke === 1 && <span title="Gets a stroke" style={{color:theme.colors.accent,marginLeft:4,fontWeight:700}}>●</span>}
                      {stroke === 0.5 && <span title="Gets a half-stroke" style={{color:theme.colors.warning,marginLeft:4,fontWeight:700}}>◐</span>}
                      {stroke > 1 && <span title={`Gets ${stroke} strokes`} style={{color:theme.colors.accent,marginLeft:4,fontWeight:700}}>●x{stroke}</span>}
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
        <div style={{fontSize:13, color:theme.colors.textSecondary, marginTop:4}}>
          <span style={{color:theme.colors.accent, fontWeight:700}}>●</span> = player received a stroke on this hole &nbsp; <span style={{color:theme.colors.warning, fontWeight:700}}>◐</span> = player received a half-stroke
        </div>
      </div>
    </div>
  );

  const mobileNav = (
    <nav style={mobileNavStyle}>
      <button style={navBtnStyle} onClick={createNewGame}>
        Create New Game
      </button>
      <button style={navBtnStyle} onClick={() => doAction("next_hole")}>Next Hole</button>
      <button style={navBtnStyle} onClick={() => setShowDebug(v => !v)}>{showDebug ? "Hide" : "Show"} Debug</button>
    </nav>
  );

  const bettingTipsCard = bettingTips.length > 0 && (
    <div style={{ ...theme.cardStyle, background: theme.colors.background, borderLeft: `4px solid ${theme.colors.accent}` }}>
      <div style={{ fontWeight: 700, color: theme.colors.accent, marginBottom: 6, fontSize: 16 }}>Betting Tips</div>
      <ul style={{ margin: 0, paddingLeft: 18 }}>
        {bettingTips.map((tip, i) => (
          <li key={i} style={{ marginBottom: 4, color: theme.colors.textPrimary, fontSize: 14 }}>{tip}</li>
        ))}
      </ul>
    </div>
  );

  return (
    <div style={{ maxWidth: 480, margin: "0 auto", fontFamily: "Inter, system-ui, sans-serif", background: theme.colors.background, minHeight: "100vh", paddingBottom: 70 }}>
      <header style={stickyHeaderStyle}>
        Wolf Goat Pig MVP
      </header>
      <main style={{padding: "12px 8px 0 8px"}}>
        <GameBanner />
        {gameState.selected_course && <div style={{marginBottom:8, fontWeight:600, color:theme.colors.primary}}>Course: {gameState.selected_course}</div>}
        {bettingTipsCard}
        {doubleAlert}
        <div style={{display:'flex',flexDirection:'row',alignItems:'center',justifyContent:'space-between',marginBottom:8}}>
          <h2 style={{margin:0,fontSize:22,color:theme.colors.primary}}>Hole {gameState.current_hole} (Par {gameState.hole_par})</h2>
          <span style={{fontSize:15,color:theme.colors.textSecondary}}><strong>Wager:</strong> {gameState.base_wager}q</span>
        </div>
        <div style={{marginBottom:8,fontSize:15,color:theme.colors.textSecondary}}><strong>Game Phase:</strong> {gameState.game_phase}</div>
        {statusBox}

        {/* Running Totals - Always Visible */}
        <div style={{ ...theme.cardStyle, marginBottom: 16, background: '#f0f7ff' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: 18, color: theme.colors.primary, fontWeight: 'bold' }}>
            💰 Current Standings
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
            {gameState.players.map(player => (
              <div key={player.id} style={{
                padding: '12px',
                background: 'white',
                borderRadius: '8px',
                border: `2px solid ${isCaptain(player.id) ? theme.colors.primary : theme.colors.border}`
              }}>
                <div style={{ fontWeight: 'bold', fontSize: 16, marginBottom: 4 }}>
                  {player.name} {isCaptain(player.id) && '⭐'}
                </div>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: player.points >= 0 ? theme.colors.success : theme.colors.error }}>
                  {player.points > 0 ? '+' : ''}{player.points}q
                </div>
                <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
                  Hdcp: {player.handicap}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Real-time Game State Tracking */}
        <GameStateWidget
          gameState={gameState}
          holeState={gameState?.hole_state}
          onAction={doAction}
        />

        {teamStatus && <div style={{ margin: "10px 0", ...theme.cardStyle }}>{teamStatus}</div>}

        {/* Scorecard */}
        <div style={{ marginBottom: 16 }}>
          <Scorecard
            players={gameState.players}
            holeHistory={gameState.hole_history || []}
            currentHole={gameState.current_hole}
          />
        </div>
        <div style={theme.cardStyle}>
          <h3 style={{marginTop:0,marginBottom:8,fontSize:17,color:theme.colors.primary}}>Players</h3>
          {playersTable}
        </div>
        <div style={theme.cardStyle}>
          <h3 style={{marginTop:0,marginBottom:8,fontSize:17,color:theme.colors.primary}}>Hitting Order</h3>
          <ol style={{paddingLeft:18,margin:0,display:'flex',flexWrap:'wrap',gap:8}}>
            {gameState.hitting_order.map(pid => (
              <li key={pid} style={{fontSize:15,margin:0}}>{gameState.players.find(p => p.id === pid)?.name}</li>
            ))}
          </ol>
        </div>
        {holeHistoryTable}
        {gameState.teams?.type === undefined && !doublePending && (
          <div style={{
            ...theme.cardStyle,
            opacity: doublePending ? 0.5 : 1,
            pointerEvents: doublePending ? 'none' : 'auto',
            background: '#fff9e6',
            border: '3px solid #ff9800',
            boxShadow: '0 4px 16px rgba(255, 152, 0, 0.3)'
          }}>
            <div style={{
              fontSize: 18,
              fontWeight: 'bold',
              color: theme.colors.warning,
              marginBottom: 12,
              textAlign: 'center'
            }}>
              ⚠️ CAPTAIN: FORM TEAMS TO START HOLE ⚠️
            </div>
            <div style={{marginBottom:8, fontSize: 14}}>
              <strong>Captain {PLAYER_NAMES[gameState.captain_id] || 'Unknown'}:</strong> Choose your strategy for Hole {gameState.current_hole}
            </div>
            <select value={partnerSelect} onChange={e => setPartnerSelect(e.target.value)} style={{...theme.inputStyle, width:'100%',marginBottom:8, fontSize: 16, padding: '12px'}}>
              <option value="">Select Partner</option>
              {availablePartners().map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <button
              style={{
                ...theme.buttonStyle,
                width:'100%',
                marginBottom:6,
                background: theme.colors.success,
                fontSize: 16,
                padding: '14px',
                fontWeight: 'bold'
              }}
              disabled={!partnerSelect}
              onClick={() => doAction("request_partner", { captain_id: gameState.captain_id, partner_id: partnerSelect })}
            >
              🤝 Request Partner
            </button>
            <button
              style={{
                ...theme.buttonStyle,
                width:'100%',
                background: theme.colors.warning,
                fontSize: 16,
                padding: '14px',
                fontWeight: 'bold'
              }}
              onClick={() => doAction("go_solo", { captain_id: gameState.captain_id })}
            >
              🐺 Go Solo (2x Wager!)
            </button>
          </div>
        )}
        {gameState.teams?.type === "pending" && requestedPartnerId && !doublePending && (
          <div style={{
            ...theme.cardStyle,
            opacity: doublePending ? 0.5 : 1,
            pointerEvents: doublePending ? 'none' : 'auto',
            background: '#e8f5e9',
            border: '3px solid #4caf50',
            boxShadow: '0 4px 16px rgba(76, 175, 80, 0.3)'
          }}>
            <div style={{
              fontSize: 18,
              fontWeight: 'bold',
              color: theme.colors.success,
              marginBottom: 12,
              textAlign: 'center'
            }}>
              🤝 PARTNERSHIP REQUEST 🤝
            </div>
            <div style={{marginBottom:12, fontSize: 16, textAlign: 'center'}}>
              <strong>Captain {PLAYER_NAMES[gameState.captain_id]}</strong> wants to partner with <strong>{PLAYER_NAMES[requestedPartnerId]}</strong>
            </div>
            <div style={{marginBottom:12, fontSize: 14, color: theme.colors.textSecondary, textAlign: 'center'}}>
              {PLAYER_NAMES[requestedPartnerId]}: Do you accept?
            </div>
            <button
              style={{
                ...theme.buttonStyle,
                width:'100%',
                marginBottom:8,
                background: theme.colors.success,
                fontSize: 16,
                padding: '14px',
                fontWeight: 'bold'
              }}
              onClick={() => doAction("accept_partner", { partner_id: requestedPartnerId, accepted: true })}
            >
              ✅ Accept Partnership
            </button>
            <button
              style={{
                ...theme.buttonStyle,
                width:'100%',
                background: theme.colors.error,
                fontSize: 16,
                padding: '14px',
                fontWeight: 'bold'
              }}
              onClick={() => doAction("decline_partner", { partner_id: requestedPartnerId, accepted: false })}
            >
              ❌ Decline (Captain Goes Solo)
            </button>
          </div>
        )}
        {(["partners", "solo"].includes(gameState.teams?.type)) && !doublePending && (
          <div style={{
            opacity: doublePending ? 0.5 : 1,
            pointerEvents: doublePending ? 'none' : 'auto',
            marginTop: 16
          }}>
            <div style={{
              background: '#e3f2fd',
              padding: '12px',
              borderRadius: '8px',
              marginBottom: '12px',
              border: `2px solid ${theme.colors.primary}`,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 16, fontWeight: 'bold', color: theme.colors.primary }}>
                ✅ Teams Formed - Ready to Score!
              </div>
              <div style={{ fontSize: 14, color: theme.colors.textSecondary, marginTop: 4 }}>
                Enter scores below to calculate points
              </div>
            </div>
            <LargeScoringButtons
              gameState={gameState}
              onScoreSubmit={handleScoreSubmit}
              onAction={doAction}
              loading={loading}
            />
          </div>
        )}
        {showDebug && (
          <div style={{ ...theme.cardStyle, background: theme.colors.background, fontSize: 12, overflowX: "auto" }}>
            <pre>{JSON.stringify(gameState, null, 2)}</pre>
          </div>
        )}
      </main>
      {mobileNav}
    </div>
  );
}

export default GamePage;