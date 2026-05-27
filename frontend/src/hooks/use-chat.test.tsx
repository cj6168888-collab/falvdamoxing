import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useSendMessage, useQuickActions } from './use-chat';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useSendMessage', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useSendMessage('case-1'), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useQuickActions', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useQuickActions('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});
