import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useHearingList,
  useCreateHearing,
  useDetectTrap,
  useRealtimeAnalysis,
} from './use-hearing';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useHearingList', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useHearingList('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useCreateHearing', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useCreateHearing(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useDetectTrap', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useDetectTrap(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useRealtimeAnalysis', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useRealtimeAnalysis(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});
