import React, { useEffect, useState } from "react";

const PLAYER_NAMES = {
  p1: "Bob",
  p2: "Scott",
  p3: "Vince",
  p4: "Mike",
};

function App() {
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scoreInputs, setScoreInputs] = useState({});
  const [partnerSelect, setPartnerSelect] = useState("");
  const [showDebug, setShowDebug] = useState(false);

  // Fetch current game state on mount
  useEffect(() => {
    fetch("/api/game/state")
      .then(res => res.json())
      .then(data => {
        setGameState(data);
        setLoading(false);
      });
  }, []);

  const refreshState = () => {
    setLoading(true);
    fetch("/api/game/state")
      .then(res => res.json())
      .then(data => {
        setGameState(data);
        setLoading(false);
      });
  };

  const doAction = async (action, payload = {}) => {
    setLoading(true);
    const res = await fetch("/api/game/action", {
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
    setLoading(true);
    fetch("/api/game/start", { method: "POST" })
      .then(res => res.json())
      .then(data => {
        setGameState(data.game_state);
        setLoading(false);
        setScoreInputs({});
        setPartnerSelect("");
      });
  };

  if (loading) return <div>Loading...</div>;
  if (!gameState) return (
    <div>
      <button onClick={restartGame}>Start Game</button>
    </div>
  );

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
    <table style={{width:'100%',borderCollapse:'collapse',marginBottom:10}}>
      <thead>
        <tr style={{background:'#f0f0f0'}}>
          <th>Name</th>
          <th>Points</th>
          <th>Role</th>
          <th>Team</th>
        </tr>
      </thead>
      <tbody>
        {gameState.players.map(player => (
          <tr key={player.id} style={{background: teamColor(player.id)}}>
            <td style={{fontWeight: isCaptain(player.id) ? 'bold' : 'normal'}}>
              {player.name} {isCaptain(player.id) && <span style={{color:'#388e3c',fontWeight:'bold',marginLeft:4}}>(Captain)</span>}
            </td>
            <td>{player.points}</td>
            <td>{isCaptain(player.id) ? 'Captain' : ''}</td>
            <td>{teamBadge(player.id)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  // Score entry table
  const scoreEntryTable = (
    <table style={{width:'100%',marginBottom:10}}>
      <thead>
        <tr style={{background:'#f0f0f0'}}>
          <th>Player</th>
          <th>Net Score</th>
        </tr>
      </thead>
      <tbody>
        {gameState.players.map(player => (
          <tr key={player.id}>
            <td>{player.name}</td>
            <td>
              <input
                type="number"
                value={scoreInputs[player.id] ?? gameState.hole_scores[player.id] ?? ""}
                onChange={e => setScoreInputs({ ...scoreInputs, [player.id]: e.target.value })}
                style={{ width: 50 }}
              />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  // Can calculate points if all scores are entered and teams are set
  const canCalculate = Object.values({ ...gameState.hole_scores, ...scoreInputs }).every(v => v !== null && v !== "") && ["partners", "solo"].includes(gameState.teams?.type);

  // Notification/status area
  const statusColor = gameState.game_status_message?.toLowerCase().includes("win") ? "#388e3c" : gameState.game_status_message?.toLowerCase().includes("error") ? "#d32f2f" : "#1976d2";
  const statusBox = (
    <div style={{background:statusColor,color:'#fff',padding:10,borderRadius:6,marginBottom:16,fontWeight:500}}>
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

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", fontFamily: "sans-serif" }}>
      <h1>Wolf Goat Pig MVP</h1>
      <button onClick={restartGame} style={{marginBottom:10}}>Restart Game</button>
      <h2>Hole {gameState.current_hole}</h2>
      <div style={{marginBottom:8}}><strong>Base Wager:</strong> {gameState.base_wager} quarter(s)</div>
      <div style={{marginBottom:8}}><strong>Game Phase:</strong> {gameState.game_phase}</div>
      {statusBox}
      {teamStatus && <div style={{ margin: "10px 0" }}>{teamStatus}</div>}
      <h3>Players</h3>
      {playersTable}
      <h3>Hitting Order</h3>
      <ol>
        {gameState.hitting_order.map(pid => (
          <li key={pid}>{gameState.players.find(p => p.id === pid)?.name}</li>
        ))}
      </ol>
      {/* Captain's actions */}
      {gameState.teams?.type === undefined && (
        <div style={{ margin: "20px 0" }}>
          <div><strong>Captain's Actions:</strong></div>
          <select value={partnerSelect} onChange={e => setPartnerSelect(e.target.value)}>
            <option value="">Select Partner</option>
            {availablePartners().map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <button disabled={!partnerSelect} onClick={() => doAction("request_partner", { captain_id: gameState.captain_id, partner_id: partnerSelect })}>Request Partner</button>
          <button onClick={() => doAction("go_solo", { captain_id: gameState.captain_id })}>Go Solo</button>
        </div>
      )}
      {/* Partner's response */}
      {gameState.teams?.type === "pending" && requestedPartnerId && (
        <div style={{ margin: "20px 0" }}>
          <div><strong>{PLAYER_NAMES[requestedPartnerId]}'s Response:</strong></div>
          <button onClick={() => doAction("accept_partner", { partner_id: requestedPartnerId })}>Accept</button>
          <button onClick={() => doAction("decline_partner", { partner_id: requestedPartnerId })}>Decline</button>
        </div>
      )}
      {/* Score input and calculate points */}
      {(["partners", "solo"].includes(gameState.teams?.type)) && (
        <div style={{ margin: "20px 0" }}>
          <div><strong>Enter Net Scores:</strong></div>
          {scoreEntryTable}
          <button
            disabled={!canCalculate}
            onClick={async () => {
              // Record all scores
              for (const pid of Object.keys(scoreInputs)) {
                await doAction("record_net_score", { player_id: pid, score: Number(scoreInputs[pid]) });
              }
              await doAction("calculate_hole_points");
            }}
          >Calculate Points</button>
        </div>
      )}
      {/* Betting actions */}
      {(["partners", "solo"].includes(gameState.teams?.type)) && (
        <div style={{ margin: "20px 0" }}>
          <div><strong>Betting Actions:</strong></div>
          {/* Offer Double (only if not already doubled) */}
          {!gameState.doubled_status && (
            <button onClick={() => doAction("offer_double", { offering_team_id: "team1", target_team_id: "team2" })}>
              Offer Double
            </button>
          )}
          {/* Accept/Decline Double (if double is pending) */}
          {gameState.doubled_status && (
            <>
              <button onClick={() => doAction("accept_double", { team_id: "team2" })}>Accept Double</button>
              <button onClick={() => doAction("decline_double", { team_id: "team2" })}>Decline Double</button>
            </>
          )}
          {/* Float (only if captain hasn't used it) */}
          {!gameState.player_float_used[gameState.captain_id] && (
            <button onClick={() => doAction("invoke_float", { captain_id: gameState.captain_id })}>
              Invoke Float
            </button>
          )}
          {/* Option (always available for MVP) */}
          <button onClick={() => doAction("toggle_option", { captain_id: gameState.captain_id })}>
            Toggle Option
          </button>
        </div>
      )}
      {/* Next hole */}
      <div style={{ margin: "20px 0" }}>
        <button onClick={() => doAction("next_hole")}>Next Hole</button>
      </div>
      {/* Collapsible debug state */}
      <div style={{ margin: "30px 0", background: "#f8f8f8", padding: 10, borderRadius: 6 }}>
        <button onClick={() => setShowDebug(v => !v)} style={{marginBottom:6}}>
          {showDebug ? "Hide" : "Show"} Full Game State (Debug)
        </button>
        {showDebug && (
          <pre style={{ fontSize: 12, overflowX: "auto" }}>{JSON.stringify(gameState, null, 2)}</pre>
        )}
      </div>
    </div>
  );
}

export default App; 