import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useDocumentList,
  useDocumentTemplates,
  useGenerateDocument,
  useDocumentSuggestions,
} from './use-document';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('useDocumentList', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useDocumentList('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useDocumentTemplates', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useDocumentTemplates(), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});

describe('useGenerateDocument', () => {
  it('returns a mutation object', () => {
    const { result } = renderHook(() => useGenerateDocument(), { wrapper: createWrapper() });
    expect(result.current.mutate).toBeDefined();
    expect(result.current.mutateAsync).toBeDefined();
    expect(result.current.isIdle).toBe(true);
  });
});

describe('useDocumentSuggestions', () => {
  it('returns query object with expected structure', () => {
    const { result } = renderHook(() => useDocumentSuggestions('case-1'), { wrapper: createWrapper() });
    expect(result.current).toHaveProperty('data');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('error');
  });
});
