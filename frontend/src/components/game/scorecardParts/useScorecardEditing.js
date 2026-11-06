// frontend/src/components/game/scorecardParts/useScorecardEditing.js
// State and handlers for the Scorecard's edit-hole and edit-player-name modals.
import { useState } from 'react';
import useCorrectionSyncFeedback from '../../../hooks/useCorrectionSyncFeedback';
import { getHoleData, isHoleCompleted } from './scorecardUtils';

export const useScorecardEditing = ({ holeHistory, currentHole, onEditHole, onPlayerNameChange }) => {
  const [editingHole, setEditingHole] = useState(null);
  const [editingPlayer, setEditingPlayer] = useState(null);
  const [editStrokes, setEditStrokes] = useState('');
  const [editQuarters, setEditQuarters] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);
  const [editSaveError, setEditSaveError] = useState(null);
  const syncFeedback = useCorrectionSyncFeedback(JSON.stringify([editingHole, editingPlayer, editStrokes, editQuarters]));
  const [editingPlayerName, setEditingPlayerName] = useState(null);
  const [editPlayerNameValue, setEditPlayerNameValue] = useState('');

  // Handle clicking on a hole cell to edit
  const handleCellClick = (hole, playerId) => {
    if (typeof hole !== 'number' || !playerId) return;

    const isCurrentHole = hole === currentHole;
    const isCompleted = isHoleCompleted(hole, currentHole, holeHistory);

    if (!isCurrentHole && !isCompleted) {
      return; // Don't allow editing future holes
    }

    const { strokes, quarters } = getHoleData(holeHistory, hole, playerId);
    setEditingHole(hole);
    setEditingPlayer(playerId);
    setEditSaveError(null);
    syncFeedback.reset();
    setEditStrokes(typeof strokes === 'number' ? strokes.toString() : '');
    setEditQuarters(typeof quarters === 'number' ? quarters.toString() : '0');
  };

  // Handle saving the edit
  const handleSaveEdit = async () => {
    if (!onEditHole || !editingHole || !editingPlayer) return;

    // Validate and parse strokes
    const parsedStrokes = editStrokes ? parseInt(editStrokes, 10) : null;
    if (parsedStrokes !== null && (isNaN(parsedStrokes) || parsedStrokes < 0 || parsedStrokes > 15)) {
      console.error('Invalid strokes value:', editStrokes);
      alert('Strokes must be a number between 0 and 15');
      return;
    }

    // Validate and parse quarters
    const parsedQuarters = editQuarters ? parseFloat(editQuarters) : 0;
    if (isNaN(parsedQuarters) || parsedQuarters < -10 || parsedQuarters > 10) {
      console.error('Invalid quarters value:', editQuarters);
      alert('Quarters must be a number between -10 and 10');
      return;
    }

    setSavingEdit(true);
    setEditSaveError(null);
    syncFeedback.reset();
    try {
      const result = await onEditHole({
        hole: editingHole,
        playerId: editingPlayer,
        strokes: parsedStrokes,
        quarters: parsedQuarters
      });
      if (result?.queued && !result?.synced) {
        syncFeedback.trackQueued(result);
        return;
      }
      setEditingHole(null);
      setEditingPlayer(null);
      setEditStrokes('');
      setEditQuarters('');
    } catch (error) {
      setEditSaveError(error?.message || 'Saving the correction failed. Retry saving.');
    } finally {
      setSavingEdit(false);
    }
  };

  // Handle canceling the edit
  const handleCancelEdit = () => {
    setEditingHole(null);
    setEditingPlayer(null);
    setEditStrokes('');
    setEditQuarters('');
  };

  // Handle clicking on a player name to edit it (simulation mode only)
  const handlePlayerNameClick = (playerId, currentName) => {
    if (!playerId || typeof currentName !== 'string') return;
    setEditingPlayerName(playerId);
    setEditPlayerNameValue(currentName);
  };

  // Handle saving the player name edit
  const handleSavePlayerName = async () => {
    if (!editingPlayerName || !onPlayerNameChange) return;

    const trimmedName = editPlayerNameValue?.trim();
    if (!trimmedName || trimmedName.length === 0) {
      alert('Player name cannot be empty');
      return;
    }

    if (trimmedName.length > 50) {
      alert('Player name must be 50 characters or less');
      return;
    }

    try {
      await onPlayerNameChange(editingPlayerName, trimmedName);
      setEditingPlayerName(null);
      setEditPlayerNameValue('');
    } catch (error) {
      console.error('Failed to update player name:', error);
      alert('Failed to update player name. Please try again.');
    }
  };

  // Handle canceling the player name edit
  const handleCancelPlayerNameEdit = () => {
    setEditingPlayerName(null);
    setEditPlayerNameValue('');
  };

  return {
    editingHole,
    editingPlayer,
    editStrokes,
    setEditStrokes,
    editQuarters,
    setEditQuarters,
    savingEdit,
    editSaveError,
    syncFeedback,
    handleCellClick,
    handleSaveEdit,
    handleCancelEdit,
    editingPlayerName,
    editPlayerNameValue,
    setEditPlayerNameValue,
    handlePlayerNameClick,
    handleSavePlayerName,
    handleCancelPlayerNameEdit
  };
};

export default useScorecardEditing;
