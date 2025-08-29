import React, { useState, useEffect } from 'react';
import { useTheme } from '../theme/Provider';

const API_URL = process.env.REACT_APP_API_URL || "";

const GHINIntegration = () => {
  const theme = useTheme();
  const [players, setPlayers] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [ghinId, setGhinId] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');
  const [ghinStatus, setGhinStatus] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);

  // Load initial data
  useEffect(() => {
    loadPlayers();
    checkGHINStatus();
    loadEnhancedLeaderboard();
  }, []);

  const loadPlayers = async () => {
    try {
      const response = await fetch(`${API_URL}/players`);
      if (response.ok) {
        const data = await response.json();
        setPlayers(data.filter(p => !p.is_ai)); // Filter out AI players
      }
    } catch (error) {
      console.error('Error loading players:', error);
    }
  };

  const checkGHINStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/ghin/diagnostic`);
      if (response.ok) {
        const data = await response.json();
        setGhinStatus(data);
      }
    } catch (error) {
      console.error('Error checking GHIN status:', error);
    }
  };

  const loadEnhancedLeaderboard = async () => {
    try {
      const response = await fetch(`${API_URL}/leaderboard/ghin-enhanced`);
      if (response.ok) {
        const data = await response.json();
        setLeaderboard(data.slice(0, 10)); // Top 10
      }
    } catch (error) {
      console.error('Error loading enhanced leaderboard:', error);
    }
  };

  const addGHINId = async () => {
    if (!selectedPlayer || !ghinId) {
      setMessage('Please select a player and enter a GHIN ID');
      setMessageType('error');
      return;
    }

    try {
      setLoading(true);
      const player = players.find(p => p.id.toString() === selectedPlayer);
      
      const response = await fetch(`${API_URL}/players/${selectedPlayer}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...player,
          ghin_id: ghinId
        })
      });

      if (response.ok) {
        setMessage(`✅ Added GHIN ID ${ghinId} to ${player.name}`);
        setMessageType('success');
        setGhinId('');
        setSelectedPlayer('');
        loadPlayers();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update player');
      }
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const syncPlayerHandicap = async (playerId) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/ghin/sync-player-handicap/${playerId}`, {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        setMessage(`✅ Synced handicap: ${data.handicap_index} for ${data.player_name}`);
        setMessageType('success');
        loadEnhancedLeaderboard();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to sync handicap');
      }
    } catch (error) {
      setMessage(`❌ Sync failed: ${error.message}`);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const syncAllHandicaps = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/ghin/sync-handicaps`, {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        setMessage(`✅ Synced ${data.synced} of ${data.total_players} players`);
        setMessageType('success');
        loadEnhancedLeaderboard();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to sync handicaps');
      }
    } catch (error) {
      setMessage(`❌ Bulk sync failed: ${error.message}`);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const cardStyle = {
    ...theme.cardStyle,
    marginBottom: '20px'
  };

  const buttonStyle = {
    ...theme.buttonStyle,
    margin: '5px',
    minWidth: '120px'
  };

  const inputStyle = {
    padding: '10px',
    border: `1px solid ${theme.colors.border}`,
    borderRadius: '4px',
    fontSize: '14px',
    width: '100%',
    marginBottom: '10px'
  };

  const selectStyle = {
    ...inputStyle,
    backgroundColor: 'white'
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
      <h1 style={{ color: theme.colors.primary, marginBottom: '30px' }}>
        🏌️ GHIN Integration
      </h1>

      {/* GHIN Status Card */}
      <div style={cardStyle}>
        <h3 style={{ color: theme.colors.primary }}>GHIN Service Status</h3>
        {ghinStatus ? (
          <div>
            <p><strong>Status:</strong> {ghinStatus.status}</p>
            <p><strong>Initialized:</strong> {ghinStatus.initialized ? '✅ Yes' : '❌ No'}</p>
            <p><strong>Configuration:</strong> {ghinStatus.config_status}</p>
            {ghinStatus.error && (
              <p style={{ color: theme.colors.error }}>
                <strong>Error:</strong> {ghinStatus.error}
              </p>
            )}
          </div>
        ) : (
          <p>Loading GHIN status...</p>
        )}
      </div>

      {/* Add GHIN ID Card */}
      <div style={cardStyle}>
        <h3 style={{ color: theme.colors.primary }}>Add GHIN ID to Player</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 200px 120px', gap: '10px', alignItems: 'end' }}>
          <div>
            <label style={{ fontSize: '14px', fontWeight: '600', marginBottom: '5px', display: 'block' }}>
              Select Player:
            </label>
            <select
              value={selectedPlayer}
              onChange={(e) => setSelectedPlayer(e.target.value)}
              style={selectStyle}
            >
              <option value="">Choose a player...</option>
              {players.map(player => (
                <option key={player.id} value={player.id}>
                  {player.name} {player.ghin_id ? `(GHIN: ${player.ghin_id})` : '(No GHIN ID)'}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ fontSize: '14px', fontWeight: '600', marginBottom: '5px', display: 'block' }}>
              GHIN ID:
            </label>
            <input
              type="text"
              value={ghinId}
              onChange={(e) => setGhinId(e.target.value)}
              placeholder="e.g. 1234567"
              style={inputStyle}
            />
          </div>
          <button
            onClick={addGHINId}
            disabled={loading || !selectedPlayer || !ghinId}
            style={buttonStyle}
          >
            {loading ? 'Adding...' : 'Add GHIN ID'}
          </button>
        </div>
      </div>

      {/* Sync Controls Card */}
      <div style={cardStyle}>
        <h3 style={{ color: theme.colors.primary }}>Handicap Sync</h3>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={syncAllHandicaps}
            disabled={loading}
            style={{...buttonStyle, backgroundColor: theme.colors.success}}
          >
            {loading ? 'Syncing...' : 'Sync All Handicaps'}
          </button>
          <button
            onClick={loadEnhancedLeaderboard}
            disabled={loading}
            style={buttonStyle}
          >
            Refresh Leaderboard
          </button>
        </div>
      </div>

      {/* Message Display */}
      {message && (
        <div style={{
          ...cardStyle,
          backgroundColor: messageType === 'success' ? theme.colors.successBg : theme.colors.errorBg,
          color: messageType === 'success' ? theme.colors.success : theme.colors.error,
          border: `1px solid ${messageType === 'success' ? theme.colors.success : theme.colors.error}`
        }}>
          {message}
        </div>
      )}

      {/* Enhanced Leaderboard */}
      <div style={cardStyle}>
        <h3 style={{ color: theme.colors.primary }}>GHIN-Enhanced Leaderboard</h3>
        {leaderboard.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: `2px solid ${theme.colors.border}` }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Rank</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Player</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>GHIN</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Handicap</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Earnings</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Win %</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Form</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((player, index) => (
                  <tr key={index} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                    <td style={{ padding: '12px' }}>{player.rank}</td>
                    <td style={{ padding: '12px', fontWeight: '600' }}>{player.player_name}</td>
                    <td style={{ padding: '12px' }}>
                      {player.ghin_id || 'None'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      {player.handicap ? player.handicap.toFixed(1) : 'N/A'}
                      {player.ghin_last_updated && (
                        <div style={{ fontSize: '12px', color: theme.colors.textSecondary }}>
                          Updated: {new Date(player.ghin_last_updated).toLocaleDateString()}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '12px' }}>${player.total_earnings?.toFixed(2) || '0.00'}</td>
                    <td style={{ padding: '12px' }}>{player.win_percentage?.toFixed(1) || '0'}%</td>
                    <td style={{ padding: '12px' }}>
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        backgroundColor: player.recent_form === 'Excellent' ? '#d4edda' :
                                        player.recent_form === 'Good' ? '#e2e8f0' :
                                        player.recent_form === 'Poor' ? '#f8d7da' : '#f8f9fa',
                        color: player.recent_form === 'Poor' ? '#721c24' : '#495057'
                      }}>
                        {player.recent_form || 'N/A'}
                      </span>
                    </td>
                    <td style={{ padding: '12px' }}>
                      {player.ghin_id && (
                        <button
                          onClick={() => syncPlayerHandicap(player.player_id || player.id)}
                          disabled={loading}
                          style={{
                            ...buttonStyle,
                            fontSize: '12px',
                            padding: '6px 12px',
                            minWidth: '80px'
                          }}
                        >
                          Sync
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>Loading leaderboard...</p>
        )}
      </div>
    </div>
  );
};

export default GHINIntegration;