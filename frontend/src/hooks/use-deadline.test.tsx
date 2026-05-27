import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useDeadlineList,
  useCreateDeadline,
  useUpdateDeadline,
  useGenerateMilestones,
} from './use-deadline';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useDeadlineList', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useDeadlineList('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useCreateDeadline', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useCreateDeadline(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useUpdateDeadline', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useUpdateDeadline(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useGenerateMilestones', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useGenerateMilestones(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});
