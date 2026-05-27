import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useEvidenceList,
  useUploadEvidence,
  useUpdateEvidence,
  useDeleteEvidence,
  useEvidenceCompleteness,
  useEvidenceGraph,
} from './use-evidence';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useEvidenceList', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useEvidenceList('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useUploadEvidence', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useUploadEvidence('case-1'), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useUpdateEvidence', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useUpdateEvidence(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useDeleteEvidence', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useDeleteEvidence(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useEvidenceCompleteness', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useEvidenceCompleteness('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useEvidenceGraph', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useEvidenceGraph('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});
