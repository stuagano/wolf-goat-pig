// frontend/src/components/game/SimpleScorekeeper.jsx
import React, { useState, useEffect } from 'react';
import { useTheme } from '../../theme/Provider';
import BettingTracker from './BettingTracker';
import '../../styles/mobile-touch.css';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * Simplified scorekeeper component - no game engine, just direct data entry
 * Client-side betting UI, single API call to complete each hole
 */
const SimpleScorekeeper = ({ gameId, players, baseWager = 0.25 }) => {
  const theme = useTheme();

  // Current hole state (all client-side until submit)
  const [currentHole, setCurrentHole] = useState(1);
  const [teamMode, setTeamMode] = useState('partners'); // 'partners' or 'solo'
  const [team1, setTeam1] = useState([]);
  const [team2, setTeam2] = useState([]);
  const [captain, setCaptain] = useState(null);
  const [opponents, setOpponents] = useState([]);
  const [currentWager, setCurrentWager] = useState(baseWager);
  const [scores, setScores] = useState({});
  const [winner, setWinner] = useState(null);
  const [holePar, setHolePar] = useState(4);

  // Game history and standings
  const [holeHistory, setHoleHistory] = useState([]);
  const [playerStandings, setPlayerStandings] = useState({});

  // UI state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [editingHole, setEditingHole] = useState(null); // Track which hole is being edited

  // Initialize player standings
  useEffect(() => {
    const standings = {};
    players.forEach(player => {
      standings[player.id] = { quarters: 0, name: player.name };
    });
    setPlayerStandings(standings);
  }, [players]);

  // Reset hole state for new hole
  const resetHole = () => {
    setTeam1([]);
    setTeam2([]);
    setCaptain(null);
    setOpponents([]);
    setCurrentWager(baseWager);
    setScores({});
    setWinner(null);
    setHolePar(4);
    setError(null);
    setEditingHole(null);
  };

  // Load hole data for editing
  const loadHoleForEdit = (hole) => {
    setEditingHole(hole.hole);
    setCurrentHole(hole.hole);
    setHolePar(hole.hole_par || 4);
    setScores(hole.gross_scores || {});
    setCurrentWager(hole.wager || baseWager);
    setWinner(hole.winner);

    // Set team mode and teams based on hole data
    if (hole.teams.type === 'partners') {
      setTeamMode('partners');
      setTeam1(hole.teams.team1 || []);
      setTeam2(hole.teams.team2 || []);
      setCaptain(null);
      setOpponents([]);
    } else {
      setTeamMode('solo');
      setCaptain(hole.teams.captain);
      setOpponents(hole.teams.opponents || []);
      setTeam1([]);
      setTeam2([]);
    }

    // Scroll to top so user can see the form
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handle team selection for partners mode
  const togglePlayerTeam = (playerId) => {
    if (team1.includes(playerId)) {
      setTeam1(team1.filter(id => id !== playerId));
    } else if (team2.includes(playerId)) {
      setTeam2(team2.filter(id => id !== playerId));
    } else {
      // Add to team with fewer players
      if (team1.length <= team2.length) {
        setTeam1([...team1, playerId]);
      } else {
        setTeam2([...team2, playerId]);
      }
    }
  };

  // Handle captain selection for solo mode
  const toggleCaptain = (playerId) => {
    if (captain === playerId) {
      setCaptain(null);
    } else {
      setCaptain(playerId);
      // Set all other players as opponents
      setOpponents(players.filter(p => p.id !== playerId).map(p => p.id));
    }
  };

  // Handle double button
  const handleDouble = () => {
    setCurrentWager(currentWager * 2);
  };

  // Handle score input
  const handleScoreChange = (playerId, value) => {
    setScores({
      ...scores,
      [playerId]: parseInt(value, 10) || 0
    });
  };

  // Validate hole data before submission
  const validateHole = () => {
    // Check teams are set
    if (teamMode === 'partners') {
      if (team1.length === 0 || team2.length === 0) {
        return 'Please select teams';
      }
      if (team1.length !== team2.length) {
        return 'Teams must have equal players';
      }
    } else {
      if (!captain) {
        return 'Please select a captain';
      }
    }

    // Check all players have scores
    const allPlayers = teamMode === 'partners'
      ? [...team1, ...team2]
      : [captain, ...opponents];

    for (const playerId of allPlayers) {
      if (!scores[playerId] || scores[playerId] === 0) {
        return 'Please enter scores for all players';
      }
    }

    // Check winner is selected
    if (!winner) {
      return 'Please select a winner';
    }

    return null;
  };

  // Submit hole to backend
  const handleSubmitHole = async () => {
    const validationError = validateHole();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const teams = teamMode === 'partners'
        ? {
            type: 'partners',
            team1: team1,
            team2: team2
          }
        : {
            type: 'solo',
            captain: captain,
            opponents: opponents
          };

      const response = await fetch(`${API_URL}/games/${gameId}/holes/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          hole_number: currentHole,
          teams: teams,
          final_wager: currentWager,
          winner: winner,
          scores: scores,
          hole_par: holePar
        })
      });

      if (!response.ok) {
        throw new Error('Failed to submit hole');
      }

      const data = await response.json();

      if (editingHole) {
        // Editing existing hole - update it in the history
        const updatedHistory = holeHistory.map(h =>
          h.hole === editingHole ? data.hole_result : h
        );
        setHoleHistory(updatedHistory);

        // Recalculate all player standings from scratch
        const newStandings = {};
        players.forEach(player => {
          newStandings[player.id] = { quarters: 0, name: player.name };
        });

        updatedHistory.forEach(hole => {
          Object.entries(hole.points_delta).forEach(([playerId, points]) => {
            newStandings[playerId].quarters += points;
          });
        });
        setPlayerStandings(newStandings);

        // Return to the next hole after the last completed hole
        setCurrentHole(Math.max(...updatedHistory.map(h => h.hole)) + 1);
        resetHole();
      } else {
        // New hole - add to history
        setHoleHistory([...holeHistory, data.hole_result]);

        // Update player standings incrementally
        const newStandings = { ...playerStandings };
        Object.entries(data.hole_result.points_delta).forEach(([playerId, points]) => {
          newStandings[playerId].quarters += points;
        });
        setPlayerStandings(newStandings);

        // Move to next hole
        setCurrentHole(currentHole + 1);
        resetHole();
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      {/* Edit Mode Banner */}
      {editingHole && (
        <div style={{
          background: '#FF9800',
          color: 'white',
          padding: '16px 20px',
          borderRadius: '12px',
          marginBottom: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          <div>
            <div style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '4px' }}>
              ✏️ Editing Hole {editingHole}
            </div>
            <div style={{ fontSize: '14px', opacity: 0.9 }}>
              Make your changes and submit to update
            </div>
          </div>
          <button
            onClick={() => {
              setCurrentHole(Math.max(...holeHistory.map(h => h.hole)) + 1);
              resetHole();
            }}
            className="touch-optimized"
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: 'bold',
              border: '2px solid white',
              borderRadius: '8px',
              background: 'transparent',
              color: 'white',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            Cancel
          </button>
        </div>
      )}

      {/* Header - Beautiful Gradient Banner */}
      <div style={{
        background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.accent})`,
        color: 'white',
        padding: '20px',
        borderRadius: '16px 16px 0 0',
        marginBottom: '2px',
        textAlign: 'center',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
      }}>
        <div style={{ fontSize: '18px', marginBottom: '8px', opacity: 0.9 }}>
          Current Hole
        </div>
        <div style={{ fontSize: '48px', fontWeight: 'bold', lineHeight: 1 }}>
          {currentHole}
        </div>
        <div style={{ fontSize: '16px', marginTop: '8px', opacity: 0.9 }}>
          Par {holePar}
        </div>
      </div>

      {/* Betting Action Tracker */}
      <BettingTracker
        gameState={{ id: gameId, current_hole: currentHole }}
        currentPlayer={players[0]?.name || 'Player1'}
      />

      {/* Current Standings - Beautiful Card Design */}
      <div style={{
        background: theme.colors.paper,
        borderRadius: '0 0 16px 16px',
        overflow: 'hidden',
        marginBottom: '20px',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
      }}>
        <div style={{
          padding: '16px 20px',
          background: theme.colors.backgroundSecondary,
          borderBottom: `3px solid ${theme.colors.border}`,
          fontSize: '18px',
          fontWeight: 'bold',
          color: theme.colors.textPrimary
        }}>
          Current Standings
        </div>

        {Object.values(playerStandings).sort((a, b) => b.quarters - a.quarters).map((player, index) => {
          const isLeader = index === 0 && player.quarters > 0;
          const isLast = index === Object.values(playerStandings).length - 1 && player.quarters < 0;

          return (
            <div
              key={player.name}
              className="touch-optimized"
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '20px',
                borderBottom: index < Object.values(playerStandings).length - 1 ? `2px solid ${theme.colors.border}` : 'none',
                background: isLeader ? 'rgba(76, 175, 80, 0.1)' :
                           isLast ? 'rgba(244, 67, 54, 0.1)' :
                           'white'
              }}
            >
              {/* Position & Name */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1 }}>
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '50%',
                  background: isLeader ? '#4CAF50' :
                             isLast ? '#f44336' :
                             theme.colors.backgroundSecondary,
                  color: isLeader || isLast ? 'white' : theme.colors.textSecondary,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold',
                  fontSize: '18px'
                }}>
                  {index + 1}
                </div>
                <span style={{ fontSize: '20px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
                  {player.name}
                </span>
              </div>

              {/* Quarters */}
              <div style={{
                fontSize: '24px',
                fontWeight: 'bold',
                color: player.quarters > 0 ? '#4CAF50' : player.quarters < 0 ? '#f44336' : theme.colors.textSecondary,
                padding: '8px 16px',
                borderRadius: '8px',
                background: player.quarters > 0 ? 'rgba(76, 175, 80, 0.1)' :
                           player.quarters < 0 ? 'rgba(244, 67, 54, 0.1)' :
                           theme.colors.backgroundSecondary
              }}>
                {player.quarters > 0 ? '+' : ''}{player.quarters}q
              </div>
            </div>
          );
        })}
      </div>

      {/* Team Mode Selection - Enhanced Style */}
      <div style={{
        background: theme.colors.paper,
        padding: '20px',
        borderRadius: '16px',
        marginBottom: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ margin: '0 0 16px', fontSize: '20px', fontWeight: 'bold', color: theme.colors.textPrimary }}>Team Mode</h3>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => setTeamMode('partners')}
            className="touch-optimized"
            style={{
              flex: 1,
              padding: '16px',
              fontSize: '18px',
              fontWeight: 'bold',
              border: teamMode === 'partners' ? `3px solid ${theme.colors.primary}` : `2px solid ${theme.colors.border}`,
              borderRadius: '12px',
              background: teamMode === 'partners' ? theme.colors.primary : 'white',
              color: teamMode === 'partners' ? 'white' : theme.colors.textPrimary,
              cursor: 'pointer',
              transition: 'all 0.2s',
              boxShadow: teamMode === 'partners' ? '0 4px 6px rgba(0,0,0,0.2)' : 'none'
            }}
          >
            Partners
          </button>
          <button
            onClick={() => setTeamMode('solo')}
            className="touch-optimized"
            style={{
              flex: 1,
              padding: '16px',
              fontSize: '18px',
              fontWeight: 'bold',
              border: teamMode === 'solo' ? `3px solid ${theme.colors.primary}` : `2px solid ${theme.colors.border}`,
              borderRadius: '12px',
              background: teamMode === 'solo' ? theme.colors.primary : 'white',
              color: teamMode === 'solo' ? 'white' : theme.colors.textPrimary,
              cursor: 'pointer',
              transition: 'all 0.2s',
              boxShadow: teamMode === 'solo' ? '0 4px 6px rgba(0,0,0,0.2)' : 'none'
            }}
          >
            Solo
          </button>
        </div>
      </div>

      {/* Team Selection */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 12px' }}>
          {teamMode === 'partners' ? 'Select Teams' : 'Select Captain'}
        </h3>

        {teamMode === 'partners' ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
            {players.map(player => {
              const inTeam1 = team1.includes(player.id);
              const inTeam2 = team2.includes(player.id);
              return (
                <button
                  key={player.id}
                  onClick={() => togglePlayerTeam(player.id)}
                  style={{
                    padding: '12px',
                    fontSize: '16px',
                    border: inTeam1 || inTeam2 ? `3px solid ${inTeam1 ? '#00bcd4' : '#ff9800'}` : `2px solid ${theme.colors.border}`,
                    borderRadius: '8px',
                    background: inTeam1 ? 'rgba(0, 188, 212, 0.1)' : inTeam2 ? 'rgba(255, 152, 0, 0.1)' : 'white',
                    cursor: 'pointer'
                  }}
                >
                  {player.name}
                  {inTeam1 && ' (Team 1)'}
                  {inTeam2 && ' (Team 2)'}
                </button>
              );
            })}
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
            {players.map(player => {
              const isCaptain = captain === player.id;
              return (
                <button
                  key={player.id}
                  onClick={() => toggleCaptain(player.id)}
                  style={{
                    padding: '12px',
                    fontSize: '16px',
                    border: isCaptain ? `3px solid #ffc107` : `2px solid ${theme.colors.border}`,
                    borderRadius: '8px',
                    background: isCaptain ? 'rgba(255, 193, 7, 0.1)' : 'white',
                    cursor: 'pointer'
                  }}
                >
                  {isCaptain && '⭐ '}{player.name}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Betting */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 12px' }}>Wager</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: theme.colors.primary }}>
            ${currentWager.toFixed(2)}
          </div>
          <button
            onClick={handleDouble}
            style={{
              padding: '12px 24px',
              fontSize: '16px',
              fontWeight: 'bold',
              border: `2px solid ${theme.colors.primary}`,
              borderRadius: '8px',
              background: theme.colors.primary,
              color: 'white',
              cursor: 'pointer'
            }}
          >
            Double
          </button>
          <button
            onClick={() => setCurrentWager(baseWager)}
            style={{
              padding: '12px 24px',
              fontSize: '14px',
              border: `2px solid ${theme.colors.border}`,
              borderRadius: '8px',
              background: 'white',
              color: theme.colors.textPrimary,
              cursor: 'pointer'
            }}
          >
            Reset
          </button>
        </div>
      </div>

      {/* Scores */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 12px' }}>Enter Scores</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
          {players.map(player => (
            <div key={player.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ flex: 1, fontWeight: 'bold' }}>{player.name}:</label>
              <input
                type="number"
                min="0"
                max="15"
                value={scores[player.id] || ''}
                onChange={(e) => handleScoreChange(player.id, e.target.value)}
                style={{
                  width: '60px',
                  padding: '8px',
                  fontSize: '16px',
                  border: `2px solid ${theme.colors.border}`,
                  borderRadius: '4px',
                  textAlign: 'center'
                }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Winner Selection */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 12px' }}>Winner</h3>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {teamMode === 'partners' ? (
            <>
              <button
                onClick={() => setWinner('team1')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '12px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  border: winner === 'team1' ? `3px solid #00bcd4` : `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  background: winner === 'team1' ? 'rgba(0, 188, 212, 0.2)' : 'white',
                  cursor: 'pointer'
                }}
              >
                Team 1
              </button>
              <button
                onClick={() => setWinner('team2')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '12px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  border: winner === 'team2' ? `3px solid #ff9800` : `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  background: winner === 'team2' ? 'rgba(255, 152, 0, 0.2)' : 'white',
                  cursor: 'pointer'
                }}
              >
                Team 2
              </button>
              <button
                onClick={() => setWinner('push')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '12px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  border: winner === 'push' ? `3px solid ${theme.colors.textSecondary}` : `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  background: winner === 'push' ? 'rgba(128, 128, 128, 0.2)' : 'white',
                  cursor: 'pointer'
                }}
              >
                Push
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setWinner('captain')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '12px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  border: winner === 'captain' ? `3px solid #ffc107` : `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  background: winner === 'captain' ? 'rgba(255, 193, 7, 0.2)' : 'white',
                  cursor: 'pointer'
                }}
              >
                Captain
              </button>
              <button
                onClick={() => setWinner('opponents')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '12px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  border: winner === 'opponents' ? `3px solid #9c27b0` : `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  background: winner === 'opponents' ? 'rgba(156, 39, 176, 0.2)' : 'white',
                  cursor: 'pointer'
                }}
              >
                Opponents
              </button>
              <button
                onClick={() => setWinner('push')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '12px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  border: winner === 'push' ? `3px solid ${theme.colors.textSecondary}` : `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  background: winner === 'push' ? 'rgba(128, 128, 128, 0.2)' : 'white',
                  cursor: 'pointer'
                }}
              >
                Push
              </button>
            </>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          background: theme.colors.error,
          color: 'white',
          padding: '12px',
          borderRadius: '8px',
          marginBottom: '20px',
          textAlign: 'center'
        }}>
          {error}
        </div>
      )}

      {/* Submit Button */}
      <button
        onClick={handleSubmitHole}
        disabled={submitting}
        style={{
          width: '100%',
          padding: '16px',
          fontSize: '20px',
          fontWeight: 'bold',
          border: 'none',
          borderRadius: '8px',
          background: submitting ? theme.colors.textSecondary : (editingHole ? '#FF9800' : theme.colors.success),
          color: 'white',
          cursor: submitting ? 'not-allowed' : 'pointer',
          marginBottom: '20px'
        }}
      >
        {submitting
          ? 'Submitting...'
          : editingHole
            ? `Update Hole ${editingHole}`
            : `Complete Hole ${currentHole}`}
      </button>

      {/* Comprehensive Scorecard Table */}
      {holeHistory.length > 0 && (
        <div style={{
          background: theme.colors.paper,
          padding: '20px',
          borderRadius: '16px',
          marginTop: '20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          overflowX: 'auto'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <h3 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
              📊 Scorecard
            </h3>
            <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
              {holeHistory.length} hole{holeHistory.length !== 1 ? 's' : ''} completed
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '14px'
            }}>
              <thead>
                <tr style={{ background: theme.colors.backgroundSecondary }}>
                  <th style={{
                    padding: '12px 8px',
                    textAlign: 'left',
                    fontWeight: 'bold',
                    borderBottom: `3px solid ${theme.colors.border}`,
                    position: 'sticky',
                    left: 0,
                    background: theme.colors.backgroundSecondary,
                    zIndex: 1
                  }}>
                    Hole
                  </th>
                  {players.map(player => (
                    <th key={player.id} style={{
                      padding: '12px 8px',
                      textAlign: 'center',
                      fontWeight: 'bold',
                      borderBottom: `3px solid ${theme.colors.border}`
                    }}>
                      {player.name}
                    </th>
                  ))}
                  <th style={{
                    padding: '12px 8px',
                    textAlign: 'center',
                    fontWeight: 'bold',
                    borderBottom: `3px solid ${theme.colors.border}`
                  }}>
                    Wager
                  </th>
                  <th style={{
                    padding: '12px 8px',
                    textAlign: 'center',
                    fontWeight: 'bold',
                    borderBottom: `3px solid ${theme.colors.border}`
                  }}>
                    Winner
                  </th>
                  <th style={{
                    padding: '12px 8px',
                    textAlign: 'center',
                    fontWeight: 'bold',
                    borderBottom: `3px solid ${theme.colors.border}`
                  }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {holeHistory.map((hole, holeIndex) => (
                  <tr key={holeIndex} style={{
                    background: holeIndex % 2 === 0 ? 'white' : theme.colors.background,
                    borderBottom: `1px solid ${theme.colors.border}`
                  }}>
                    <td style={{
                      padding: '12px 8px',
                      fontWeight: 'bold',
                      position: 'sticky',
                      left: 0,
                      background: holeIndex % 2 === 0 ? 'white' : theme.colors.background,
                      borderRight: `2px solid ${theme.colors.border}`
                    }}>
                      {hole.hole}
                    </td>
                    {players.map(player => {
                      const playerScore = hole.gross_scores?.[player.id];
                      const isWinner = (
                        (hole.winner === 'team1' && hole.teams?.team1?.includes(player.id)) ||
                        (hole.winner === 'team2' && hole.teams?.team2?.includes(player.id)) ||
                        (hole.winner === 'captain' && hole.teams?.captain === player.id) ||
                        (hole.winner === 'opponents' && hole.teams?.opponents?.includes(player.id))
                      );

                      return (
                        <td key={player.id} style={{
                          padding: '12px 8px',
                          textAlign: 'center',
                          fontWeight: isWinner ? 'bold' : 'normal',
                          background: isWinner ? 'rgba(76, 175, 80, 0.15)' : 'transparent',
                          color: isWinner ? '#4CAF50' : theme.colors.textPrimary
                        }}>
                          {playerScore !== undefined ? playerScore : '-'}
                          {isWinner && ' ✓'}
                        </td>
                      );
                    })}
                    <td style={{
                      padding: '12px 8px',
                      textAlign: 'center',
                      fontWeight: 'bold',
                      color: theme.colors.primary
                    }}>
                      ${hole.wager?.toFixed(2) || '0.00'}
                    </td>
                    <td style={{
                      padding: '12px 8px',
                      textAlign: 'center',
                      fontSize: '12px',
                      color: theme.colors.textSecondary
                    }}>
                      {hole.winner === 'push' ? 'Push' :
                       hole.winner === 'team1' ? 'Team 1' :
                       hole.winner === 'team2' ? 'Team 2' :
                       hole.winner === 'captain' ? 'Captain' :
                       hole.winner === 'opponents' ? 'Opponents' :
                       hole.winner}
                    </td>
                    <td style={{
                      padding: '12px 8px',
                      textAlign: 'center'
                    }}>
                      <button
                        onClick={() => loadHoleForEdit(hole)}
                        className="touch-optimized"
                        style={{
                          padding: '6px 12px',
                          fontSize: '12px',
                          border: `1px solid ${theme.colors.primary}`,
                          borderRadius: '6px',
                          background: 'white',
                          color: theme.colors.primary,
                          cursor: 'pointer',
                          transition: 'all 0.2s'
                        }}
                      >
                        ✏️ Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleScorekeeper;
