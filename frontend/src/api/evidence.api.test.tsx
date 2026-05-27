import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  analyzeRisk,
  checkCompleteness,
  correctEvidence,
  deleteEvidence,
  analyzeEvidenceRelationships,
  askEvidenceQuestion,
  getEvidenceGraph,
  updateEvidence,
  uploadEvidence,
  useEvidence,
  useEvidenceCount,
} from './evidence.api';
import type { ReactNode } from 'react';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockGet = axiosInstance.get as Mock;
const mockPost = axiosInstance.post as Mock;
const mockPut = axiosInstance.put as Mock;
const mockDelete = axiosInstance.delete as Mock;

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

const evidenceItems = [
  { id: 'ev-1', name: '转账记录' },
  { id: 'ev-2', name: '聊天记录' },
];

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPut.mockReset();
  mockDelete.mockReset();
});

describe('evidence api hooks', () => {
  it('loads evidence from evidence_list response shape', async () => {
    mockGet.mockResolvedValueOnce({ data: { evidence_list: evidenceItems } });

    const { result } = renderHook(() => useEvidence('12'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(evidenceItems));
    expect(mockGet).toHaveBeenCalledWith('/api/v2/evidence-graph/evidence/list', {
      params: { case_id: 12 },
    });
  });

  it('loads evidence from items response shape', async () => {
    mockGet.mockResolvedValueOnce({ data: { items: evidenceItems } });

    const { result } = renderHook(() => useEvidence('12'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(evidenceItems));
  });

  it('falls back to an empty list for unexpected response shape', async () => {
    mockGet.mockResolvedValueOnce({ data: { data: 'unexpected' } });

    const { result } = renderHook(() => useEvidence('12'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual([]));
  });

  it('does not request evidence without case id', () => {
    renderHook(() => useEvidence(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });

  it('loads evidence count', async () => {
    mockGet.mockResolvedValueOnce({ data: evidenceItems });

    const { result } = renderHook(() => useEvidenceCount('12'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toBe(2));
    expect(mockGet).toHaveBeenCalledWith('/api/v2/evidence-graph/evidence/list', {
      params: { case_id: 12 },
    });
  });
});

describe('evidence api commands', () => {
  it('uploads evidence as multipart form data', async () => {
    const formData = new FormData();
    formData.append('files', new File(['hello'], 'evidence.txt', { type: 'text/plain' }));
    const response = { uploaded: 1 };
    mockPost.mockResolvedValueOnce({ data: response });

    await expect(uploadEvidence('12', formData)).resolves.toEqual(response);
    expect(mockPost).toHaveBeenCalledWith('/api/documents/upload-batch/12', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  });

  it('updates evidence with id merged into payload', async () => {
    const response = { id: 'ev-1', name: '修正后的证据' };
    mockPut.mockResolvedValueOnce({ data: response });

    await expect(updateEvidence('ev-1', { name: '修正后的证据' })).resolves.toEqual(response);
    expect(mockPut).toHaveBeenCalledWith('/api/v2/evidence-graph/evidence/update', {
      id: 'ev-1',
      name: '修正后的证据',
    });
  });

  it('deletes evidence', async () => {
    const response = { status: 204 };
    mockDelete.mockResolvedValueOnce(response);

    await expect(deleteEvidence('ev-1')).resolves.toEqual(response);
    expect(mockDelete).toHaveBeenCalledWith('/api/evidence/ev-1');
  });

  it('checks completeness and analyzes risk', async () => {
    mockPost
      .mockResolvedValueOnce({ data: { score: 86 } })
      .mockResolvedValueOnce({ data: { risks: [] } });

    await expect(checkCompleteness('12')).resolves.toEqual({ score: 86 });
    await expect(analyzeRisk('12')).resolves.toEqual({ risks: [] });

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/evidence/check-completeness', { caseId: '12' });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/evidence/risk-analyze/12');
  });

  it('submits evidence corrections', async () => {
    const payload = { evidenceId: 'ev-1', corrections: { type: '书证' } };
    mockPost.mockResolvedValueOnce({ data: { corrected: true } });

    await expect(correctEvidence(payload)).resolves.toEqual({ corrected: true });
    expect(mockPost).toHaveBeenCalledWith('/api/v2/evidence-graph/evidence/correct', payload);
  });

  it('loads evidence graph data', async () => {
    const graph = { nodes: [], edges: [] };
    mockGet.mockResolvedValueOnce({ data: graph });

    await expect(getEvidenceGraph('12')).resolves.toEqual(graph);
    expect(mockGet).toHaveBeenCalledWith('/api/v2/evidence-graph/graph/data', {
      params: { case_id: 12, view_type: 'default' },
    });
  });

  it('analyzes graph relationships and asks case evidence questions', async () => {
    mockPost
      .mockResolvedValueOnce({ data: { relationships: 1 } })
      .mockResolvedValueOnce({ data: { answer: '可以证明付款事实' } });

    await expect(analyzeEvidenceRelationships('12')).resolves.toEqual({ relationships: 1 });
    await expect(askEvidenceQuestion('12', '这份证据能证明什么？', 'conv-1')).resolves.toEqual({
      answer: '可以证明付款事实',
    });

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/v2/evidence-graph/relationships/analyze', {
      case_id: 12,
      force_refresh: true,
    });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/evidence/qa', {
      case_id: 12,
      question: '这份证据能证明什么？',
      conversation_id: 'conv-1',
    });
  });
});
