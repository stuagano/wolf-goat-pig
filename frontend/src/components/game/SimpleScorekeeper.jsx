// frontend/src/components/game/SimpleScorekeeper.jsx
import React, { useState, useEffect } from 'react';
import { useTheme } from '../../theme/Provider';
import GameCompletionView from './GameCompletionView';
import { triggerBadgeNotification } from '../BadgeNotification';
import '../../styles/mobile-touch.css';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * Helper component to display player name with authentication indicator
 */
const PlayerName = ({ name, isAuthenticated }) => (
  <>
    {name}
    {isAuthenticated && <span style={{ marginLeft: '4px', fontSize: '12px' }}>🔒</span>}
  </>
);

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
  // eslint-disable-next-line no-unused-vars
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

  // Phase 2: Betting mechanics
  const [optionActive, setOptionActive] = useState(false);
  const [optionTurnedOff, setOptionTurnedOff] = useState(false);
  const [duncanInvoked, setDuncanInvoked] = useState(false);

  // Game history and standings
  const [holeHistory, setHoleHistory] = useState(initialHoleHistory);
  const [playerStandings, setPlayerStandings] = useState({});

  // UI state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [editingHole, setEditingHole] = useState(null); // Track which hole is being edited
  const [editingPlayerName, setEditingPlayerName] = useState(null); // Track which player name is being edited
  const [editPlayerNameValue, setEditPlayerNameValue] = useState(''); // Player name input value
  const [localPlayers, setLocalPlayers] = useState(players); // Local copy of players for immediate UI updates
  const [showUsageStats, setShowUsageStats] = useState(false); // Toggle for usage statistics section
  const [courseData, setCourseData] = useState(null); // Course data with hole information

  // Fetch course data
  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        // Get game state to find course name
        const gameResponse = await fetch(`${API_URL}/games/${gameId}/state`);
        if (gameResponse.ok) {
          const gameData = await gameResponse.json();
          const courseName = gameData.course_name || 'Wing Point Golf & Country Club';

          // Fetch course details
          const courseResponse = await fetch(`${API_URL}/courses`);
          if (courseResponse.ok) {
            const coursesData = await courseResponse.json();
            // /courses returns an object with course names as keys, not an array
            const course = coursesData[courseName];
            if (course) {
              setCourseData(course);
            }
          }
        }
      } catch (err) {
        console.error('Error fetching course data:', err);
      }
    };

    if (gameId) {
      fetchCourseData();
    }
  }, [gameId]);

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
          setOptionActive(wagerData.option_active || false);
          if (wagerData.option_active) {
            setGoatId(wagerData.goat_id);
          }
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
    setOptionTurnedOff(false); // Reset Option for next hole
    setDuncanInvoked(false); // Reset Duncan for next hole
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
  // Toggle players in/out of Team 1. Team 2 is automatically all other players.
  const togglePlayerTeam = (playerId) => {
    if (team1.includes(playerId)) {
      // Remove from team1 (they'll go to team2 automatically)
      setTeam1(team1.filter(id => id !== playerId));
    } else {
      // Add to team1
      setTeam1([...team1, playerId]);
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
      if (team1.length === 0) {
        return 'Please select at least one player for Team 1';
      }
      if (team1.length === players.length) {
        return 'Cannot select all players for Team 1. Select half for Team 1, the rest will automatically be Team 2.';
      }

      // Calculate implicit team2 (players not in team1)
      const implicitTeam2 = players.filter(p => !team1.includes(p.id)).map(p => p.id);

      if (team1.length !== implicitTeam2.length) {
        return `Select exactly ${Math.floor(players.length / 2)} players for Team 1. Currently selected: ${team1.length}`;
      }
    } else {
      if (!captain) {
        return 'Please select a captain';
      }
    }

    // Calculate all players (with implicit team2 for partners mode)
    let allPlayers;
    if (teamMode === 'partners') {
      const implicitTeam2 = players.filter(p => !team1.includes(p.id)).map(p => p.id);
      allPlayers = [...team1, ...implicitTeam2];
    } else {
      allPlayers = [captain, ...opponents];
    }

    // Check all players have scores
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
      // For partners mode, Team 2 is always calculated as players not in Team 1
      const teams = teamMode === 'partners'
        ? {
          type: 'partners',
          team1: team1,
          team2: players.filter(p => !team1.includes(p.id)).map(p => p.id)
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
          option_turned_off: optionTurnedOff,
          duncan_invoked: duncanInvoked,
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

      // Check for achievement unlocks for all players
      await checkAchievements();

    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Check achievements for all players and trigger notifications
  const checkAchievements = async () => {
    try {
      // Check achievements for each player
      for (const player of players) {
        const response = await fetch(`${API_URL}/api/badges/admin/check-achievements/${player.id}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        if (response.ok) {
          const data = await response.json();

          // Trigger badge notification for each newly earned badge
          if (data.badges_earned && data.badges_earned.length > 0) {
            data.badges_earned.forEach(badge => {
              triggerBadgeNotification(badge);
            });
          }
        }
      }
    } catch (err) {
      // Silently fail - achievements are nice-to-have, not critical
      console.warn('Failed to check achievements:', err);
    }
  };

  // Handle player name editing
  const handlePlayerNameClick = (playerId, currentName) => {
    setEditingPlayerName(playerId);
    setEditPlayerNameValue(currentName);
  };

  const handleSavePlayerName = async () => {
    if (!editingPlayerName || !editPlayerNameValue.trim()) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/games/${gameId}/players/${editingPlayerName}/name`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: editPlayerNameValue.trim() })
      });

      if (!response.ok) {
        throw new Error('Failed to update player name');
      }

      // Update local players state immediately for better UX
      const updatedPlayers = localPlayers.map(p =>
        p.id === editingPlayerName ? { ...p, name: editPlayerNameValue.trim() } : p
      );
      setLocalPlayers(updatedPlayers);

      // Also update player standings
      if (playerStandings[editingPlayerName]) {
        setPlayerStandings({
          ...playerStandings,
          [editingPlayerName]: {
            ...playerStandings[editingPlayerName],
            name: editPlayerNameValue.trim()
          }
        });
      }

      // Close the edit modal
      setEditingPlayerName(null);
      setEditPlayerNameValue('');
    } catch (err) {
      console.error('Failed to update player name:', err);
      alert('Failed to update player name. Please try again.');
    }
  };

  const handleCancelPlayerNameEdit = () => {
    setEditingPlayerName(null);
    setEditPlayerNameValue('');
  };

  // Check if game is complete (all 18 holes played)
  const isGameComplete = currentHole > 18 && holeHistory.length === 18;

  // Show completion view if game is complete
  if (isGameComplete) {
    return (
      <GameCompletionView
        players={players}
        playerStandings={playerStandings}
        holeHistory={holeHistory}
        onNewGame={() => {
          // Reset to start a new game
          window.location.reload();
        }}
      />
    );
  }

  return (
    <div data-testid="scorekeeper-container" style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
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
                  const holeNumber = i + 1;
                  const hole = holeHistory.find(h => h.hole === holeNumber);
                  // Try to get par from hole history first, then from course data, then default to 4
                  const par = hole?.hole_par || courseData?.holes?.find(h => h.hole_number === holeNumber)?.par || 4;
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

              {/* Handicap Row */}
              <tr style={{ background: 'rgba(156, 39, 176, 0.1)', borderBottom: `2px solid ${theme.colors.border}` }}>
                <td style={{
                  padding: '6px',
                  fontWeight: 'bold',
                  fontSize: '11px',
                  position: 'sticky',
                  left: 0,
                  background: 'rgba(156, 39, 176, 0.1)',
                  borderRight: `2px solid ${theme.colors.border}`,
                  zIndex: 1
                }}>
                  HDCP
                </td>
                {[...Array(18)].map((_, i) => {
                  const holeNumber = i + 1;
                  const handicap = courseData?.holes?.find(h => h.hole_number === holeNumber)?.stroke_index || holeNumber;
                  const showDivider = i === 8; // After hole 9
                  return (
                    <td key={i} style={{
                      padding: '6px 4px',
                      textAlign: 'center',
                      fontSize: '11px',
                      fontWeight: 'bold',
                      borderLeft: showDivider ? `2px solid ${theme.colors.border}` : 'none'
                    }}>
                      {handicap}
                    </td>
                  );
                })}
                <td style={{ padding: '6px', textAlign: 'center', fontSize: '11px', borderLeft: `2px solid ${theme.colors.border}`, background: 'rgba(76, 175, 80, 0.05)' }}>-</td>
                <td style={{ padding: '6px', textAlign: 'center', fontSize: '11px', borderLeft: `2px solid ${theme.colors.border}`, background: 'rgba(76, 175, 80, 0.05)' }}>-</td>
                <td style={{ padding: '6px', textAlign: 'center', fontSize: '11px', borderLeft: `2px solid ${theme.colors.border}`, background: 'rgba(33, 150, 243, 0.05)' }}>-</td>
              </tr>

              {localPlayers.map((player, playerIdx) => {
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
                      <td
                        style={{
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
                          zIndex: 1,
                          cursor: 'pointer'
                        }}
                        onClick={() => handlePlayerNameClick(player.id, player.name)}
                        title="Click to edit player name"
                      >
                        <PlayerName name={player.name} isAuthenticated={player.is_authenticated} />
                        <span style={{ fontSize: '10px', marginLeft: '4px', opacity: 0.5 }}>✏️</span>
                      </td>
                      {/* Front 9 Strokes */}
                      {[...Array(9)].map((_, i) => {
                        const holeNumber = i + 1;
                        const hole = holeHistory.find(h => h.hole === holeNumber);
                        const score = hole?.gross_scores?.[player.id];
                        const par = hole?.hole_par || 4;
                        const diff = score ? score - par : null;

                        // Calculate strokes player receives on this hole using Creecher Feature
                        const getStrokesForHole = (handicap, strokeIndex) => {
                          if (!handicap || handicap <= 0) return 0;

                          const fullHandicap = Math.floor(handicap);
                          const hasFractional = (handicap % 1) >= 0.5;

                          // Creecher Feature implementation
                          if (handicap <= 6) {
                            // All allocated holes get 0.5
                            return strokeIndex <= fullHandicap ? 0.5 : 0;
                          } else if (handicap <= 18) {
                            // Easiest 6 of allocated holes get 0.5, rest get 1.0
                            if (strokeIndex <= fullHandicap) {
                              const easiestSix = Array.from({ length: fullHandicap }, (_, idx) => fullHandicap - idx);
                              return easiestSix.slice(0, 6).includes(strokeIndex) ? 0.5 : 1.0;
                            }
                            // Fractional: add 0.5 to next hole
                            if (hasFractional && strokeIndex === fullHandicap + 1) {
                              return 0.5;
                            }
                            return 0;
                          } else {
                            // Handicap > 18
                            // Base 18: holes 13-18 get 0.5, holes 1-12 get 1.0
                            const extraStrokes = fullHandicap - 18;
                            const extraHalfStrokes = extraStrokes * 2;

                            if (strokeIndex >= 13 && strokeIndex <= 18) {
                              // Easiest 6 holes get base 0.5
                              // Check if they get extra half from wrap-around
                              const halfsNeeded = extraHalfStrokes;
                              const holesGettingExtra = Math.min(halfsNeeded, 12);
                              if (strokeIndex <= holesGettingExtra) {
                                return 1.0; // 0.5 base + 0.5 extra
                              }
                              return 0.5;
                            } else {
                              // Hardest 12 holes get base 1.0
                              // Check if they get extra half from wrap-around
                              const halfsNeeded = extraHalfStrokes;
                              const holesGettingExtra = Math.min(halfsNeeded, 12);
                              if (strokeIndex <= holesGettingExtra) {
                                return 1.5; // 1.0 base + 0.5 extra
                              }
                              return 1.0;
                            }
                          }
                        };

                        // Get the actual stroke index (handicap) for this hole from course data
                        const holeHandicap = courseData?.holes?.find(h => h.hole_number === holeNumber)?.stroke_index || holeNumber;
                        const strokesReceived = getStrokesForHole(player.handicap || 0, holeHandicap);

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
                            color: score ? theme.colors.textPrimary : theme.colors.textSecondary,
                            position: 'relative'
                          }}>
                            <div>
                              {score ? (
                                diff !== null && diff !== 0 ? (
                                  <span style={indicatorStyle}>{score}</span>
                                ) : score
                              ) : '-'}
                            </div>
                            {/* Stroke indicator for upcoming holes */}
                            {!score && strokesReceived > 0 && (
                              <div style={{
                                fontSize: '9px',
                                color: strokesReceived === 0.5 ? '#FF9800' : strokesReceived === 1.0 ? '#2196F3' : '#9C27B0',
                                fontWeight: 'bold',
                                marginTop: '2px'
                              }}>
                                {strokesReceived === 0.5 ? '½' : strokesReceived === 1.0 ? '1' : strokesReceived === 1.5 ? '1½' : strokesReceived}
                              </div>
                            )}
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
                        const holeNumber = i + 10;
                        const hole = holeHistory.find(h => h.hole === holeNumber);
                        const score = hole?.gross_scores?.[player.id];
                        const par = hole?.hole_par || 4;
                        const diff = score ? score - par : null;

                        // Calculate strokes player receives on this hole using Creecher Feature
                        const getStrokesForHole = (handicap, strokeIndex) => {
                          if (!handicap || handicap <= 0) return 0;

                          const fullHandicap = Math.floor(handicap);
                          const hasFractional = (handicap % 1) >= 0.5;

                          // Creecher Feature implementation
                          if (handicap <= 6) {
                            // All allocated holes get 0.5
                            return strokeIndex <= fullHandicap ? 0.5 : 0;
                          } else if (handicap <= 18) {
                            // Easiest 6 of allocated holes get 0.5, rest get 1.0
                            if (strokeIndex <= fullHandicap) {
                              const easiestSix = Array.from({ length: fullHandicap }, (_, idx) => fullHandicap - idx);
                              return easiestSix.slice(0, 6).includes(strokeIndex) ? 0.5 : 1.0;
                            }
                            // Fractional: add 0.5 to next hole
                            if (hasFractional && strokeIndex === fullHandicap + 1) {
                              return 0.5;
                            }
                            return 0;
                          } else {
                            // Handicap > 18
                            // Base 18: holes 13-18 get 0.5, holes 1-12 get 1.0
                            const extraStrokes = fullHandicap - 18;
                            const extraHalfStrokes = extraStrokes * 2;

                            if (strokeIndex >= 13 && strokeIndex <= 18) {
                              // Easiest 6 holes get base 0.5
                              // Check if they get extra half from wrap-around
                              const halfsNeeded = extraHalfStrokes;
                              const holesGettingExtra = Math.min(halfsNeeded, 12);
                              if (strokeIndex <= holesGettingExtra) {
                                return 1.0; // 0.5 base + 0.5 extra
                              }
                              return 0.5;
                            } else {
                              // Hardest 12 holes get base 1.0
                              // Check if they get extra half from wrap-around
                              const halfsNeeded = extraHalfStrokes;
                              const holesGettingExtra = Math.min(halfsNeeded, 12);
                              if (strokeIndex <= holesGettingExtra) {
                                return 1.5; // 1.0 base + 0.5 extra
                              }
                              return 1.0;
                            }
                          }
                        };

                        // Get the actual stroke index (handicap) for this hole from course data
                        const holeHandicap = courseData?.holes?.find(h => h.hole_number === holeNumber)?.stroke_index || holeNumber;
                        const strokesReceived = getStrokesForHole(player.handicap || 0, holeHandicap);

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
                            color: score ? theme.colors.textPrimary : theme.colors.textSecondary,
                            position: 'relative'
                          }}>
                            <div>
                              {score ? (
                                diff !== null && diff !== 0 ? (
                                  <span style={indicatorStyle}>{score}</span>
                                ) : score
                              ) : '-'}
                            </div>
                            {/* Stroke indicator for upcoming holes */}
                            {!score && strokesReceived > 0 && (
                              <div style={{
                                fontSize: '9px',
                                color: strokesReceived === 0.5 ? '#FF9800' : strokesReceived === 1.0 ? '#2196F3' : '#9C27B0',
                                fontWeight: 'bold',
                                marginTop: '2px'
                              }}>
                                {strokesReceived === 0.5 ? '½' : strokesReceived === 1.0 ? '1' : strokesReceived === 1.5 ? '1½' : strokesReceived}
                              </div>
                            )}
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
        <div data-testid="current-hole" style={{ fontSize: '48px', fontWeight: 'bold', lineHeight: 1 }}>
          Hole {currentHole}
        </div>
        <div style={{ fontSize: '16px', marginTop: '8px', opacity: 0.9 }}>
          Par {holePar}
        </div>
      </div>

      {/* Stroke Allocation Display - Shows who gets strokes on this hole */}
      {!isHoepfinger && rotationOrder.length > 0 && (() => {
        // Calculate stroke allocation for current hole using Creecher Feature logic
        const getStrokesForHole = (handicap, strokeIndex) => {
          if (!handicap || !strokeIndex) return 0;

          const fullStrokes = Math.floor(handicap);
          const hasHalfStroke = (handicap - fullStrokes) >= 0.5;

          // Creecher Feature: For handicaps >18, easiest holes get ONLY half strokes
          if (handicap > 18 && strokeIndex >= 13 && strokeIndex <= 18) {
            const creecherStrokes = Math.min(Math.floor(handicap - 18), 6);
            const easiestHoles = [18, 17, 16, 15, 14, 13];
            if (easiestHoles.slice(0, creecherStrokes).includes(strokeIndex)) {
              return 0.5;
            }
          }

          // Full strokes on hardest holes
          if (strokeIndex <= fullStrokes) {
            return 1.0;
          }

          // Half stroke on next hardest hole for fractional handicaps
          if (hasHalfStroke && strokeIndex === fullStrokes + 1) {
            return 0.5;
          }

          return 0;
        };

        // Default stroke index pattern (hardest to easiest, can be customized per course)
        const defaultStrokeIndex = currentHole; // Simple: hole number = stroke index

        const playersWithStrokes = players
          .map(player => ({
            ...player,
            strokes: getStrokesForHole(player.handicap || 0, defaultStrokeIndex)
          }))
          .filter(p => p.strokes > 0);

        if (playersWithStrokes.length === 0) return null;

        return (
          <div style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: '12px',
            padding: '16px',
            marginBottom: '16px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.15)',
            border: '2px solid rgba(255,255,255,0.2)'
          }}>
            <div style={{
              fontSize: '14px',
              fontWeight: 'bold',
              marginBottom: '12px',
              color: 'white',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              ⛳ STROKES ON HOLE {currentHole}
              <span style={{ fontSize: '11px', fontWeight: 'normal', opacity: 0.9 }}>
                (Stroke Index: {defaultStrokeIndex})
              </span>
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {playersWithStrokes.map(player => (
                <div
                  key={player.id}
                  style={{
                    padding: '10px 16px',
                    borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.95)',
                    color: '#333',
                    fontWeight: 'bold',
                    fontSize: '15px',
                    border: '2px solid rgba(255,255,255,0.3)',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <span>{player.name}</span>
                  <span style={{
                    background: player.strokes === 0.5 ? '#FF9800' : '#4CAF50',
                    color: 'white',
                    padding: '4px 10px',
                    borderRadius: '12px',
                    fontSize: '13px',
                    fontWeight: 'bold'
                  }}>
                    {player.strokes === 0.5 ? '½ STROKE' : player.strokes === 1 ? '1 STROKE' : `${player.strokes} STROKES`}
                  </span>
                </div>
              ))}
            </div>
            <div style={{
              marginTop: '10px',
              padding: '8px 12px',
              background: 'rgba(255,255,255,0.15)',
              borderRadius: '6px',
              fontSize: '11px',
              color: 'white',
              fontStyle: 'italic'
            }}>
              💡 Players receive strokes based on handicap and hole difficulty (stroke index)
            </div>
          </div>
        );
      })()}

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

      {/* Simplified Betting Actions */}
      {!isHoepfinger && rotationOrder.length > 0 && !editingHole && (() => {
        // Determine who can make betting decisions
        let eligiblePlayerId = null;

        // If scores are entered, find the player with the lowest score in the hole
        const playersWithScores = Object.entries(scores).filter(([_, score]) => score > 0);
        if (playersWithScores.length > 0) {
          const lowestScoreEntry = playersWithScores.reduce((lowest, current) =>
            current[1] < lowest[1] ? current : lowest
          );
          eligiblePlayerId = lowestScoreEntry[0];
        } else {
          // No scores yet - check if captain is furthest behind
          const captainPlayerId = rotationOrder[captainIndex];
          const captainStanding = playerStandings[captainPlayerId];
          if (captainStanding) {
            const isCaptainFurthestBehind = Object.values(playerStandings).every(standing =>
              standing === captainStanding || captainStanding.quarters <= standing.quarters
            );
            if (isCaptainFurthestBehind) {
              eligiblePlayerId = captainPlayerId;
            }
          }
        }

        if (!eligiblePlayerId) return null;

        const eligiblePlayer = players.find(p => p.id === eligiblePlayerId);

        return (
          <div style={{
            background: theme.colors.paper,
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '12px',
            border: `1px solid ${theme.colors.border}`
          }}>
            <div style={{ fontSize: '12px', color: theme.colors.textSecondary, marginBottom: '8px' }}>
              Betting by: <strong>{eligiblePlayer?.name}</strong>
            </div>
            <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
              <button
                onClick={() => setCurrentWager(currentWager * 2)}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '6px',
                  background: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  fontSize: '13px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                ×2
              </button>
              <button
                onClick={() => setCurrentWager(nextHoleWager * 4)}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '6px',
                  background: '#FF9800',
                  color: 'white',
                  border: 'none',
                  fontSize: '13px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                ×4
              </button>
              <button
                onClick={() => setCurrentWager(nextHoleWager * 8)}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '6px',
                  background: '#F44336',
                  color: 'white',
                  border: 'none',
                  fontSize: '13px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                ×8
              </button>
              <button
                onClick={() => setCurrentWager(nextHoleWager)}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '6px',
                  background: theme.colors.backgroundSecondary,
                  border: `1px solid ${theme.colors.border}`,
                  fontSize: '13px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}
              >
                Reset
              </button>
            </div>
            <input
              type="number"
              min={nextHoleWager}
              step={nextHoleWager}
              value={currentWager}
              onChange={(e) => {
                const value = parseInt(e.target.value, 10);
                if (value >= nextHoleWager) {
                  setCurrentWager(value);
                }
              }}
              style={{
                width: '100%',
                padding: '8px',
                fontSize: '14px',
                border: `1px solid ${theme.colors.border}`,
                borderRadius: '6px',
                textAlign: 'center'
              }}
              placeholder="Custom wager"
            />
          </div>
        );
      })()}

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
      {(carryOver || vinniesVariation || optionActive) && (
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
          {optionActive && (
            <div style={{
              padding: '6px 12px',
              borderRadius: '6px',
              background: '#2196F3',
              color: 'white',
              fontSize: '12px',
              fontWeight: 'bold'
            }}>
              🎲 THE OPTION (2x)
            </div>
          )}
          <div style={{ fontSize: '14px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
            Base Wager: {nextHoleWager}Q
          </div>
        </div>
      )}

      {/* Simplified Wager Display */}
      <div style={{
        background: theme.colors.paper,
        borderRadius: '8px',
        padding: '12px',
        marginBottom: '12px',
        border: `1px solid ${theme.colors.border}`
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <div style={{ fontSize: '13px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
            Current Wager
          </div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: theme.colors.primary }}>
            {currentWager}Q
          </div>
        </div>

        {/* Active Modifiers */}
        {(carryOver || (optionActive && !optionTurnedOff) || vinniesVariation || joesSpecialWager) && (
          <div style={{ fontSize: '11px', color: theme.colors.textSecondary, display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {carryOver && <span style={{ padding: '2px 6px', background: '#fff3e0', borderRadius: '4px', color: '#FF5722' }}>Carry-Over ×2</span>}
            {optionActive && !optionTurnedOff && <span style={{ padding: '2px 6px', background: '#e3f2fd', borderRadius: '4px', color: '#2196F3' }}>Option ×2</span>}
            {vinniesVariation && <span style={{ padding: '2px 6px', background: '#f3e5f5', borderRadius: '4px', color: '#9C27B0' }}>Vinnie's ×2</span>}
            {joesSpecialWager && <span style={{ padding: '2px 6px', background: '#fff3e0', borderRadius: '4px', color: '#F57C00' }}>Joe's Special</span>}
          </div>
        )}

        {/* Mode & Betting Controls */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '8px', paddingTop: '8px', borderTop: `1px solid ${theme.colors.border}` }}>
          <div style={{ fontSize: '11px', color: theme.colors.textSecondary, flex: 1 }}>
            {teamMode === 'partners' ? '👥 Partners' : '🎯 Solo'}
          </div>
          <button
            onClick={() => setCurrentWager(Math.max(1, currentWager / 2))}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              background: theme.colors.backgroundSecondary,
              border: `1px solid ${theme.colors.border}`,
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            ÷2
          </button>
          <button
            onClick={() => setCurrentWager(currentWager * 2)}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              background: theme.colors.backgroundSecondary,
              border: `1px solid ${theme.colors.border}`,
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            ×2
          </button>
          {optionActive && !optionTurnedOff && goatId && (
            <button
              onClick={() => setOptionTurnedOff(true)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                background: '#ffebee',
                border: '1px solid #f44336',
                fontSize: '11px',
                color: '#d32f2f',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              Turn Off Option
            </button>
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
                  <PlayerName name={player.name} isAuthenticated={player.is_authenticated} />
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

      {/* Usage Statistics - Collapsible */}
      {holeHistory.length > 0 && (
        <div style={{
          background: theme.colors.paper,
          borderRadius: '8px',
          overflow: 'hidden',
          marginBottom: '12px',
          border: `1px solid ${theme.colors.border}`
        }}>
          <div
            onClick={() => setShowUsageStats(!showUsageStats)}
            style={{
              padding: '10px 12px',
              background: theme.colors.backgroundSecondary,
              fontSize: '13px',
              fontWeight: 'bold',
              color: theme.colors.textPrimary,
              cursor: 'pointer',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
            <span>Rule Compliance & Usage</span>
            <span style={{ fontSize: '16px' }}>{showUsageStats ? '▼' : '▶'}</span>
          </div>

          {showUsageStats && <div style={{ padding: '12px' }}>
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

            {/* Rule Summary */}
            <div style={{
              padding: '8px 12px',
              background: '#f9fafb',
              borderTop: `1px solid ${theme.colors.border}`,
              fontSize: '10px',
              color: theme.colors.textSecondary
            }}>
              <div>• Solo: Must go solo once (by hole 16)</div>
              <div>• Float: One-time use per player</div>
              <div>• Option: Auto when captain furthest down</div>
            </div>
          </div>}
        </div>
      )}

      {/* Solo Requirement Warning Banner - Phase 3 */}
      {players.length === 4 && currentHole >= 13 && currentHole <= 16 && (() => {
        const playersNeedingSolo = Object.values(playerStandings).filter(p => (p.soloCount || 0) === 0);
        if (playersNeedingSolo.length > 0) {
          return (
            <div style={{
              background: 'linear-gradient(135deg, #FF6B6B 0%, #FFB347 100%)',
              padding: '20px',
              borderRadius: '16px',
              marginBottom: '20px',
              boxShadow: '0 4px 12px rgba(255, 107, 107, 0.3)',
              border: '3px solid #FF4757'
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                marginBottom: '12px'
              }}>
                <div style={{ fontSize: '32px' }}>⚠️</div>
                <div>
                  <div style={{
                    fontSize: '20px',
                    fontWeight: 'bold',
                    color: 'white',
                    marginBottom: '4px'
                  }}>
                    Solo Requirement Alert!
                  </div>
                  <div style={{
                    fontSize: '14px',
                    color: 'rgba(255, 255, 255, 0.95)'
                  }}>
                    {currentHole === 16
                      ? '🚨 LAST CHANCE - Hoepfinger starts next hole!'
                      : `Only ${17 - currentHole} hole${17 - currentHole === 1 ? '' : 's'} until Hoepfinger`}
                  </div>
                </div>
              </div>

              <div style={{
                background: 'rgba(255, 255, 255, 0.95)',
                padding: '12px',
                borderRadius: '8px',
                marginBottom: '8px'
              }}>
                <div style={{
                  fontSize: '14px',
                  fontWeight: 'bold',
                  color: '#d32f2f',
                  marginBottom: '8px'
                }}>
                  Players who MUST go solo:
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {playersNeedingSolo.map((player, idx) => (
                    <div key={idx} style={{
                      background: '#FF4757',
                      color: 'white',
                      padding: '6px 12px',
                      borderRadius: '20px',
                      fontSize: '14px',
                      fontWeight: 'bold',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                    }}>
                      {player.name}
                    </div>
                  ))}
                </div>
              </div>

              <div style={{
                fontSize: '12px',
                color: 'white',
                fontWeight: 'bold',
                opacity: 0.9
              }}>
                📖 Rule: Each player must go solo at least once in the first 16 holes
              </div>
            </div>
          );
        }
        return null;
      })()}

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
            data-testid="go-solo-button"
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

        {/* The Duncan checkbox - only shown in Solo mode */}
        {teamMode === 'solo' && (
          <div style={{
            marginTop: '12px',
            padding: '12px',
            background: '#F3E5F5',
            borderRadius: '8px',
            border: '2px solid #9C27B0'
          }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 'bold',
              color: '#6A1B9A'
            }}>
              <input
                type="checkbox"
                checked={duncanInvoked}
                onChange={(e) => setDuncanInvoked(e.target.checked)}
                style={{ width: '18px', height: '18px', cursor: 'pointer' }}
              />
              <span>🏆 The Duncan (Captain goes solo before hitting - 3-for-2 payout)</span>
            </label>
          </div>
        )}
      </div>

      {/* Team Selection */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 8px' }}>
          {teamMode === 'partners' ? 'Select Team 1' : 'Select Captain'}
        </h3>
        {teamMode === 'partners' && (
          <p style={{
            margin: '0 0 12px',
            fontSize: '14px',
            color: theme.colors.textSecondary,
            fontStyle: 'italic'
          }}>
            Click players to add them to Team 1. Remaining players will automatically be Team 2.
          </p>
        )}

        {teamMode === 'partners' ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              {players.map(player => {
                const inTeam1 = team1.includes(player.id);
                const inTeam2 = !inTeam1; // Implicit team 2
                return (
                  <button
                    key={player.id}
                    data-testid={`partner-${player.id}`}
                    onClick={() => togglePlayerTeam(player.id)}
                    style={{
                      padding: '12px',
                      fontSize: '16px',
                      border: inTeam1 ? `3px solid #00bcd4` : `2px solid ${theme.colors.border}`,
                      borderRadius: '8px',
                      background: inTeam1 ? 'rgba(0, 188, 212, 0.1)' : inTeam2 ? 'rgba(255, 152, 0, 0.05)' : 'white',
                      cursor: 'pointer',
                      opacity: inTeam2 ? 0.8 : 1
                    }}
                  >
                    <PlayerName name={player.name} isAuthenticated={player.is_authenticated} />
                    {inTeam1 && ' (Team 1)'}
                    {inTeam2 && ' (Team 2 ↺)'}
                  </button>
                );
              })}
            </div>
          </>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
            {players.map(player => {
              const isCaptain = captain === player.id;
              return (
                <button
                  key={player.id}
                  data-testid={`partner-${player.id}`}
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
              <label style={{ flex: 1, fontWeight: 'bold' }}>
                {player.name}
                :
              </label>
              <input
                data-testid={`score-input-${player.id}`}
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
        data-testid="complete-hole-button"
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

      {/* Edit Player Name Modal */}
      {editingPlayerName && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1001,
          padding: '20px'
        }}>
          <div style={{
            background: 'white',
            padding: '24px',
            borderRadius: '12px',
            maxWidth: '400px',
            width: '100%',
            boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '16px', color: theme.colors.primary }}>
              Edit Player Name
            </h3>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: theme.colors.textPrimary }}>
                Player Name:
              </label>
              <input
                type="text"
                value={editPlayerNameValue}
                onChange={(e) => setEditPlayerNameValue(e.target.value)}
                placeholder="Enter player name"
                maxLength="50"
                autoFocus
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleSavePlayerName();
                  }
                }}
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '16px',
                  border: `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                  boxSizing: 'border-box'
                }}
                onFocus={(e) => e.target.style.borderColor = theme.colors.primary}
                onBlur={(e) => e.target.style.borderColor = theme.colors.border}
              />
              <p style={{ fontSize: '12px', color: theme.colors.textSecondary, marginTop: '8px', marginBottom: 0 }}>
                Press Enter to save, or click Save button
              </p>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={handleCancelPlayerNameEdit}
                style={{
                  padding: '10px 20px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  border: `2px solid ${theme.colors.border}`,
                  borderRadius: '8px',
                  background: 'white',
                  color: theme.colors.textPrimary,
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSavePlayerName}
                style={{
                  padding: '10px 20px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  border: 'none',
                  borderRadius: '8px',
                  background: theme.colors.primary,
                  color: 'white',
                  cursor: 'pointer'
                }}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleScorekeeper;
