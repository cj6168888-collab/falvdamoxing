import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  useCaseDetail,
  useCases,
  useExportData,
  useInterpretations,
  useLawDetail,
  useLaws,
  useSemanticSearch,
  useStats,
  useTriggerImport,
} from './legal-knowledge.api';
import type { ReactNode } from 'react';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockGet = axiosInstance.get as Mock;
const mockPost = axiosInstance.post as Mock;

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
});

describe('legal knowledge api queries', () => {
  it('loads legal knowledge resources', async () => {
    const responses: Record<string, unknown> = {
      '/api/legal-knowledge/laws': { laws: [{ id: 'law-1' }], total: 1, page: 2, page_size: 10 },
      '/api/legal-knowledge/laws/law-1': { id: 'law-1' },
      '/api/legal-knowledge/interpretations': { interpretations: [{ id: 'int-1' }], total: 1, page: 1, page_size: 20 },
      '/api/legal-knowledge/cases': { cases: [{ id: 'case-1' }], total: 1, page: 1, page_size: 20 },
      '/api/legal-knowledge/cases/case-1': { id: 'case-1' },
      '/api/legal-knowledge/stats': { laws: 10 },
      '/api/legal-knowledge/search': { results: [] },
    };
    mockGet.mockImplementation((url: string) => Promise.resolve({ data: responses[url] }));

    const lawsHook = renderHook(() => useLaws('contract', 'civil', 'Civil Code', 2, 10), { wrapper: createWrapper() });
    const lawDetailHook = renderHook(() => useLawDetail('law-1'), { wrapper: createWrapper() });
    const interpretationsHook = renderHook(() => useInterpretations('loan'), { wrapper: createWrapper() });
    const casesHook = renderHook(() => useCases('contract', 'guiding'), { wrapper: createWrapper() });
    const caseDetailHook = renderHook(() => useCaseDetail('case-1'), { wrapper: createWrapper() });
    const statsHook = renderHook(() => useStats(), { wrapper: createWrapper() });
    const semanticHook = renderHook(() => useSemanticSearch('loan', 'laws', 5), { wrapper: createWrapper() });

    await waitFor(() => expect(lawsHook.result.current.data).toEqual({ laws: [{ id: 'law-1' }], total: 1, page: 2, page_size: 10 }));
    await waitFor(() => expect(lawDetailHook.result.current.data).toEqual({ id: 'law-1' }));
    await waitFor(() => expect(interpretationsHook.result.current.data).toEqual({ interpretations: [{ id: 'int-1' }], total: 1, page: 1, page_size: 20 }));
    await waitFor(() => expect(casesHook.result.current.data).toEqual({ cases: [{ id: 'case-1' }], total: 1, page: 1, page_size: 20 }));
    await waitFor(() => expect(caseDetailHook.result.current.data).toEqual({ id: 'case-1' }));
    await waitFor(() => expect(statsHook.result.current.data).toEqual({ laws: 10 }));
    await waitFor(() => expect(semanticHook.result.current.data).toEqual({ results: [] }));

    expect(mockGet).toHaveBeenCalledWith('/api/legal-knowledge/laws', {
      params: { keyword: 'contract', category: 'civil', law_name: 'Civil Code', page: 2, page_size: 10 },
    });
    expect(mockGet).toHaveBeenCalledWith('/api/legal-knowledge/laws/law-1');
    expect(mockGet).toHaveBeenCalledWith('/api/legal-knowledge/interpretations', {
      params: { keyword: 'loan', page: 1, page_size: 20 },
    });
    expect(mockGet).toHaveBeenCalledWith('/api/legal-knowledge/cases', {
      params: { keyword: 'contract', case_type: 'guiding', page: 1, page_size: 20 },
    });
    expect(mockGet).toHaveBeenCalledWith('/api/legal-knowledge/cases/case-1');
    expect(mockGet).toHaveBeenCalledWith('/api/legal-knowledge/stats');
    expect(mockGet).toHaveBeenCalledWith('/api/legal-knowledge/search', {
      params: { keyword: 'loan', search_type: 'laws', limit: 5 },
    });
  });

  it('does not run disabled legal knowledge searches', () => {
    renderHook(() => useLaws(), { wrapper: createWrapper() });
    renderHook(() => useLawDetail(''), { wrapper: createWrapper() });
    renderHook(() => useInterpretations(), { wrapper: createWrapper() });
    renderHook(() => useCases(), { wrapper: createWrapper() });
    renderHook(() => useCaseDetail(''), { wrapper: createWrapper() });
    renderHook(() => useSemanticSearch('a'), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('legal knowledge api mutations', () => {
  it('triggers import and exports data', async () => {
    mockPost.mockResolvedValueOnce({ data: { imported: true } });
    mockGet.mockResolvedValueOnce({ data: { exported: true } });

    const triggerImport = renderHook(() => useTriggerImport(), { wrapper: createWrapper() });
    const exportData = renderHook(() => useExportData('laws', 'csv'), { wrapper: createWrapper() });

    await expect(triggerImport.result.current.mutateAsync()).resolves.toEqual({ imported: true });
    await expect(exportData.result.current.mutateAsync()).resolves.toEqual({ exported: true });

    expect(mockPost).toHaveBeenCalledWith('/api/legal-knowledge/import');
    expect(mockGet).toHaveBeenCalledWith('/api/legal-knowledge/export', {
      params: { export_type: 'laws', format: 'csv' },
    });
  });
});
