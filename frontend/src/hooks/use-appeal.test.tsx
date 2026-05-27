import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useAppealList,
  useAppealArgumentsList,
  useCreateAppeal,
  useCreateAppealArgument,
} from './use-appeal';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useAppealList', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useAppealList('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useAppealArgumentsList', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useAppealArgumentsList('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useCreateAppeal', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useCreateAppeal(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useCreateAppealArgument', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useCreateAppealArgument(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});
