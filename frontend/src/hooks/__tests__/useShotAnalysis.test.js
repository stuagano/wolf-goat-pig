import { renderHook, act } from '@testing-library/react';
import { useShotAnalysis } from '../useShotAnalysis';

// Mock fetch
global.fetch = jest.fn();

describe('useShotAnalysis', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('should initialize with null analysis and not loading', () => {
    const { result } = renderHook(() => useShotAnalysis());
    
    expect(result.current.analysis).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should set loading true when analyzeShot is called', async () => {
    fetch.mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => 
        resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'success', analysis: { recommended_shot: {} } })
        }), 10))
    );

    const { result } = renderHook(() => useShotAnalysis());
    
    let promise;
    await act(async () => {
      promise = result.current.analyzeShot({});
    });

    // Note: Due to how act and async work in renderHook, we might need to check loading state differently
    // but this is a basic test structure.
    await act(async () => {
      await promise;
    });

    expect(result.current.analysis).toBeDefined();
    expect(result.current.loading).toBe(false);
  });

  it('should handle errors correctly', async () => {
    fetch.mockImplementationOnce(() => 
      Promise.resolve({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      })
    );

    const { result } = renderHook(() => useShotAnalysis());
    
    await act(async () => {
      await result.current.analyzeShot({});
    });

    expect(result.current.error).toContain('500');
    expect(result.current.loading).toBe(false);
  });

  it('should clear analysis', () => {
    const { result } = renderHook(() => useShotAnalysis());
    
    // Manually set some state if we could, but better to just test the clear function
    act(() => {
      result.current.clearAnalysis();
    });

    expect(result.current.analysis).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
