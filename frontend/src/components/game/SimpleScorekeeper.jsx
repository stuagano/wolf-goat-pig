// frontend/src/components/game/SimpleScorekeeper.jsx
// Updated: Offline-first sync for unreliable golf course connectivity
// Refactored: Using custom hooks for state management (incremental migration)
import React, { useState, useEffect, useMemo, useReducer, useCallback } from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../theme/Provider';
import { Input } from '../ui';
import GameCompletionView from './GameCompletionView';
import Scorecard from './Scorecard';
import ShotAnalysisWidget from './ShotAnalysisWidget';
import BettingOddsPanel from '../BettingOddsPanel';
import CommissionerChat from '../CommissionerChat';
import { triggerBadgeNotification } from '../BadgeNotification';
import { SyncStatusBanner } from '../SyncStatusIndicator';
import { useHoleSync, useUIState, useBettingState } from '../../hooks';
import { gameReducer, createInitialState, gameActions } from './gameReducer';
import syncManager from '../../services/syncManager';
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
 * Reusable styles for hitting order arrow buttons
 */
const ARROW_BUTTON_STYLE = {
  background: 'rgba(255,255,255,0.3)',
  border: 'none',
  borderRadius: '50%',
  width: '22px',
  height: '22px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  cursor: 'pointer',
  fontSize: '12px',
  padding: '0'
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
  
  // UI state management (refactored to custom hook)
  const ui = useUIState();

  // ============================================================
  // GAME STATE - Using useReducer for consolidated state management
  // ============================================================
  
  // Try to restore from local storage first (survives page refresh)
  const restoredState = useMemo(() => {
    const localState = syncManager.loadLocalGameState(gameId);
    if (localState?.holeHistory && localState.holeHistory.length > initialHoleHistory.length) {
      console.log('[Scorekeeper] Restored from local storage:', localState.holeHistory.length, 'holes');
      return localState;
    }
    return null;
  }, [gameId, initialHoleHistory.length]);

  // Initialize game state reducer
  const [gameState, dispatch] = useReducer(
    gameReducer,
    { baseWager, initialCurrentHole, initialHoleHistory, players, restoredState },
    createInitialState
  );

  // Destructure game state for convenience (maintains existing variable names)
  const { hole, teams, betting: bettingState, rotation, aardvark, history } = gameState;
  
  // Hole state
  const currentHole = hole.currentHole;
  const scores = hole.scores;
  const quarters = hole.quarters;
  const holeNotes = hole.notes;
  const winner = hole.winner;
  
  // Team state
  const teamMode = teams.mode;
  const team1 = teams.team1;
  // eslint-disable-next-line no-unused-vars -- team2 computed from team1, kept for clarity
  const team2 = teams.team2;
  const captain = teams.captain;
  const opponents = teams.opponents;
  
  // Betting state (from reducer)
  const currentWager = bettingState.currentWager;
  // eslint-disable-next-line no-unused-vars -- used in resetHole, exposed for future use
  const nextHoleWager = bettingState.nextHoleWager;
  const floatInvokedBy = bettingState.floatInvokedBy;
  const optionInvokedBy = bettingState.optionInvokedBy;
  // eslint-disable-next-line no-unused-vars -- betting state, exposed for future UI
  const optionActive = bettingState.optionActive;
  // eslint-disable-next-line no-unused-vars -- betting state, exposed for future UI
  const optionTurnedOff = bettingState.optionTurnedOff;
  const duncanInvoked = bettingState.duncanInvoked;
  // eslint-disable-next-line no-unused-vars -- betting state, exposed for future UI
  const carryOver = bettingState.carryOver;
  // eslint-disable-next-line no-unused-vars -- betting state, exposed for future UI
  const vinniesVariation = bettingState.vinniesVariation;
  // eslint-disable-next-line no-unused-vars -- betting state, exposed for future UI
  const joesSpecialWager = bettingState.joesSpecialWager;
  
  // Rotation state
  const rotationOrder = rotation.order;
  const captainIndex = rotation.captainIndex;
  const isHoepfinger = rotation.isHoepfinger;
  // eslint-disable-next-line no-unused-vars -- rotation state, exposed for Hoepfinger rule UI
  const goatId = rotation.goatId;
  const phase = rotation.phase;
  
  // Aardvark state
  const aardvarkRequestedTeam = aardvark.requestedTeam;
  const aardvarkTossed = aardvark.tossed;
  const aardvarkSolo = aardvark.solo;
  const invisibleAardvarkTossed = aardvark.invisibleTossed;
  
  // History state
  const holeHistory = history.holes;
  const playerStandings = history.playerStandings;

  // ============================================================
  // ACTION DISPATCHERS - Maintain existing setter function names
  // ============================================================
  
  // Hole actions
  const setCurrentHole = useCallback((h) => dispatch(gameActions.setCurrentHole(h)), []);
  const setScores = useCallback((s) => dispatch(gameActions.setScores(s)), []);
  const setQuarters = useCallback((q) => dispatch(gameActions.setQuarters(q)), []);
  const setHoleNotes = useCallback((n) => dispatch(gameActions.setHoleNotes(n)), []);
  const setWinner = useCallback((w) => dispatch(gameActions.setWinner(w)), []);
  
  // Team actions
  const setTeamMode = useCallback((m) => dispatch(gameActions.setTeamMode(m)), []);
  const setTeam1 = useCallback((t) => dispatch(gameActions.setTeam1(t)), []);
  const setTeam2 = useCallback((t) => dispatch(gameActions.setTeam2(t)), []);
  const setCaptain = useCallback((c) => dispatch(gameActions.setCaptain(c)), []);
  const setOpponents = useCallback((o) => dispatch(gameActions.setOpponents(o)), []);
  
  // Betting actions
  const setCurrentWager = useCallback((w) => dispatch(gameActions.setCurrentWager(w)), []);
  const setNextHoleWager = useCallback((w) => dispatch(gameActions.setNextHoleWager(w)), []);
  const setFloatInvokedBy = useCallback((p) => dispatch(gameActions.setFloatInvokedBy(p)), []);
  const setOptionInvokedBy = useCallback((p) => dispatch(gameActions.setOptionInvokedBy(p)), []);
  const setOptionActive = useCallback((a) => dispatch(gameActions.setOptionActive(a)), []);
  const setOptionTurnedOff = useCallback((o) => dispatch(gameActions.setOptionTurnedOff(o)), []);
  const setDuncanInvoked = useCallback((d) => dispatch(gameActions.setDuncanInvoked(d)), []);
  const setCarryOver = useCallback((c) => dispatch(gameActions.setCarryOver(c)), []);
  const setVinniesVariation = useCallback((v) => dispatch(gameActions.setVinniesVariation(v)), []);
  const setJoesSpecialWager = useCallback((w) => dispatch(gameActions.setJoesSpecialWager(w)), []);
  
  // Rotation actions
  const setRotationOrder = useCallback((o) => dispatch(gameActions.setRotationOrder(o)), []);
  const setCaptainIndex = useCallback((i) => dispatch(gameActions.setCaptainIndex(i)), []);
  const setIsHoepfinger = useCallback((h) => dispatch(gameActions.setIsHoepfinger(h)), []);
  const setGoatId = useCallback((id) => dispatch(gameActions.setGoatId(id)), []);
  const setPhase = useCallback((p) => dispatch(gameActions.setPhase(p)), []);
  
  // Aardvark actions
  const setAardvarkRequestedTeam = useCallback((t) => dispatch(gameActions.setAardvarkRequestedTeam(t)), []);
  const setAardvarkTossed = useCallback((t) => dispatch(gameActions.setAardvarkTossed(t)), []);
  const setAardvarkSolo = useCallback((s) => dispatch(gameActions.setAardvarkSolo(s)), []);
  const setInvisibleAardvarkTossed = useCallback((t) => dispatch(gameActions.setInvisibleAardvarkTossed(t)), []);
  
  // History actions
  const setHoleHistory = useCallback((h) => dispatch(gameActions.setHoleHistory(h)), []);
  const setPlayerStandings = useCallback((s) => dispatch(gameActions.setPlayerStandings(s)), []);
  
  // ============================================================
  // BETTING STATE HOOK - Interactive betting (offers, events)
  // ============================================================
  
  const betting = useBettingState({
    currentHole,
    currentWager,
    setCurrentWager,
    players,
  });
  
  // Destructure commonly used betting state
  // Only destructure what's currently used - full API available via `betting` object
  const {
    currentHoleBettingEvents, setCurrentHoleBettingEvents,
    setPendingOffer,
    addBettingEvent,
    logBettingAction,
    getPlayerName,
  } = betting;
  // Additional betting features available: betting.bettingHistory, betting.createOffer, 
  // betting.respondToOffer, betting.showBettingHistory, betting.historyTab, betting.pendingOffer

  // UI state (migrated to useUIState hook)
  // Destructure commonly used UI state for convenience
  const {
    submitting, setSubmitting,
    error, setError,
    showTeamSelection, setShowTeamSelection,
    showGolfScores, setShowGolfScores,
    showCommissioner, setShowCommissioner,
    showNotes, setShowNotes,
    showSpecialActions, setShowSpecialActions,
    showUsageStats, setShowUsageStats,
    // eslint-disable-next-line no-unused-vars -- UI state, exposed for advanced betting accordion
    showAdvancedBetting, setShowAdvancedBetting,
    showShotAnalysis, setShowShotAnalysis,
    showBettingOdds, setShowBettingOdds,
    editingHole, setEditingHole,
    editingPlayerName,
    editPlayerNameValue, setEditPlayerNameValue,
    isEditingCompleteGame, setIsEditingCompleteGame,
    isGameMarkedComplete, setIsGameMarkedComplete,
    startEditingPlayerName,
    cancelEditingPlayerName: handleCancelPlayerNameEdit,
  } = ui;
  
  // Offline-first sync hook
  // eslint-disable-next-line no-unused-vars -- sync state exposed for future offline indicator UI
  const { syncHole, pendingCount, isOnline, lastError: syncError } = useHoleSync(gameId);
  const [localPlayers, setLocalPlayers] = useState(players); // Local copy of players for immediate UI updates
  const [courseData, setCourseData] = useState(null); // Course data with hole information
  const [editingOrder, setEditingOrder] = useState(false); // Track if user is editing hitting order
  const [expandedPlayers, setExpandedPlayers] = useState({ 0: true }); // Track which player cards are expanded (first player by default)

  // Betting state (bettingHistory, pendingOffer, currentHoleBettingEvents) migrated to useBettingState hook

  // Derive current hole par from course data (pars are constants and don't change)
  // No defaults - only use actual course data
  const holePar = courseData?.holes?.find(h => h.hole_number === currentHole)?.par;

  // Track course data loading state
  const [courseDataError, setCourseDataError] = useState(null);
  const [courseDataLoading, setCourseDataLoading] = useState(false);

  // Auto-collapse team selection when teams are set
  // Team selection stays visible so players can see teams during the hole
  // (Auto-collapse removed per user request)

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

  // Save game state locally whenever holeHistory changes (survives page refresh)
  useEffect(() => {
    if (gameId && holeHistory.length > 0) {
      syncManager.saveLocalGameState(gameId, {
        holeHistory,
        currentHole,
        playerStandings,
      });
    }
  }, [gameId, holeHistory, currentHole, playerStandings]);

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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- setPlayerStandings is stable (useCallback)
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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- setters are stable (useCallback), only trigger on data changes
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
    setHoleNotes('');
    setWinner(null);
    setFloatInvokedBy(null);
    setOptionInvokedBy(null);
    setError(null);
    setEditingHole(null);
    // carryOverApplied state removed (was unused)
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
    setHoleNotes(hole.notes || '');
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

  // Betting functions (logBettingAction, getPlayerName, addBettingEvent, createOffer, respondToOffer)
  // are now provided by useBettingState hook

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
  // eslint-disable-next-line no-unused-vars -- betting narrative for future betting history UI
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

    // Safe array bounds: ensure we have values before calling Math.min
    const handicapValues = Object.values(playerHandicaps);
    const lowestHandicap = handicapValues.length > 0 ? Math.min(...handicapValues) : 0;

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
      // Safe array bounds: filter undefined values and provide fallback
      const team1Scores = team1.map(id => netScores[id]).filter(s => s !== undefined);
      const team2Scores = team2Ids.map(id => netScores[id]).filter(s => s !== undefined);
      team1Net = team1Scores.length > 0 ? Math.min(...team1Scores) : 0;
      team2Net = team2Scores.length > 0 ? Math.min(...team2Scores) : 0;
    } else {
      // Solo mode: captain vs opponents
      team1Net = netScores[captain] ?? 0; // Captain's net score with fallback
      // Safe array bounds for opponents
      const opponentScores = opponents.map(id => netScores[id]).filter(s => s !== undefined);
      team2Net = opponentScores.length > 0 ? Math.min(...opponentScores) : 0;
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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- setWinner is stable (useCallback)
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
        quarters_only: true,
        notes: holeNotes || null
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

      // Sync to backend using offline-first approach
      // This will queue the sync if offline or on slow connection
      const syncResult = await syncHole(
        holeQuarters,
        optionalDetails,
        editingHole ? currentHole : currentHole + 1
      );

      // Handle permanent errors (like validation failures)
      if (!syncResult.success && syncResult.permanent) {
        const rawError = syncResult.error || 'Failed to save quarters';
        
        // Handle zero-sum validation error from backend
        if (rawError.includes('Zero-sum validation failed')) {
          throw new Error(`Quarters don't balance!\n\n${rawError}\n\n💡 Each hole must sum to zero. Check the wager and winner settings.`);
        }

        throw new Error(rawError);
      }
      
      // If queued for later sync, that's still a success - data is saved locally
      // The UI will show pending sync indicator

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

  // Handle player name editing - uses useUIState hook
  // eslint-disable-next-line no-unused-vars
  const handlePlayerNameClick = (playerId, currentName) => {
    startEditingPlayerName(playerId, currentName);
  };

  // Handle reordering hitting order
  const movePlayerInOrder = async (fromIndex, direction) => {
    const toIndex = fromIndex + direction;
    if (toIndex < 0 || toIndex >= rotationOrder.length) return;

    const newOrder = [...rotationOrder];
    [newOrder[fromIndex], newOrder[toIndex]] = [newOrder[toIndex], newOrder[fromIndex]];

    // Update local state immediately for responsive UI
    setRotationOrder(newOrder);

    // Persist to backend
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/games/${gameId}/tee-order`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_order: newOrder })
      });

      if (!response.ok) {
        throw new Error('Failed to update hitting order');
      }
    } catch (error) {
      console.error('Error updating hitting order:', error);
      // Revert on error
      setRotationOrder(rotationOrder);
    }
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
      handleCancelPlayerNameEdit();
    } catch (err) {
      console.error('Failed to update player name:', err);
      alert('Failed to update player name. Please try again.');
    }
  };

  // handleCancelPlayerNameEdit is now provided by useUIState hook

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
  // This is called when user clicks a cell and saves in the Scorecard modal
  const handleEditHoleFromScorecard = ({ hole, playerId, strokes, quarters }) => {
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

      // Load this hole into edit mode with updated values
      loadHoleForEdit({ ...holeData, gross_scores: updatedScores, points_delta: updatedPointsDelta });
    }
  };

  // Direct hole jump - load any hole for editing
  const jumpToHole = (holeNumber) => {
    const holeData = holeHistory.find(h => h.hole === holeNumber);
    if (holeData) {
      loadHoleForEdit(holeData);
    } else {
      setCurrentHole(holeNumber);
      resetHole();
    }
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
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
        courseHoles={courseData?.holes || []}
        strokeAllocation={strokeAllocation}
      />
    );
  }

  return (
    <div data-testid="scorekeeper-container" className="thumb-zone-container" style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      {/* Sync Status Banner - Shows when offline or pending uploads */}
      <SyncStatusBanner />
      
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

        {/* Quick Hole Navigation - Shows completed holes as clickable chips */}
        {holeHistory.length > 0 && (
          <div style={{
            marginTop: '8px',
            padding: '8px',
            background: theme.colors.backgroundSecondary,
            borderRadius: '8px'
          }}>
            <div style={{ fontSize: '11px', color: theme.colors.textSecondary, marginBottom: '6px' }}>
              Tap any hole to edit:
            </div>
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
              {Array.from({ length: Math.max(currentHole - 1, holeHistory.length) }, (_, i) => i + 1).map(hole => {
                const holeData = holeHistory.find(h => h.hole === hole);
                const isEditing = editingHole === hole;
                return (
                  <button
                    key={hole}
                    onClick={() => holeData ? loadHoleForEdit(holeData) : jumpToHole(hole)}
                    className="touch-optimized"
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '6px',
                      border: isEditing ? `2px solid ${theme.colors.warning}` : holeData ? `1px solid ${theme.colors.primary}` : `1px solid ${theme.colors.border}`,
                      background: isEditing ? theme.colors.warning : holeData ? 'white' : '#f5f5f5',
                      color: isEditing ? 'white' : holeData ? theme.colors.primary : theme.colors.textSecondary,
                      fontSize: '13px',
                      fontWeight: 'bold',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    {hole}
                  </button>
                );
              })}
            </div>
            
            {/* Undo last hole button */}
            <button
              onClick={() => {
                if (window.confirm(`Undo hole ${holeHistory[holeHistory.length - 1].hole}? This will remove all data for that hole.`)) {
                  const lastHole = holeHistory[holeHistory.length - 1];
                  setHoleHistory(prev => prev.slice(0, -1));
                  setCurrentHole(lastHole.hole);
                  const newStandings = { ...playerStandings };
                  players.forEach(p => {
                    const delta = lastHole.points_delta?.[p.id] || 0;
                    if (newStandings[p.id]) {
                      newStandings[p.id] = {
                        ...newStandings[p.id],
                        quarters: (newStandings[p.id].quarters || 0) - delta
                      };
                    }
                  });
                  setPlayerStandings(newStandings);
                  resetHole();
                }
              }}
              className="touch-optimized"
              style={{
                marginTop: '8px',
                padding: '6px 12px',
                fontSize: '12px',
                border: '1px solid #f44336',
                borderRadius: '6px',
                background: 'white',
                color: '#f44336',
                cursor: 'pointer'
              }}
            >
              ↩️ Undo Last Hole
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
              {/* Left: Hole Number with Selector */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <select
                  data-testid="hole-selector"
                  value={currentHole}
                  onChange={(e) => {
                    const selectedHole = parseInt(e.target.value, 10);
                    const holeData = holeHistory.find(h => h.hole === selectedHole);
                    if (holeData) {
                      // Load existing hole for editing
                      loadHoleForEdit(holeData);
                    } else {
                      // Jump to new hole
                      setCurrentHole(selectedHole);
                      resetHole();
                    }
                  }}
                  style={{
                    fontSize: '36px',
                    fontWeight: 'bold',
                    background: 'rgba(255,255,255,0.15)',
                    border: '2px solid rgba(255,255,255,0.3)',
                    borderRadius: '8px',
                    color: 'white',
                    padding: '4px 8px',
                    cursor: 'pointer',
                    appearance: 'none',
                    WebkitAppearance: 'none',
                    width: '70px',
                    textAlign: 'center'
                  }}
                >
                  {Array.from({ length: 18 }, (_, i) => i + 1).map(hole => {
                    const hasData = holeHistory.some(h => h.hole === hole);
                    return (
                      <option key={hole} value={hole} style={{ color: 'black' }}>
                        {hole}{hasData ? ' ✓' : ''}
                      </option>
                    );
                  })}
                </select>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                  <div style={{ fontSize: '12px', opacity: 0.9, textTransform: 'uppercase' }}>
                    Hole
                  </div>
                  {editingHole && (
                    <div style={{ fontSize: '10px', background: 'rgba(255,152,0,0.8)', padding: '2px 6px', borderRadius: '4px', marginTop: '2px' }}>
                      Editing
                    </div>
                  )}
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
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px'
                }}>
                  <div style={{
                    fontSize: '10px',
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                    opacity: 0.8
                  }}>
                    Hitting Order
                  </div>
                  <button
                    onClick={() => setEditingOrder(!editingOrder)}
                    style={{
                      background: editingOrder ? theme.colors.primary : 'rgba(255,255,255,0.2)',
                      color: 'white',
                      border: 'none',
                      borderRadius: '12px',
                      padding: '4px 10px',
                      fontSize: '11px',
                      fontWeight: 'bold',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    {editingOrder ? '✓ Done' : '✏️ Edit'}
                  </button>
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
                        {editingOrder && index > 0 && (
                          <button onClick={() => movePlayerInOrder(index, -1)} style={ARROW_BUTTON_STYLE}>
                            ▲
                          </button>
                        )}
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
                            marginLeft: '2px'
                          }}>
                            ◐
                          </span>
                        )}
                        {editingOrder && index < rotationOrder.length - 1 && (
                          <button onClick={() => movePlayerInOrder(index, 1)} style={ARROW_BUTTON_STYLE}>
                            ▼
                          </button>
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


      {/* Float & Option Tracking - Collapsed by default */}
      <div style={{
        background: theme.colors.paper,
        borderRadius: '8px',
        marginBottom: '12px',
        border: `1px solid ${theme.colors.border}`,
        overflow: 'hidden'
      }}>
        <div
          onClick={() => setShowSpecialActions(!showSpecialActions)}
          style={{
            padding: '10px 12px',
            fontSize: '13px',
            fontWeight: 'bold',
            color: theme.colors.textSecondary,
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: theme.colors.backgroundSecondary
          }}
        >
          <span>
            Special Actions
            {(floatInvokedBy || optionInvokedBy) && (
              <span style={{ marginLeft: '8px', color: theme.colors.primary, fontSize: '12px' }}>
                (active)
              </span>
            )}
          </span>
          <span style={{ fontSize: '14px' }}>{showSpecialActions ? '▼' : '▶'}</span>
        </div>

        {showSpecialActions && (
          <div style={{ padding: '12px' }}>
            {/* Float Selection */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '13px', fontWeight: 'bold', marginBottom: '6px' }}>
                Float: <span style={{ fontWeight: 'normal', color: theme.colors.textSecondary }}>(one-time per player)</span>
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {players.map(player => {
                  const hasUsedFloat = playerStandings[player.id]?.floatCount >= 1;
                  return (
                    <button
                      key={player.id}
                      onClick={() => setFloatInvokedBy(floatInvokedBy === player.id ? null : player.id)}
                      className="touch-optimized"
                      disabled={hasUsedFloat}
                      style={{
                        padding: '6px 12px',
                        fontSize: '13px',
                        border: `2px solid ${floatInvokedBy === player.id ? theme.colors.primary : hasUsedFloat ? '#ccc' : theme.colors.border}`,
                        borderRadius: '6px',
                        background: floatInvokedBy === player.id ? theme.colors.primary : hasUsedFloat ? '#f5f5f5' : 'white',
                        color: floatInvokedBy === player.id ? 'white' : hasUsedFloat ? '#999' : theme.colors.text,
                        cursor: hasUsedFloat ? 'not-allowed' : 'pointer',
                        opacity: hasUsedFloat ? 0.6 : 1
                      }}
                    >
                      {player.name.split(' ')[0]}{hasUsedFloat && ' ✓'}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Option Selection */}
            <div>
              <div style={{ fontSize: '13px', fontWeight: 'bold', marginBottom: '6px' }}>
                Option Triggered:
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {players.map(player => (
                  <button
                    key={player.id}
                    onClick={() => setOptionInvokedBy(optionInvokedBy === player.id ? null : player.id)}
                    className="touch-optimized"
                    style={{
                      padding: '6px 12px',
                      fontSize: '13px',
                      border: `2px solid ${optionInvokedBy === player.id ? theme.colors.warning : theme.colors.border}`,
                      borderRadius: '6px',
                      background: optionInvokedBy === player.id ? theme.colors.warning : 'white',
                      color: optionInvokedBy === player.id ? 'white' : theme.colors.text,
                      cursor: 'pointer'
                    }}
                  >
                    {player.name.split(' ')[0]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
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

      {/* Betting Odds - Collapsible */}
      <div style={{
        background: theme.colors.paper,
        borderRadius: '8px',
        marginBottom: '12px',
        border: `1px solid ${theme.colors.border}`,
        overflow: 'hidden'
      }}>
        <div
          onClick={() => setShowBettingOdds(!showBettingOdds)}
          style={{
            padding: '10px 12px',
            fontSize: '13px',
            fontWeight: 'bold',
            color: theme.colors.textSecondary,
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: theme.colors.backgroundSecondary
          }}
        >
          <span>📊 Real-Time Odds</span>
          <span style={{ fontSize: '14px' }}>{showBettingOdds ? '▼' : '▶'}</span>
        </div>
        {showBettingOdds && (
          <div style={{ padding: '12px' }}>
            <BettingOddsPanel 
              gameState={{
                active: true,
                current_hole: currentHole,
                players: players.map(p => ({
                  ...p,
                  current_score: scores[p.id] || 0,
                  shots_taken: scores[p.id] || 0, // Simplified
                  distance_to_pin: 0, // Would need manual entry or GPS
                  lie_type: 'fairway',
                  is_captain: p.id === captain,
                  team_id: team1.includes(p.id) ? 'team1' : (teamMode === 'partners' ? 'team2' : null)
                })),
                teams: { type: teamMode },
                current_wager: currentWager,
                is_doubled: false, // Need to track this from betting events
                current_hole_par: holePar || 4
              }}
              onBettingAction={(scenario) => {
                console.log('Suggested betting action:', scenario);
                // Integration with actual betting state would go here
              }}
            />
          </div>
        )}
      </div>

      {/* Shot Analysis - Collapsible */}
      <div style={{
        background: theme.colors.paper,
        borderRadius: '8px',
        marginBottom: '12px',
        border: `1px solid ${theme.colors.border}`,
        overflow: 'hidden'
      }}>
        <div
          onClick={() => setShowShotAnalysis(!showShotAnalysis)}
          style={{
            padding: '10px 12px',
            fontSize: '13px',
            fontWeight: 'bold',
            color: theme.colors.textSecondary,
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: theme.colors.backgroundSecondary
          }}
        >
          <span>🎯 Shot Recommendations</span>
          <span style={{ fontSize: '14px' }}>{showShotAnalysis ? '▼' : '▶'}</span>
        </div>
        {showShotAnalysis && (
          <div style={{ padding: '12px' }}>
            <ShotAnalysisWidget 
              holeNumber={currentHole}
              players={players}
              captainId={captain}
              teamMode={teamMode}
              playerStandings={playerStandings}
              initialDistance={courseData?.holes?.find(h => h.hole_number === currentHole)?.yards || 150}
            />
          </div>
        )}
      </div>

      {/* Team Mode Selection - Enhanced Style */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        border: `1px solid ${theme.colors.border}`,
        transition: 'box-shadow 0.2s ease',
        borderLeft: `4px solid ${theme.colors.primary}`
      }}>
        <h3 style={{
          margin: '0 0 16px',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          fontSize: '12px',
          fontWeight: 'bold',
          color: theme.colors.textPrimary
        }}>Team Mode</h3>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => setTeamMode('partners')}
            className="touch-optimized"
            style={{
              flex: 1,
              padding: '12px 20px',
              fontSize: '16px',
              fontWeight: 'bold',
              border: teamMode === 'partners' ? `2px solid ${theme.colors.primary}` : `1px solid ${theme.colors.border}`,
              borderRadius: '8px',
              background: teamMode === 'partners' ? theme.colors.primary : 'white',
              color: teamMode === 'partners' ? 'white' : theme.colors.textPrimary,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              boxShadow: teamMode === 'partners' ? '0 2px 4px rgba(0,0,0,0.1)' : 'none'
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
              padding: '12px 20px',
              fontSize: '16px',
              fontWeight: 'bold',
              border: teamMode === 'solo' ? `2px solid ${theme.colors.primary}` : `1px solid ${theme.colors.border}`,
              borderRadius: '8px',
              background: teamMode === 'solo' ? theme.colors.primary : 'white',
              color: teamMode === 'solo' ? 'white' : theme.colors.textPrimary,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              boxShadow: teamMode === 'solo' ? '0 2px 4px rgba(0,0,0,0.1)' : 'none'
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

      {/* Team Selection - Collapsible */}
      <div style={{
        background: theme.colors.paper,
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3
          onClick={() => setShowTeamSelection(!showTeamSelection)}
          style={{
            margin: '0 0 8px',
            cursor: 'pointer',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <span>
            {teamMode === 'partners' ? 'Teams' : 'Captain Selection'}
            {/* Show summary when collapsed */}
            {!showTeamSelection && (
              <span style={{ fontWeight: 'normal', fontSize: '14px', color: theme.colors.textSecondary, marginLeft: '8px' }}>
                {teamMode === 'partners'
                  ? (team1.length > 0
                      ? `(Team 1: ${team1.map(id => players.find(p => p.id === id)?.name?.split(' ')[0]).join(', ')} vs Team 2)`
                      : '(tap to select)')
                  : (captain
                      ? `(⭐ ${players.find(p => p.id === captain)?.name?.split(' ')[0]} vs all)`
                      : '(tap to select)')
                }
              </span>
            )}
          </span>
          <span style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
            {showTeamSelection ? '▼' : '▶'}
          </span>
        </h3>
        {showTeamSelection && teamMode === 'partners' && (
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

        {showTeamSelection && (teamMode === 'partners' ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(3, Math.ceil(players.length / 2))}, 1fr)`, gap: '12px' }}>
              {players.map(player => {
                const inTeam1 = team1.includes(player.id);
                // inTeam2 is implicit (anyone not in team1)
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
                      background: inTeam1 ? 'rgba(0, 188, 212, 0.15)' : 'white',
                      cursor: 'pointer',
                      fontWeight: inTeam1 ? 600 : 400
                    }}
                  >
                    <PlayerName name={player.name} isAuthenticated={player.is_authenticated} />
                    {inTeam1 && ' (Team 1)'}
                  </button>
                );
              })}
            </div>

            {/* 5-Man and 6-Man Aardvark - Compact */}
            {(players.length === 5 || players.length === 6) && team1.length >= 2 && (
              <div style={{
                marginTop: '12px',
                padding: '10px',
                background: '#E3F2FD',
                borderRadius: '8px',
                border: '1px solid #90CAF9'
              }}>
                <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#1565C0', marginBottom: '8px' }}>
                  Aardvark: {players[players.length === 5 ? 4 : 5]?.name?.split(' ')[0] || 'Player ' + (players.length)}
                </div>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => { setAardvarkRequestedTeam('team1'); setAardvarkTossed(false); setAardvarkSolo(false); }}
                    style={{
                      padding: '6px 10px', fontSize: '12px',
                      border: aardvarkRequestedTeam === 'team1' && !aardvarkTossed && !aardvarkSolo ? '2px solid #00bcd4' : '1px solid #90CAF9',
                      borderRadius: '6px',
                      background: aardvarkRequestedTeam === 'team1' && !aardvarkTossed && !aardvarkSolo ? '#B2EBF2' : 'white',
                      cursor: 'pointer'
                    }}
                  >→ T1</button>
                  <button
                    onClick={() => { setAardvarkRequestedTeam('team2'); setAardvarkTossed(false); setAardvarkSolo(false); }}
                    style={{
                      padding: '6px 10px', fontSize: '12px',
                      border: aardvarkRequestedTeam === 'team2' && !aardvarkTossed && !aardvarkSolo ? '2px solid #ff9800' : '1px solid #90CAF9',
                      borderRadius: '6px',
                      background: aardvarkRequestedTeam === 'team2' && !aardvarkTossed && !aardvarkSolo ? '#FFE0B2' : 'white',
                      cursor: 'pointer'
                    }}
                  >→ T2</button>
                  <button
                    onClick={() => { setAardvarkTossed(!aardvarkTossed); }}
                    disabled={!aardvarkRequestedTeam || aardvarkSolo}
                    style={{
                      padding: '6px 10px', fontSize: '12px',
                      border: aardvarkTossed ? '2px solid #d32f2f' : '1px solid #90CAF9',
                      borderRadius: '6px',
                      background: aardvarkTossed ? '#FFCDD2' : 'white',
                      cursor: !aardvarkRequestedTeam || aardvarkSolo ? 'not-allowed' : 'pointer',
                      opacity: !aardvarkRequestedTeam || aardvarkSolo ? 0.5 : 1
                    }}
                  >Tossed</button>
                  <button
                    onClick={() => { setAardvarkSolo(!aardvarkSolo); setAardvarkTossed(false); }}
                    style={{
                      padding: '6px 10px', fontSize: '12px',
                      border: aardvarkSolo ? '2px solid #7B1FA2' : '1px solid #90CAF9',
                      borderRadius: '6px',
                      background: aardvarkSolo ? '#E1BEE7' : 'white',
                      cursor: 'pointer'
                    }}
                  >Solo</button>
                </div>
              </div>
            )}

            {/* 4-Man Invisible Aardvark - Compact */}
            {players.length === 4 && team1.length === 2 && (
              <div style={{
                marginTop: '12px',
                padding: '8px 10px',
                background: '#FFF8E1',
                borderRadius: '6px',
                border: '1px dashed #FFB74D',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '13px' }}>
                  <input
                    type="checkbox"
                    checked={invisibleAardvarkTossed}
                    onChange={(e) => setInvisibleAardvarkTossed(e.target.checked)}
                    style={{ width: '16px', height: '16px' }}
                  />
                  <span style={{ color: invisibleAardvarkTossed ? '#d32f2f' : '#795548', fontWeight: invisibleAardvarkTossed ? 'bold' : 'normal' }}>
                    Invisible Aardvark tossed{invisibleAardvarkTossed && ' (3:2)'}
                  </span>
                </label>
              </div>
            )}
          </>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(3, Math.ceil(players.length / 2))}, 1fr)`, gap: '12px' }}>
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
        ))}
      </div>

      {/* Quarters Entry (Primary) - Enhanced Player Cards */}
      <div style={{ marginBottom: '20px' }}>
        {/* Section Header with Sum */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px',
          padding: '8px 12px',
          background: theme.colors.backgroundSecondary,
          borderRadius: '8px'
        }}>
          <h3 style={{
            margin: 0,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            fontSize: '12px',
            fontWeight: 'bold',
            color: theme.colors.textSecondary
          }}>Enter Quarters</h3>
          <div style={{ fontSize: '14px', fontWeight: 'bold' }}>
            Sum: {(() => {
              const sum = players.reduce((acc, p) => acc + (parseFloat(quarters[p.id]) || 0), 0);
              const color = Math.abs(sum) < 0.001 ? '#4CAF50' : '#f44336';
              const displaySum = Math.abs(sum) < 0.001 ? '0' : (sum > 0 ? '+' : '') + sum.toFixed(1);
              return <span style={{ color }}>{displaySum}</span>;
            })()}
          </div>
        </div>

        {/* Player Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {players.map((player, idx) => {
            const currentVal = parseFloat(quarters[player.id]) || 0;
            const playerStrokes = scores[player.id];
            const isExpanded = expandedPlayers[idx] || false;

            const adjustQuarters = (delta) => {
              setQuarters({ ...quarters, [player.id]: (currentVal + delta).toString() });
            };

            const toggleExpanded = () => {
              setExpandedPlayers(prev => ({
                ...prev,
                [idx]: !prev[idx]
              }));
            };

            return (
              <div
                key={player.id}
                style={{
                  background: theme.colors.paper,
                  borderRadius: '16px',
                  border: `2px solid ${isExpanded ? theme.colors.primary : theme.colors.border}`,
                  boxShadow: isExpanded ? '0 4px 12px rgba(0,0,0,0.1)' : '0 2px 4px rgba(0,0,0,0.05)',
                  overflow: 'hidden',
                  transition: 'all 0.2s ease'
                }}
              >
                {/* Player Header - Always Visible */}
                <div
                  onClick={toggleExpanded}
                  style={{
                    padding: '16px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    background: isExpanded ? 'rgba(0, 0, 0, 0.02)' : 'transparent'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {/* Trophy icon for expanded player */}
                    {isExpanded && (
                      <div style={{
                        background: 'rgba(255, 193, 7, 0.1)',
                        padding: '8px',
                        borderRadius: '10px'
                      }}>
                        <span style={{ fontSize: '20px' }}>🏆</span>
                      </div>
                    )}

                    <div>
                      <h3 style={{
                        margin: 0,
                        fontSize: '18px',
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        {player.name}
                        {player.handicap != null && (
                          <span style={{
                            background: theme.colors.backgroundSecondary,
                            color: theme.colors.textSecondary,
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontWeight: 'bold'
                          }}>
                            HDCP {player.handicap}
                          </span>
                        )}
                      </h3>
                      <p style={{
                        margin: '4px 0 0',
                        fontSize: '12px',
                        color: theme.colors.textSecondary,
                        fontWeight: '500'
                      }}>
                        Strokes on this hole: {playerStrokes || 0}
                      </p>
                    </div>
                  </div>

                  {/* Score Display */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px'
                  }}>
                    <div style={{
                      background: theme.colors.backgroundSecondary,
                      border: `1px solid ${theme.colors.border}`,
                      width: '48px',
                      height: '48px',
                      borderRadius: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <span style={{
                        fontSize: '24px',
                        fontWeight: 'bold',
                        color: currentVal > 0 ? '#4CAF50' : currentVal < 0 ? '#f44336' : theme.colors.textPrimary
                      }}>
                        {currentVal > 0 ? `+${currentVal}` : currentVal || 0}
                      </span>
                    </div>

                    <button style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      background: theme.colors.backgroundSecondary,
                      border: `1px solid ${theme.colors.border}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      cursor: 'pointer'
                    }}>
                      <span style={{ fontSize: '18px' }}>{isExpanded ? '▼' : '▶'}</span>
                    </button>
                  </div>
                </div>

                {/* Expanded Controls */}
                {isExpanded && (
                  <div style={{ padding: '0 16px 16px' }}>
                    {/* Manual Entry */}
                    <div style={{ marginBottom: '12px' }}>
                      <label style={{
                        display: 'block',
                        fontSize: '11px',
                        fontWeight: 'bold',
                        color: theme.colors.textSecondary,
                        textTransform: 'uppercase',
                        marginBottom: '6px'
                      }}>
                        Manual Entry
                      </label>
                      <input
                        data-testid={`quarters-input-${player.id}`}
                        type="text"
                        inputMode="numeric"
                        pattern="-?[0-9]*\.?[0-9]*"
                        value={quarters[player.id] ?? ''}
                        onChange={(e) => {
                          const val = e.target.value;
                          if (val === '' || val === '-' || /^-?\d*\.?\d*$/.test(val)) {
                            setQuarters({ ...quarters, [player.id]: val });
                          }
                        }}
                        placeholder="0"
                        style={{
                          width: '100%',
                          padding: '14px',
                          fontSize: '24px',
                          fontWeight: 'bold',
                          border: `2px solid ${currentVal > 0 ? '#4CAF50' : currentVal < 0 ? '#f44336' : theme.colors.border}`,
                          borderRadius: '12px',
                          textAlign: 'center',
                          color: currentVal > 0 ? '#4CAF50' : currentVal < 0 ? '#f44336' : theme.colors.textPrimary,
                          background: currentVal !== 0
                            ? currentVal > 0 ? 'rgba(76,175,80,0.05)' : 'rgba(244,67,54,0.05)'
                            : 'white',
                          outline: 'none'
                        }}
                      />
                    </div>

                    {/* Quick Adjust Buttons */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '8px' }}>
                      {[-10, -5, -1, +1, +5, +10].map((delta) => (
                        <button
                          key={delta}
                          onClick={() => adjustQuarters(delta)}
                          className="touch-optimized"
                          style={{
                            padding: '12px 8px',
                            borderRadius: '10px',
                            border: `2px solid ${delta < 0 ? '#EF5350' : '#66BB6A'}`,
                            background: delta < 0
                              ? 'linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%)'
                              : 'linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)',
                            color: delta < 0 ? '#C62828' : '#2E7D32',
                            fontWeight: 'bold',
                            fontSize: '14px',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.08)'
                          }}
                          onMouseDown={(e) => {
                            e.target.style.transform = 'scale(0.95)';
                          }}
                          onMouseUp={(e) => {
                            e.target.style.transform = 'scale(1)';
                          }}
                          onMouseLeave={(e) => {
                            e.target.style.transform = 'scale(1)';
                          }}
                        >
                          {delta > 0 ? `+${delta}` : delta}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Quick Actions */}
        <div style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            onClick={() => {
              const allZero = {};
              players.forEach(p => { allZero[p.id] = '0'; });
              setQuarters(allZero);
            }}
            className="touch-optimized"
            style={{
              padding: '10px 16px',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 'bold',
              border: `2px solid ${theme.colors.border}`,
              background: 'white',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}
          >
            Push (all 0)
          </button>
          <button
            onClick={() => {
              const cleared = {};
              players.forEach(p => { cleared[p.id] = ''; });
              setQuarters(cleared);
            }}
            className="touch-optimized"
            style={{
              padding: '10px 16px',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 'bold',
              border: `2px solid ${theme.colors.border}`,
              background: 'white',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Scores (Optional) - Collapsible */}
      <div style={{ marginBottom: '20px' }}>
        <div
          onClick={() => setShowGolfScores(!showGolfScores)}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 16px',
            background: theme.colors.paper,
            borderRadius: '8px',
            cursor: 'pointer',
            border: `2px solid ${theme.colors.border}`,
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
          }}
        >
          <h3 style={{
            margin: 0,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            fontSize: '12px',
            fontWeight: 'bold',
            color: theme.colors.textSecondary
          }}>
            Golf Scores <span style={{ fontWeight: 'normal', fontSize: '11px', opacity: 0.7 }}>(optional)</span>
          </h3>
          <button style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            background: theme.colors.backgroundSecondary,
            border: `1px solid ${theme.colors.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer'
          }}>
            <span style={{ fontSize: '16px' }}>{showGolfScores ? '▼' : '▶'}</span>
          </button>
        </div>
        {showGolfScores && (
          <div style={{
            marginTop: '12px',
            padding: '16px',
            background: theme.colors.paper,
            borderRadius: '8px',
            border: `2px solid ${theme.colors.border}`
          }}>
            <div style={{ fontSize: '12px', color: theme.colors.textSecondary, marginBottom: '12px' }}>
              Enter strokes for tracking only
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(2, Math.ceil(players.length / 3))}, 1fr)`, gap: '12px' }}>
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
        )}
      </div>

      {/* Ask Commissioner Section - Collapsible */}
      <div style={{ marginBottom: '20px' }}>
        <div
          onClick={() => setShowCommissioner(!showCommissioner)}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 16px',
            background: theme.colors.paper,
            borderRadius: '8px',
            cursor: 'pointer',
            border: `2px solid ${theme.colors.border}`,
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
          }}
        >
          <h3 style={{
            margin: 0,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            fontSize: '12px',
            fontWeight: 'bold',
            color: theme.colors.textSecondary
          }}>
            Ask Commissioner <span style={{ fontWeight: 'normal', fontSize: '11px', opacity: 0.7 }}>(optional)</span>
          </h3>
          <button style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            background: theme.colors.backgroundSecondary,
            border: `1px solid ${theme.colors.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer'
          }}>
            <span style={{ fontSize: '16px' }}>{showCommissioner ? '▼' : '▶'}</span>
          </button>
        </div>
        {showCommissioner && (
          <div style={{
            marginTop: '12px',
            padding: '16px',
            background: theme.colors.paper,
            borderRadius: '8px',
            border: `2px solid ${theme.colors.border}`
          }}>
            <CommissionerChat
              inline={true}
              gameState={{
                players,
                current_hole: currentHole,
                standings: playerStandings
              }}
              onSaveToNotes={(text) => {
                // Append commissioner ruling to notes with timestamp
                const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const ruling = `[${timestamp}] Commissioner: ${text}`;
                setHoleNotes(prev => prev ? `${prev}\n\n${ruling}` : ruling);
              }}
            />
          </div>
        )}
      </div>

      {/* Hole Notes (Optional) - Collapsible */}
      <div style={{ marginBottom: '20px' }}>
        <div
          onClick={() => setShowNotes(!showNotes)}
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 16px',
            background: theme.colors.paper,
            borderRadius: '8px',
            cursor: 'pointer',
            border: `2px solid ${theme.colors.border}`,
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
          }}
        >
          <h3 style={{
            margin: 0,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            fontSize: '12px',
            fontWeight: 'bold',
            color: theme.colors.textSecondary
          }}>
            Notes <span style={{ fontWeight: 'normal', fontSize: '11px', opacity: 0.7 }}>(optional)</span>
            {!showNotes && holeNotes && (
              <span style={{ marginLeft: '8px', fontSize: '11px', color: theme.colors.primary, fontWeight: 'bold' }}>
                ●
              </span>
            )}
          </h3>
          <button style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            background: theme.colors.backgroundSecondary,
            border: `1px solid ${theme.colors.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer'
          }}>
            <span style={{ fontSize: '16px' }}>{showNotes ? '▼' : '▶'}</span>
          </button>
        </div>
        {showNotes && (
          <div style={{
            marginTop: '12px',
            padding: '16px',
            background: theme.colors.paper,
            borderRadius: '8px',
            border: `2px solid ${theme.colors.border}`
          }}>
            <textarea
              value={holeNotes}
              onChange={(e) => setHoleNotes(e.target.value)}
              placeholder="Add notes about this hole (disputes, unusual situations, etc.)"
              style={{
                width: '100%',
                minHeight: '60px',
                padding: '10px',
                fontSize: '14px',
                border: `2px solid ${theme.colors.border}`,
                borderRadius: '6px',
                resize: 'vertical',
                fontFamily: 'inherit',
                backgroundColor: theme.colors.inputBackground || theme.colors.paper,
                color: theme.colors.textPrimary
              }}
            />
          </div>
        )}
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

      {/* Old submit button removed - now in thumb zone below */}

      {/* Sticky Bottom Thumb Zone - Primary Actions */}
      <div className="thumb-zone">
        <div className="thumb-zone-inner">
          {/* Previous Hole Navigation */}
          <button
            className="thumb-zone-nav"
            onClick={() => {
              if (currentHole > 1) {
                // Set editing mode for previous hole
                const prevHoleData = holeHistory.find(h => h.hole === currentHole - 1);
                if (prevHoleData) {
                  setEditingHole(currentHole - 1);
                  // Restore that hole's data for editing
                  setScores(prevHoleData.scores || {});
                  setQuarters(prevHoleData.quarters || {});
                  setHoleNotes(prevHoleData.notes || '');
                  setWinner(prevHoleData.winner || null);
                } else {
                  // Just navigate back
                  setCurrentHole(currentHole - 1);
                }
              }
            }}
            disabled={currentHole <= 1}
            aria-label={`Go to hole ${currentHole - 1}`}
          >
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <span style={{ fontSize: '18px' }}>◀</span>
              <span className="hole-num">{currentHole > 1 ? currentHole - 1 : ''}</span>
            </div>
          </button>

          {/* Primary Action - Complete/Update Hole */}
          <button
            data-testid="complete-hole-button"
            className={`thumb-zone-primary ${editingHole ? 'editing' : ''}`}
            onClick={handleSubmitHole}
            disabled={submitting}
          >
            {submitting
              ? 'Submitting...'
              : editingHole
                ? `Update Hole ${editingHole}`
                : `✓ Complete Hole ${currentHole}`}
          </button>

          {/* Next Hole Navigation */}
          <button
            className="thumb-zone-nav"
            onClick={() => {
              if (currentHole < 18) {
                // Check if next hole has data
                const nextHoleData = holeHistory.find(h => h.hole === currentHole + 1);
                if (nextHoleData) {
                  setEditingHole(currentHole + 1);
                  setScores(nextHoleData.scores || {});
                  setQuarters(nextHoleData.quarters || {});
                  setHoleNotes(nextHoleData.notes || '');
                  setWinner(nextHoleData.winner || null);
                } else {
                  setCurrentHole(currentHole + 1);
                  // Reset state for new hole
                  setScores({});
                  setQuarters({});
                  setHoleNotes('');
                  setWinner(null);
                  setEditingHole(null);
                }
              }
            }}
            disabled={currentHole >= 18 && !holeHistory.find(h => h.hole === currentHole + 1)}
            aria-label={`Go to hole ${currentHole + 1}`}
          >
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <span style={{ fontSize: '18px' }}>▶</span>
              <span className="hole-num">{currentHole < 18 ? currentHole + 1 : ''}</span>
            </div>
          </button>
        </div>
      </div>

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

/**
 * PropTypes for SimpleScorekeeper
 * Specific shapes for better validation and documentation
 */
SimpleScorekeeper.propTypes = {
  /** Unique game identifier */
  gameId: PropTypes.string.isRequired,
  
  /** Array of player objects */
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    handicap: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    user_id: PropTypes.string,
    tee_order: PropTypes.number,
    is_authenticated: PropTypes.bool,
    ghin_id: PropTypes.string,
  })).isRequired,
  
  /** Base wager amount in quarters (default: 1) */
  baseWager: PropTypes.number,
  
  /** History of completed holes */
  initialHoleHistory: PropTypes.arrayOf(PropTypes.shape({
    hole: PropTypes.number.isRequired,
    points_delta: PropTypes.objectOf(PropTypes.number),
    gross_scores: PropTypes.objectOf(PropTypes.number),
    teams: PropTypes.shape({
      type: PropTypes.oneOf(['partners', 'solo']),
      team1: PropTypes.arrayOf(PropTypes.string),
      team2: PropTypes.arrayOf(PropTypes.string),
      captain: PropTypes.string,
      opponents: PropTypes.arrayOf(PropTypes.string),
    }),
    winner: PropTypes.oneOf(['team1', 'team2', 'captain', 'opponents', 'push', null]),
    wager: PropTypes.number,
    phase: PropTypes.string,
    rotation_order: PropTypes.arrayOf(PropTypes.string),
    captain_index: PropTypes.number,
    notes: PropTypes.string,
    float_invoked_by: PropTypes.string,
    option_invoked_by: PropTypes.string,
    duncan_invoked: PropTypes.bool,
    option_turned_off: PropTypes.bool,
    betting_events: PropTypes.arrayOf(PropTypes.shape({
      eventId: PropTypes.string,
      eventType: PropTypes.string,
      hole: PropTypes.number,
      actor: PropTypes.string,
      timestamp: PropTypes.string,
      details: PropTypes.object,
    })),
  })),
  
  /** Starting hole number (default: 1) */
  initialCurrentHole: PropTypes.number,
  
  /** Name of the golf course */
  courseName: PropTypes.string,
  
  /** Pre-calculated stroke allocation from backend */
  initialStrokeAllocation: PropTypes.objectOf(
    PropTypes.objectOf(PropTypes.number)
  ),
};

export default SimpleScorekeeper;
