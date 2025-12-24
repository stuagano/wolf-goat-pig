import { renderHook, act } from '@testing-library/react';
import {
  useAsyncState,
  asyncReducer,
  ASYNC_ACTIONS,
  initialAsyncState
} from '../useAsyncState';

describe('useAsyncState', () => {
  describe('initialAsyncState', () => {
    it('has correct default values', () => {
      expect(initialAsyncState()).toEqual({
        submitting: false,
        error: null,
        courseData: null,
        courseDataLoading: false,
        courseDataError: null,
        rotationError: null,
      });
    });
  });

  describe('asyncReducer', () => {
    it('START_SUBMIT sets submitting and clears error', () => {
      const state = { ...initialAsyncState(), error: 'Previous error' };
      const result = asyncReducer(state, { type: ASYNC_ACTIONS.START_SUBMIT });
      expect(result.submitting).toBe(true);
      expect(result.error).toBeNull();
    });

    it('SUBMIT_SUCCESS clears submitting and error', () => {
      const state = { ...initialAsyncState(), submitting: true };
      const result = asyncReducer(state, { type: ASYNC_ACTIONS.SUBMIT_SUCCESS });
      expect(result.submitting).toBe(false);
      expect(result.error).toBeNull();
    });

    it('SUBMIT_ERROR sets error and clears submitting', () => {
      const state = { ...initialAsyncState(), submitting: true };
      const result = asyncReducer(state, { type: ASYNC_ACTIONS.SUBMIT_ERROR, error: 'Failed' });
      expect(result.submitting).toBe(false);
      expect(result.error).toBe('Failed');
    });

    it('START_COURSE_LOAD sets loading and clears error', () => {
      const state = { ...initialAsyncState(), courseDataError: 'Previous' };
      const result = asyncReducer(state, { type: ASYNC_ACTIONS.START_COURSE_LOAD });
      expect(result.courseDataLoading).toBe(true);
      expect(result.courseDataError).toBeNull();
    });

    it('COURSE_LOAD_SUCCESS sets data and clears loading/error', () => {
      const courseData = { name: 'Test Course', holes: [] };
      const state = { ...initialAsyncState(), courseDataLoading: true };
      const result = asyncReducer(state, { type: ASYNC_ACTIONS.COURSE_LOAD_SUCCESS, data: courseData });
      expect(result.courseDataLoading).toBe(false);
      expect(result.courseData).toEqual(courseData);
      expect(result.courseDataError).toBeNull();
    });

    it('COURSE_LOAD_ERROR sets error and clears loading', () => {
      const state = { ...initialAsyncState(), courseDataLoading: true };
      const result = asyncReducer(state, { type: ASYNC_ACTIONS.COURSE_LOAD_ERROR, error: 'Not found' });
      expect(result.courseDataLoading).toBe(false);
      expect(result.courseDataError).toBe('Not found');
    });

    it('SET_ROTATION_ERROR sets rotation error', () => {
      const state = initialAsyncState();
      const result = asyncReducer(state, { type: ASYNC_ACTIONS.SET_ROTATION_ERROR, error: 'Invalid rotation' });
      expect(result.rotationError).toBe('Invalid rotation');
    });

    it('CLEAR_ERRORS clears all errors', () => {
      const state = {
        ...initialAsyncState(),
        error: 'Submit error',
        courseDataError: 'Course error',
        rotationError: 'Rotation error',
      };
      const result = asyncReducer(state, { type: ASYNC_ACTIONS.CLEAR_ERRORS });
      expect(result.error).toBeNull();
      expect(result.courseDataError).toBeNull();
      expect(result.rotationError).toBeNull();
    });

    it('RESET returns to initial state', () => {
      const state = {
        submitting: true,
        error: 'Error',
        courseData: { name: 'Course' },
        courseDataLoading: true,
        courseDataError: 'Course error',
        rotationError: 'Rotation error',
      };
      const result = asyncReducer(state, { type: ASYNC_ACTIONS.RESET });
      expect(result).toEqual(initialAsyncState());
    });

    it('handles unknown action', () => {
      const state = initialAsyncState();
      expect(asyncReducer(state, { type: 'UNKNOWN' })).toEqual(state);
    });
  });

  describe('useAsyncState hook', () => {
    it('returns state and actions', () => {
      const { result } = renderHook(() => useAsyncState());
      expect(result.current.state.submitting).toBe(false);
      expect(typeof result.current.actions.startSubmit).toBe('function');
    });

    it('computes hasError when no errors', () => {
      const { result } = renderHook(() => useAsyncState());
      expect(result.current.hasError).toBe(false);
    });

    it('computes hasError when error exists', () => {
      const { result } = renderHook(() => useAsyncState());
      act(() => result.current.actions.submitError('Failed'));
      expect(result.current.hasError).toBe(true);
    });

    it('computes hasError when courseDataError exists', () => {
      const { result } = renderHook(() => useAsyncState());
      act(() => result.current.actions.courseLoadError('Not found'));
      expect(result.current.hasError).toBe(true);
    });

    it('computes hasError when rotationError exists', () => {
      const { result } = renderHook(() => useAsyncState());
      act(() => result.current.actions.setRotationError('Invalid'));
      expect(result.current.hasError).toBe(true);
    });

    it('computes isLoading when submitting', () => {
      const { result } = renderHook(() => useAsyncState());
      expect(result.current.isLoading).toBe(false);

      act(() => result.current.actions.startSubmit());
      expect(result.current.isLoading).toBe(true);

      act(() => result.current.actions.submitSuccess());
      expect(result.current.isLoading).toBe(false);
    });

    it('computes isLoading when loading course data', () => {
      const { result } = renderHook(() => useAsyncState());
      act(() => result.current.actions.startCourseLoad());
      expect(result.current.isLoading).toBe(true);

      act(() => result.current.actions.courseLoadSuccess({ name: 'Test' }));
      expect(result.current.isLoading).toBe(false);
    });

    it('submit workflow works', () => {
      const { result } = renderHook(() => useAsyncState());

      act(() => result.current.actions.startSubmit());
      expect(result.current.state.submitting).toBe(true);
      expect(result.current.isLoading).toBe(true);

      act(() => result.current.actions.submitSuccess());
      expect(result.current.state.submitting).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    it('course load workflow works', () => {
      const { result } = renderHook(() => useAsyncState());
      const courseData = { name: 'Test Course', holes: [1, 2, 3] };

      act(() => result.current.actions.startCourseLoad());
      expect(result.current.state.courseDataLoading).toBe(true);

      act(() => result.current.actions.courseLoadSuccess(courseData));
      expect(result.current.state.courseDataLoading).toBe(false);
      expect(result.current.state.courseData).toEqual(courseData);
    });

    it('clearErrors clears all error types', () => {
      const { result } = renderHook(() => useAsyncState());

      act(() => result.current.actions.submitError('Submit failed'));
      act(() => result.current.actions.courseLoadError('Load failed'));
      act(() => result.current.actions.setRotationError('Rotation failed'));
      expect(result.current.hasError).toBe(true);

      act(() => result.current.actions.clearErrors());
      expect(result.current.hasError).toBe(false);
    });

    it('reset clears everything', () => {
      const { result } = renderHook(() => useAsyncState());

      act(() => result.current.actions.startSubmit());
      act(() => result.current.actions.courseLoadSuccess({ name: 'Test' }));
      act(() => result.current.actions.reset());

      expect(result.current.state).toEqual(initialAsyncState());
    });
  });
});
