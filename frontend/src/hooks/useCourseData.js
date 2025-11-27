/**
 * useCourseData - Course data fetching and caching hook
 *
 * Centralizes course data fetching that was previously duplicated across
 * SimpleScorekeeper.jsx, LargeScoringButtons.jsx, and MobileScorecard.jsx.
 *
 * Features:
 * - Caches course data to avoid redundant API calls
 * - Provides loading and error states
 * - Exposes helper functions for accessing hole data
 */

import { useState, useEffect, useCallback, useMemo } from 'react';

const API_URL = process.env.REACT_APP_API_URL || '';

// Module-level cache for course data (persists across component instances)
const courseCache = new Map();

/**
 * Custom hook for fetching and caching course data
 *
 * @param {string} courseName - Name of the course to fetch
 * @returns {Object} Course data, loading state, and helper functions
 */
export const useCourseData = (courseName) => {
  const [courseData, setCourseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch course data with caching
  useEffect(() => {
    const fetchCourseData = async () => {
      if (!courseName) {
        setLoading(false);
        return;
      }

      // Check cache first
      if (courseCache.has(courseName)) {
        setCourseData(courseCache.get(courseName));
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_URL}/courses`);

        if (!response.ok) {
          throw new Error(`Failed to fetch courses: ${response.status}`);
        }

        const coursesData = await response.json();
        const course = coursesData[courseName];

        if (course) {
          // Cache the course data
          courseCache.set(courseName, course);
          setCourseData(course);
        } else {
          console.warn(`Course "${courseName}" not found in courses data`);
          setError(`Course "${courseName}" not found`);
        }
      } catch (err) {
        console.error('Error fetching course data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchCourseData();
  }, [courseName]);

  /**
   * Get hole data for a specific hole number
   *
   * @param {number} holeNumber - Hole number (1-18)
   * @returns {Object|null} Hole data or null
   */
  const getHoleData = useCallback((holeNumber) => {
    if (!courseData?.holes) return null;
    return courseData.holes.find(h => h.hole_number === holeNumber) || null;
  }, [courseData]);

  /**
   * Get par for a specific hole
   *
   * @param {number} holeNumber - Hole number (1-18)
   * @returns {number|null} Par value or null
   */
  const getHolePar = useCallback((holeNumber) => {
    const hole = getHoleData(holeNumber);
    return hole?.par ?? null;
  }, [getHoleData]);

  /**
   * Get stroke index (handicap) for a specific hole
   *
   * @param {number} holeNumber - Hole number (1-18)
   * @returns {number|null} Stroke index (1-18) or null
   */
  const getStrokeIndex = useCallback((holeNumber) => {
    const hole = getHoleData(holeNumber);
    return hole?.handicap ?? null;
  }, [getHoleData]);

  /**
   * Get yardage for a specific hole
   *
   * @param {number} holeNumber - Hole number (1-18)
   * @returns {number|null} Yardage or null
   */
  const getHoleYards = useCallback((holeNumber) => {
    const hole = getHoleData(holeNumber);
    return hole?.yards ?? null;
  }, [getHoleData]);

  /**
   * Get total par for front 9
   *
   * @returns {number}
   */
  const getFront9Par = useMemo(() => {
    if (!courseData?.holes) return 0;
    return courseData.holes
      .filter(h => h.hole_number <= 9)
      .reduce((sum, h) => sum + (h.par || 0), 0);
  }, [courseData]);

  /**
   * Get total par for back 9
   *
   * @returns {number}
   */
  const getBack9Par = useMemo(() => {
    if (!courseData?.holes) return 0;
    return courseData.holes
      .filter(h => h.hole_number > 9 && h.hole_number <= 18)
      .reduce((sum, h) => sum + (h.par || 0), 0);
  }, [courseData]);

  /**
   * Get total par for all 18 holes
   *
   * @returns {number}
   */
  const getTotalPar = useMemo(() => {
    return getFront9Par + getBack9Par;
  }, [getFront9Par, getBack9Par]);

  /**
   * Get all holes formatted for scorecard display
   *
   * @returns {Array} Array of hole objects with standardized format
   */
  const getScorecardHoles = useMemo(() => {
    if (!courseData?.holes) return [];
    return courseData.holes.map(h => ({
      hole: h.hole_number,
      par: h.par,
      handicap: h.handicap,
      yards: h.yards
    }));
  }, [courseData]);

  /**
   * Check if course data is available
   *
   * @returns {boolean}
   */
  const hasData = useMemo(() => {
    return courseData !== null && courseData.holes?.length > 0;
  }, [courseData]);

  /**
   * Clear the cache for a specific course or all courses
   *
   * @param {string} specificCourse - Optional course name to clear
   */
  const clearCache = useCallback((specificCourse = null) => {
    if (specificCourse) {
      courseCache.delete(specificCourse);
    } else {
      courseCache.clear();
    }
  }, []);

  /**
   * Force refetch course data (bypasses cache)
   */
  const refetch = useCallback(async () => {
    if (courseName) {
      courseCache.delete(courseName);
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_URL}/courses`);
        if (response.ok) {
          const coursesData = await response.json();
          const course = coursesData[courseName];
          if (course) {
            courseCache.set(courseName, course);
            setCourseData(course);
          }
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
  }, [courseName]);

  return {
    // State
    courseData,
    loading,
    error,
    hasData,

    // Hole accessors
    getHoleData,
    getHolePar,
    getStrokeIndex,
    getHoleYards,

    // Aggregates
    getFront9Par,
    getBack9Par,
    getTotalPar,
    getScorecardHoles,

    // Cache control
    clearCache,
    refetch
  };
};

export default useCourseData;
