import { renderHook, act } from '@testing-library/react';
import { useUIState } from '../useUIState';

describe('useUIState', () => {
  describe('initial state', () => {
    test('should initialize with default section visibility', () => {
      const { result } = renderHook(() => useUIState());
      
      expect(result.current.showTeamSelection).toBe(true);
      expect(result.current.showGolfScores).toBe(false);
      expect(result.current.showCommissioner).toBe(false);
      expect(result.current.showNotes).toBe(false);
      expect(result.current.showSpecialActions).toBe(false);
      expect(result.current.showUsageStats).toBe(false);
      expect(result.current.showAdvancedBetting).toBe(false);
    });

    test('should initialize with no errors and not submitting', () => {
      const { result } = renderHook(() => useUIState());
      
      expect(result.current.submitting).toBe(false);
      expect(result.current.error).toBeNull();
    });

    test('should initialize with no editing states', () => {
      const { result } = renderHook(() => useUIState());
      
      expect(result.current.editingHole).toBeNull();
      expect(result.current.editingPlayerName).toBeNull();
      expect(result.current.editPlayerNameValue).toBe('');
      expect(result.current.isEditingCompleteGame).toBe(false);
      expect(result.current.isGameMarkedComplete).toBe(false);
    });
  });

  describe('toggleSection', () => {
    test('should toggle teamSelection visibility', () => {
      const { result } = renderHook(() => useUIState());
      
      expect(result.current.showTeamSelection).toBe(true);
      
      act(() => {
        result.current.toggleSection('teamSelection');
      });
      
      expect(result.current.showTeamSelection).toBe(false);
      
      act(() => {
        result.current.toggleSection('teamSelection');
      });
      
      expect(result.current.showTeamSelection).toBe(true);
    });

    test('should toggle golfScores visibility', () => {
      const { result } = renderHook(() => useUIState());
      
      expect(result.current.showGolfScores).toBe(false);
      
      act(() => {
        result.current.toggleSection('golfScores');
      });
      
      expect(result.current.showGolfScores).toBe(true);
    });

    test('should toggle commissioner visibility', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.toggleSection('commissioner');
      });
      
      expect(result.current.showCommissioner).toBe(true);
    });

    test('should toggle notes visibility', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.toggleSection('notes');
      });
      
      expect(result.current.showNotes).toBe(true);
    });

    test('should toggle specialActions visibility', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.toggleSection('specialActions');
      });
      
      expect(result.current.showSpecialActions).toBe(true);
    });

    test('should toggle usageStats visibility', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.toggleSection('usageStats');
      });
      
      expect(result.current.showUsageStats).toBe(true);
    });

    test('should toggle advancedBetting visibility', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.toggleSection('advancedBetting');
      });
      
      expect(result.current.showAdvancedBetting).toBe(true);
    });

    test('should warn on unknown section', () => {
      const { result } = renderHook(() => useUIState());
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      
      act(() => {
        result.current.toggleSection('unknownSection');
      });
      
      expect(warnSpy).toHaveBeenCalledWith('Unknown section: unknownSection');
      warnSpy.mockRestore();
    });
  });

  describe('player name editing', () => {
    test('should start editing player name', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.startEditingPlayerName('player-123', 'John Doe');
      });
      
      expect(result.current.editingPlayerName).toBe('player-123');
      expect(result.current.editPlayerNameValue).toBe('John Doe');
    });

    test('should cancel editing player name', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.startEditingPlayerName('player-123', 'John Doe');
      });
      
      act(() => {
        result.current.cancelEditingPlayerName();
      });
      
      expect(result.current.editingPlayerName).toBeNull();
      expect(result.current.editPlayerNameValue).toBe('');
    });
  });

  describe('error handling', () => {
    test('should set error', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.setError('Something went wrong');
      });
      
      expect(result.current.error).toBe('Something went wrong');
    });

    test('should clear error', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.setError('Something went wrong');
      });
      
      act(() => {
        result.current.clearError();
      });
      
      expect(result.current.error).toBeNull();
    });

    test('should set error with auto-clear', async () => {
      jest.useFakeTimers();
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.setErrorWithAutoClear('Temporary error', 1000);
      });
      
      expect(result.current.error).toBe('Temporary error');
      
      act(() => {
        jest.advanceTimersByTime(1000);
      });
      
      expect(result.current.error).toBeNull();
      jest.useRealTimers();
    });

    test('should not auto-clear error when clearAfterMs is 0', () => {
      jest.useFakeTimers();
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.setErrorWithAutoClear('Permanent error', 0);
      });
      
      expect(result.current.error).toBe('Permanent error');
      
      act(() => {
        jest.advanceTimersByTime(5000);
      });
      
      expect(result.current.error).toBe('Permanent error');
      jest.useRealTimers();
    });
  });

  describe('submitting state', () => {
    test('should toggle submitting state', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.setSubmitting(true);
      });
      
      expect(result.current.submitting).toBe(true);
      
      act(() => {
        result.current.setSubmitting(false);
      });
      
      expect(result.current.submitting).toBe(false);
    });
  });

  describe('resetForNewHole', () => {
    test('should reset error and editing hole', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.setError('Some error');
        result.current.setEditingHole(5);
      });
      
      expect(result.current.error).toBe('Some error');
      expect(result.current.editingHole).toBe(5);
      
      act(() => {
        result.current.resetForNewHole();
      });
      
      expect(result.current.error).toBeNull();
      expect(result.current.editingHole).toBeNull();
    });
  });

  describe('direct setters', () => {
    test('should set editing hole directly', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.setEditingHole(7);
      });
      
      expect(result.current.editingHole).toBe(7);
    });

    test('should set isEditingCompleteGame directly', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.setIsEditingCompleteGame(true);
      });
      
      expect(result.current.isEditingCompleteGame).toBe(true);
    });

    test('should set isGameMarkedComplete directly', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.setIsGameMarkedComplete(true);
      });
      
      expect(result.current.isGameMarkedComplete).toBe(true);
    });

    test('should set editPlayerNameValue directly', () => {
      const { result } = renderHook(() => useUIState());
      
      act(() => {
        result.current.setEditPlayerNameValue('New Name');
      });
      
      expect(result.current.editPlayerNameValue).toBe('New Name');
    });
  });
});
