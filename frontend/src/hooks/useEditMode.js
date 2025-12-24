/**
 * useEditMode - Edit mode state management
 *
 * Manages:
 * - editingHole (hole number being edited, null if not editing)
 * - editingPlayerName (player id being renamed)
 * - editPlayerNameValue (current value in player name input)
 * - isEditingCompleteGame (editing a completed game)
 */

import { useReducer, useMemo } from 'react';

export const EDIT_ACTIONS = {
  START_HOLE_EDIT: 'START_HOLE_EDIT',
  END_HOLE_EDIT: 'END_HOLE_EDIT',
  START_PLAYER_NAME_EDIT: 'START_PLAYER_NAME_EDIT',
  UPDATE_PLAYER_NAME_VALUE: 'UPDATE_PLAYER_NAME_VALUE',
  END_PLAYER_NAME_EDIT: 'END_PLAYER_NAME_EDIT',
  SET_EDITING_COMPLETE_GAME: 'SET_EDITING_COMPLETE_GAME',
  RESET: 'RESET',
};

export const initialEditState = () => ({
  editingHole: null,
  editingPlayerName: null,
  editPlayerNameValue: '',
  isEditingCompleteGame: false,
});

export function editReducer(state, action) {
  switch (action.type) {
    case EDIT_ACTIONS.START_HOLE_EDIT:
      return { ...state, editingHole: action.hole };

    case EDIT_ACTIONS.END_HOLE_EDIT:
      return { ...state, editingHole: null };

    case EDIT_ACTIONS.START_PLAYER_NAME_EDIT:
      return {
        ...state,
        editingPlayerName: action.playerId,
        editPlayerNameValue: action.currentName || '',
      };

    case EDIT_ACTIONS.UPDATE_PLAYER_NAME_VALUE:
      return { ...state, editPlayerNameValue: action.value };

    case EDIT_ACTIONS.END_PLAYER_NAME_EDIT:
      return {
        ...state,
        editingPlayerName: null,
        editPlayerNameValue: '',
      };

    case EDIT_ACTIONS.SET_EDITING_COMPLETE_GAME:
      return { ...state, isEditingCompleteGame: action.isEditing };

    case EDIT_ACTIONS.RESET:
      return initialEditState();

    default:
      return state;
  }
}

export function useEditMode() {
  const [state, dispatch] = useReducer(editReducer, null, initialEditState);

  const actions = useMemo(() => ({
    startHoleEdit: (hole) => dispatch({ type: EDIT_ACTIONS.START_HOLE_EDIT, hole }),
    endHoleEdit: () => dispatch({ type: EDIT_ACTIONS.END_HOLE_EDIT }),
    startPlayerNameEdit: (playerId, currentName) =>
      dispatch({ type: EDIT_ACTIONS.START_PLAYER_NAME_EDIT, playerId, currentName }),
    updatePlayerNameValue: (value) =>
      dispatch({ type: EDIT_ACTIONS.UPDATE_PLAYER_NAME_VALUE, value }),
    endPlayerNameEdit: () => dispatch({ type: EDIT_ACTIONS.END_PLAYER_NAME_EDIT }),
    setEditingCompleteGame: (isEditing) =>
      dispatch({ type: EDIT_ACTIONS.SET_EDITING_COMPLETE_GAME, isEditing }),
    reset: () => dispatch({ type: EDIT_ACTIONS.RESET }),
  }), []);

  const isEditingHole = useMemo(() => state.editingHole !== null, [state.editingHole]);

  const isEditingPlayerName = useMemo(() =>
    state.editingPlayerName !== null,
  [state.editingPlayerName]);

  const isAnyEditActive = useMemo(() =>
    isEditingHole || isEditingPlayerName || state.isEditingCompleteGame,
  [isEditingHole, isEditingPlayerName, state.isEditingCompleteGame]);

  return { state, dispatch, actions, isEditingHole, isEditingPlayerName, isAnyEditActive };
}

export default useEditMode;
