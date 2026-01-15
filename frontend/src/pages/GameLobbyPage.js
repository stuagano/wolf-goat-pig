import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTheme } from '../theme/Provider';
import { useSheetSync } from '../context';
import CommissionerChat from '../components/CommissionerChat';
import TeeTossModal from '../components/game/TeeTossModal';

const API_URL = process.env.REACT_APP_API_URL || "";

function GameLobbyPage() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { gameId } = useParams();
  const { syncData: leaderboardPlayers } = useSheetSync();

  const [lobby, setLobby] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [starting, setStarting] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showAddPlayer, setShowAddPlayer] = useState(false);
  const [newPlayerName, setNewPlayerName] = useState('');
  const [newPlayerHandicap, setNewPlayerHandicap] = useState('18.0');
  const [addingPlayer, setAddingPlayer] = useState(false);
  const [editingPlayer, setEditingPlayer] = useState(null); // {player_slot_id, field: 'name' or 'handicap', value}
  const [deletingPlayer, setDeletingPlayer] = useState(null);
  const [showTeeToss, setShowTeeToss] = useState(false);
  const [teeOrderSet, setTeeOrderSet] = useState(false);
  // settingTeeOrder tracks API call state - used in handleSetTeeOrder
  // eslint-disable-next-line no-unused-vars
  const [settingTeeOrder, setSettingTeeOrder] = useState(false);
  const [playerSuggestions, setPlayerSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Poll lobby status every 2 seconds
  useEffect(() => {
    const fetchLobby = async () => {
      try {
        const response = await fetch(`${API_URL}/games/${gameId}/lobby`);

        if (!response.ok) {
          throw new Error('Game not found');
        }

        const data = await response.json();
        setLobby(data);
        setError('');

        // Check if tee order is set
        if (data.tee_order_set !== undefined) {
          setTeeOrderSet(data.tee_order_set);
        }

        // Update session in localStorage to keep it fresh
        const currentSession = localStorage.getItem(`wgp_session_${gameId}`);
        if (currentSession) {
          const sessionData = JSON.parse(currentSession);
          sessionData.timestamp = Date.now();
          sessionData.status = data.status;
          localStorage.setItem(`wgp_session_${gameId}`, JSON.stringify(sessionData));
        }

        // If game has started, redirect to game page
        if (data.status === 'in_progress' || data.status === 'completed') {
          navigate(`/game/${gameId}`);
        }
      } catch (err) {
        console.error('Error fetching lobby:', err);
        setError(err.message || 'Failed to load lobby');
      } finally {
        setLoading(false);
      }
    };

    fetchLobby();
    const interval = setInterval(fetchLobby, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [gameId, navigate]);

  const startGame = async () => {
    setStarting(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/games/${gameId}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to start game');
      }

      // Navigate to game page
      navigate(`/game/${gameId}`);

    } catch (err) {
      console.error('Error starting game:', err);
      setError(err.message || 'Failed to start game');
      setStarting(false);
    }
  };

  const copyJoinCode = () => {
    if (lobby?.join_code) {
      navigator.clipboard.writeText(lobby.join_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const copyJoinLink = () => {
    if (lobby?.join_code) {
      const link = `${window.location.origin}/join/${lobby.join_code}`;
      navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Handle player name input and show suggestions
  const handlePlayerNameChange = (value) => {
    setNewPlayerName(value);

    if (value.trim().length >= 2 && leaderboardPlayers.length > 0) {
      // Find matching players (fuzzy match)
      const matches = leaderboardPlayers
        .filter(player => {
          const playerName = (player.player_name || player.name || '').toLowerCase();
          const searchTerm = value.toLowerCase().trim();

          // Match if player name starts with search term or contains it
          return playerName.includes(searchTerm);
        })
        .slice(0, 5); // Limit to 5 suggestions

      setPlayerSuggestions(matches);
      setShowSuggestions(matches.length > 0);
    } else {
      setPlayerSuggestions([]);
      setShowSuggestions(false);
    }
  };

  // Select a suggested player
  const selectSuggestedPlayer = (player) => {
    setNewPlayerName(player.player_name || player.name);
    // Try to use the player's handicap if available
    // Note: leaderboard doesn't have handicap data, but we can default it
    setShowSuggestions(false);
    setPlayerSuggestions([]);
  };

  const handleAddPlayer = async (e) => {
    e.preventDefault();
    if (!newPlayerName.trim() || !newPlayerHandicap) {
      setError('Please enter player name and handicap');
      return;
    }

    setAddingPlayer(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/games/join/${lobby.join_code}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_name: newPlayerName.trim(),
          handicap: parseFloat(newPlayerHandicap)
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to add player');
      }

      // Reset form
      setNewPlayerName('');
      setNewPlayerHandicap('18.0');
      setShowAddPlayer(false);

      // Refresh will happen via polling

    } catch (err) {
      console.error('Error adding player:', err);
      setError(err.message || 'Failed to add player');
    } finally {
      setAddingPlayer(false);
    }
  };

  const handleRemovePlayer = async (playerSlotId) => {
    if (!window.confirm('Are you sure you want to remove this player?')) {
      return;
    }

    setDeletingPlayer(playerSlotId);
    setError('');

    try {
      const response = await fetch(`${API_URL}/games/${gameId}/players/${playerSlotId}`, {
        method: 'DELETE'
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to remove player');
      }

      // Refresh will happen via polling

    } catch (err) {
      console.error('Error removing player:', err);
      setError(err.message || 'Failed to remove player');
    } finally {
      setDeletingPlayer(null);
    }
  };

  const handleUpdatePlayer = async (playerSlotId, field, value) => {
    setError('');

    try {
      const endpoint = field === 'name'
        ? `/games/${gameId}/players/${playerSlotId}/name`
        : `/games/${gameId}/players/${playerSlotId}/handicap`;

      const body = field === 'name'
        ? { name: value }
        : { handicap: parseFloat(value) };

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `Failed to update ${field}`);
      }

      setEditingPlayer(null);
      // Refresh will happen via polling

    } catch (err) {
      console.error(`Error updating ${field}:`, err);
      setError(err.message || `Failed to update ${field}`);
    }
  };

  const handleSetTeeOrder = async (orderedPlayers) => {
    setSettingTeeOrder(true);
    setError('');

    try {
      console.log('Ordered players received:', orderedPlayers);

      // Map ordered players to their slot IDs
      const playerOrder = orderedPlayers.map(player => player.player_slot_id || player.id);
      console.log('Player order to send:', playerOrder);

      const response = await fetch(`${API_URL}/games/${gameId}/tee-order`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_order: playerOrder })
      });

      const data = await response.json();
      console.log('Response from backend:', data);

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to set tee order');
      }

      setTeeOrderSet(true);
      setShowTeeToss(false);
      // Refresh will happen via polling

    } catch (err) {
      console.error('Error setting tee order:', err);
      setError(err.message || 'Failed to set tee order');
    } finally {
      setSettingTeeOrder(false);
    }
  };

  if (loading) {
    return (
      <div style={{
        maxWidth: 600,
        margin: '0 auto',
        padding: 20,
        fontFamily: theme.typography.fontFamily
      }}>
        <div style={theme.cardStyle}>
          <p style={{ textAlign: 'center', color: theme.colors.textPrimary }}>
            Loading lobby...
          </p>
        </div>
      </div>
    );
  }

  if (error && !lobby) {
    return (
      <div style={{
        maxWidth: 600,
        margin: '0 auto',
        padding: 20,
        fontFamily: theme.typography.fontFamily
      }}>
        <div style={theme.cardStyle}>
          <h2 style={{ color: theme.colors.error }}>Error</h2>
          <p>{error}</p>
          <button
            onClick={() => navigate('/')}
            style={{
              ...theme.buttonStyle,
              marginTop: 16
            }}
          >
            ← Back to Home
          </button>
        </div>
      </div>
    );
  }

  const canStart = lobby?.players_joined >= 2 && lobby?.players_joined <= lobby?.max_players && teeOrderSet;
  const canSetTeeOrder = lobby?.players_joined >= 2 && !teeOrderSet;

  // Convert lobby players to format expected by TeeTossModal
  const playersForToss = lobby?.players ? lobby.players.map(p => ({
    id: p.player_slot_id,
    player_slot_id: p.player_slot_id,
    name: p.player_name,
    handicap: p.handicap
  })) : [];

  return (
    <div style={{
      maxWidth: 600,
      margin: '0 auto',
      padding: 20,
      fontFamily: theme.typography.fontFamily
    }}>
      <div style={theme.cardStyle}>
        <h1 style={{ color: theme.colors.primary, marginBottom: 8 }}>
          🎮 Game Lobby
        </h1>
        <p style={{ color: theme.colors.textSecondary, marginBottom: 24 }}>
          Waiting for players to join...
        </p>

        {/* Join Code Display */}
        <div style={{
          background: theme.colors.primary,
          color: 'white',
          padding: 24,
          borderRadius: 12,
          textAlign: 'center',
          marginBottom: 24
        }}>
          <div style={{ fontSize: 14, marginBottom: 8, opacity: 0.9 }}>
            Join Code:
          </div>
          <div style={{
            fontSize: 48,
            fontWeight: 700,
            letterSpacing: 8,
            fontFamily: 'monospace',
            marginBottom: 16
          }}>
            {lobby?.join_code}
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
            <button
              onClick={copyJoinCode}
              style={{
                padding: '8px 16px',
                background: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600
              }}
            >
              {copied ? '✓ Copied!' : '📋 Copy Code'}
            </button>
            <button
              onClick={copyJoinLink}
              style={{
                padding: '8px 16px',
                background: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600
              }}
            >
              🔗 Copy Link
            </button>
          </div>
        </div>

        {/* Game Info */}
        <div style={{
          background: '#f5f5f5',
          padding: 16,
          borderRadius: 8,
          marginBottom: 24
        }}>
          <div style={{ marginBottom: 8 }}>
            <strong>Course:</strong> {lobby?.course_name || 'Not selected'}
          </div>
          <div style={{ marginBottom: 8 }}>
            <strong>Players:</strong> {lobby?.players_joined} / {lobby?.max_players}
          </div>
          <div>
            <strong>Status:</strong>{' '}
            <span style={{
              color: canStart ? theme.colors.success : theme.colors.warning,
              fontWeight: 600
            }}>
              {canStart ? 'Ready to start!' : `Waiting for ${Math.max(2 - lobby?.players_joined, 0)} more player(s)`}
            </span>
          </div>
        </div>

        {/* Players List */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ color: theme.colors.primary, margin: 0 }}>
            Players Joined:
          </h3>
          <button
            onClick={() => setShowAddPlayer(!showAddPlayer)}
            disabled={lobby?.players_joined >= lobby?.max_players}
            style={{
              padding: '6px 12px',
              background: theme.colors.primary,
              color: 'white',
              border: 'none',
              borderRadius: 6,
              cursor: lobby?.players_joined >= lobby?.max_players ? 'not-allowed' : 'pointer',
              fontSize: 14,
              fontWeight: 600,
              opacity: lobby?.players_joined >= lobby?.max_players ? 0.5 : 1
            }}
          >
            {showAddPlayer ? '✕ Cancel' : '+ Add Player'}
          </button>
        </div>

        {/* Add Player Form */}
        {showAddPlayer && (
          <form onSubmit={handleAddPlayer} style={{
            background: '#f0f7ff',
            padding: 16,
            borderRadius: 8,
            marginBottom: 16,
            border: '2px solid ' + theme.colors.primary
          }}>
            <div style={{ marginBottom: 12, position: 'relative' }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 600, fontSize: 14 }}>
                Player Name:
              </label>
              <input
                type="text"
                value={newPlayerName}
                onChange={(e) => handlePlayerNameChange(e.target.value)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)} // Delay to allow click
                onFocus={() => {
                  if (newPlayerName.trim().length >= 2 && playerSuggestions.length > 0) {
                    setShowSuggestions(true);
                  }
                }}
                placeholder="Enter player name (e.g., Steve)"
                maxLength={50}
                required
                autoComplete="off"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: 6,
                  border: '1px solid #ddd',
                  fontSize: 14,
                  boxSizing: 'border-box'
                }}
              />

              {/* Player Name Suggestions Dropdown */}
              {showSuggestions && playerSuggestions.length > 0 && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  background: 'white',
                  border: '1px solid #ddd',
                  borderTop: 'none',
                  borderRadius: '0 0 6px 6px',
                  boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                  maxHeight: '200px',
                  overflowY: 'auto',
                  zIndex: 1000
                }}>
                  <div style={{
                    padding: '8px 12px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    color: '#666',
                    borderBottom: '1px solid #eee',
                    background: '#f9f9f9'
                  }}>
                    Did you mean...
                  </div>
                  {playerSuggestions.map((player, index) => (
                    <div
                      key={index}
                      onClick={() => selectSuggestedPlayer(player)}
                      style={{
                        padding: '10px 12px',
                        cursor: 'pointer',
                        borderBottom: index < playerSuggestions.length - 1 ? '1px solid #f0f0f0' : 'none',
                        fontSize: 14,
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        transition: 'background-color 0.15s'
                      }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = '#f5f5f5'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                    >
                      <span style={{ fontWeight: 500 }}>
                        {player.player_name || player.name}
                      </span>
                      <span style={{ fontSize: 12, color: '#999' }}>
                        {player.games_played || 0} games
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 600, fontSize: 14 }}>
                Handicap:
              </label>
              <input
                type="number"
                value={newPlayerHandicap}
                onChange={(e) => setNewPlayerHandicap(e.target.value)}
                min="0"
                max="54"
                step="0.1"
                required
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: 6,
                  border: '1px solid #ddd',
                  fontSize: 14,
                  boxSizing: 'border-box'
                }}
              />
            </div>
            <button
              type="submit"
              disabled={addingPlayer}
              style={{
                ...theme.buttonStyle,
                width: '100%',
                cursor: addingPlayer ? 'not-allowed' : 'pointer',
                opacity: addingPlayer ? 0.6 : 1
              }}
            >
              {addingPlayer ? 'Adding...' : 'Add Player'}
            </button>
          </form>
        )}

        <div style={{ marginBottom: 24 }}>
          {lobby?.players && lobby.players.length > 0 ? (
            lobby.players.map((player, index) => {
              const isEditingName = editingPlayer?.player_slot_id === player.player_slot_id && editingPlayer?.field === 'name';
              const isEditingHandicap = editingPlayer?.player_slot_id === player.player_slot_id && editingPlayer?.field === 'handicap';
              const isDeleting = deletingPlayer === player.player_slot_id;

              return (
                <div
                  key={player.player_slot_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: 16,
                    background: index % 2 === 0 ? 'white' : '#f9f9f9',
                    borderRadius: 8,
                    marginBottom: 8,
                    border: `1px solid ${theme.colors.border}`,
                    opacity: isDeleting ? 0.5 : 1
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
                    <div style={{
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      background: theme.colors.primary,
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 700,
                      fontSize: 18
                    }}>
                      {index + 1}
                    </div>
                    <div style={{ flex: 1 }}>
                      {/* Player Name - Editable */}
                      {isEditingName ? (
                        <div style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
                          <input
                            type="text"
                            value={editingPlayer.value}
                            onChange={(e) => setEditingPlayer({ ...editingPlayer, value: e.target.value })}
                            style={{
                              flex: 1,
                              padding: '4px 8px',
                              fontSize: 14,
                              borderRadius: 4,
                              border: '1px solid ' + theme.colors.primary
                            }}
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                handleUpdatePlayer(player.player_slot_id, 'name', editingPlayer.value);
                              } else if (e.key === 'Escape') {
                                setEditingPlayer(null);
                              }
                            }}
                          />
                          <button
                            onClick={() => handleUpdatePlayer(player.player_slot_id, 'name', editingPlayer.value)}
                            style={{
                              padding: '4px 8px',
                              background: theme.colors.success,
                              color: 'white',
                              border: 'none',
                              borderRadius: 4,
                              cursor: 'pointer',
                              fontSize: 12
                            }}
                          >
                            ✓
                          </button>
                          <button
                            onClick={() => setEditingPlayer(null)}
                            style={{
                              padding: '4px 8px',
                              background: '#ccc',
                              color: 'white',
                              border: 'none',
                              borderRadius: 4,
                              cursor: 'pointer',
                              fontSize: 12
                            }}
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <div
                          onClick={() => setEditingPlayer({ player_slot_id: player.player_slot_id, field: 'name', value: player.player_name })}
                          style={{
                            fontWeight: 600,
                            fontSize: 16,
                            cursor: 'pointer',
                            padding: '2px 4px',
                            borderRadius: 4,
                            display: 'inline-block',
                            marginBottom: 2
                          }}
                          title="Click to edit name"
                        >
                          {player.player_name} ✏️
                        </div>
                      )}

                      {/* Handicap - Editable */}
                      {isEditingHandicap ? (
                        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                          <span style={{ fontSize: 13, color: theme.colors.textSecondary }}>Handicap:</span>
                          <input
                            type="number"
                            value={editingPlayer.value}
                            onChange={(e) => setEditingPlayer({ ...editingPlayer, value: e.target.value })}
                            min="0"
                            max="54"
                            step="0.1"
                            style={{
                              width: 60,
                              padding: '4px 8px',
                              fontSize: 13,
                              borderRadius: 4,
                              border: '1px solid ' + theme.colors.primary
                            }}
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                handleUpdatePlayer(player.player_slot_id, 'handicap', editingPlayer.value);
                              } else if (e.key === 'Escape') {
                                setEditingPlayer(null);
                              }
                            }}
                          />
                          <button
                            onClick={() => handleUpdatePlayer(player.player_slot_id, 'handicap', editingPlayer.value)}
                            style={{
                              padding: '2px 6px',
                              background: theme.colors.success,
                              color: 'white',
                              border: 'none',
                              borderRadius: 4,
                              cursor: 'pointer',
                              fontSize: 11
                            }}
                          >
                            ✓
                          </button>
                          <button
                            onClick={() => setEditingPlayer(null)}
                            style={{
                              padding: '2px 6px',
                              background: '#ccc',
                              color: 'white',
                              border: 'none',
                              borderRadius: 4,
                              cursor: 'pointer',
                              fontSize: 11
                            }}
                          >
                            ✕
                          </button>
                        </div>
                      ) : (
                        <div
                          onClick={() => setEditingPlayer({ player_slot_id: player.player_slot_id, field: 'handicap', value: player.handicap })}
                          style={{
                            fontSize: 13,
                            color: theme.colors.textSecondary,
                            cursor: 'pointer',
                            padding: '2px 4px',
                            borderRadius: 4,
                            display: 'inline-block'
                          }}
                          title="Click to edit handicap"
                        >
                          Handicap: {player.handicap} ✏️
                          {player.is_authenticated && ' • 🔒'}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Remove Button */}
                  <button
                    onClick={() => handleRemovePlayer(player.player_slot_id)}
                    disabled={isDeleting}
                    style={{
                      padding: '6px 12px',
                      background: theme.colors.error,
                      color: 'white',
                      border: 'none',
                      borderRadius: 6,
                      cursor: isDeleting ? 'not-allowed' : 'pointer',
                      fontSize: 12,
                      fontWeight: 600,
                      opacity: isDeleting ? 0.6 : 1
                    }}
                    title="Remove player"
                  >
                    {isDeleting ? '...' : '✕ Remove'}
                  </button>
                </div>
              );
            })
          ) : (
            <p style={{ color: theme.colors.textSecondary, fontStyle: 'italic' }}>
              No players have joined yet
            </p>
          )}
        </div>

        {error && (
          <div style={{
            background: '#ffebee',
            color: theme.colors.error,
            padding: 12,
            borderRadius: 8,
            marginBottom: 16
          }}>
            {error}
          </div>
        )}

        {/* Set Tee Order Button */}
        {canSetTeeOrder && (
          <button
            onClick={() => setShowTeeToss(true)}
            style={{
              ...theme.buttonStyle,
              width: '100%',
              fontSize: 18,
              padding: '16px 24px',
              background: theme.colors.primary,
              marginBottom: 16
            }}
          >
            🎯 Set Tee Order (Toss Tees)
          </button>
        )}

        {/* Tee Order Status */}
        {teeOrderSet && (
          <div style={{
            background: '#e8f5e9',
            border: '2px solid ' + theme.colors.success,
            borderRadius: 8,
            padding: 16,
            marginBottom: 16,
            textAlign: 'center'
          }}>
            <div style={{ fontSize: 18, fontWeight: 600, color: theme.colors.success, marginBottom: 4 }}>
              ✓ Tee Order Set!
            </div>
            <div style={{ fontSize: 14, color: theme.colors.textSecondary }}>
              Ready to start the game
            </div>
          </div>
        )}

        {/* Start Game Button (for creator or anyone in dev mode) */}
        <button
          onClick={startGame}
          disabled={!canStart || starting}
          style={{
            ...theme.buttonStyle,
            width: '100%',
            fontSize: 18,
            padding: '16px 24px',
            background: (!canStart || starting) ? theme.colors.textSecondary : theme.colors.success,
            cursor: (!canStart || starting) ? 'not-allowed' : 'pointer'
          }}
        >
          {starting ? 'Starting Game...' : canStart ? '🚀 Start Game' : !teeOrderSet ? '⚠️ Set Tee Order First' : `Need ${Math.max(2 - lobby?.players_joined, 0)} More Player(s)`}
        </button>

        {/* Instructions */}
        <div style={{
          marginTop: 24,
          padding: 16,
          background: '#e3f2fd',
          borderRadius: 8,
          fontSize: 14
        }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 600 }}>
            📱 Share this code with your friends:
          </p>
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            <li>They visit {window.location.origin}</li>
            <li>Click "Join Game"</li>
            <li>Enter code: <strong>{lobby?.join_code}</strong></li>
          </ol>
          <p style={{ margin: '12px 0 0 0', fontSize: 13, color: theme.colors.textSecondary }}>
            Or share the direct link using the "Copy Link" button above!
          </p>
        </div>

        {/* Testing Note */}
        <div style={{
          marginTop: 16,
          padding: 12,
          background: '#fff3e0',
          borderRadius: 8,
          fontSize: 13,
          color: '#e65100'
        }}>
          <strong>💡 Testing Tip:</strong> Open <code>/join/{lobby?.join_code}</code> in
          multiple browser windows (or incognito) to simulate different players joining!
        </div>
      </div>

      {/* Tee Toss Modal */}
      {showTeeToss && (
        <TeeTossModal
          players={playersForToss}
          onClose={() => setShowTeeToss(false)}
          onOrderComplete={handleSetTeeOrder}
        />
      )}

      <CommissionerChat gameState={null} />
    </div>
  );
}

export default GameLobbyPage;
