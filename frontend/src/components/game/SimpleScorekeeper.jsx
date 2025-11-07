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
const SimpleScorekeeper = ({
  gameId,
  players,
  baseWager = 1,
  initialHoleHistory = [],
  initialCurrentHole = 1
}) => {
  const theme = useTheme();

  // Current hole state (all client-side until submit)
  const [currentHole, setCurrentHole] = useState(initialCurrentHole);
  const [teamMode, setTeamMode] = useState('partners'); // 'partners' or 'solo'
  const [team1, setTeam1] = useState([]);
  const [team2, setTeam2] = useState([]);
  const [captain, setCaptain] = useState(null);
  const [opponents, setOpponents] = useState([]);
  const [currentWager, setCurrentWager] = useState(baseWager);
  const [scores, setScores] = useState({});
  const [winner, setWinner] = useState(null);
  const [holePar, setHolePar] = useState(4);
  const [floatInvokedBy, setFloatInvokedBy] = useState(null); // Player ID who invoked float
  const [optionInvokedBy, setOptionInvokedBy] = useState(null); // Player ID who triggered option

  // Rotation tracking (Phase 1)
  const [rotationOrder, setRotationOrder] = useState(players.map(p => p.id));
  const [captainIndex, setCaptainIndex] = useState(0);
  const [isHoepfinger, setIsHoepfinger] = useState(false);
  const [goatId, setGoatId] = useState(null);
  const [phase, setPhase] = useState('normal');
  const [joesSpecialWager, setJoesSpecialWager] = useState(null);
  const [nextHoleWager, setNextHoleWager] = useState(baseWager);
  const [carryOver, setCarryOver] = useState(false);
  const [vinniesVariation, setVinniesVariation] = useState(false);
  const [carryOverApplied, setCarryOverApplied] = useState(false);

  // Game history and standings
  const [holeHistory, setHoleHistory] = useState(initialHoleHistory);
  const [playerStandings, setPlayerStandings] = useState({});

  // UI state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [editingHole, setEditingHole] = useState(null); // Track which hole is being edited

  // Initialize player standings from hole history
  useEffect(() => {
    const standings = {};
    players.forEach(player => {
      standings[player.id] = {
        quarters: 0,
        name: player.name,
        soloCount: 0,
        floatCount: 0,
        optionCount: 0
      };
    });

    // Recalculate quarters and usage stats from hole history
    holeHistory.forEach(hole => {
      // Track quarters
      if (hole.points_delta) {
        Object.entries(hole.points_delta).forEach(([playerId, points]) => {
          if (standings[playerId]) {
            standings[playerId].quarters += points;
          }
        });
      }

      // Track solo usage
      if (hole.teams?.type === 'solo' && hole.teams?.captain) {
        if (standings[hole.teams.captain]) {
          standings[hole.teams.captain].soloCount += 1;
        }
      }

      // Track float usage
      if (hole.float_invoked_by && standings[hole.float_invoked_by]) {
        standings[hole.float_invoked_by].floatCount += 1;
      }

      // Track option usage
      if (hole.option_invoked_by && standings[hole.option_invoked_by]) {
        standings[hole.option_invoked_by].optionCount += 1;
      }
    });

    setPlayerStandings(standings);
  }, [players, holeHistory]);

  // Fetch rotation and wager info when hole changes
  useEffect(() => {
    const fetchRotationAndWager = async () => {
      try {
        // Fetch next rotation
        const rotationRes = await fetch(`${API_URL}/games/${gameId}/next-rotation`);
        if (rotationRes.ok) {
          const rotationData = await rotationRes.json();

          if (rotationData.is_hoepfinger) {
            setIsHoepfinger(true);
            setGoatId(rotationData.goat_id);
            setPhase('hoepfinger');
            // Don't set rotation yet - Goat will select position
          } else {
            setIsHoepfinger(false);
            setRotationOrder(rotationData.rotation_order);
            setCaptainIndex(rotationData.captain_index);
            setPhase('normal');
            setGoatId(null);
            setJoesSpecialWager(null);
          }
        }

        // Fetch next hole wager
        const wagerRes = await fetch(`${API_URL}/games/${gameId}/next-hole-wager`);
        if (wagerRes.ok) {
          const wagerData = await wagerRes.json();
          setNextHoleWager(wagerData.base_wager);
          setCurrentWager(wagerData.base_wager);
          setCarryOver(wagerData.carry_over || false);
          setVinniesVariation(wagerData.vinnies_variation || false);
        }
      } catch (err) {
        console.error('Error fetching rotation/wager:', err);
      }
    };

    if (gameId) {
      fetchRotationAndWager();
    }
  }, [gameId, currentHole, holeHistory]);

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
    setFloatInvokedBy(null);
    setOptionInvokedBy(null);
    setError(null);
    setEditingHole(null);
    setCarryOverApplied(carryOver); // Set to true if carry-over was active
    setJoesSpecialWager(null); // Reset Joe's Special for next hole
  };

  // Load hole data for editing
  const loadHoleForEdit = (hole) => {
    setEditingHole(hole.hole);
    setCurrentHole(hole.hole);
    setHolePar(hole.hole_par || 4);
    setScores(hole.gross_scores || {});
    setCurrentWager(hole.wager || baseWager);
    setWinner(hole.winner);
    setFloatInvokedBy(hole.float_invoked_by || null);
    setOptionInvokedBy(hole.option_invoked_by || null);

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
  // First 2 clicks are teammates (team1), next clicks are team2
  const togglePlayerTeam = (playerId) => {
    if (team1.includes(playerId)) {
      setTeam1(team1.filter(id => id !== playerId));
    } else if (team2.includes(playerId)) {
      setTeam2(team2.filter(id => id !== playerId));
    } else {
      // First 2 players go to team1, rest go to team2
      const totalSelected = team1.length + team2.length;
      if (totalSelected < 2) {
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
          rotation_order: rotationOrder,
          captain_index: captainIndex,
          phase: phase,
          joes_special_wager: joesSpecialWager,
          teams: teams,
          final_wager: currentWager,
          winner: winner,
          scores: scores,
          hole_par: holePar,
          float_invoked_by: floatInvokedBy,
          option_invoked_by: optionInvokedBy,
          carry_over_applied: carryOverApplied
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

      {/* Golf-Style Scorecard at Top */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '12px',
        marginBottom: '20px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        overflowX: 'auto',
        position: 'sticky',
        top: '0',
        zIndex: 10
      }}>
          <h3 style={{ margin: '0 0 12px', fontSize: '18px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
            📊 SCORECARD
          </h3>

          <div style={{ overflowX: 'auto' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '13px',
              minWidth: '600px'
            }}>
              <thead>
                <tr style={{ background: theme.colors.backgroundSecondary }}>
                  <th style={{
                    padding: '8px 6px',
                    textAlign: 'left',
                    fontWeight: 'bold',
                    borderBottom: `2px solid ${theme.colors.border}`,
                    position: 'sticky',
                    left: 0,
                    background: theme.colors.backgroundSecondary,
                    zIndex: 2
                  }}>
                    HOLE
                  </th>
                  {[...Array(9)].map((_, i) => (
                    <th key={i} style={{
                      padding: '8px 4px',
                      textAlign: 'center',
                      fontWeight: 'bold',
                      borderBottom: `2px solid ${theme.colors.border}`,
                      background: theme.colors.backgroundSecondary
                    }}>
                      {i + 1}
                    </th>
                  ))}
                  <th style={{
                    padding: '8px 6px',
                    textAlign: 'center',
                    fontWeight: 'bold',
                    borderBottom: `2px solid ${theme.colors.border}`,
                    borderLeft: `2px solid ${theme.colors.border}`,
                    background: 'rgba(76, 175, 80, 0.1)'
                  }}>
                    OUT
                  </th>
                  {[...Array(9)].map((_, i) => (
                    <th key={i + 9} style={{
                      padding: '8px 4px',
                      textAlign: 'center',
                      fontWeight: 'bold',
                      borderBottom: `2px solid ${theme.colors.border}`,
                      background: theme.colors.backgroundSecondary
                    }}>
                      {i + 10}
                    </th>
                  ))}
                  <th style={{
                    padding: '8px 6px',
                    textAlign: 'center',
                    fontWeight: 'bold',
                    borderBottom: `2px solid ${theme.colors.border}`,
                    borderLeft: `2px solid ${theme.colors.border}`,
                    background: 'rgba(76, 175, 80, 0.1)'
                  }}>
                    IN
                  </th>
                  <th style={{
                    padding: '8px 6px',
                    textAlign: 'center',
                    fontWeight: 'bold',
                    borderBottom: `2px solid ${theme.colors.border}`,
                    borderLeft: `2px solid ${theme.colors.border}`,
                    background: 'rgba(33, 150, 243, 0.1)'
                  }}>
                    TOT
                  </th>
                </tr>
              </thead>
              <tbody>
                {/* Par Row */}
                <tr style={{ background: 'rgba(255, 193, 7, 0.1)', borderBottom: `2px solid ${theme.colors.border}` }}>
                  <td style={{
                    padding: '6px',
                    fontWeight: 'bold',
                    fontSize: '11px',
                    position: 'sticky',
                    left: 0,
                    background: 'rgba(255, 193, 7, 0.1)',
                    borderRight: `2px solid ${theme.colors.border}`,
                    zIndex: 1
                  }}>
                    PAR
                  </td>
                  {[...Array(18)].map((_, i) => {
                    const hole = holeHistory.find(h => h.hole === (i + 1));
                    const par = hole?.hole_par || (i + 1 <= 9 ? 4 : 4); // Default to 4 if not available
                    const showDivider = i === 8; // After hole 9
                    return (
                      <td key={i} style={{
                        padding: '6px 4px',
                        textAlign: 'center',
                        fontSize: '11px',
                        fontWeight: 'bold',
                        borderLeft: showDivider ? `2px solid ${theme.colors.border}` : 'none'
                      }}>
                        {par}
                      </td>
                    );
                  })}
                  <td style={{ padding: '6px', textAlign: 'center', fontSize: '11px', fontWeight: 'bold', borderLeft: `2px solid ${theme.colors.border}`, background: 'rgba(76, 175, 80, 0.05)' }}>36</td>
                  <td style={{ padding: '6px', textAlign: 'center', fontSize: '11px', fontWeight: 'bold', borderLeft: `2px solid ${theme.colors.border}`, background: 'rgba(76, 175, 80, 0.05)' }}>36</td>
                  <td style={{ padding: '6px', textAlign: 'center', fontSize: '11px', fontWeight: 'bold', borderLeft: `2px solid ${theme.colors.border}`, background: 'rgba(33, 150, 243, 0.05)' }}>72</td>
                </tr>

                {players.map((player, playerIdx) => {
                  // Calculate stroke totals
                  let outStroke = 0, inStroke = 0;
                  let outQuarters = 0, inQuarters = 0;

                  holeHistory.forEach(hole => {
                    const score = hole.gross_scores?.[player.id] || 0;
                    const quarters = hole.points_delta?.[player.id] || 0;
                    if (hole.hole <= 9) {
                      outStroke += score;
                      outQuarters += quarters;
                    } else {
                      inStroke += score;
                      inQuarters += quarters;
                    }
                  });

                  return (
                    <React.Fragment key={player.id}>
                      {/* Stroke Row */}
                      <tr style={{
                        background: playerIdx % 2 === 0 ? 'white' : theme.colors.background,
                        borderTop: playerIdx === 0 ? `2px solid ${theme.colors.border}` : 'none'
                      }}>
                        <td style={{
                          padding: '8px 6px',
                          fontWeight: 'bold',
                          position: 'sticky',
                          left: 0,
                          background: playerIdx % 2 === 0 ? 'white' : theme.colors.background,
                          borderRight: `2px solid ${theme.colors.border}`,
                          fontSize: '12px',
                          maxWidth: '80px',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          zIndex: 1
                        }}>
                          {player.name}
                        </td>
                        {/* Front 9 Strokes */}
                        {[...Array(9)].map((_, i) => {
                          const hole = holeHistory.find(h => h.hole === (i + 1));
                          const score = hole?.gross_scores?.[player.id];
                          const par = hole?.hole_par || 4;
                          const diff = score ? score - par : null;

                          // Determine indicator style based on score relative to par
                          let indicatorStyle = {};
                          if (diff === -1) {
                            // Birdie - Circle
                            indicatorStyle = {
                              display: 'inline-block',
                              width: '24px',
                              height: '24px',
                              lineHeight: '20px',
                              borderRadius: '50%',
                              border: '2px solid #4CAF50'
                            };
                          } else if (diff === 1) {
                            // Bogey - Square
                            indicatorStyle = {
                              display: 'inline-block',
                              width: '24px',
                              height: '24px',
                              lineHeight: '20px',
                              border: '2px solid #f44336'
                            };
                          } else if (diff >= 2) {
                            // Double bogey or worse - Double square (thicker border)
                            indicatorStyle = {
                              display: 'inline-block',
                              width: '24px',
                              height: '24px',
                              lineHeight: '20px',
                              border: '3px double #f44336'
                            };
                          }

                          return (
                            <td key={i} style={{
                              padding: '8px 4px',
                              textAlign: 'center',
                              fontWeight: score ? 'bold' : 'normal',
                              color: score ? theme.colors.textPrimary : theme.colors.textSecondary
                            }}>
                              {score ? (
                                diff !== null && diff !== 0 ? (
                                  <span style={indicatorStyle}>{score}</span>
                                ) : score
                              ) : '-'}
                            </td>
                          );
                        })}
                        <td style={{
                          padding: '8px 6px',
                          textAlign: 'center',
                          fontWeight: 'bold',
                          borderLeft: `2px solid ${theme.colors.border}`,
                          background: 'rgba(76, 175, 80, 0.05)'
                        }}>
                          {outStroke || '-'}
                        </td>
                        {/* Back 9 Strokes */}
                        {[...Array(9)].map((_, i) => {
                          const hole = holeHistory.find(h => h.hole === (i + 10));
                          const score = hole?.gross_scores?.[player.id];
                          const par = hole?.hole_par || 4;
                          const diff = score ? score - par : null;

                          // Determine indicator style based on score relative to par
                          let indicatorStyle = {};
                          if (diff === -1) {
                            // Birdie - Circle
                            indicatorStyle = {
                              display: 'inline-block',
                              width: '24px',
                              height: '24px',
                              lineHeight: '20px',
                              borderRadius: '50%',
                              border: '2px solid #4CAF50'
                            };
                          } else if (diff === 1) {
                            // Bogey - Square
                            indicatorStyle = {
                              display: 'inline-block',
                              width: '24px',
                              height: '24px',
                              lineHeight: '20px',
                              border: '2px solid #f44336'
                            };
                          } else if (diff >= 2) {
                            // Double bogey or worse - Double square (thicker border)
                            indicatorStyle = {
                              display: 'inline-block',
                              width: '24px',
                              height: '24px',
                              lineHeight: '20px',
                              border: '3px double #f44336'
                            };
                          }

                          return (
                            <td key={i + 9} style={{
                              padding: '8px 4px',
                              textAlign: 'center',
                              fontWeight: score ? 'bold' : 'normal',
                              color: score ? theme.colors.textPrimary : theme.colors.textSecondary
                            }}>
                              {score ? (
                                diff !== null && diff !== 0 ? (
                                  <span style={indicatorStyle}>{score}</span>
                                ) : score
                              ) : '-'}
                            </td>
                          );
                        })}
                        <td style={{
                          padding: '8px 6px',
                          textAlign: 'center',
                          fontWeight: 'bold',
                          borderLeft: `2px solid ${theme.colors.border}`,
                          background: 'rgba(76, 175, 80, 0.05)'
                        }}>
                          {inStroke || '-'}
                        </td>
                        <td style={{
                          padding: '8px 6px',
                          textAlign: 'center',
                          fontWeight: 'bold',
                          fontSize: '14px',
                          borderLeft: `2px solid ${theme.colors.border}`,
                          background: 'rgba(33, 150, 243, 0.05)'
                        }}>
                          {(outStroke + inStroke) || '-'}
                        </td>
                      </tr>

                      {/* Quarters Row */}
                      <tr style={{
                        background: playerIdx % 2 === 0 ? 'white' : theme.colors.background,
                        borderBottom: `1px solid ${theme.colors.border}`
                      }}>
                        <td style={{
                          padding: '6px',
                          fontSize: '11px',
                          fontStyle: 'italic',
                          color: theme.colors.textSecondary,
                          position: 'sticky',
                          left: 0,
                          background: playerIdx % 2 === 0 ? 'white' : theme.colors.background,
                          borderRight: `2px solid ${theme.colors.border}`,
                          zIndex: 1
                        }}>
                          Quarters
                        </td>
                        {/* Front 9 Quarters */}
                        {[...Array(9)].map((_, i) => {
                          const hole = holeHistory.find(h => h.hole === (i + 1));
                          const quarters = hole?.points_delta?.[player.id];
                          const hasValue = quarters !== undefined && quarters !== null;

                          // Check for special actions
                          const wasSolo = hole?.teams?.type === 'solo' && hole?.teams?.captain === player.id;
                          const usedFloat = hole?.float_invoked_by === player.id;
                          const usedOption = hole?.option_invoked_by === player.id;

                          return (
                            <td key={i} style={{
                              padding: '6px 4px',
                              textAlign: 'center',
                              fontSize: '11px',
                              fontWeight: hasValue ? 'bold' : 'normal',
                              color: hasValue ? (quarters > 0 ? '#4CAF50' : quarters < 0 ? '#f44336' : theme.colors.textSecondary) : theme.colors.textSecondary,
                              position: 'relative'
                            }}>
                              <div>
                                {hasValue ? (quarters > 0 ? `+${quarters}` : quarters) : '·'}
                              </div>
                              {(wasSolo || usedFloat || usedOption) && (
                                <div style={{
                                  display: 'flex',
                                  gap: '2px',
                                  justifyContent: 'center',
                                  marginTop: '2px',
                                  fontSize: '9px'
                                }}>
                                  {wasSolo && (
                                    <span style={{
                                      background: theme.colors.primary,
                                      color: 'white',
                                      padding: '1px 3px',
                                      borderRadius: '3px',
                                      fontWeight: 'bold'
                                    }}>S</span>
                                  )}
                                  {usedFloat && (
                                    <span style={{
                                      background: '#2196F3',
                                      color: 'white',
                                      padding: '1px 3px',
                                      borderRadius: '3px',
                                      fontWeight: 'bold'
                                    }}>F</span>
                                  )}
                                  {usedOption && (
                                    <span style={{
                                      background: theme.colors.warning,
                                      color: 'white',
                                      padding: '1px 3px',
                                      borderRadius: '3px',
                                      fontWeight: 'bold'
                                    }}>O</span>
                                  )}
                                </div>
                              )}
                            </td>
                          );
                        })}
                        <td style={{
                          padding: '6px',
                          textAlign: 'center',
                          fontSize: '11px',
                          fontWeight: 'bold',
                          borderLeft: `2px solid ${theme.colors.border}`,
                          background: 'rgba(76, 175, 80, 0.05)',
                          color: outQuarters > 0 ? '#4CAF50' : outQuarters < 0 ? '#f44336' : theme.colors.textSecondary
                        }}>
                          {outQuarters !== 0 ? (outQuarters > 0 ? `+${outQuarters}` : outQuarters) : '-'}
                        </td>
                        {/* Back 9 Quarters */}
                        {[...Array(9)].map((_, i) => {
                          const hole = holeHistory.find(h => h.hole === (i + 10));
                          const quarters = hole?.points_delta?.[player.id];
                          const hasValue = quarters !== undefined && quarters !== null;

                          // Check for special actions
                          const wasSolo = hole?.teams?.type === 'solo' && hole?.teams?.captain === player.id;
                          const usedFloat = hole?.float_invoked_by === player.id;
                          const usedOption = hole?.option_invoked_by === player.id;

                          return (
                            <td key={i + 9} style={{
                              padding: '6px 4px',
                              textAlign: 'center',
                              fontSize: '11px',
                              fontWeight: hasValue ? 'bold' : 'normal',
                              color: hasValue ? (quarters > 0 ? '#4CAF50' : quarters < 0 ? '#f44336' : theme.colors.textSecondary) : theme.colors.textSecondary,
                              position: 'relative'
                            }}>
                              <div>
                                {hasValue ? (quarters > 0 ? `+${quarters}` : quarters) : '·'}
                              </div>
                              {(wasSolo || usedFloat || usedOption) && (
                                <div style={{
                                  display: 'flex',
                                  gap: '2px',
                                  justifyContent: 'center',
                                  marginTop: '2px',
                                  fontSize: '9px'
                                }}>
                                  {wasSolo && (
                                    <span style={{
                                      background: theme.colors.primary,
                                      color: 'white',
                                      padding: '1px 3px',
                                      borderRadius: '3px',
                                      fontWeight: 'bold'
                                    }}>S</span>
                                  )}
                                  {usedFloat && (
                                    <span style={{
                                      background: '#2196F3',
                                      color: 'white',
                                      padding: '1px 3px',
                                      borderRadius: '3px',
                                      fontWeight: 'bold'
                                    }}>F</span>
                                  )}
                                  {usedOption && (
                                    <span style={{
                                      background: theme.colors.warning,
                                      color: 'white',
                                      padding: '1px 3px',
                                      borderRadius: '3px',
                                      fontWeight: 'bold'
                                    }}>O</span>
                                  )}
                                </div>
                              )}
                            </td>
                          );
                        })}
                        <td style={{
                          padding: '6px',
                          textAlign: 'center',
                          fontSize: '11px',
                          fontWeight: 'bold',
                          borderLeft: `2px solid ${theme.colors.border}`,
                          background: 'rgba(76, 175, 80, 0.05)',
                          color: inQuarters > 0 ? '#4CAF50' : inQuarters < 0 ? '#f44336' : theme.colors.textSecondary
                        }}>
                          {inQuarters !== 0 ? (inQuarters > 0 ? `+${inQuarters}` : inQuarters) : '-'}
                        </td>
                        <td style={{
                          padding: '6px',
                          textAlign: 'center',
                          fontSize: '12px',
                          fontWeight: 'bold',
                          borderLeft: `2px solid ${theme.colors.border}`,
                          background: 'rgba(33, 150, 243, 0.05)',
                          color: (outQuarters + inQuarters) > 0 ? '#4CAF50' : (outQuarters + inQuarters) < 0 ? '#f44336' : theme.colors.textSecondary
                        }}>
                          {(outQuarters + inQuarters) !== 0 ? ((outQuarters + inQuarters) > 0 ? `+${outQuarters + inQuarters}` : (outQuarters + inQuarters)) : '-'}
                        </td>
                      </tr>
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Quick Actions for Last Hole */}
          {holeHistory.length > 0 && (
            <div style={{
              marginTop: '12px',
              paddingTop: '12px',
              borderTop: `1px solid ${theme.colors.border}`,
              fontSize: '12px',
              color: theme.colors.textSecondary
            }}>
              <button
                onClick={() => loadHoleForEdit(holeHistory[holeHistory.length - 1])}
                className="touch-optimized"
                style={{
                  padding: '6px 12px',
                  fontSize: '12px',
                  border: `1px solid ${theme.colors.primary}`,
                  borderRadius: '6px',
                  background: 'white',
                  color: theme.colors.primary,
                  cursor: 'pointer'
                }}
              >
                ✏️ Edit Last Hole
              </button>
            </div>
          )}
        </div>

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

      {/* Rotation Order Display */}
      {!isHoepfinger && rotationOrder.length > 0 && (
        <div style={{
          background: theme.colors.paper,
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '16px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            fontSize: '14px',
            fontWeight: 'bold',
            marginBottom: '12px',
            color: theme.colors.textSecondary,
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Hitting Order
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {rotationOrder.map((playerId, index) => {
              const player = players.find(p => p.id === playerId);
              const isCaptain = index === captainIndex;
              return (
                <div
                  key={playerId}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '8px',
                    background: isCaptain ? '#2196F3' : theme.colors.backgroundSecondary,
                    color: isCaptain ? 'white' : theme.colors.textPrimary,
                    fontWeight: isCaptain ? 'bold' : 'normal',
                    fontSize: '14px',
                    border: isCaptain ? '2px solid #1976D2' : 'none'
                  }}
                >
                  {index + 1}. {player?.name || playerId}
                  {isCaptain && ' 👑'}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Hoepfinger Phase UI */}
      {isHoepfinger && goatId && (
        <div style={{
          background: '#FFF8E1',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '16px',
          border: '2px solid #FFD54F',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            fontSize: '16px',
            fontWeight: 'bold',
            marginBottom: '12px',
            color: '#F57C00',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            🎯 HOEPFINGER PHASE
          </div>
          <div style={{ marginBottom: '12px', color: '#5D4037' }}>
            <strong>{players.find(p => p.id === goatId)?.name}</strong> (Goat) selects hitting position
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
            {players.map((player, index) => (
              <button
                key={index}
                onClick={() => {
                  // Goat selects their position
                  const newRotation = [...players.map(p => p.id)];
                  // Move goat to selected position
                  const goatIndex = newRotation.indexOf(goatId);
                  const temp = newRotation[goatIndex];
                  newRotation[goatIndex] = newRotation[index];
                  newRotation[index] = temp;
                  setRotationOrder(newRotation);
                  setCaptainIndex(0); // First player hits first
                }}
                style={{
                  padding: '12px 20px',
                  borderRadius: '8px',
                  background: theme.colors.primary,
                  color: 'white',
                  border: 'none',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                Position {index + 1}
              </button>
            ))}
          </div>

          {/* Joe's Special Wager Selector */}
          <div style={{
            marginTop: '16px',
            paddingTop: '16px',
            borderTop: '1px solid #FFD54F'
          }}>
            <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '8px', color: '#5D4037' }}>
              Joe's Special - Set Wager:
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              {[2, 4, 8].map(wager => (
                <button
                  key={wager}
                  onClick={() => {
                    setJoesSpecialWager(wager);
                    setCurrentWager(wager);
                  }}
                  style={{
                    padding: '12px 24px',
                    borderRadius: '8px',
                    background: joesSpecialWager === wager ? '#4CAF50' : theme.colors.backgroundSecondary,
                    color: joesSpecialWager === wager ? 'white' : theme.colors.textPrimary,
                    border: joesSpecialWager === wager ? '2px solid #388E3C' : 'none',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    cursor: 'pointer'
                  }}
                >
                  {wager}Q
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Wager Indicators */}
      {(carryOver || vinniesVariation) && (
        <div style={{
          background: theme.colors.paper,
          borderRadius: '12px',
          padding: '12px 16px',
          marginBottom: '16px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          display: 'flex',
          gap: '12px',
          alignItems: 'center'
        }}>
          {carryOver && (
            <div style={{
              padding: '6px 12px',
              borderRadius: '6px',
              background: '#FF5722',
              color: 'white',
              fontSize: '12px',
              fontWeight: 'bold'
            }}>
              🔄 CARRY-OVER
            </div>
          )}
          {vinniesVariation && (
            <div style={{
              padding: '6px 12px',
              borderRadius: '6px',
              background: '#9C27B0',
              color: 'white',
              fontSize: '12px',
              fontWeight: 'bold'
            }}>
              ⚡ VINNIE'S VARIATION
            </div>
          )}
          <div style={{ fontSize: '14px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
            Base Wager: {nextHoleWager}Q
          </div>
        </div>
      )}

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
                {player.quarters > 0 ? '+' : ''}{player.quarters}Q
              </div>
            </div>
          );
        })}
      </div>

      {/* Usage Statistics */}
      {holeHistory.length > 0 && (
        <div style={{
          background: theme.colors.paper,
          borderRadius: '16px',
          overflow: 'hidden',
          marginBottom: '20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <div style={{
            padding: '16px 20px',
            background: theme.colors.backgroundSecondary,
            borderBottom: `3px solid ${theme.colors.border}`,
            fontSize: '18px',
            fontWeight: 'bold',
            color: theme.colors.textPrimary
          }}>
            Rule Compliance & Usage
          </div>

          <div style={{ padding: '16px' }}>
            {Object.values(playerStandings).map((player, idx) => {
              const soloCount = player.soloCount || 0;
              const floatCount = player.floatCount || 0;
              const optionCount = player.optionCount || 0;

              // Rule requirements
              const soloRequired = 1; // Everyone must go solo at least once
              const floatAvailable = 1; // One float per player per round
              const soloMet = soloCount >= soloRequired;
              const floatUsed = floatCount >= floatAvailable;

              return (
                <div
                  key={idx}
                  style={{
                    padding: '12px',
                    borderBottom: idx < Object.values(playerStandings).length - 1 ? `1px solid ${theme.colors.border}` : 'none',
                    background: idx % 2 === 0 ? 'white' : theme.colors.background
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px'
                  }}>
                    <div style={{
                      fontSize: '16px',
                      fontWeight: 'bold',
                      color: theme.colors.textPrimary,
                      flex: 1
                    }}>
                      {player.name}
                    </div>
                    <div style={{
                      display: 'flex',
                      gap: '16px',
                      fontSize: '14px',
                      color: theme.colors.textSecondary
                    }}>
                      {/* Solo Count */}
                      <div style={{ textAlign: 'center' }}>
                        <div style={{
                          fontSize: '20px',
                          fontWeight: 'bold',
                          color: soloMet ? '#4CAF50' : '#f44336'
                        }}>
                          {soloCount}/{soloRequired}
                        </div>
                        <div style={{ fontSize: '11px' }}>Solo</div>
                        {!soloMet && (
                          <div style={{
                            fontSize: '9px',
                            color: '#f44336',
                            fontWeight: 'bold',
                            marginTop: '2px'
                          }}>
                            Required
                          </div>
                        )}
                      </div>

                      {/* Float Count */}
                      <div style={{ textAlign: 'center' }}>
                        <div style={{
                          fontSize: '20px',
                          fontWeight: 'bold',
                          color: floatUsed ? '#9E9E9E' : theme.colors.primary
                        }}>
                          {floatCount}/{floatAvailable}
                        </div>
                        <div style={{ fontSize: '11px' }}>Float</div>
                        {floatUsed && (
                          <div style={{
                            fontSize: '9px',
                            color: '#9E9E9E',
                            marginTop: '2px'
                          }}>
                            Used
                          </div>
                        )}
                      </div>

                      {/* Option Count (informational) */}
                      <div style={{ textAlign: 'center' }}>
                        <div style={{
                          fontSize: '20px',
                          fontWeight: 'bold',
                          color: theme.colors.warning
                        }}>
                          {optionCount}
                        </div>
                        <div style={{ fontSize: '11px' }}>Option</div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Rule Summary */}
          <div style={{
            padding: '12px 16px',
            background: '#f9fafb',
            borderTop: `1px solid ${theme.colors.border}`,
            fontSize: '11px',
            color: theme.colors.textSecondary
          }}>
            <div style={{ marginBottom: '4px' }}>
              <strong>Rules:</strong>
            </div>
            <div>• Solo: Each player must go solo at least once (by hole 16)</div>
            <div>• Float: One-time use per player per round</div>
            <div>• Option: Auto-triggered when captain is furthest down (Goat)</div>
          </div>
        </div>
      )}

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
            {currentWager}Q
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
              <button
                onClick={() => setWinner('team1_flush')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '12px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  border: winner === 'team1_flush' ? `3px solid #e91e63` : `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  background: winner === 'team1_flush' ? 'rgba(233, 30, 99, 0.2)' : 'white',
                  cursor: 'pointer'
                }}
              >
                Team 1 Flush
              </button>
              <button
                onClick={() => setWinner('team2_flush')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '12px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  border: winner === 'team2_flush' ? `3px solid #e91e63` : `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  background: winner === 'team2_flush' ? 'rgba(233, 30, 99, 0.2)' : 'white',
                  cursor: 'pointer'
                }}
              >
                Team 2 Flush
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
              <button
                onClick={() => setWinner('captain_flush')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '12px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  border: winner === 'captain_flush' ? `3px solid #e91e63` : `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  background: winner === 'captain_flush' ? 'rgba(233, 30, 99, 0.2)' : 'white',
                  cursor: 'pointer'
                }}
              >
                Captain Flush
              </button>
              <button
                onClick={() => setWinner('opponents_flush')}
                style={{
                  flex: 1,
                  minWidth: '120px',
                  padding: '12px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  border: winner === 'opponents_flush' ? `3px solid #e91e63` : `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  background: winner === 'opponents_flush' ? 'rgba(233, 30, 99, 0.2)' : 'white',
                  cursor: 'pointer'
                }}
              >
                Opponents Flush
              </button>
            </>
          )}
        </div>
      </div>

      {/* Float & Option Tracking */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 12px' }}>Special Actions (Optional)</h3>

        {/* Float Selection */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '8px' }}>
            Float Invoked By: <span style={{ fontSize: '12px', fontWeight: 'normal', color: theme.colors.textSecondary }}>(one-time use per player)</span>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {players.map(player => {
              const hasUsedFloat = playerStandings[player.id]?.floatCount >= 1;
              return (
                <button
                  key={player.id}
                  onClick={() => setFloatInvokedBy(floatInvokedBy === player.id ? null : player.id)}
                  className="touch-optimized"
                  disabled={hasUsedFloat}
                  style={{
                    padding: '8px 16px',
                    fontSize: '14px',
                    border: `2px solid ${floatInvokedBy === player.id ? theme.colors.primary : hasUsedFloat ? '#ccc' : theme.colors.border}`,
                    borderRadius: '6px',
                    background: floatInvokedBy === player.id ? theme.colors.primary : hasUsedFloat ? '#f5f5f5' : 'white',
                    color: floatInvokedBy === player.id ? 'white' : hasUsedFloat ? '#999' : theme.colors.text,
                    cursor: hasUsedFloat ? 'not-allowed' : 'pointer',
                    opacity: hasUsedFloat ? 0.6 : 1,
                    position: 'relative'
                  }}
                  title={hasUsedFloat ? `${player.name} has already used their float` : ''}
                >
                  {player.name}
                  {hasUsedFloat && (
                    <span style={{
                      fontSize: '10px',
                      marginLeft: '4px',
                      color: '#666'
                    }}>✓</span>
                  )}
                </button>
              );
            })}
            <button
              onClick={() => setFloatInvokedBy(null)}
              className="touch-optimized"
              style={{
                padding: '8px 16px',
                fontSize: '14px',
                border: `2px solid ${theme.colors.border}`,
                borderRadius: '6px',
                background: 'white',
                color: theme.colors.textSecondary,
                cursor: 'pointer'
              }}
            >
              None
            </button>
          </div>
        </div>

        {/* Option Selection */}
        <div>
          <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '8px' }}>
            Option Triggered For:
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {players.map(player => (
              <button
                key={player.id}
                onClick={() => setOptionInvokedBy(optionInvokedBy === player.id ? null : player.id)}
                className="touch-optimized"
                style={{
                  padding: '8px 16px',
                  fontSize: '14px',
                  border: `2px solid ${optionInvokedBy === player.id ? theme.colors.warning : theme.colors.border}`,
                  borderRadius: '6px',
                  background: optionInvokedBy === player.id ? theme.colors.warning : 'white',
                  color: optionInvokedBy === player.id ? 'white' : theme.colors.text,
                  cursor: 'pointer'
                }}
              >
                {player.name}
              </button>
            ))}
            <button
              onClick={() => setOptionInvokedBy(null)}
              className="touch-optimized"
              style={{
                padding: '8px 16px',
                fontSize: '14px',
                border: `2px solid ${theme.colors.border}`,
                borderRadius: '6px',
                background: 'white',
                color: theme.colors.textSecondary,
                cursor: 'pointer'
              }}
            >
              None
            </button>
          </div>
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

      {/* Old scorecard removed - now showing golf-style scorecard at top */}
    </div>
  );
};

export default SimpleScorekeeper;
