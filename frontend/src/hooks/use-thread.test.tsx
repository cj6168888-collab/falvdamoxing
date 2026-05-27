import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useThreadList,
  useCounterClaimList,
  useCreateThread,
  useUpdateThread,
} from './use-thread';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useThreadList', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useThreadList('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useCounterClaimList', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useCounterClaimList('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useCreateThread', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useCreateThread(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useUpdateThread', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useUpdateThread(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});
