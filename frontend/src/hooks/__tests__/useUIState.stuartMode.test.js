// frontend/src/hooks/__tests__/useUIState.stuartMode.test.js
import { renderHook, act } from '@testing-library/react';
import { useUIState } from '../useUIState';
import { useFeatureFlags } from '../useFeatureFlags';

vi.mock('../useFeatureFlags', () => ({ useFeatureFlags: vi.fn() }));

beforeEach(() => {
  localStorage.clear();
  useFeatureFlags.mockReturnValue({ stuart_mode: true });
});

test.each(['auto', 'coach'])('disabled feature overrides saved %s and all setters', (mode) => {
  useFeatureFlags.mockReturnValue({ stuart_mode: false });
  localStorage.setItem('wgp_assist_mode', mode);
  localStorage.setItem('wgp_stuart_mode', 'true');
  const { result, rerender } = renderHook(() => useUIState());
  expect(result.current.assistMode).toBe('off');
  act(() => { result.current.setAssistMode('auto'); result.current.toggleStuartMode(); });
  expect(result.current.stuartMode).toBe(false);
  expect(result.current.coachMode).toBe(false);
  useFeatureFlags.mockReturnValue({ stuart_mode: true });
  rerender();
  act(() => { result.current.setAssistMode('auto'); });
  expect(result.current.stuartMode).toBe(true);
  useFeatureFlags.mockReturnValue({ stuart_mode: false });
  rerender();
  expect(result.current.assistMode).toBe('off');
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
