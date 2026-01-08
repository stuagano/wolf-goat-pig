/**
 * Custom hook for managing UI state (collapsible sections, modals, etc.)
 * Extracted from SimpleScorekeeper to reduce complexity
 */
import { useState, useCallback } from 'react';

/**
 * useUIState - Manages UI toggles and visual state
 * 
 * @returns {Object} UI state and toggle functions
 */
export function useUIState() {
  // Collapsible sections state
  const [showTeamSelection, setShowTeamSelection] = useState(true);
  const [showGolfScores, setShowGolfScores] = useState(false);
  const [showCommissioner, setShowCommissioner] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [showSpecialActions, setShowSpecialActions] = useState(false);
  const [showUsageStats, setShowUsageStats] = useState(false);
  const [showAdvancedBetting, setShowAdvancedBetting] = useState(false);
  
  // Loading and error states
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  
  // Editing states
  const [editingHole, setEditingHole] = useState(null);
  const [editingPlayerName, setEditingPlayerName] = useState(null);
  const [editPlayerNameValue, setEditPlayerNameValue] = useState('');
  const [isEditingCompleteGame, setIsEditingCompleteGame] = useState(false);
  const [isGameMarkedComplete, setIsGameMarkedComplete] = useState(false);

  /**
   * Toggle a section's visibility
   */
  const toggleSection = useCallback((section) => {
    switch (section) {
      case 'teamSelection':
        setShowTeamSelection(prev => !prev);
        break;
      case 'golfScores':
        setShowGolfScores(prev => !prev);
        break;
      case 'commissioner':
        setShowCommissioner(prev => !prev);
        break;
      case 'notes':
        setShowNotes(prev => !prev);
        break;
      case 'specialActions':
        setShowSpecialActions(prev => !prev);
        break;
      case 'usageStats':
        setShowUsageStats(prev => !prev);
        break;
      case 'advancedBetting':
        setShowAdvancedBetting(prev => !prev);
        break;
      default:
        console.warn(`Unknown section: ${section}`);
    }
  }, []);

  /**
   * Start editing a player name
   */
  const startEditingPlayerName = useCallback((playerId, currentName) => {
    setEditingPlayerName(playerId);
    setEditPlayerNameValue(currentName);
  }, []);

  /**
   * Cancel editing player name
   */
  const cancelEditingPlayerName = useCallback(() => {
    setEditingPlayerName(null);
    setEditPlayerNameValue('');
  }, []);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Set error with optional auto-clear
   */
  const setErrorWithAutoClear = useCallback((errorMessage, clearAfterMs = 0) => {
    setError(errorMessage);
    if (clearAfterMs > 0) {
      setTimeout(() => setError(null), clearAfterMs);
    }
  }, []);

  /**
   * Reset UI state for new hole
   */
  const resetForNewHole = useCallback(() => {
    setError(null);
    setEditingHole(null);
  }, []);

  return {
    // Section visibility
    showTeamSelection,
    showGolfScores,
    showCommissioner,
    showNotes,
    showSpecialActions,
    showUsageStats,
    showAdvancedBetting,
    
    // Section setters
    setShowTeamSelection,
    setShowGolfScores,
    setShowCommissioner,
    setShowNotes,
    setShowSpecialActions,
    setShowUsageStats,
    setShowAdvancedBetting,
    
    // Loading/error
    submitting,
    setSubmitting,
    error,
    setError,
    clearError,
    setErrorWithAutoClear,
    
    // Editing states
    editingHole,
    setEditingHole,
    editingPlayerName,
    editPlayerNameValue,
    setEditPlayerNameValue,
    isEditingCompleteGame,
    setIsEditingCompleteGame,
    isGameMarkedComplete,
    setIsGameMarkedComplete,
    
    // Actions
    toggleSection,
    startEditingPlayerName,
    cancelEditingPlayerName,
    resetForNewHole,
  };
}

export default useUIState;
