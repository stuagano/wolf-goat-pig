/**
 * useAsyncState - Async/API state management
 *
 * Manages:
 * - submitting (is form submitting)
 * - error (error message)
 * - courseData, courseDataError, courseDataLoading
 * - rotationError
 */

import { useReducer, useMemo } from 'react';

export const ASYNC_ACTIONS = {
  START_SUBMIT: 'START_SUBMIT',
  SUBMIT_SUCCESS: 'SUBMIT_SUCCESS',
  SUBMIT_ERROR: 'SUBMIT_ERROR',
  START_COURSE_LOAD: 'START_COURSE_LOAD',
  COURSE_LOAD_SUCCESS: 'COURSE_LOAD_SUCCESS',
  COURSE_LOAD_ERROR: 'COURSE_LOAD_ERROR',
  SET_ROTATION_ERROR: 'SET_ROTATION_ERROR',
  CLEAR_ERRORS: 'CLEAR_ERRORS',
  RESET: 'RESET',
};

export const initialAsyncState = () => ({
  submitting: false,
  error: null,
  courseData: null,
  courseDataLoading: false,
  courseDataError: null,
  rotationError: null,
});

export function asyncReducer(state, action) {
  switch (action.type) {
    case ASYNC_ACTIONS.START_SUBMIT:
      return { ...state, submitting: true, error: null };

    case ASYNC_ACTIONS.SUBMIT_SUCCESS:
      return { ...state, submitting: false, error: null };

    case ASYNC_ACTIONS.SUBMIT_ERROR:
      return { ...state, submitting: false, error: action.error };

    case ASYNC_ACTIONS.START_COURSE_LOAD:
      return { ...state, courseDataLoading: true, courseDataError: null };

    case ASYNC_ACTIONS.COURSE_LOAD_SUCCESS:
      return { ...state, courseDataLoading: false, courseData: action.data, courseDataError: null };

    case ASYNC_ACTIONS.COURSE_LOAD_ERROR:
      return { ...state, courseDataLoading: false, courseDataError: action.error };

    case ASYNC_ACTIONS.SET_ROTATION_ERROR:
      return { ...state, rotationError: action.error };

    case ASYNC_ACTIONS.CLEAR_ERRORS:
      return { ...state, error: null, courseDataError: null, rotationError: null };

    case ASYNC_ACTIONS.RESET:
      return initialAsyncState();

    default:
      return state;
  }
}

export function useAsyncState() {
  const [state, dispatch] = useReducer(asyncReducer, null, initialAsyncState);

  const actions = useMemo(() => ({
    startSubmit: () => dispatch({ type: ASYNC_ACTIONS.START_SUBMIT }),
    submitSuccess: () => dispatch({ type: ASYNC_ACTIONS.SUBMIT_SUCCESS }),
    submitError: (error) => dispatch({ type: ASYNC_ACTIONS.SUBMIT_ERROR, error }),
    startCourseLoad: () => dispatch({ type: ASYNC_ACTIONS.START_COURSE_LOAD }),
    courseLoadSuccess: (data) => dispatch({ type: ASYNC_ACTIONS.COURSE_LOAD_SUCCESS, data }),
    courseLoadError: (error) => dispatch({ type: ASYNC_ACTIONS.COURSE_LOAD_ERROR, error }),
    setRotationError: (error) => dispatch({ type: ASYNC_ACTIONS.SET_ROTATION_ERROR, error }),
    clearErrors: () => dispatch({ type: ASYNC_ACTIONS.CLEAR_ERRORS }),
    reset: () => dispatch({ type: ASYNC_ACTIONS.RESET }),
  }), []);

  const hasError = useMemo(() =>
    !!(state.error || state.courseDataError || state.rotationError),
  [state.error, state.courseDataError, state.rotationError]);

  const isLoading = useMemo(() =>
    state.submitting || state.courseDataLoading,
  [state.submitting, state.courseDataLoading]);

  return { state, dispatch, actions, hasError, isLoading };
}

export default useAsyncState;
