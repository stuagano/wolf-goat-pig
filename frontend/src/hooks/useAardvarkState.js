/**
 * useAardvarkState - Aardvark mechanics state management
 *
 * Manages the Aardvark (5th player) and Invisible Aardvark (4-man) mechanics:
 * - aardvarkRequestedTeam ('team1' or 'team2')
 * - aardvarkTossed (was Aardvark rejected?)
 * - aardvarkSolo (Aardvark going solo - Tunkarri)
 * - invisibleAardvarkTossed (4-man game variant)
 */

import { useReducer, useMemo } from 'react';

export const AARDVARK_ACTIONS = {
  REQUEST_TEAM: 'REQUEST_TEAM',
  TOSS: 'TOSS',
  GO_SOLO: 'GO_SOLO',
  INVISIBLE_TOSS: 'INVISIBLE_TOSS',
  ACCEPT: 'ACCEPT',
  RESET: 'RESET',
};

export const initialAardvarkState = () => ({
  requestedTeam: null,
  tossed: false,
  solo: false,
  invisibleTossed: false,
});

export function aardvarkReducer(state, action) {
  switch (action.type) {
    case AARDVARK_ACTIONS.REQUEST_TEAM:
      return { ...state, requestedTeam: action.team };

    case AARDVARK_ACTIONS.TOSS:
      return { ...state, tossed: true, requestedTeam: null };

    case AARDVARK_ACTIONS.GO_SOLO:
      return { ...state, solo: true, tossed: true, requestedTeam: null };

    case AARDVARK_ACTIONS.INVISIBLE_TOSS:
      return { ...state, invisibleTossed: true };

    case AARDVARK_ACTIONS.ACCEPT:
      return { ...state, tossed: false, requestedTeam: null };

    case AARDVARK_ACTIONS.RESET:
      return initialAardvarkState();

    default:
      return state;
  }
}

export function useAardvarkState() {
  const [state, dispatch] = useReducer(aardvarkReducer, null, initialAardvarkState);

  const actions = useMemo(() => ({
    requestTeam: (team) => dispatch({ type: AARDVARK_ACTIONS.REQUEST_TEAM, team }),
    toss: () => dispatch({ type: AARDVARK_ACTIONS.TOSS }),
    goSolo: () => dispatch({ type: AARDVARK_ACTIONS.GO_SOLO }),
    invisibleToss: () => dispatch({ type: AARDVARK_ACTIONS.INVISIBLE_TOSS }),
    accept: () => dispatch({ type: AARDVARK_ACTIONS.ACCEPT }),
    reset: () => dispatch({ type: AARDVARK_ACTIONS.RESET }),
  }), []);

  const isAardvarkActive = useMemo(() =>
    state.requestedTeam !== null && !state.tossed,
  [state.requestedTeam, state.tossed]);

  return { state, dispatch, actions, isAardvarkActive };
}

export default useAardvarkState;
