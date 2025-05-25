import React, { useEffect, useState } from "react";

function App() {
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch current game state on mount
  useEffect(() => {
    fetch("/api/game/state")
      .then(res => res.json())
      .then(data => {
        setGameState(data);
        setLoading(false);
      });
  }, []);

  const startGame = () => {
    setLoading(true);
    fetch("/api/game/start", { method: "POST" })
      .then(res => res.json())
      .then(data => {
        setGameState(data.game_state);
        setLoading(false);
      });
  };

  if (loading) return <div>Loading...</div>;

  if (!gameState) return (
    <div>
      <button onClick={startGame}>Start Game</button>
    </div>
  );

  return (
    <div>
      <h1>Wolf Goat Pig MVP</h1>
      <button onClick={startGame}>Restart Game</button>
      <h2>Hole {gameState.current_hole}</h2>
      <div><strong>Captain:</strong> {gameState.players.find(p => p.id === gameState.captain_id)?.name}</div>
      <div><strong>Base Wager:</strong> {gameState.base_wager} quarter(s)</div>
      <div><strong>Game Phase:</strong> {gameState.game_phase}</div>
      <div><strong>Status:</strong> {gameState.game_status_message}</div>
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
    </div>
  );
}

export default App; 