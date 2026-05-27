import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  buildProfile,
  getKnowledgeGraph,
  queryKnowledge,
  recordInteraction,
  resolveGap,
  useEvidenceGaps,
  useKnowledgeGraph,
  useProfile,
} from './profile.api';
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

describe('profile api queries', () => {
  it('loads profile, knowledge graph, and evidence gaps', async () => {
    const responses: Record<string, unknown> = {
      '/api/v2/profile/summary/case-1': { case_id: 'case-1' },
      '/api/v2/profile/knowledge-graph/case-1': { nodes: [], edges: [] },
      '/api/v2/profile/gaps/case-1': { gaps: [] },
    };
    mockGet.mockImplementation((url: string) => Promise.resolve({ data: responses[url] }));

    const profileHook = renderHook(() => useProfile('case-1'), { wrapper: createWrapper() });
    const graphHook = renderHook(() => useKnowledgeGraph('case-1'), { wrapper: createWrapper() });
    const gapsHook = renderHook(() => useEvidenceGaps('case-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(profileHook.result.current.data).toEqual({ case_id: 'case-1' }));
    await waitFor(() => expect(graphHook.result.current.data).toEqual({ nodes: [], edges: [] }));
    await waitFor(() => expect(gapsHook.result.current.data).toEqual({ gaps: [] }));

    expect(mockGet).toHaveBeenCalledWith('/api/v2/profile/summary/case-1');
    expect(mockGet).toHaveBeenCalledWith('/api/v2/profile/knowledge-graph/case-1');
    expect(mockGet).toHaveBeenCalledWith('/api/v2/profile/gaps/case-1');
  });

  it('does not request profile resources without a case id', () => {
    renderHook(() => useProfile(''), { wrapper: createWrapper() });
    renderHook(() => useKnowledgeGraph(''), { wrapper: createWrapper() });
    renderHook(() => useEvidenceGaps(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('profile api commands', () => {
  it('loads graph and writes profile actions', async () => {
    mockGet.mockResolvedValueOnce({ data: { nodes: [] } });
    mockPost.mockResolvedValue({ data: { ok: true } });

    await expect(getKnowledgeGraph('case-1')).resolves.toEqual({ nodes: [] });
    await expect(recordInteraction(12, 'hello', 'chat')).resolves.toEqual({ ok: true });
    await expect(queryKnowledge(12, 'facts', 'evidence')).resolves.toEqual({ ok: true });
    await expect(resolveGap(12, 'gap-1', 'resolved')).resolves.toEqual({ ok: true });
    await expect(buildProfile(12, false)).resolves.toEqual({ ok: true });

    expect(mockGet).toHaveBeenCalledWith('/api/v2/profile/knowledge-graph/case-1');
    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/v2/profile/interaction', {
      case_id: 12,
      user_input: 'hello',
      input_type: 'chat',
      system_response: '',
    });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/v2/profile/knowledge/query', {
      case_id: 12,
      query: 'facts',
      knowledge_type: 'evidence',
    });
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/v2/profile/gap/resolve', {
      case_id: 12,
      gap_id: 'gap-1',
      resolution: 'resolved',
    });
    expect(mockPost).toHaveBeenNthCalledWith(4, '/api/v2/profile/build', {
      case_id: 12,
      use_ai: false,
    });
  });
});
