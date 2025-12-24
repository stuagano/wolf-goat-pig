import { renderHook, act } from '@testing-library/react';
import {
  useEditMode,
  editReducer,
  EDIT_ACTIONS,
  initialEditState
} from '../useEditMode';

describe('useEditMode', () => {
  describe('initialEditState', () => {
    it('has correct default values', () => {
      expect(initialEditState()).toEqual({
        editingHole: null,
        editingPlayerName: null,
        editPlayerNameValue: '',
        isEditingCompleteGame: false,
      });
    });
  });

  describe('editReducer', () => {
    it('START_HOLE_EDIT sets editingHole', () => {
      const state = initialEditState();
      const result = editReducer(state, { type: EDIT_ACTIONS.START_HOLE_EDIT, hole: 5 });
      expect(result.editingHole).toBe(5);
    });

    it('END_HOLE_EDIT clears editingHole', () => {
      const state = { ...initialEditState(), editingHole: 5 };
      const result = editReducer(state, { type: EDIT_ACTIONS.END_HOLE_EDIT });
      expect(result.editingHole).toBeNull();
    });

    it('START_PLAYER_NAME_EDIT sets player and value', () => {
      const state = initialEditState();
      const result = editReducer(state, {
        type: EDIT_ACTIONS.START_PLAYER_NAME_EDIT,
        playerId: 'p1',
        currentName: 'Alice',
      });
      expect(result.editingPlayerName).toBe('p1');
      expect(result.editPlayerNameValue).toBe('Alice');
    });

    it('START_PLAYER_NAME_EDIT defaults value to empty string', () => {
      const state = initialEditState();
      const result = editReducer(state, {
        type: EDIT_ACTIONS.START_PLAYER_NAME_EDIT,
        playerId: 'p1',
      });
      expect(result.editPlayerNameValue).toBe('');
    });

    it('UPDATE_PLAYER_NAME_VALUE updates the value', () => {
      const state = { ...initialEditState(), editingPlayerName: 'p1', editPlayerNameValue: 'Al' };
      const result = editReducer(state, {
        type: EDIT_ACTIONS.UPDATE_PLAYER_NAME_VALUE,
        value: 'Alice',
      });
      expect(result.editPlayerNameValue).toBe('Alice');
    });

    it('END_PLAYER_NAME_EDIT clears player and value', () => {
      const state = { ...initialEditState(), editingPlayerName: 'p1', editPlayerNameValue: 'Alice' };
      const result = editReducer(state, { type: EDIT_ACTIONS.END_PLAYER_NAME_EDIT });
      expect(result.editingPlayerName).toBeNull();
      expect(result.editPlayerNameValue).toBe('');
    });

    it('SET_EDITING_COMPLETE_GAME sets flag', () => {
      const state = initialEditState();
      const result = editReducer(state, {
        type: EDIT_ACTIONS.SET_EDITING_COMPLETE_GAME,
        isEditing: true,
      });
      expect(result.isEditingCompleteGame).toBe(true);
    });

    it('RESET returns to initial state', () => {
      const state = {
        editingHole: 5,
        editingPlayerName: 'p1',
        editPlayerNameValue: 'Alice',
        isEditingCompleteGame: true,
      };
      const result = editReducer(state, { type: EDIT_ACTIONS.RESET });
      expect(result).toEqual(initialEditState());
    });

    it('handles unknown action', () => {
      const state = initialEditState();
      expect(editReducer(state, { type: 'UNKNOWN' })).toEqual(state);
    });
  });

  describe('useEditMode hook', () => {
    it('returns state and actions', () => {
      const { result } = renderHook(() => useEditMode());
      expect(result.current.state.editingHole).toBeNull();
      expect(typeof result.current.actions.startHoleEdit).toBe('function');
    });

    it('computes isEditingHole correctly', () => {
      const { result } = renderHook(() => useEditMode());
      expect(result.current.isEditingHole).toBe(false);

      act(() => result.current.actions.startHoleEdit(3));
      expect(result.current.isEditingHole).toBe(true);

      act(() => result.current.actions.endHoleEdit());
      expect(result.current.isEditingHole).toBe(false);
    });

    it('computes isEditingPlayerName correctly', () => {
      const { result } = renderHook(() => useEditMode());
      expect(result.current.isEditingPlayerName).toBe(false);

      act(() => result.current.actions.startPlayerNameEdit('p1', 'Alice'));
      expect(result.current.isEditingPlayerName).toBe(true);

      act(() => result.current.actions.endPlayerNameEdit());
      expect(result.current.isEditingPlayerName).toBe(false);
    });

    it('computes isAnyEditActive when hole editing', () => {
      const { result } = renderHook(() => useEditMode());
      expect(result.current.isAnyEditActive).toBe(false);

      act(() => result.current.actions.startHoleEdit(1));
      expect(result.current.isAnyEditActive).toBe(true);
    });

    it('computes isAnyEditActive when player name editing', () => {
      const { result } = renderHook(() => useEditMode());
      act(() => result.current.actions.startPlayerNameEdit('p1'));
      expect(result.current.isAnyEditActive).toBe(true);
    });

    it('computes isAnyEditActive when editing complete game', () => {
      const { result } = renderHook(() => useEditMode());
      act(() => result.current.actions.setEditingCompleteGame(true));
      expect(result.current.isAnyEditActive).toBe(true);
    });

    it('player name edit workflow', () => {
      const { result } = renderHook(() => useEditMode());

      // Start editing
      act(() => result.current.actions.startPlayerNameEdit('p1', 'Alice'));
      expect(result.current.state.editingPlayerName).toBe('p1');
      expect(result.current.state.editPlayerNameValue).toBe('Alice');

      // Update value
      act(() => result.current.actions.updatePlayerNameValue('Alicia'));
      expect(result.current.state.editPlayerNameValue).toBe('Alicia');

      // End editing
      act(() => result.current.actions.endPlayerNameEdit());
      expect(result.current.state.editingPlayerName).toBeNull();
      expect(result.current.state.editPlayerNameValue).toBe('');
    });

    it('hole edit workflow', () => {
      const { result } = renderHook(() => useEditMode());

      act(() => result.current.actions.startHoleEdit(7));
      expect(result.current.state.editingHole).toBe(7);
      expect(result.current.isEditingHole).toBe(true);

      act(() => result.current.actions.endHoleEdit());
      expect(result.current.state.editingHole).toBeNull();
      expect(result.current.isEditingHole).toBe(false);
    });

    it('reset clears all edit state', () => {
      const { result } = renderHook(() => useEditMode());

      act(() => result.current.actions.startHoleEdit(5));
      act(() => result.current.actions.startPlayerNameEdit('p1', 'Bob'));
      act(() => result.current.actions.setEditingCompleteGame(true));
      act(() => result.current.actions.reset());

      expect(result.current.isAnyEditActive).toBe(false);
      expect(result.current.state).toEqual(initialEditState());
    });
  });
});
