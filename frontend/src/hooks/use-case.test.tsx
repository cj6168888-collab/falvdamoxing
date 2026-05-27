import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useCaseList, useCaseDetail, useCreateCase, useUpdateCase, useDeleteCase, useCurrentCase } from './use-case';
import { useCaseStore } from '@/stores/case.store';
import { createMockCase } from '@/test/fixtures';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useCaseList', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useCaseList({ status: 'active' }), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useCaseDetail', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useCaseDetail('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useCreateCase', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useCreateCase(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useUpdateCase', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useUpdateCase('case-1'), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useDeleteCase', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useDeleteCase(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useCurrentCase', () => {
  it('returns current case from store', () => {
    const mockCase = createMockCase({ id: 'case-1', title: 'Test Case' });
    useCaseStore.setState({ currentCase: mockCase });

    const { result } = renderHook(() => useCurrentCase());

    expect(result.current?.id).toBe('case-1');
    expect(result.current?.title).toBe('Test Case');
  });

  it('returns null when no current case', () => {
    useCaseStore.setState({ currentCase: null });

    const { result } = renderHook(() => useCurrentCase());

    expect(result.current).toBeNull();
  });
});
