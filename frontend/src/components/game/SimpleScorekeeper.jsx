// frontend/src/components/game/SimpleScorekeeper.jsx
// Updated: Force redeploy - single scorecard layout
import React, { useState, useEffect, useMemo } from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';
import { Input } from '../ui';
import GameCompletionView from './GameCompletionView';
import Scorecard from './Scorecard';
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

PlayerName.propTypes = {
  name: PropTypes.string.isRequired,
  isAuthenticated: PropTypes.bool,
};

/**
 * Simplified scorekeeper component - no game engine, just direct data entry
 * Client-side betting UI, single API call to complete each hole
 */
const SimpleScorekeeper = ({
  gameId,
  players,
  baseWager = 1,
  initialHoleHistory = [],
  initialCurrentHole = 1,
  courseName = 'Wing Point Golf & Country Club',
  initialStrokeAllocation = null
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
  const [quarters, setQuarters] = useState({}); // Manual quarters entry
  const [winner, setWinner] = useState(null);
  const [floatInvokedBy, setFloatInvokedBy] = useState(null); // Player ID who invoked float
  const [optionInvokedBy, setOptionInvokedBy] = useState(null); // Player ID who triggered option

  // Rotation tracking (Phase 1)
  // Sort players by tee_order if available, otherwise use original order
  const [rotationOrder, setRotationOrder] = useState(() => {
    const sortedPlayers = [...players].sort((a, b) => {
      // If both have tee_order, sort by it
      if (a.tee_order != null && b.tee_order != null) {
        return a.tee_order - b.tee_order;
      }
      // If only one has tee_order, prioritize it
      if (a.tee_order != null) return -1;
      if (b.tee_order != null) return 1;
      // Otherwise maintain original order
      return 0;
    });
    return sortedPlayers.map(p => p.id);
  });
  const [captainIndex, setCaptainIndex] = useState(0);
  const [isHoepfinger, setIsHoepfinger] = useState(false);
  const [goatId, setGoatId] = useState(null);
  const [phase, setPhase] = useState('normal');
  const [joesSpecialWager, setJoesSpecialWager] = useState(null);
  const [nextHoleWager, setNextHoleWager] = useState(baseWager);
  const [carryOver, setCarryOver] = useState(false);
  const [vinniesVariation, setVinniesVariation] = useState(false);
  // eslint-disable-next-line no-unused-vars
  const [carryOverApplied, setCarryOverApplied] = useState(false); // Kept for potential future use

  // Phase 2: Betting mechanics
  const [optionActive, setOptionActive] = useState(false);
  const [optionTurnedOff, setOptionTurnedOff] = useState(false);
  const [duncanInvoked, setDuncanInvoked] = useState(false);

  // Aardvark mechanics (5-man game)
  const [aardvarkRequestedTeam, setAardvarkRequestedTeam] = useState(null); // 'team1' or 'team2'
  const [aardvarkTossed, setAardvarkTossed] = useState(false); // Was Aardvark rejected?
  const [aardvarkSolo, setAardvarkSolo] = useState(false); // Aardvark going solo (Tunkarri)
  // Invisible Aardvark (4-man game)
  const [invisibleAardvarkTossed, setInvisibleAardvarkTossed] = useState(false);

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
  const [bettingHistory, setBettingHistory] = useState([]); // Track betting actions
  const [showBettingHistory, setShowBettingHistory] = useState(false); // Toggle betting history panel
  const [historyTab, setHistoryTab] = useState('current'); // 'current', 'last', 'game'
  const [showAdvancedBetting, setShowAdvancedBetting] = useState(false); // Accordion for betting rules
  const [isEditingCompleteGame, setIsEditingCompleteGame] = useState(false); // Allow editing completed games
  const [isGameMarkedComplete, setIsGameMarkedComplete] = useState(false); // Track if game has been saved as complete

  // Interactive betting state (Offer/Accept flow)
  const [pendingOffer, setPendingOffer] = useState(null);
  // Shape: { offer_id, offer_type, offered_by, wager_before, wager_after, timestamp, status }
  const [currentHoleBettingEvents, setCurrentHoleBettingEvents] = useState([]);
  // Events for current hole - builds the betting narrative

  // Derive current hole par from course data (pars are constants and don't change)
  // No defaults - only use actual course data
  const holePar = courseData?.holes?.find(h => h.hole_number === currentHole)?.par;

  // Track course data loading state
  const [courseDataError, setCourseDataError] = useState(null);
  const [courseDataLoading, setCourseDataLoading] = useState(false);

  // Fetch course data
  useEffect(() => {
    const fetchCourseData = async () => {
      setCourseDataLoading(true);
      setCourseDataError(null);
      try {
        // Fetch course details
        const courseResponse = await fetch(`${API_URL}/courses`);
        if (!courseResponse.ok) {
          throw new Error(`Failed to fetch courses: ${courseResponse.status} ${courseResponse.statusText}`);
        }

        const coursesData = await courseResponse.json();
        if (!coursesData || typeof coursesData !== 'object') {
          throw new Error('Invalid courses response: expected object');
        }

        // /courses returns an object with course names as keys, not an array
        const course = coursesData[courseName];
        if (!course) {
          throw new Error(`Course "${courseName}" not found in courses data`);
        }

        // Validate course data structure
        if (!course.holes || !Array.isArray(course.holes)) {
          throw new Error(`Course "${courseName}" has invalid holes data`);
        }

        setCourseData(course);
      } catch (err) {
        console.error('Error fetching course data:', err);
        setCourseDataError(err.message);
        // Don't set courseData to null - keep any existing data
      } finally {
        setCourseDataLoading(false);
      }
    };

    if (courseName) {
      fetchCourseData();
    }
  }, [courseName]);

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

  // Track rotation/wager loading errors
  const [rotationError, setRotationError] = useState(null);

  // Fetch rotation and wager info when hole changes
  useEffect(() => {
    const fetchRotationAndWager = async () => {
      setRotationError(null);
      try {
        // Fetch next rotation
        const rotationRes = await fetch(`${API_URL}/games/${gameId}/next-rotation`);
        if (!rotationRes.ok) {
          throw new Error(`Failed to fetch rotation: ${rotationRes.status}`);
        }

        const rotationData = await rotationRes.json();
        if (!rotationData || typeof rotationData !== 'object') {
          throw new Error('Invalid rotation response');
        }

        if (rotationData.is_hoepfinger) {
          setIsHoepfinger(true);
          setGoatId(rotationData.goat_id);
          setPhase('hoepfinger');
          // Don't set rotation yet - Goat will select position
        } else {
          setIsHoepfinger(false);
          // Validate rotation_order is an array
          if (!Array.isArray(rotationData.rotation_order)) {
            throw new Error('Invalid rotation_order: expected array');
          }
          setRotationOrder(rotationData.rotation_order);
          setCaptainIndex(typeof rotationData.captain_index === 'number' ? rotationData.captain_index : 0);
          setPhase('normal');
          setGoatId(null);
          setJoesSpecialWager(null);
        }

        // Fetch next hole wager
        const wagerRes = await fetch(`${API_URL}/games/${gameId}/next-hole-wager`);
        if (!wagerRes.ok) {
          throw new Error(`Failed to fetch wager: ${wagerRes.status}`);
        }

        const wagerData = await wagerRes.json();
        if (!wagerData || typeof wagerData !== 'object') {
          throw new Error('Invalid wager response');
        }

        // Validate and set wager data with safe defaults
        const baseWagerValue = typeof wagerData.base_wager === 'number' ? wagerData.base_wager : baseWager;
        setNextHoleWager(baseWagerValue);
        setCurrentWager(baseWagerValue);
        setCarryOver(wagerData.carry_over || false);
        setVinniesVariation(wagerData.vinnies_variation || false);
        setOptionActive(wagerData.option_active || false);
        if (wagerData.option_active) {
          setGoatId(wagerData.goat_id);
        }
      } catch (err) {
        console.error('Error fetching rotation/wager:', err);
        setRotationError(err.message);
        // Set safe defaults on error
        setCurrentWager(baseWager);
        setNextHoleWager(baseWager);
      }
    };

    if (gameId) {
      fetchRotationAndWager();
    }
  }, [gameId, currentHole, holeHistory, baseWager]);

  // Reset hole state for new hole
  const resetHole = () => {
    setTeam1([]);
    setTeam2([]);
    setCaptain(null);
    setOpponents([]);
    setCurrentWager(baseWager);
    setScores({});
    setQuarters({});
    setWinner(null);
    setFloatInvokedBy(null);
    setOptionInvokedBy(null);
    setError(null);
    setEditingHole(null);
    setCarryOverApplied(carryOver); // Set to true if carry-over was active
    setJoesSpecialWager(null); // Reset Joe's Special for next hole
    setOptionTurnedOff(false); // Reset Option for next hole
    setDuncanInvoked(false); // Reset Duncan for next hole
    // Reset Aardvark state
    setAardvarkRequestedTeam(null);
    setAardvarkTossed(false);
    setAardvarkSolo(false);
    setInvisibleAardvarkTossed(false);
    // Reset interactive betting state
    setPendingOffer(null);
    setCurrentHoleBettingEvents([]);
  };

  // Load hole data for editing
  const loadHoleForEdit = (hole) => {
    setEditingHole(hole.hole);
    setCurrentHole(hole.hole); // Setting currentHole automatically updates derived holePar
    setScores(hole.gross_scores || {});
    setQuarters(hole.points_delta || {}); // Load quarters from points_delta
    setCurrentWager(hole.wager || baseWager);
    setWinner(hole.winner);
    setFloatInvokedBy(hole.float_invoked_by || null);
    setOptionInvokedBy(hole.option_invoked_by || null);

    // Restore betting state from hole data
    setCurrentHoleBettingEvents(hole.betting_events || []);
    setPendingOffer(null); // Clear any pending offers when loading for edit
    setDuncanInvoked(hole.duncan_invoked || false);
    setOptionTurnedOff(hole.option_turned_off || false);

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

  // Log a betting action to history
  const logBettingAction = (actionType, details = {}) => {
    const playerName = details.playerId
      ? localPlayers.find(p => p.id === details.playerId)?.name || 'Unknown'
      : null;

    const newEvent = {
      eventId: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      hole: currentHole,
      eventType: actionType,
      actor: playerName || details.actor || 'System',
      timestamp: new Date().toISOString(),
      details: {
        ...details,
        wager: currentWager
      }
    };

    setBettingHistory(prev => [...prev, newEvent]);
  };

  // Helper to get player name by ID
  const getPlayerName = (playerId) => {
    return localPlayers.find(p => p.id === playerId)?.name || 'Unknown';
  };

  // Add a betting event to current hole's events
  const addBettingEvent = (event) => {
    const fullEvent = {
      ...event,
      hole: currentHole,
      timestamp: event.timestamp || new Date().toISOString(),
      actor: event.offered_by || event.response_by || event.actor
    };
    setCurrentHoleBettingEvents(prev => [...prev, fullEvent]);
    // Also log to global betting history
    logBettingAction(event.eventType, fullEvent);
  };

  // Create a betting offer (Double, Float, etc.)
  const createOffer = (offerType, offeredBy) => {
    if (pendingOffer) return; // Can't offer while another is pending

    const offer = {
      offer_id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      offer_type: offerType,
      offered_by: offeredBy,
      wager_before: currentWager,
      wager_after: currentWager * 2,
      timestamp: new Date().toISOString(),
      status: 'pending'
    };
    setPendingOffer(offer);
    addBettingEvent({
      eventType: `${offerType.toUpperCase()}_OFFERED`,
      offered_by: offeredBy,
      wager_before: offer.wager_before,
      wager_after: offer.wager_after
    });
  };

  // Respond to a pending betting offer
  const respondToOffer = (response, respondedBy) => {
    if (!pendingOffer) return;

    if (response === 'accept') {
      setCurrentWager(pendingOffer.wager_after);
      addBettingEvent({
        eventType: `${pendingOffer.offer_type.toUpperCase()}_ACCEPTED`,
        response_by: respondedBy,
        wager_before: pendingOffer.wager_before,
        wager_after: pendingOffer.wager_after
      });
    } else {
      addBettingEvent({
        eventType: `${pendingOffer.offer_type.toUpperCase()}_DECLINED`,
        response_by: respondedBy,
        wager_before: pendingOffer.wager_before
      });
    }
    setPendingOffer(null);
  };

  // Announce an action (Duncan, Option Off) - no accept needed
  const announceAction = (actionType, announcedBy) => {
    addBettingEvent({
      eventType: `${actionType.toUpperCase()}_ANNOUNCED`,
      announced_by: announcedBy,
      actor: announcedBy
    });
  };

  // Build betting narrative from events
  const buildBettingNarrative = (events) => {
    if (!events || !events.length) return null;

    return events.map(e => {
      const actor = getPlayerName(e.offered_by || e.response_by || e.announced_by || e.actor);
      switch(e.eventType) {
        case 'DOUBLE_OFFERED': return `${actor} doubles`;
        case 'DOUBLE_ACCEPTED': return 'accepted';
        case 'DOUBLE_DECLINED': return 'declined';
        case 'FLOAT_OFFERED': return `${actor} floats`;
        case 'FLOAT_ACCEPTED': return 'accepted';
        case 'FLOAT_DECLINED': return 'declined';
        case 'DUNCAN_ANNOUNCED': return `${actor} calls Duncan`;
        case 'OPTION_OFF_ANNOUNCED': return `${actor} turns off Option`;
        case 'OPTION_ACTIVE': return 'Option active';
        default: return null;
      }
    }).filter(Boolean).join(' → ');
  };

  // Get current betting narrative
  const currentBettingNarrative = useMemo(() => {
    return buildBettingNarrative(currentHoleBettingEvents);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentHoleBettingEvents]);

  // Handle score input
  const handleScoreChange = (playerId, value) => {
    setScores({
      ...scores,
      [playerId]: parseInt(value, 10) || 0
    });
  };

  // Note: calculateQuartersForHole removed - quarters are now entered manually

  // Use stroke allocation from backend if provided (preferred - calculated with Creecher Feature rules)
  // Falls back to local calculation only if backend data is not available
  const strokeAllocation = useMemo(() => {
    // If we have stroke allocation from the backend, use it (it's more accurate)
    if (initialStrokeAllocation && Object.keys(initialStrokeAllocation).length > 0) {
      return initialStrokeAllocation;
    }

    // Fallback: calculate locally if backend didn't provide stroke allocation
    if (!courseData?.holes) return {};

    const allocation = {};

    // Calculate net handicaps relative to lowest handicap player
    const playerHandicaps = localPlayers.reduce((acc, player) => {
      acc[player.id] = player.handicap || 0;
      return acc;
    }, {});

    const lowestHandicap = Math.min(...Object.values(playerHandicaps));

    const netHandicaps = {};
    Object.entries(playerHandicaps).forEach(([playerId, handicap]) => {
      netHandicaps[playerId] = Math.max(0, handicap - lowestHandicap);
    });

    const getStrokesForHole = (netHandicap, strokeIndex) => {
      if (!netHandicap || netHandicap <= 0) return 0;

      const fullHandicap = Math.floor(netHandicap);
      const hasFractional = (netHandicap % 1) >= 0.5;

      // Creecher Feature implementation
      if (netHandicap <= 6) {
        // All allocated holes get 0.5
        return strokeIndex <= fullHandicap ? 0.5 : 0;
      } else if (netHandicap <= 18) {
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
          const halfsNeeded = extraHalfStrokes;
          const holesGettingExtra = Math.min(halfsNeeded, 12);
          if (strokeIndex <= holesGettingExtra) {
            return 1.0; // 0.5 base + 0.5 extra
          }
          return 0.5;
        } else {
          // Hardest 12 holes get base 1.0
          const halfsNeeded = extraHalfStrokes;
          const holesGettingExtra = Math.min(halfsNeeded, 12);
          if (strokeIndex <= holesGettingExtra) {
            return 1.5; // 1.0 base + 0.5 extra
          }
          return 1.0;
        }
      }
    };

    localPlayers.forEach(player => {
      allocation[player.id] = {};
      const netHandicap = netHandicaps[player.id];

      for (let holeNum = 1; holeNum <= 18; holeNum++) {
        const holeData = courseData.holes.find(h => h.hole_number === holeNum);
        if (holeData?.handicap) {
          allocation[player.id][holeNum] = getStrokesForHole(netHandicap, holeData.handicap);
        }
      }
    });

    return allocation;
  }, [courseData, localPlayers, initialStrokeAllocation]);

  // Calculate net scores and auto-detect winner
  const calculateNetScoresAndWinner = useMemo(() => {
    // Need all scores entered and teams formed
    const allScoresEntered = players.every(p => scores[p.id] !== undefined && scores[p.id] !== null);
    const teamsFormed = teamMode === 'partners'
      ? team1.length > 0 && team1.length < players.length
      : captain !== null;

    if (!allScoresEntered || !teamsFormed) {
      return { netScores: {}, suggestedWinner: null, team1Net: null, team2Net: null };
    }

    // Calculate net scores (gross - strokes received)
    const netScores = {};
    players.forEach(player => {
      const gross = scores[player.id] || 0;
      const strokesReceived = strokeAllocation?.[player.id]?.[currentHole] || 0;
      netScores[player.id] = gross - strokesReceived;
    });

    // Calculate team totals based on best ball (lowest net score on team)
    let team1Net, team2Net;

    if (teamMode === 'partners') {
      const team2Ids = players.filter(p => !team1.includes(p.id)).map(p => p.id);
      team1Net = Math.min(...team1.map(id => netScores[id]));
      team2Net = Math.min(...team2Ids.map(id => netScores[id]));
    } else {
      // Solo mode: captain vs opponents
      team1Net = netScores[captain]; // Captain's net score
      team2Net = Math.min(...opponents.map(id => netScores[id])); // Best of opponents
    }

    // Determine suggested winner
    let suggestedWinner = null;
    if (team1Net < team2Net) {
      suggestedWinner = teamMode === 'partners' ? 'team1' : 'captain';
    } else if (team2Net < team1Net) {
      suggestedWinner = teamMode === 'partners' ? 'team2' : 'opponents';
    } else {
      suggestedWinner = 'push'; // Tied = push
    }

    return { netScores, suggestedWinner, team1Net, team2Net };
  }, [scores, players, team1, captain, opponents, teamMode, strokeAllocation, currentHole]);

  // Auto-set winner when scores suggest a clear result
  useEffect(() => {
    const { suggestedWinner } = calculateNetScoresAndWinner;
    if (suggestedWinner && !winner) {
      // Auto-set the winner based on net scores
      setWinner(suggestedWinner);
    }
  }, [calculateNetScoresAndWinner, winner]);

  // Validate hole data before submission
  const validateHole = () => {
    // Simplified validation: only quarters matter now
    const allPlayers = players.map(p => p.id);

    // Validate quarters: must be entered for all players and sum to zero
    const quartersEntered = Object.keys(quarters).length > 0;
    if (!quartersEntered) {
      return 'Please enter quarters for all players';
    }

    // Check all players have quarters
    for (const playerId of allPlayers) {
      if (quarters[playerId] === undefined || quarters[playerId] === '') {
        return 'Please enter quarters for all players';
      }
    }

    // Validate zero-sum (allow decimals for split scoring)
    const quartersSum = allPlayers.reduce((sum, playerId) => {
      const q = parseFloat(quarters[playerId]) || 0;
      return sum + q;
    }, 0);

    // Use small epsilon for floating point comparison
    if (Math.abs(quartersSum) > 0.001) {
      return `Quarters must sum to zero. Current sum: ${quartersSum > 0 ? '+' : ''}${quartersSum.toFixed(2)}`;
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

      // QUARTERS-ONLY MODE: Use manually-entered quarters
      // Build pointsDelta from user-entered quarters (supports decimals for split scoring)
      const pointsDelta = {};
      players.forEach(player => {
        pointsDelta[player.id] = parseFloat(quarters[player.id]) || 0;
      });

      // Zero-sum already validated in validateHole()

      // Build hole result object (local, no server needed for calculation)
      const holeResult = {
        hole: currentHole,
        points_delta: pointsDelta,
        gross_scores: scores,
        teams: teams,
        winner: null, // Winner not used - quarters entered manually
        wager: currentWager,
        phase: phase,
        rotation_order: rotationOrder,
        captain_index: captainIndex,
        quarters_only: true
      };

      // Log hole completion to betting history
      logBettingAction('Hole Completed', {
        actor: 'Quarters entered manually',
        wager: currentWager,
        winner: null,
        scores: scores
      });

      // Update local state first (optimistic update)
      let updatedHistory;
      if (editingHole) {
        // Editing existing hole - update it in the history
        updatedHistory = holeHistory.map(h =>
          h.hole === editingHole ? holeResult : h
        );
      } else {
        // New hole - add to history
        updatedHistory = [...holeHistory, holeResult];
      }
      setHoleHistory(updatedHistory);

      // Recalculate all player standings from the updated history
      const newStandings = {};
      players.forEach(player => {
        newStandings[player.id] = {
          quarters: 0,
          name: player.name,
          soloCount: 0,
          floatCount: 0,
          optionCount: 0
        };
      });

      updatedHistory.forEach(hole => {
        const delta = hole.points_delta || {};
        Object.entries(delta).forEach(([playerId, points]) => {
          if (newStandings[playerId]) {
            newStandings[playerId].quarters += typeof points === 'number' ? points : 0;
          }
        });
        // Track solo usage
        if (hole.teams?.type === 'solo' && hole.teams?.captain) {
          if (newStandings[hole.teams.captain]) {
            newStandings[hole.teams.captain].soloCount += 1;
          }
        }
      });
      setPlayerStandings(newStandings);

      // Build hole_quarters for the quarters-only endpoint
      const holeQuarters = {};
      updatedHistory.forEach(hole => {
        if (hole.points_delta) {
          holeQuarters[String(hole.hole)] = hole.points_delta;
        }
      });

      // Build optional details for metadata
      const optionalDetails = {};
      updatedHistory.forEach(hole => {
        optionalDetails[String(hole.hole)] = {
          teams: hole.teams,
          winner: hole.winner,
          wager: hole.wager,
          gross_scores: hole.gross_scores,
          phase: hole.phase
        };
      });

      // Sync to backend using quarters-only endpoint
      const response = await fetch(`${API_URL}/games/${gameId}/quarters-only`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          hole_quarters: holeQuarters,
          optional_details: optionalDetails,
          current_hole: editingHole ? currentHole : currentHole + 1
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const rawError = errorData.detail || errorData.message || 'Failed to save quarters';

        // Handle zero-sum validation error from backend
        if (rawError.includes('Zero-sum validation failed')) {
          throw new Error(`Quarters don't balance!\n\n${rawError}\n\n💡 Each hole must sum to zero. Check the wager and winner settings.`);
        }

        throw new Error(rawError);
      }

      // Move to next hole or return from editing
      if (editingHole) {
        const maxHole = updatedHistory.length > 0
          ? Math.max(...updatedHistory.map(h => h.hole))
          : 0;
        setCurrentHole(maxHole + 1);
        resetHole();
      } else {
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

  // Track achievement check status
  const [achievementCheckFailed, setAchievementCheckFailed] = useState(false);

  // Check achievements for all players and trigger notifications
  const checkAchievements = async () => {
    let failedPlayers = [];
    setAchievementCheckFailed(false);

    for (const player of players) {
      try {
        const response = await fetch(`${API_URL}/api/badges/admin/check-achievements/${player.id}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        if (!response.ok) {
          console.warn(`Achievement check failed for ${player.name}: ${response.status}`);
          failedPlayers.push(player.name);
          continue;
        }

        const data = await response.json();
        if (!data || typeof data !== 'object') {
          console.warn(`Invalid achievement response for ${player.name}`);
          failedPlayers.push(player.name);
          continue;
        }

        // Trigger badge notification for each newly earned badge
        if (Array.isArray(data.badges_earned) && data.badges_earned.length > 0) {
          data.badges_earned.forEach(badge => {
            if (badge && typeof badge === 'object') {
              triggerBadgeNotification(badge);
            }
          });
        }
      } catch (err) {
        console.warn(`Achievement check error for ${player.name}:`, err);
        failedPlayers.push(player.name);
      }
    }

    // If any achievements failed to check, set the warning flag
    if (failedPlayers.length > 0) {
      setAchievementCheckFailed(true);
      console.warn(`Achievement check failed for: ${failedPlayers.join(', ')}`);
    }
  };

  // Handle player name editing - exported for potential external use
  // eslint-disable-next-line no-unused-vars
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

  // Memoize courseHoles transformation to prevent Scorecard re-renders
  const scorecardCourseHoles = useMemo(() => {
    if (!courseData?.holes) return [];
    return courseData.holes.map(h => ({
      hole: h.hole_number,
      par: h.par,
      handicap: h.handicap,
      yards: h.yards
    }));
  }, [courseData?.holes]);

  // Handler for editing a hole from the scorecard
  const handleEditHoleFromScorecard = ({ hole, playerId, strokes, quarters }) => {
    // Load the hole for editing
    const holeData = holeHistory.find(h => h.hole === hole);
    if (holeData) {
      // Update the scores for this specific player
      const updatedScores = { ...holeData.gross_scores };
      if (strokes !== null) {
        updatedScores[playerId] = strokes;
      }

      // Update points delta if quarters were changed
      const updatedPointsDelta = { ...holeData.points_delta };
      if (quarters !== null && quarters !== undefined) {
        updatedPointsDelta[playerId] = quarters;
      }

      // Load this hole into edit mode
      loadHoleForEdit({ ...holeData, gross_scores: updatedScores, points_delta: updatedPointsDelta });
    }
  };

  // Check if game is complete (all 18 holes played)
  const isGameComplete = currentHole > 18 && holeHistory.length === 18;

  // Handler to mark game as complete in the database
  const handleMarkComplete = async () => {
    if (!gameId) {
      console.error('No game ID available');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/games/${gameId}/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to mark game as complete');
      }

      const result = await response.json();
      console.log('Game marked as complete:', result);
      setIsGameMarkedComplete(true);
    } catch (error) {
      console.error('Error marking game complete:', error);
      alert(`Failed to save game: ${error.message}`);
    }
  };

  // Show completion view if game is complete and not in edit mode
  if (isGameComplete && !isEditingCompleteGame) {
    return (
      <GameCompletionView
        players={players}
        playerStandings={playerStandings}
        holeHistory={holeHistory}
        onNewGame={() => {
          // Reset to start a new game
          window.location.reload();
        }}
        onEditScores={() => {
          // Enter edit mode - set to hole 19 so ALL holes appear as "completed" and editable
          setIsEditingCompleteGame(true);
          setCurrentHole(19); // All holes 1-18 will show as completed (editable)
        }}
        onMarkComplete={handleMarkComplete}
        isCompleted={isGameMarkedComplete}
      />
    );
  }

  return (
    <div data-testid="scorekeeper-container" style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      {/* Loading/Error/Warning Banners */}
      {courseDataLoading && (
        <div style={{
          background: '#e3f2fd',
          color: '#1976d2',
          padding: '10px 14px',
          borderRadius: '8px',
          marginBottom: '12px',
          fontSize: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span>⏳</span>
          <span>Loading course data...</span>
        </div>
      )}

      {courseDataError && (
        <div style={{
          background: '#f44336',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span style={{ fontSize: '18px' }}>⚠️</span>
          <div>
            <strong>Course Data Error:</strong> {courseDataError}
            <div style={{ fontSize: '12px', opacity: 0.9, marginTop: '4px' }}>
              Hole par and handicap data may be unavailable
            </div>
          </div>
        </div>
      )}

      {rotationError && (
        <div style={{
          background: '#ff9800',
          color: 'white',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <span style={{ fontSize: '18px' }}>⚠️</span>
          <div>
            <strong>Rotation/Wager Error:</strong> {rotationError}
            <div style={{ fontSize: '12px', opacity: 0.9, marginTop: '4px' }}>
              Using default wager. Rotation may be incorrect.
            </div>
          </div>
        </div>
      )}

      {achievementCheckFailed && (
        <div style={{
          background: '#9c27b0',
          color: 'white',
          padding: '10px 14px',
          borderRadius: '8px',
          marginBottom: '12px',
          fontSize: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span>🏆</span>
          <span>Achievement check failed - some badges may not have been recorded</span>
          <button
            onClick={() => setAchievementCheckFailed(false)}
            style={{
              marginLeft: 'auto',
              background: 'transparent',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Editing Completed Game Banner */}
      {isEditingCompleteGame && (
        <div style={{
          background: 'linear-gradient(135deg, #ff9800 0%, #f57c00 100%)',
          color: 'white',
          padding: '16px 20px',
          borderRadius: '12px',
          marginBottom: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 4px 6px rgba(0,0,0,0.15)'
        }}>
          <div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px' }}>
              Editing Completed Game
            </div>
            <div style={{ fontSize: '14px', opacity: 0.9 }}>
              Click on any hole in the scorecard below to edit it
            </div>
          </div>
          <button
            onClick={() => {
              setIsEditingCompleteGame(false);
              setCurrentHole(19); // Return to completed state
            }}
            style={{
              padding: '10px 20px',
              fontSize: '16px',
              fontWeight: 'bold',
              borderRadius: '8px',
              border: '2px solid white',
              background: 'transparent',
              color: 'white',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.target.style.background = 'rgba(255,255,255,0.2)';
            }}
            onMouseOut={(e) => {
              e.target.style.background = 'transparent';
            }}
          >
            Done Editing
          </button>
        </div>
      )}

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
        marginBottom: '20px',
        position: 'sticky',
        top: '0',
        zIndex: 10
      }}>
        <Scorecard
          players={localPlayers}
          holeHistory={holeHistory}
          currentHole={currentHole}
          onEditHole={handleEditHoleFromScorecard}
          courseHoles={scorecardCourseHoles}
          strokeAllocation={strokeAllocation}
          isEditingCompleteGame={isEditingCompleteGame}
        />

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

      {/* Enhanced Hole Title Section - Combines hole info, hitting order, and strokes */}
      {(() => {
        const strokeIndex = courseData?.holes?.find(h => h.hole_number === currentHole)?.handicap;

        // Use the already-calculated strokeAllocation which has correct Creecher Feature logic
        // This ensures consistency between the Scorecard and the Hitting Order display
        const playerStrokesMap = {};
        players.forEach(player => {
          // Get strokes from the centralized strokeAllocation (includes Creecher half strokes)
          playerStrokesMap[player.id] = strokeAllocation?.[player.id]?.[currentHole] || 0;
        });

        return (
          <div style={{
            background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.accent})`,
            color: 'white',
            borderRadius: '16px',
            marginBottom: '16px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            overflow: 'hidden'
          }}>
            {/* Main Header Row */}
            <div style={{
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid rgba(255,255,255,0.2)'
            }}>
              {/* Left: Hole Number */}
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                <div data-testid="current-hole" style={{ fontSize: '42px', fontWeight: 'bold', lineHeight: 1 }}>
                  {currentHole}
                </div>
                <div style={{ fontSize: '14px', opacity: 0.9, textTransform: 'uppercase' }}>
                  Hole
                </div>
              </div>

              {/* Center: Par & Stroke Index */}
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', opacity: 0.8, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Par</div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{holePar || '-'}</div>
                </div>
                {strokeIndex && (
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '11px', opacity: 0.8, textTransform: 'uppercase', letterSpacing: '0.5px' }}>SI</div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{strokeIndex}</div>
                  </div>
                )}
              </div>

              {/* Right: Wager */}
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '11px', opacity: 0.8, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Wager</div>
                <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{currentWager}q</div>
              </div>
            </div>

            {/* Hitting Order Row with Stroke Indicators */}
            {!isHoepfinger && rotationOrder.length > 0 && (
              <div style={{
                padding: '12px 16px',
                background: 'rgba(0,0,0,0.15)'
              }}>
                <div style={{
                  fontSize: '10px',
                  textTransform: 'uppercase',
                  letterSpacing: '1px',
                  opacity: 0.8,
                  marginBottom: '8px'
                }}>
                  Hitting Order
                </div>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
                  {rotationOrder.map((playerId, index) => {
                    const player = players.find(p => p.id === playerId);
                    const isCaptain = index === captainIndex;
                    const playerStrokes = playerStrokesMap[playerId] || 0;
                    const hasFullStroke = playerStrokes >= 1;
                    const hasHalfStroke = (playerStrokes % 1) >= 0.4;
                    const fullStrokeCount = Math.floor(playerStrokes);

                    return (
                      <div
                        key={playerId}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '6px 10px',
                          borderRadius: '20px',
                          background: isCaptain ? 'rgba(33, 150, 243, 0.9)' : 'rgba(255,255,255,0.2)',
                          fontSize: '13px',
                          fontWeight: isCaptain ? 'bold' : '500',
                          border: isCaptain ? '2px solid rgba(255,255,255,0.5)' : '1px solid rgba(255,255,255,0.15)'
                        }}
                      >
                        <span style={{
                          fontSize: '11px',
                          opacity: 0.8,
                          fontWeight: 'bold',
                          minWidth: '14px'
                        }}>
                          {index + 1}.
                        </span>
                        <span>{player?.name || playerId}</span>
                        {isCaptain && <span>👑</span>}
                        {/* Stroke indicators inline */}
                        {hasFullStroke && (
                          <span style={{
                            background: '#4CAF50',
                            color: 'white',
                            padding: '2px 6px',
                            borderRadius: '10px',
                            fontSize: '10px',
                            fontWeight: 'bold',
                            marginLeft: '2px'
                          }}>
                            {fullStrokeCount > 1 ? `●${fullStrokeCount}` : '●'}
                          </span>
                        )}
                        {hasHalfStroke && (
                          <span style={{
                            background: '#FF9800',
                            color: 'white',
                            padding: '2px 6px',
                            borderRadius: '10px',
                            fontSize: '10px',
                            fontWeight: 'bold',
                            marginLeft: hasFullStroke ? '2px' : '2px'
                          }}>
                            ◐
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Strokes Legend (compact, only if someone gets strokes) */}
            {!isHoepfinger && strokeIndex && Object.values(playerStrokesMap).some(s => s > 0) && (
              <div style={{
                padding: '8px 16px',
                background: 'rgba(0,0,0,0.1)',
                fontSize: '11px',
                opacity: 0.9,
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                flexWrap: 'wrap'
              }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ background: '#4CAF50', color: 'white', padding: '1px 5px', borderRadius: '8px', fontSize: '9px' }}>●</span>
                  Full stroke
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ background: '#FF9800', color: 'white', padding: '1px 5px', borderRadius: '8px', fontSize: '9px' }}>◐</span>
                  Half stroke (Creecher)
                </span>
              </div>
            )}
          </div>
        );
      })()}

      {/* Betting Controls - Always visible */}
      {(() => {
        // Calculate multiplier from base wager
        const multiplier = nextHoleWager > 0 ? Math.round(currentWager / nextHoleWager) : 1;
        const hasMultiplier = multiplier > 1;

        return (
        <div style={{
          background: '#f0f7ff',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '12px',
          border: `2px solid ${theme.colors.border}`,
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
        }}>
          {/* Current Wager Display with Multiplier Badge */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            marginBottom: '12px'
          }}>
            {/* Multiplier Badge - only show when doubled */}
            {hasMultiplier && (
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #4CAF50, #45a049)',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '20px',
                fontSize: '20px',
                fontWeight: 'bold',
                boxShadow: '0 2px 8px rgba(76, 175, 80, 0.3)'
              }}>
                {multiplier}×
              </span>
            )}
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '36px', fontWeight: 'bold', color: theme.colors.primary }}>
                {currentWager}Q
              </div>
              {/* Base vs Total breakdown */}
              {hasMultiplier && (
                <div style={{ fontSize: '12px', color: theme.colors.textSecondary, marginTop: '2px' }}>
                  Base: {nextHoleWager}Q × {multiplier} = {currentWager}Q
                </div>
              )}
            </div>
          </div>

          {/* Active Modifiers */}
          {(carryOver || (optionActive && !optionTurnedOff) || vinniesVariation || joesSpecialWager) && (
            <div style={{
              fontSize: '10px',
              color: theme.colors.textSecondary,
              display: 'flex',
              gap: '6px',
              flexWrap: 'wrap',
              justifyContent: 'center',
              marginBottom: '16px'
            }}>
              {carryOver && <span style={{ padding: '3px 8px', background: '#fff3e0', borderRadius: '4px', color: '#FF5722', fontWeight: 'bold' }}>Carry-Over ×2</span>}
              {optionActive && !optionTurnedOff && (
                <span style={{ padding: '3px 8px', background: '#e3f2fd', borderRadius: '4px', color: '#2196F3', fontWeight: 'bold' }}>
                  Option ×2 <span style={{ fontSize: '9px', opacity: 0.8 }}>(AUTO - {getPlayerName(goatId)} is Goat)</span>
                </span>
              )}
              {optionActive && optionTurnedOff && (
                <span style={{ padding: '3px 8px', background: '#e0e0e0', borderRadius: '4px', color: '#757575', fontWeight: 'bold', textDecoration: 'line-through' }}>
                  Option OFF
                </span>
              )}
              {vinniesVariation && <span style={{ padding: '3px 8px', background: '#f3e5f5', borderRadius: '4px', color: '#9C27B0', fontWeight: 'bold' }}>Vinnie's ×2</span>}
              {joesSpecialWager && <span style={{ padding: '3px 8px', background: '#fff3e0', borderRadius: '4px', color: '#F57C00', fontWeight: 'bold' }}>Joe's Special</span>}
            </div>
          )}

          {/* Betting Narrative - shows history of betting actions this hole */}
          {currentBettingNarrative && (
            <div style={{
              fontSize: '12px',
              color: theme.colors.textSecondary,
              textAlign: 'center',
              marginBottom: '12px',
              padding: '8px 12px',
              background: theme.colors.backgroundSecondary,
              borderRadius: '6px',
              fontStyle: 'italic'
            }}>
              {currentBettingNarrative}
            </div>
          )}

          {/* Pending Offer Panel - shown when a betting offer is active */}
          {pendingOffer && (
            <div style={{
              background: '#FFF3E0',
              padding: '16px',
              borderRadius: '8px',
              marginBottom: '16px',
              border: '2px solid #FF9800',
              textAlign: 'center'
            }}>
              <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '8px', color: '#E65100' }}>
                {getPlayerName(pendingOffer.offered_by)} offers {pendingOffer.offer_type.toUpperCase()}!
              </div>
              <div style={{ marginBottom: '12px', fontSize: '14px', color: '#5D4037' }}>
                Wager: {pendingOffer.wager_before}Q → {pendingOffer.wager_after}Q
              </div>
              <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                <button
                  onClick={() => respondToOffer('accept', captain || team1[0])}
                  className="touch-optimized"
                  style={{
                    padding: '12px 24px',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    background: 'linear-gradient(135deg, #4CAF50, #45a049)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    boxShadow: '0 2px 8px rgba(76, 175, 80, 0.3)'
                  }}
                >
                  Accept
                </button>
                <button
                  onClick={() => respondToOffer('decline', captain || team1[0])}
                  className="touch-optimized"
                  style={{
                    padding: '12px 24px',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    background: 'linear-gradient(135deg, #f44336, #d32f2f)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    boxShadow: '0 2px 8px rgba(244, 67, 54, 0.3)'
                  }}
                >
                  Decline
                </button>
              </div>
            </div>
          )}

          {/* Betting Controls */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            {/* Decrement Button */}
            <button
              onClick={() => setCurrentWager(Math.max(nextHoleWager, currentWager - 1))}
              disabled={currentWager <= nextHoleWager}
              className="touch-optimized"
              style={{
                flex: '0 0 48px',
                height: '48px',
                borderRadius: '8px',
                background: currentWager <= nextHoleWager ? theme.colors.backgroundSecondary : '#f5f5f5',
                border: `2px solid ${theme.colors.border}`,
                fontSize: '24px',
                fontWeight: 'bold',
                color: currentWager <= nextHoleWager ? theme.colors.textSecondary : theme.colors.textPrimary,
                cursor: currentWager <= nextHoleWager ? 'not-allowed' : 'pointer',
                opacity: currentWager <= nextHoleWager ? 0.5 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              −
            </button>

            {/* Increment Button */}
            <button
              onClick={() => setCurrentWager(currentWager + 1)}
              className="touch-optimized"
              style={{
                flex: '0 0 48px',
                height: '48px',
                borderRadius: '8px',
                background: '#f5f5f5',
                border: `2px solid ${theme.colors.border}`,
                fontSize: '24px',
                fontWeight: 'bold',
                color: theme.colors.textPrimary,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              +
            </button>

            {/* Advanced Betting Rules - Hidden by default */}
            {showAdvancedBetting && (
              <>
            {/* Double Button - Offer flow */}
            <button
              onClick={() => createOffer('double', captain || team1[0] || rotationOrder[captainIndex])}
              disabled={pendingOffer !== null}
              className="touch-optimized"
              style={{
                flex: 1,
                minWidth: '80px',
                height: '48px',
                borderRadius: '8px',
                background: pendingOffer ? '#e0e0e0' : 'linear-gradient(135deg, #4CAF50, #45a049)',
                border: 'none',
                fontSize: '14px',
                fontWeight: 'bold',
                color: pendingOffer ? '#9e9e9e' : 'white',
                cursor: pendingOffer ? 'not-allowed' : 'pointer',
                boxShadow: pendingOffer ? 'none' : '0 2px 8px rgba(76, 175, 80, 0.3)',
                transition: 'all 0.2s'
              }}
            >
              {pendingOffer?.offer_type === 'double' ? 'Pending...' : 'Double'}
            </button>

            {/* Float Button - Captain only, once per round */}
            {(() => {
              const currentCaptain = captain || team1[0] || rotationOrder[captainIndex];
              const hasUsedFloat = playerStandings[currentCaptain]?.floatCount >= 1;
              const isFloatPending = pendingOffer?.offer_type === 'float';
              return (
                <button
                  onClick={() => {
                    createOffer('float', currentCaptain);
                    setFloatInvokedBy(currentCaptain);
                  }}
                  disabled={pendingOffer !== null || hasUsedFloat || floatInvokedBy}
                  className="touch-optimized"
                  style={{
                    flex: 1,
                    minWidth: '80px',
                    height: '48px',
                    borderRadius: '8px',
                    background: (pendingOffer || hasUsedFloat || floatInvokedBy)
                      ? '#e0e0e0'
                      : 'linear-gradient(135deg, #FF9800, #F57C00)',
                    border: 'none',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    color: (pendingOffer || hasUsedFloat || floatInvokedBy) ? '#9e9e9e' : 'white',
                    cursor: (pendingOffer || hasUsedFloat || floatInvokedBy) ? 'not-allowed' : 'pointer',
                    boxShadow: (pendingOffer || hasUsedFloat || floatInvokedBy)
                      ? 'none'
                      : '0 2px 8px rgba(255, 152, 0, 0.3)',
                    transition: 'all 0.2s'
                  }}
                  title={hasUsedFloat ? 'Float already used this round' : floatInvokedBy ? 'Float already invoked this hole' : 'Captain doubles the wager'}
                >
                  {isFloatPending ? 'Pending...' : hasUsedFloat ? 'Float Used' : floatInvokedBy ? 'Floated' : 'Float'}
                </button>
              );
            })()}

            {/* High Stakes Quick Actions (shown when wager >= 8Q) */}
            {currentWager >= 8 && (
              <>
                <button
                  onClick={() => setCurrentWager(Math.floor(currentWager / 2))}
                  className="touch-optimized"
                  style={{
                    flex: '0 0 48px',
                    height: '48px',
                    borderRadius: '8px',
                    background: '#fff3e0',
                    border: '2px solid #FF9800',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    color: '#F57C00',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.2s'
                  }}
                  title="Halve the wager"
                >
                  ÷2
                </button>
                <button
                  onClick={() => setCurrentWager(nextHoleWager)}
                  className="touch-optimized"
                  style={{
                    flex: '0 0 auto',
                    padding: '0 16px',
                    height: '48px',
                    borderRadius: '8px',
                    background: theme.colors.backgroundSecondary,
                    border: `2px solid ${theme.colors.border}`,
                    fontSize: '12px',
                    fontWeight: 'bold',
                    color: theme.colors.textPrimary,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.2s'
                  }}
                  title={`Reset to base wager (${nextHoleWager}Q)`}
                >
                  Reset ({nextHoleWager}Q)
                </button>
              </>
            )}
              </>
            )}
          </div>

          {/* Turn Off Option Button - announces the action and halves the wager */}
          {optionActive && !optionTurnedOff && goatId && (
            <button
              onClick={() => {
                setOptionTurnedOff(true);
                // Halve the wager since Option was providing 2x multiplier
                setCurrentWager(Math.max(baseWager, Math.floor(currentWager / 2)));
                announceAction('option_off', goatId);
              }}
              className="touch-optimized"
              style={{
                width: '100%',
                marginTop: '8px',
                padding: '10px',
                borderRadius: '6px',
                background: 'linear-gradient(135deg, #f44336, #d32f2f)',
                border: 'none',
                fontSize: '13px',
                color: 'white',
                cursor: 'pointer',
                fontWeight: 'bold',
                boxShadow: '0 2px 8px rgba(244, 67, 54, 0.3)'
              }}
            >
              {getPlayerName(goatId)} Turns Off Option (Halve Wager)
            </button>
          )}
        </div>
        );
      })()}

      {/* Advanced Betting Rules Accordion */}
      <div style={{
        background: theme.colors.paper,
        borderRadius: '8px',
        marginBottom: '12px',
        border: `1px solid ${theme.colors.border}`,
        overflow: 'hidden'
      }}>
        <button
          onClick={() => setShowAdvancedBetting(!showAdvancedBetting)}
          style={{
            width: '100%',
            padding: '12px 16px',
            background: showAdvancedBetting ? theme.colors.backgroundSecondary : 'transparent',
            border: 'none',
            fontSize: '14px',
            fontWeight: 'bold',
            color: theme.colors.textPrimary,
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <span>Advanced Betting Rules</span>
          <span style={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            {showAdvancedBetting ? '▲' : '▼'} Double, Float, Option, etc.
          </span>
        </button>
      </div>

      {showAdvancedBetting && (
        <>
      {/* Betting History Panel */}
      <div style={{
        background: theme.colors.paper,
        borderRadius: '8px',
        marginBottom: '12px',
        border: `1px solid ${theme.colors.border}`,
        overflow: 'hidden'
      }}>
        {/* Toggle Header */}
        <button
          onClick={() => setShowBettingHistory(!showBettingHistory)}
          style={{
            width: '100%',
            padding: '12px 16px',
            background: showBettingHistory ? theme.colors.backgroundSecondary : 'transparent',
            border: 'none',
            borderBottom: showBettingHistory ? `1px solid ${theme.colors.border}` : 'none',
            fontSize: '14px',
            fontWeight: 'bold',
            color: theme.colors.textPrimary,
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <span>📜 Betting History</span>
          <span style={{ fontSize: '12px', color: theme.colors.textSecondary }}>
            {showBettingHistory ? '▲' : '▼'} {bettingHistory.length} events
          </span>
        </button>

        {/* History Content */}
        {showBettingHistory && (
          <div style={{ padding: '12px' }}>
            {/* Tab Buttons */}
            <div style={{
              display: 'flex',
              borderBottom: `2px solid ${theme.colors.border}`,
              marginBottom: '12px'
            }}>
              {[
                { key: 'current', label: 'Current Hole' },
                { key: 'last', label: 'Last Hole' },
                { key: 'game', label: 'Full Game' }
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setHistoryTab(tab.key)}
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    background: historyTab === tab.key ? theme.colors.primary : 'transparent',
                    color: historyTab === tab.key ? 'white' : theme.colors.textPrimary,
                    border: 'none',
                    borderRadius: '6px 6px 0 0',
                    fontSize: '12px',
                    fontWeight: historyTab === tab.key ? 'bold' : 'normal',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Event List */}
            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
              {(() => {
                const filteredEvents = bettingHistory.filter(event => {
                  if (historyTab === 'current') return event.hole === currentHole;
                  if (historyTab === 'last') return event.hole === currentHole - 1;
                  return true; // 'game' shows all
                });

                if (filteredEvents.length === 0) {
                  return (
                    <div style={{
                      textAlign: 'center',
                      padding: '20px',
                      color: theme.colors.textSecondary,
                      fontSize: '13px'
                    }}>
                      No events yet
                    </div>
                  );
                }

                return filteredEvents.slice().reverse().map(event => (
                  <div
                    key={event.eventId}
                    style={{
                      padding: '10px 12px',
                      background: theme.colors.background,
                      borderRadius: '6px',
                      marginBottom: '8px',
                      borderLeft: `4px solid ${
                        event.eventType === 'Double' ? '#4CAF50' :
                        event.eventType === 'Hole Completed' ? '#2196F3' :
                        theme.colors.primary
                      }`
                    }}
                  >
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start'
                    }}>
                      <div>
                        <div style={{
                          fontWeight: 'bold',
                          fontSize: '13px',
                          color: theme.colors.textPrimary,
                          marginBottom: '2px'
                        }}>
                          {event.eventType}
                          {event.eventType === 'Double' && event.details?.to && (
                            <span style={{ fontWeight: 'normal', marginLeft: '6px' }}>
                              → {event.details.to}Q
                            </span>
                          )}
                        </div>
                        <div style={{
                          fontSize: '11px',
                          color: theme.colors.textSecondary
                        }}>
                          {event.actor} • Hole {event.hole}
                        </div>
                      </div>
                      <div style={{
                        fontSize: '10px',
                        color: theme.colors.textSecondary
                      }}>
                        {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </div>
                ));
              })()}
            </div>
          </div>
        )}
      </div>

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
        </>
      )}

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

        {/* The Duncan - Announcement button (only shown in Solo mode) */}
        {teamMode === 'solo' && (
          <div style={{
            marginTop: '12px',
            padding: '12px',
            background: duncanInvoked ? '#E1BEE7' : '#F3E5F5',
            borderRadius: '8px',
            border: `2px solid ${duncanInvoked ? '#7B1FA2' : '#9C27B0'}`
          }}>
            <button
              onClick={() => {
                const newValue = !duncanInvoked;
                setDuncanInvoked(newValue);
                if (newValue && captain) {
                  announceAction('duncan', captain);
                }
              }}
              className="touch-optimized"
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '8px',
                background: duncanInvoked
                  ? 'linear-gradient(135deg, #7B1FA2, #6A1B9A)'
                  : 'linear-gradient(135deg, #9C27B0, #7B1FA2)',
                border: 'none',
                fontSize: '14px',
                fontWeight: 'bold',
                color: 'white',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(156, 39, 176, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              {duncanInvoked ? (
                <>✓ Duncan Called - 3-for-2 Payout</>
              ) : (
                <>🏆 Call The Duncan (Solo before hitting)</>
              )}
            </button>
            {duncanInvoked && (
              <div style={{
                marginTop: '8px',
                fontSize: '12px',
                color: '#6A1B9A',
                textAlign: 'center'
              }}>
                Captain goes solo before hitting. Click again to cancel.
              </div>
            )}
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
            {players.length === 5
              ? 'Click to select 2 or 3 players for Team 1. The rest will be Team 2.'
              : 'Click players to add them to Team 1. Remaining players will automatically be Team 2.'}
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

            {/* 5-Man Aardvark UI */}
            {players.length === 5 && team1.length >= 2 && (
              <div style={{
                marginTop: '16px',
                padding: '12px',
                background: 'linear-gradient(135deg, #E1F5FE, #B3E5FC)',
                borderRadius: '8px',
                border: '2px solid #03A9F4'
              }}>
                <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#01579B' }}>
                  🦡 Aardvark (5th Player: {players[4]?.name})
                </div>
                <div style={{ fontSize: '13px', color: '#0277BD', marginBottom: '12px' }}>
                  The Aardvark can request to join a team. If rejected ("tossed"), they join the other team and risk doubles.
                </div>

                {!aardvarkSolo ? (
                  <>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
                      <button
                        onClick={() => { setAardvarkRequestedTeam('team1'); setAardvarkTossed(false); }}
                        style={{
                          padding: '10px 16px',
                          fontSize: '14px',
                          fontWeight: 'bold',
                          border: aardvarkRequestedTeam === 'team1' && !aardvarkTossed ? '3px solid #00bcd4' : '2px solid #90CAF9',
                          borderRadius: '8px',
                          background: aardvarkRequestedTeam === 'team1' && !aardvarkTossed ? 'rgba(0, 188, 212, 0.2)' : 'white',
                          cursor: 'pointer'
                        }}
                      >
                        Request Team 1 ✓
                      </button>
                      <button
                        onClick={() => { setAardvarkRequestedTeam('team2'); setAardvarkTossed(false); }}
                        style={{
                          padding: '10px 16px',
                          fontSize: '14px',
                          fontWeight: 'bold',
                          border: aardvarkRequestedTeam === 'team2' && !aardvarkTossed ? '3px solid #ff9800' : '2px solid #90CAF9',
                          borderRadius: '8px',
                          background: aardvarkRequestedTeam === 'team2' && !aardvarkTossed ? 'rgba(255, 152, 0, 0.2)' : 'white',
                          cursor: 'pointer'
                        }}
                      >
                        Request Team 2 ✓
                      </button>
                    </div>

                    {aardvarkRequestedTeam && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={aardvarkTossed}
                            onChange={(e) => setAardvarkTossed(e.target.checked)}
                            style={{ width: '18px', height: '18px' }}
                          />
                          <span style={{ fontWeight: 'bold', color: '#d32f2f' }}>
                            ❌ Tossed! (Risk doubles, joins other team)
                          </span>
                        </label>
                      </div>
                    )}

                    <button
                      onClick={() => setAardvarkSolo(true)}
                      style={{
                        marginTop: '12px',
                        padding: '8px 14px',
                        fontSize: '13px',
                        border: '2px solid #9C27B0',
                        borderRadius: '6px',
                        background: 'rgba(156, 39, 176, 0.1)',
                        cursor: 'pointer',
                        color: '#7B1FA2'
                      }}
                    >
                      🎯 Tunkarri (Aardvark goes solo - 3 for 2)
                    </button>
                  </>
                ) : (
                  <div>
                    <div style={{ fontWeight: 'bold', color: '#7B1FA2', marginBottom: '8px' }}>
                      🎯 Tunkarri Active - Aardvark is going solo!
                    </div>
                    <div style={{ fontSize: '13px', color: '#6A1B9A', marginBottom: '8px' }}>
                      Aardvark plays alone vs both teams. Wins 3Q for every 2Q wagered if best net score.
                    </div>
                    <button
                      onClick={() => setAardvarkSolo(false)}
                      style={{
                        padding: '6px 12px',
                        fontSize: '12px',
                        border: '1px solid #9C27B0',
                        borderRadius: '4px',
                        background: 'white',
                        cursor: 'pointer'
                      }}
                    >
                      Cancel Tunkarri
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* 4-Man Invisible Aardvark UI */}
            {players.length === 4 && team1.length === 2 && (
              <div style={{
                marginTop: '16px',
                padding: '12px',
                background: 'linear-gradient(135deg, #FFF3E0, #FFE0B2)',
                borderRadius: '8px',
                border: '2px dashed #FF9800'
              }}>
                <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#E65100' }}>
                  👻 Invisible Aardvark
                </div>
                <div style={{ fontSize: '13px', color: '#EF6C00', marginBottom: '12px' }}>
                  The Invisible Aardvark automatically joins Team 2 (the "forcibly formed" team).
                  Team 2 can "toss" it to double the wager (3 for 2 if they win).
                </div>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={invisibleAardvarkTossed}
                    onChange={(e) => setInvisibleAardvarkTossed(e.target.checked)}
                    style={{ width: '20px', height: '20px' }}
                  />
                  <span style={{ fontWeight: 'bold', color: invisibleAardvarkTossed ? '#d32f2f' : '#5D4037' }}>
                    {invisibleAardvarkTossed ? '❌ Invisible Aardvark TOSSED! (Wager doubled, 3 for 2)' : 'Toss the Invisible Aardvark?'}
                  </span>
                </label>
              </div>
            )}
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

      {/* Quarters Entry (Primary) */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px',
        border: '2px solid #4CAF50'
      }}>
        <h3 style={{ margin: '0 0 4px' }}>Quarters</h3>
        <div style={{ fontSize: '12px', color: theme.colors.textSecondary, marginBottom: '12px' }}>
          Must sum to zero: {(() => {
            const sum = players.reduce((acc, p) => acc + (parseFloat(quarters[p.id]) || 0), 0);
            const color = Math.abs(sum) < 0.001 ? '#4CAF50' : '#f44336';
            const displaySum = Math.abs(sum) < 0.001 ? '0' : (sum > 0 ? '+' : '') + sum.toFixed(2);
            return <span style={{ fontWeight: 'bold', color }}>{displaySum}</span>;
          })()}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
          {players.map(player => (
            <div key={player.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ flex: 1, fontWeight: 'bold' }}>
                {player.name}
                :
              </label>
              <Input
                data-testid={`quarters-input-${player.id}`}
                type="number"
                inputMode="decimal"
                step="any"
                value={quarters[player.id] ?? ''}
                onChange={(e) => setQuarters(prev => ({ ...prev, [player.id]: e.target.value }))}
                variant="inline"
                inputStyle={{
                  width: '80px',
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

      {/* Scores (Optional) */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 4px' }}>
          Golf Scores <span style={{ fontWeight: 'normal', fontSize: '14px', color: theme.colors.textSecondary }}>(optional)</span>
        </h3>
        <div style={{ fontSize: '12px', color: theme.colors.textSecondary, marginBottom: '12px' }}>
          Enter strokes for tracking only
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
          {players.map(player => (
            <div key={player.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ flex: 1, fontWeight: 'bold' }}>
                {player.name}
                :
              </label>
              <Input
                data-testid={`score-input-${player.id}`}
                type="number"
                inputMode="numeric"
                pattern="[0-9]*"
                min="0"
                max="15"
                value={scores[player.id] || ''}
                onChange={(e) => handleScoreChange(player.id, e.target.value)}
                variant="inline"
                inputStyle={{
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

      {/* Error Display with Helpful Guidance */}
      {error && (
        <div style={{
          background: error.includes('💡') ? '#FFF3E0' : theme.colors.error,
          color: error.includes('💡') ? '#E65100' : 'white',
          padding: '16px',
          borderRadius: '8px',
          marginBottom: '20px',
          border: error.includes('💡') ? '2px solid #FF9800' : 'none'
        }}>
          {error.includes('💡') ? (
            <>
              <div style={{ fontWeight: 'bold', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '20px' }}>⚠️</span>
                {error.split('\n\n')[0]}
              </div>
              <div style={{
                background: 'rgba(255, 152, 0, 0.1)',
                padding: '12px',
                borderRadius: '6px',
                fontSize: '14px',
                lineHeight: '1.5'
              }}>
                {error.split('\n\n')[1]}
              </div>
              <button
                onClick={() => setError(null)}
                style={{
                  marginTop: '12px',
                  padding: '8px 16px',
                  background: '#FF9800',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                Got it, let me fix this
              </button>
            </>
          ) : (
            <div style={{ textAlign: 'center' }}>{error}</div>
          )}
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
              <Input
                type="text"
                value={editPlayerNameValue}
                onChange={(e) => setEditPlayerNameValue(e.target.value)}
                placeholder="Enter player name"
                maxLength="50"
                autoFocus
                variant="inline"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleSavePlayerName();
                  }
                }}
                inputStyle={{
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

SimpleScorekeeper.propTypes = {
  gameId: PropTypes.string.isRequired,
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    handicap: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    user_id: PropTypes.string,
  })).isRequired,
  baseWager: PropTypes.number,
  initialHoleHistory: PropTypes.arrayOf(PropTypes.object),
  initialCurrentHole: PropTypes.number,
  courseName: PropTypes.string,
  initialStrokeAllocation: PropTypes.object,
};

export default SimpleScorekeeper;
