// frontend/src/hooks/__tests__/useUIState.stuartMode.test.js
import { renderHook, act } from '@testing-library/react';
import { useUIState } from '../useUIState';

beforeEach(() => {
  localStorage.clear();
});

test('stuartMode defaults to false', () => {
  const { result } = renderHook(() => useUIState());
  expect(result.current.stuartMode).toBe(false);
});

test('toggleStuartMode flips stuartMode', () => {
  const { result } = renderHook(() => useUIState());
  act(() => { result.current.toggleStuartMode(); });
  expect(result.current.stuartMode).toBe(true);
  act(() => { result.current.toggleStuartMode(); });
  expect(result.current.stuartMode).toBe(false);
});

test('stuartMode persists to localStorage', () => {
  const { result } = renderHook(() => useUIState());
  act(() => { result.current.toggleStuartMode(); });
  expect(localStorage.getItem('wgp_stuart_mode')).toBe('true');
});

test('stuartMode restores from localStorage on mount', () => {
  localStorage.setItem('wgp_stuart_mode', 'true');
  const { result } = renderHook(() => useUIState());
  expect(result.current.stuartMode).toBe(true);
});
