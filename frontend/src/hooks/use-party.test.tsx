import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  usePartyList,
  useCreateParty,
  useUpdateParty,
  useDeleteParty,
} from './use-party';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('usePartyList', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => usePartyList('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useCreateParty', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useCreateParty(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useUpdateParty', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useUpdateParty(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useDeleteParty', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useDeleteParty(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});
