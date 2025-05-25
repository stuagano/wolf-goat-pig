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

  // Helper: get available partners for captain
  const availablePartners = () => {
    if (!gameState) return [];
    return gameState.players
      .filter(p => p.id !== gameState.captain_id)
      .map(p => ({ id: p.id, name: p.name }));
  };

  // Helper: is this player the requested partner?
  const requestedPartnerId = gameState.teams?.requested;

  // Helper: show team status
  let teamStatus = null;
  if (gameState.teams?.type === "pending") {
    teamStatus = <div>Captain requests {PLAYER_NAMES[gameState.teams.requested]} as partner. Awaiting response.</div>;
  } else if (gameState.teams?.type === "partners") {
    teamStatus = <div>Team: {PLAYER_NAMES[gameState.teams.team1[0]]} & {PLAYER_NAMES[gameState.teams.team1[1]]} vs {PLAYER_NAMES[gameState.teams.team2[0]]} & {PLAYER_NAMES[gameState.teams.team2[1]]}</div>;
  } else if (gameState.teams?.type === "solo") {
    teamStatus = <div>Captain {PLAYER_NAMES[gameState.teams.captain]} is solo vs {gameState.teams.opponents.map(pid => PLAYER_NAMES[pid]).join(", ")}</div>;
  }

  // Score input fields
  const scoreFields = gameState.players.map(player => (
    <div key={player.id}>
      {player.name}: <input
        type="number"
        value={scoreInputs[player.id] ?? gameState.hole_scores[player.id] ?? ""}
        onChange={e => setScoreInputs({ ...scoreInputs, [player.id]: e.target.value })}
        style={{ width: 50 }}
      />
    </div>
  ));

  // Can calculate points if all scores are entered and teams are set
  const canCalculate = Object.values({ ...gameState.hole_scores, ...scoreInputs }).every(v => v !== null && v !== "") && ["partners", "solo"].includes(gameState.teams?.type);

  return (
    <div style={{ maxWidth: 500, margin: "0 auto", fontFamily: "sans-serif" }}>
      <h1>Wolf Goat Pig MVP</h1>
      <button onClick={restartGame}>Restart Game</button>
      <h2>Hole {gameState.current_hole}</h2>
      <div><strong>Captain:</strong> {gameState.players.find(p => p.id === gameState.captain_id)?.name}</div>
      <div><strong>Base Wager:</strong> {gameState.base_wager} quarter(s)</div>
      <div><strong>Game Phase:</strong> {gameState.game_phase}</div>
      <div><strong>Status:</strong> {gameState.game_status_message}</div>
      {teamStatus && <div style={{ margin: "10px 0" }}>{teamStatus}</div>}
      <h3>Players</h3>
      <ul>
        {gameState.players.map(player => (
          <li key={player.id}>
            {player.name} (Points: {player.points})
          </li>
        ))}
      </ul>
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
          {scoreFields}
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
      {/* Raw game state for debugging/visibility */}
      <div style={{ margin: "30px 0", background: "#f8f8f8", padding: 10, borderRadius: 6 }}>
        <strong>Full Game State (Debug):</strong>
        <pre style={{ fontSize: 12, overflowX: "auto" }}>{JSON.stringify(gameState, null, 2)}</pre>
      </div>
    </div>
  );
}

export default App; 