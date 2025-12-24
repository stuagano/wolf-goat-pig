import { renderHook, act } from '@testing-library/react';
import {
  useUIToggles,
  uiReducer,
  UI_ACTIONS,
  initialUIState
} from '../useUIToggles';

describe('useUIToggles', () => {
  describe('initialUIState', () => {
    it('has correct default values', () => {
      expect(initialUIState()).toEqual({
        showUsageStats: false,
        showBettingHistory: false,
        showAdvancedBetting: false,
        showTeamSelection: false,
        showGolfScores: true,
        showCommissioner: false,
        showNotes: false,
        historyTab: 'holes',
        isGameMarkedComplete: false,
        localPlayers: [],
      });
    });
  });

  describe('uiReducer', () => {
    it('TOGGLE_USAGE_STATS toggles showUsageStats', () => {
      const state = initialUIState();
      const result = uiReducer(state, { type: UI_ACTIONS.TOGGLE_USAGE_STATS });
      expect(result.showUsageStats).toBe(true);
      const result2 = uiReducer(result, { type: UI_ACTIONS.TOGGLE_USAGE_STATS });
      expect(result2.showUsageStats).toBe(false);
    });

    it('TOGGLE_BETTING_HISTORY toggles showBettingHistory', () => {
      const state = initialUIState();
      const result = uiReducer(state, { type: UI_ACTIONS.TOGGLE_BETTING_HISTORY });
      expect(result.showBettingHistory).toBe(true);
    });

    it('TOGGLE_ADVANCED_BETTING toggles showAdvancedBetting', () => {
      const state = initialUIState();
      const result = uiReducer(state, { type: UI_ACTIONS.TOGGLE_ADVANCED_BETTING });
      expect(result.showAdvancedBetting).toBe(true);
    });

    it('TOGGLE_TEAM_SELECTION toggles showTeamSelection', () => {
      const state = initialUIState();
      const result = uiReducer(state, { type: UI_ACTIONS.TOGGLE_TEAM_SELECTION });
      expect(result.showTeamSelection).toBe(true);
    });

    it('TOGGLE_GOLF_SCORES toggles showGolfScores', () => {
      const state = initialUIState();
      expect(state.showGolfScores).toBe(true);
      const result = uiReducer(state, { type: UI_ACTIONS.TOGGLE_GOLF_SCORES });
      expect(result.showGolfScores).toBe(false);
    });

    it('TOGGLE_COMMISSIONER toggles showCommissioner', () => {
      const state = initialUIState();
      const result = uiReducer(state, { type: UI_ACTIONS.TOGGLE_COMMISSIONER });
      expect(result.showCommissioner).toBe(true);
    });

    it('TOGGLE_NOTES toggles showNotes', () => {
      const state = initialUIState();
      const result = uiReducer(state, { type: UI_ACTIONS.TOGGLE_NOTES });
      expect(result.showNotes).toBe(true);
    });

    it('SET_HISTORY_TAB sets the history tab', () => {
      const state = initialUIState();
      const result = uiReducer(state, { type: UI_ACTIONS.SET_HISTORY_TAB, tab: 'betting' });
      expect(result.historyTab).toBe('betting');
    });

    it('SET_GAME_COMPLETE sets game complete flag', () => {
      const state = initialUIState();
      const result = uiReducer(state, { type: UI_ACTIONS.SET_GAME_COMPLETE, complete: true });
      expect(result.isGameMarkedComplete).toBe(true);
    });

    it('SET_LOCAL_PLAYERS updates local players', () => {
      const state = initialUIState();
      const players = [{ id: 'p1', name: 'Alice' }];
      const result = uiReducer(state, { type: UI_ACTIONS.SET_LOCAL_PLAYERS, players });
      expect(result.localPlayers).toEqual(players);
    });

    it('SHOW_PANEL shows a specific panel', () => {
      const state = initialUIState();
      const result = uiReducer(state, { type: UI_ACTIONS.SHOW_PANEL, panel: 'showUsageStats' });
      expect(result.showUsageStats).toBe(true);
    });

    it('HIDE_PANEL hides a specific panel', () => {
      const state = { ...initialUIState(), showUsageStats: true };
      const result = uiReducer(state, { type: UI_ACTIONS.HIDE_PANEL, panel: 'showUsageStats' });
      expect(result.showUsageStats).toBe(false);
    });

    it('SHOW_PANEL ignores invalid panel names', () => {
      const state = initialUIState();
      const result = uiReducer(state, { type: UI_ACTIONS.SHOW_PANEL, panel: 'invalidPanel' });
      expect(result).toEqual(state);
    });

    it('HIDE_PANEL ignores invalid panel names', () => {
      const state = initialUIState();
      const result = uiReducer(state, { type: UI_ACTIONS.HIDE_PANEL, panel: 'invalidPanel' });
      expect(result).toEqual(state);
    });

    it('RESET returns to initial state', () => {
      const state = {
        ...initialUIState(),
        showUsageStats: true,
        showBettingHistory: true,
        historyTab: 'betting',
        isGameMarkedComplete: true,
      };
      const result = uiReducer(state, { type: UI_ACTIONS.RESET });
      expect(result).toEqual(initialUIState());
    });

    it('handles unknown action', () => {
      const state = initialUIState();
      expect(uiReducer(state, { type: 'UNKNOWN' })).toEqual(state);
    });
  });

  describe('useUIToggles hook', () => {
    it('returns state and actions', () => {
      const { result } = renderHook(() => useUIToggles());
      expect(result.current.state.showUsageStats).toBe(false);
      expect(typeof result.current.actions.toggleUsageStats).toBe('function');
    });

    it('accepts initial players', () => {
      const players = [{ id: 'p1', name: 'Alice' }];
      const { result } = renderHook(() => useUIToggles(players));
      expect(result.current.state.localPlayers).toEqual(players);
    });

    it('computes anyPanelOpen when no panels open', () => {
      const { result } = renderHook(() => useUIToggles());
      expect(result.current.anyPanelOpen).toBe(false);
    });

    it('computes anyPanelOpen when panel is open', () => {
      const { result } = renderHook(() => useUIToggles());
      act(() => result.current.actions.toggleUsageStats());
      expect(result.current.anyPanelOpen).toBe(true);
    });

    it('computes hasLocalPlayers correctly', () => {
      const { result } = renderHook(() => useUIToggles());
      expect(result.current.hasLocalPlayers).toBe(false);

      act(() => result.current.actions.setLocalPlayers([{ id: 'p1' }]));
      expect(result.current.hasLocalPlayers).toBe(true);
    });

    it('toggle actions work correctly', () => {
      const { result } = renderHook(() => useUIToggles());

      act(() => result.current.actions.toggleBettingHistory());
      expect(result.current.state.showBettingHistory).toBe(true);

      act(() => result.current.actions.toggleAdvancedBetting());
      expect(result.current.state.showAdvancedBetting).toBe(true);

      act(() => result.current.actions.toggleTeamSelection());
      expect(result.current.state.showTeamSelection).toBe(true);

      act(() => result.current.actions.toggleCommissioner());
      expect(result.current.state.showCommissioner).toBe(true);

      act(() => result.current.actions.toggleNotes());
      expect(result.current.state.showNotes).toBe(true);
    });

    it('setHistoryTab changes tab', () => {
      const { result } = renderHook(() => useUIToggles());
      act(() => result.current.actions.setHistoryTab('betting'));
      expect(result.current.state.historyTab).toBe('betting');
    });

    it('setGameComplete changes flag', () => {
      const { result } = renderHook(() => useUIToggles());
      act(() => result.current.actions.setGameComplete(true));
      expect(result.current.state.isGameMarkedComplete).toBe(true);
    });

    it('showPanel and hidePanel work', () => {
      const { result } = renderHook(() => useUIToggles());
      act(() => result.current.actions.showPanel('showCommissioner'));
      expect(result.current.state.showCommissioner).toBe(true);

      act(() => result.current.actions.hidePanel('showCommissioner'));
      expect(result.current.state.showCommissioner).toBe(false);
    });

    it('reset returns to initial state', () => {
      const { result } = renderHook(() => useUIToggles([{ id: 'p1' }]));
      act(() => result.current.actions.toggleUsageStats());
      act(() => result.current.actions.setGameComplete(true));
      act(() => result.current.actions.reset());

      expect(result.current.state.showUsageStats).toBe(false);
      expect(result.current.state.isGameMarkedComplete).toBe(false);
      expect(result.current.state.localPlayers).toEqual([]);
    });
  });
});
