import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../theme/Provider';

const API_URL = process.env.REACT_APP_API_URL || "";

function TestMultiplayerPage() {
  const theme = useTheme();
  const navigate = useNavigate();

  const [testData, setTestData] = useState({
    joinCode: '',
    gameId: '',
    player1: { name: 'Alice', handicap: '10' },
    player2: { name: 'Bob', handicap: '15' },
    player3: { name: 'Charlie', handicap: '20' },
    player4: { name: 'Diana', handicap: '12' }
  });

  const [logs, setLogs] = useState([]);

  const addLog = (message, type = 'info') => {
    setLogs(prev => [...prev, { message, type, time: new Date().toLocaleTimeString() }]);
  };

  const createTestGame = async () => {
    addLog('Creating test game...', 'info');

    try {
      const response = await fetch(`${API_URL}/games/create?course_name=Wing Point Golf & Country Club&player_count=4`, {
        method: 'POST'
      });

      const data = await response.json();

      if (response.ok) {
        setTestData(prev => ({
          ...prev,
          joinCode: data.join_code,
          gameId: data.game_id
        }));
        addLog(`✓ Game created! Code: ${data.join_code}, ID: ${data.game_id}`, 'success');
      } else {
        addLog(`✗ Failed to create game: ${data.detail}`, 'error');
      }
    } catch (err) {
      addLog(`✗ Error: ${err.message}`, 'error');
    }
  };

  const joinAsPlayer = async (playerNum) => {
    const player = testData[`player${playerNum}`];

    if (!testData.joinCode) {
      addLog('✗ No join code! Create a game first.', 'error');
      return;
    }

    addLog(`Joining as ${player.name}...`, 'info');

    try {
      const response = await fetch(`${API_URL}/games/join/${testData.joinCode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_name: player.name,
          handicap: parseFloat(player.handicap)
        })
      });

      const data = await response.json();

      if (response.ok) {
        addLog(`✓ ${player.name} joined! (${data.players_joined}/${data.max_players} players)`, 'success');
      } else {
        addLog(`✗ ${player.name} failed to join: ${data.detail}`, 'error');
      }
    } catch (err) {
      addLog(`✗ Error joining as ${player.name}: ${err.message}`, 'error');
    }
  };

  const joinAllPlayers = async () => {
    addLog('Joining all 4 players sequentially...', 'info');
    for (let i = 1; i <= 4; i++) {
      await joinAsPlayer(i);
      // Small delay between joins
      await new Promise(resolve => setTimeout(resolve, 300));
    }
  };

  const viewLobby = () => {
    if (testData.gameId) {
      navigate(`/lobby/${testData.gameId}`);
    } else {
      addLog('✗ No game ID available', 'error');
    }
  };

  const openJoinPage = () => {
    if (testData.joinCode) {
      window.open(`/join/${testData.joinCode}`, '_blank');
    } else {
      addLog('✗ No join code available', 'error');
    }
  };

  const clearLogs = () => {
    setLogs([]);
  };

  return (
    <div style={{
      maxWidth: 800,
      margin: '0 auto',
      padding: 20,
      fontFamily: theme.typography.fontFamily
    }}>
      <div style={theme.cardStyle}>
        <h1 style={{ color: theme.colors.primary, marginBottom: 8 }}>
          🧪 Multiplayer Testing Lab
        </h1>
        <p style={{ color: theme.colors.textSecondary, marginBottom: 24 }}>
          Test the join code flow without multiple Auth0 accounts
        </p>

        {/* Current Game Info */}
        {testData.joinCode && (
          <div style={{
            background: '#e3f2fd',
            padding: 16,
            borderRadius: 8,
            marginBottom: 24
          }}>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>Current Test Game:</div>
            <div>Join Code: <code style={{
              background: '#fff',
              padding: '2px 8px',
              borderRadius: 4,
              fontWeight: 700,
              fontSize: 18
            }}>{testData.joinCode}</code></div>
            <div style={{ fontSize: 13, color: theme.colors.textSecondary, marginTop: 4 }}>
              Game ID: {testData.gameId}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ color: theme.colors.primary, marginBottom: 12 }}>
            Quick Actions:
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <button
              onClick={createTestGame}
              style={{
                ...theme.buttonStyle,
                fontSize: 14,
                padding: '12px 16px'
              }}
            >
              1️⃣ Create Game
            </button>
            <button
              onClick={joinAllPlayers}
              disabled={!testData.joinCode}
              style={{
                ...theme.buttonStyle,
                fontSize: 14,
                padding: '12px 16px',
                background: !testData.joinCode ? theme.colors.textSecondary : theme.colors.primary,
                cursor: !testData.joinCode ? 'not-allowed' : 'pointer'
              }}
            >
              2️⃣ Join All Players
            </button>
            <button
              onClick={viewLobby}
              disabled={!testData.gameId}
              style={{
                ...theme.buttonStyle,
                fontSize: 14,
                padding: '12px 16px',
                background: !testData.gameId ? theme.colors.textSecondary : theme.colors.success,
                cursor: !testData.gameId ? 'not-allowed' : 'pointer'
              }}
            >
              3️⃣ View Lobby
            </button>
            <button
              onClick={openJoinPage}
              disabled={!testData.joinCode}
              style={{
                ...theme.buttonStyle,
                fontSize: 14,
                padding: '12px 16px',
                background: !testData.joinCode ? theme.colors.textSecondary : theme.colors.accent,
                cursor: !testData.joinCode ? 'not-allowed' : 'pointer'
              }}
            >
              🔗 Open Join Page
            </button>
          </div>
        </div>

        {/* Individual Player Joins */}
        <div style={{ marginBottom: 24 }}>
          <h3 style={{ color: theme.colors.primary, marginBottom: 12 }}>
            Join as Individual Players:
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            {[1, 2, 3, 4].map(num => {
              const player = testData[`player${num}`];
              return (
                <button
                  key={num}
                  onClick={() => joinAsPlayer(num)}
                  disabled={!testData.joinCode}
                  style={{
                    ...theme.buttonStyle,
                    fontSize: 14,
                    padding: '12px 16px',
                    background: !testData.joinCode ? theme.colors.textSecondary : '#9c27b0',
                    cursor: !testData.joinCode ? 'not-allowed' : 'pointer'
                  }}
                >
                  Join as {player.name} ({player.handicap})
                </button>
              );
            })}
          </div>
        </div>

        {/* Activity Log */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ color: theme.colors.primary, margin: 0 }}>
              Activity Log:
            </h3>
            <button
              onClick={clearLogs}
              style={{
                padding: '4px 12px',
                fontSize: 12,
                background: 'transparent',
                color: theme.colors.textSecondary,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: 4,
                cursor: 'pointer'
              }}
            >
              Clear
            </button>
          </div>
          <div style={{
            background: '#1e1e1e',
            color: '#d4d4d4',
            padding: 16,
            borderRadius: 8,
            maxHeight: 300,
            overflowY: 'auto',
            fontFamily: 'monospace',
            fontSize: 13
          }}>
            {logs.length === 0 ? (
              <div style={{ color: '#666' }}>No activity yet...</div>
            ) : (
              logs.map((log, index) => (
                <div
                  key={index}
                  style={{
                    marginBottom: 4,
                    color: log.type === 'error' ? '#f48771' : log.type === 'success' ? '#89d185' : '#d4d4d4'
                  }}
                >
                  <span style={{ color: '#666' }}>[{log.time}]</span> {log.message}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Instructions */}
        <div style={{
          background: '#fff3e0',
          padding: 16,
          borderRadius: 8,
          fontSize: 14
        }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 600 }}>
            📚 How to Test:
          </p>
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            <li>Click "Create Game" to generate a join code</li>
            <li>Use "Join All Players" to quickly add 4 test players</li>
            <li>Click "View Lobby" to see the waiting room</li>
            <li>Or use "Open Join Page" to test in a new window</li>
          </ol>
          <p style={{ margin: '12px 0 0 0', fontSize: 13, color: theme.colors.textSecondary }}>
            💡 Pro tip: Open <code>/join/{testData.joinCode}</code> in incognito windows
            to simulate real players joining from different devices!
          </p>
        </div>

        {/* Back Button */}
        <button
          onClick={() => navigate('/')}
          style={{
            ...theme.buttonStyle,
            width: '100%',
            marginTop: 16,
            background: 'transparent',
            color: theme.colors.textSecondary,
            border: `1px solid ${theme.colors.border}`
          }}
        >
          ← Back to Home
        </button>
      </div>
    </div>
  );
}

export default TestMultiplayerPage;
