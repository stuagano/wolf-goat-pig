// =============================================================================
// useStrokeAllocation Hook - Creecher Feature Calculations
// Calculates stroke allocations per player per hole with half-stroke support
// =============================================================================

import { useState, useCallback, useMemo } from 'react';
import {
  Player,
  Course,
  CourseHole,
  HoleStrokeAllocation,
  StrokeAllocationState,
  UseStrokeAllocationReturn,
} from '../types';

// =============================================================================
// Stroke Calculation Logic
// =============================================================================

/**
 * Calculate stroke allocation for a single player on a single hole
 * Implements the Creecher Feature with half-stroke support
 */
function calculatePlayerStrokeAllocation(
  player: Player,
  hole: CourseHole,
  lowestHandicap: number,
  creecherEnabled: boolean
): HoleStrokeAllocation {
  // Relative handicap (difference from lowest handicap player)
  const relativeHandicap = player.handicap - lowestHandicap;

  // Course hole handicap determines stroke priority (1 = hardest)
  const courseHoleHandicap = hole.handicap;

  // Full strokes: if relativeHandicap >= courseHoleHandicap, player gets a stroke
  // For 18-hole: strokes on holes where handicap rank <= player's strokes
  // For 36-hole: can get 2 strokes on hardest holes

  let fullStrokes = 0;
  let halfStroke = false;

  if (relativeHandicap >= 18) {
    // Very high handicap: 2+ strokes on some holes
    if (courseHoleHandicap <= (relativeHandicap - 18)) {
      fullStrokes = 2;
    } else if (courseHoleHandicap <= relativeHandicap) {
      fullStrokes = 1;
    }
  } else if (relativeHandicap > 0) {
    // Standard handicap allocation
    if (courseHoleHandicap <= relativeHandicap) {
      fullStrokes = 1;
    }
  }

  // Creecher Feature: Half-stroke on borderline holes
  // Player gets 0.5 stroke on the hole just outside their allocation
  if (creecherEnabled && relativeHandicap > 0) {
    const nextHoleRank = relativeHandicap + 1;
    if (courseHoleHandicap === nextHoleRank && nextHoleRank <= 18) {
      halfStroke = true;
    }
  }

  const totalStrokes = fullStrokes + (halfStroke ? 0.5 : 0);

  return {
    playerId: player.id,
    playerHandicap: player.handicap,
    courseHoleHandicap,
    fullStrokes,
    halfStroke,
    totalStrokes,
    netScore: null, // Calculated when gross score is known
  };
}

/**
 * Calculate stroke allocations for all players on a specific hole
 */
function calculateHoleAllocations(
  holeNumber: number,
  players: Player[],
  course: Course,
  creecherEnabled: boolean
): HoleStrokeAllocation[] {
  const hole = course.holes.find(h => h.holeNumber === holeNumber);
  if (!hole) return [];

  // Find lowest handicap for relative calculations
  const lowestHandicap = Math.min(...players.map(p => p.handicap));

  return players.map(player =>
    calculatePlayerStrokeAllocation(player, hole, lowestHandicap, creecherEnabled)
  );
}

// =============================================================================
// Hook Implementation
// =============================================================================

interface UseStrokeAllocationOptions {
  players: Player[];
  course: Course;
  creecherEnabled?: boolean;
}

export function useStrokeAllocation({
  players,
  course,
  creecherEnabled = true,
}: UseStrokeAllocationOptions): UseStrokeAllocationReturn {
  const [allocations, setAllocations] = useState<StrokeAllocationState>({
    allocations: {},
    creecherEnabled,
    displayMode: 'gross',
  });

  // Pre-calculate allocations for all holes
  const allHoleAllocations = useMemo(() => {
    const result: Record<number, HoleStrokeAllocation[]> = {};
    course.holes.forEach(hole => {
      result[hole.holeNumber] = calculateHoleAllocations(
        hole.holeNumber,
        players,
        course,
        allocations.creecherEnabled
      );
    });
    return result;
  }, [players, course, allocations.creecherEnabled]);

  // Update allocations state when memoized values change
  useMemo(() => {
    setAllocations(prev => ({
      ...prev,
      allocations: allHoleAllocations,
    }));
  }, [allHoleAllocations]);

  const calculateAllocations = useCallback((
    holeNumber: number,
    playersArg: Player[],
    courseArg: Course
  ): HoleStrokeAllocation[] => {
    return calculateHoleAllocations(
      holeNumber,
      playersArg,
      courseArg,
      allocations.creecherEnabled
    );
  }, [allocations.creecherEnabled]);

  const getPlayerAllocation = useCallback((
    playerId: string,
    holeNumber: number
  ): HoleStrokeAllocation | null => {
    const holeAllocations = allHoleAllocations[holeNumber];
    if (!holeAllocations) return null;
    return holeAllocations.find(a => a.playerId === playerId) || null;
  }, [allHoleAllocations]);

  const calculateNetScore = useCallback((
    playerId: string,
    holeNumber: number,
    grossScore: number
  ): number => {
    const allocation = getPlayerAllocation(playerId, holeNumber);
    if (!allocation) return grossScore;
    return grossScore - allocation.totalStrokes;
  }, [getPlayerAllocation]);

  const setDisplayMode = useCallback((mode: 'gross' | 'net' | 'both') => {
    setAllocations(prev => ({
      ...prev,
      displayMode: mode,
    }));
  }, []);

  return {
    allocations,
    calculateAllocations,
    getPlayerAllocation,
    calculateNetScore,
    setDisplayMode,
  };
}

export default useStrokeAllocation;

// =============================================================================
// Utility Functions (exported for testing)
// =============================================================================

export const strokeCalculations = {
  calculatePlayerStrokeAllocation,
  calculateHoleAllocations,
};
