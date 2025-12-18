import { useState, useEffect, useCallback, useRef } from 'react';
import useFetchAsync from './useFetchAsync';

/**
 * Custom hook for real-time odds calculation and management.
 * Provides automated updates, caching, and performance optimization.
 */
const useOddsCalculation = ({
  gameState,
  autoUpdate = true,
  updateInterval = 5000,
  useMonteCarloThreshold = 4, // Enable Monte Carlo for 4+ players
  performanceTarget = 50, // Target calculation time in ms
  maxRetries = 3,
  enableCaching = true,
  onOddsUpdate,
  onError
} = {}) => {

  // Use centralized fetch hook for consistent error handling and retry logic
  const {
    loading: fetchLoading,
    error: fetchError,
    post,
    clearError: clearFetchError
  } = useFetchAsync({
    throwOnError: false,
    retryCount: maxRetries,
    retryDelay: 100 // Will use exponential backoff in useFetchAsync
  });

  // State management
  const [oddsData, setOddsData] = useState(null);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [calculationHistory, setCalculationHistory] = useState([]);
  const [performanceMetrics, setPerformanceMetrics] = useState({
    averageCalculationTime: 0,
    successRate: 0,
    cacheHitRate: 0
  });

  // Refs for managing intervals and caching
  const updateIntervalRef = useRef(null);
  const cacheRef = useRef(new Map());
  const performanceRef = useRef({
    totalCalculations: 0,
    successfulCalculations: 0,
    totalCalculationTime: 0,
    cacheHits: 0,
    cacheMisses: 0
  });

  // Cache key generation
  const generateCacheKey = useCallback((gameState) => {
    if (!gameState) return null;
    
    const keyData = {
      hole: gameState.current_hole,
      players: gameState.players?.map(p => ({
        id: p.id,
        handicap: p.handicap,
        distance: Math.round(p.distance_to_pin || 0),
        lie: p.lie_type,
        shots: p.shots_taken
      })),
      teams: gameState.teams?.type,
      wager: gameState.current_wager,
      doubled: gameState.is_doubled
    };
    
    return JSON.stringify(keyData);
  }, []);

  // Check cache for existing calculation
  const checkCache = useCallback((cacheKey) => {
    if (!enableCaching || !cacheKey) return null;
    
    const cached = cacheRef.current.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < 30000) { // 30-second cache
      performanceRef.current.cacheHits++;
      return cached.data;
    }
    
    performanceRef.current.cacheMisses++;
    return null;
  }, [enableCaching]);

  // Store calculation in cache
  const storeInCache = useCallback((cacheKey, data) => {
    if (!enableCaching || !cacheKey) return;
    
    cacheRef.current.set(cacheKey, {
      data,
      timestamp: Date.now()
    });
    
    // Cleanup old cache entries
    if (cacheRef.current.size > 50) {
      const oldestKey = cacheRef.current.keys().next().value;
      cacheRef.current.delete(oldestKey);
    }
  }, [enableCaching]);

  // Main odds calculation function
  const calculateOdds = useCallback(async (gameStateData = gameState, options = {}) => {
    if (!gameStateData?.players || !gameStateData.active) {
      return null;
    }

    const startTime = Date.now();
    setError(null);
    clearFetchError();

    try {
      // Check cache first
      const cacheKey = generateCacheKey(gameStateData);
      const cachedResult = checkCache(cacheKey);

      if (cachedResult) {
        setOddsData(cachedResult);
        return cachedResult;
      }

      // Determine calculation parameters
      const playerCount = gameStateData.players.length;
      const useMonteCarloSimulation =
        options.forceMonteCarloMode ||
        playerCount >= useMonteCarloThreshold ||
        gameStateData.teams?.type === 'solo' ||
        gameStateData.players.some(p => (p.distance_to_pin || 0) > 200);

      // Prepare request payload
      const requestPayload = {
        players: gameStateData.players.map(player => ({
          id: player.id,
          name: player.name,
          handicap: player.handicap || 18,
          current_score: player.current_score || 0,
          shots_taken: player.shots_taken || 0,
          distance_to_pin: player.distance_to_pin || 0,
          lie_type: player.lie_type || 'fairway',
          is_captain: player.is_captain || false,
          team_id: player.team_id || null,
          confidence_factor: player.confidence_factor || 1.0
        })),
        hole_state: {
          hole_number: gameStateData.current_hole || 1,
          par: gameStateData.current_hole_par || 4,
          difficulty_rating: gameStateData.hole_difficulty || 3.0,
          weather_factor: gameStateData.weather_factor || 1.0,
          pin_position: gameStateData.pin_position || 'middle',
          course_conditions: gameStateData.course_conditions || 'normal',
          teams: gameStateData.teams?.type || 'pending',
          current_wager: gameStateData.current_wager || 1,
          is_doubled: gameStateData.is_doubled || false,
          line_of_scrimmage_passed: gameStateData.line_of_scrimmage_passed || false
        },
        use_monte_carlo: useMonteCarloSimulation,
        simulation_params: {
          num_simulations: options.simulationCount || (useMonteCarloSimulation ? 5000 : 1000),
          max_time_ms: options.maxCalculationTime || (performanceTarget * 0.6) // Leave buffer for network
        }
      };

      // Use centralized fetch hook (handles retries, loading, and error states)
      const response = await post(
        '/api/wgp/calculate-odds',
        requestPayload,
        'Calculate odds'
      );

      if (!response) {
        throw new Error('Failed to calculate odds');
      }

      const calculationTime = Date.now() - startTime;

      // Update performance metrics
      performanceRef.current.totalCalculations++;
      performanceRef.current.successfulCalculations++;
      performanceRef.current.totalCalculationTime += calculationTime;

      // Process and enhance response
      const enhancedOddsData = {
        ...response,
        client_calculation_time: calculationTime,
        cache_used: false,
        monte_carlo_used: useMonteCarloSimulation
      };

      // Store in cache
      storeInCache(cacheKey, enhancedOddsData);

      // Update state
      setOddsData(enhancedOddsData);
      setLastUpdate(new Date());

      // Add to calculation history
      setCalculationHistory(prev => {
        const newHistory = [...prev, {
          timestamp: enhancedOddsData.timestamp,
          calculation_time: calculationTime,
          server_time: enhancedOddsData.calculation_time_ms,
          confidence: enhancedOddsData.confidence_level,
          team_probabilities: enhancedOddsData.team_probabilities,
          monte_carlo_used: useMonteCarloSimulation
        }].slice(-50); // Keep last 50 calculations
        return newHistory;
      });

      // Trigger callback
      if (onOddsUpdate) {
        onOddsUpdate(enhancedOddsData);
      }

      return enhancedOddsData;

    } catch (err) {
      console.error('Odds calculation error:', err);

      performanceRef.current.totalCalculations++;
      const errorMessage = err.message || 'Failed to calculate odds';
      setError(errorMessage);

      if (onError) {
        onError(err);
      }

      return null;
    }
  }, [
    gameState,
    generateCacheKey,
    checkCache,
    storeInCache,
    useMonteCarloThreshold,
    performanceTarget,
    post,
    clearFetchError,
    onOddsUpdate,
    onError
  ]);

  // Quick odds calculation (simplified)
  const calculateQuickOdds = useCallback(async (playersData) => {
    if (!playersData || playersData.length < 2) {
      return null;
    }

    try {
      // Use centralized fetch hook
      return await post(
        '/api/wgp/quick-odds',
        playersData,
        'Calculate quick odds'
      );
    } catch (err) {
      console.error('Quick odds calculation error:', err);
      return null;
    }
  }, [post]);

  // Update performance metrics
  const updatePerformanceMetrics = useCallback(() => {
    const perf = performanceRef.current;
    
    setPerformanceMetrics({
      averageCalculationTime: perf.totalCalculations > 0 
        ? perf.totalCalculationTime / perf.totalCalculations 
        : 0,
      successRate: perf.totalCalculations > 0 
        ? perf.successfulCalculations / perf.totalCalculations 
        : 0,
      cacheHitRate: (perf.cacheHits + perf.cacheMisses) > 0 
        ? perf.cacheHits / (perf.cacheHits + perf.cacheMisses) 
        : 0
    });
  }, []);

  // Effect to periodically update performance metrics
  useEffect(() => {
    const interval = setInterval(updatePerformanceMetrics, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, [updatePerformanceMetrics]);

  // Auto-update effect
  useEffect(() => {
    if (autoUpdate && gameState?.active && updateInterval > 0) {
      // Initial calculation
      calculateOdds();
      
      // Set up interval
      updateIntervalRef.current = setInterval(() => {
        calculateOdds();
      }, updateInterval);
      
      return () => {
        if (updateIntervalRef.current) {
          clearInterval(updateIntervalRef.current);
        }
      };
    }
  }, [autoUpdate, gameState?.active, updateInterval, calculateOdds]);

  // Game state change effect
  useEffect(() => {
    if (gameState?.active && !autoUpdate) {
      // Manual calculation when game state changes significantly
      const significantChange = 
        gameState.current_hole !== oddsData?.hole_number ||
        gameState.teams?.type !== oddsData?.team_configuration ||
        gameState.players?.some(p => 
          Math.abs((p.distance_to_pin || 0) - (oddsData?.player_distances?.[p.id] || 0)) > 10
        );
      
      if (significantChange) {
        calculateOdds();
      }
    }
  }, [gameState, oddsData, autoUpdate, calculateOdds]);

  // Cleanup effect
  useEffect(() => {
    return () => {
      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current);
      }
    };
  }, []);

  // Sync error states from useFetchAsync
  useEffect(() => {
    if (fetchError) {
      setError(fetchError);
    }
  }, [fetchError]);

  // Public API
  return {
    // Data
    oddsData,
    loading: fetchLoading, // Use loading state from useFetchAsync
    error: error || fetchError, // Combine local and fetch errors
    lastUpdate,
    calculationHistory,
    performanceMetrics,

    // Actions
    calculateOdds,
    calculateQuickOdds,
    refreshOdds: () => calculateOdds(gameState, { forceRefresh: true }),
    clearError: () => {
      setError(null);
      clearFetchError();
    },
    clearCache: () => cacheRef.current.clear(),

    // Utils
    isCalculationStale: lastUpdate ? Date.now() - lastUpdate.getTime() > updateInterval * 2 : true,
    canCalculate: gameState?.active && gameState?.players?.length >= 2,

    // Performance insights
    isPerformanceOptimal: performanceMetrics.averageCalculationTime < performanceTarget,
    cacheEfficiency: performanceMetrics.cacheHitRate,

    // Configuration
    setAutoUpdate: (enabled) => {
      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current);
      }
      if (enabled && gameState?.active) {
        updateIntervalRef.current = setInterval(() => {
          calculateOdds();
        }, updateInterval);
      }
    }
  };
};

export default useOddsCalculation;
