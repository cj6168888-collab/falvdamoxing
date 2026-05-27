import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import type { CaseFilters } from '@/types/case.types';
import {
  analyzeCase,
  closeCase,
  createCase,
  deleteCase,
  getCaseStrategy,
  getCaseStructure,
  reopenCase,
  updateCase,
  useCase,
  useCases,
} from './case.api';
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

const rawCase = {
  id: 7,
  title: '合同纠纷',
  case_type: 'contract',
  status: 'negotiating',
  description: '合同履行争议',
  claim_amount: '120000',
  plaintiff: '张三',
  defendant: '李四',
  evidence_count: 4,
  document_count: 2,
  deadline_count: 1,
  created_at: '2026-05-01T00:00:00.000Z',
  updated_at: '2026-05-10T00:00:00.000Z',
};

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPut.mockReset();
  mockDelete.mockReset();
});

describe('case api hooks', () => {
  it('loads and transforms case list', async () => {
    const filters: CaseFilters = { status: 'negotiating', type: 'contract' };
    mockGet.mockResolvedValueOnce({ data: [rawCase] });

    const { result } = renderHook(() => useCases(filters), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data?.[0]?.id).toBe('7'));
    expect(result.current.data?.[0]).toMatchObject({
      title: '合同纠纷',
      type: 'contract',
      status: 'negotiating',
      amount: 120000,
      plaintiff: { name: '张三' },
      defendant: { name: '李四' },
      evidenceCount: 4,
      documentCount: 2,
      deadlineCount: 1,
      createdAt: '2026-05-01T00:00:00.000Z',
      updatedAt: '2026-05-10T00:00:00.000Z',
    });
    expect(mockGet).toHaveBeenCalledWith('/api/cases', { params: filters });
  });

  it('loads and transforms case detail', async () => {
    mockGet.mockResolvedValueOnce({ data: rawCase });

    const { result } = renderHook(() => useCase('7'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data?.id).toBe('7'));
    expect(result.current.data?.title).toBe('合同纠纷');
    expect(mockGet).toHaveBeenCalledWith('/api/cases/7');
  });

  it('does not request case detail without an id', () => {
    renderHook(() => useCase(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('case api commands', () => {
  it('creates a case', async () => {
    const created = { id: 'case-new', title: '新案件' };
    mockPost.mockResolvedValueOnce({ data: created });

    await expect(createCase({ title: '新案件' })).resolves.toEqual(created);
    expect(mockPost).toHaveBeenCalledWith('/api/cases', { title: '新案件' });
  });

  it('updates a case', async () => {
    const updated = { id: '7', title: '更新后的案件' };
    mockPut.mockResolvedValueOnce({ data: updated });

    await expect(updateCase('7', { title: '更新后的案件' })).resolves.toEqual(updated);
    expect(mockPut).toHaveBeenCalledWith('/api/cases/7', { title: '更新后的案件' });
  });

  it('deletes a case', async () => {
    const response = { status: 204 };
    mockDelete.mockResolvedValueOnce(response);

    await expect(deleteCase('7')).resolves.toEqual(response);
    expect(mockDelete).toHaveBeenCalledWith('/api/cases/7');
  });

  it('closes and reopens a case', async () => {
    mockPost.mockResolvedValue({ data: { ok: true } });

    await closeCase('7');
    await reopenCase('7');

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/cases/7/close');
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/cases/7/reopen');
  });

  it('requests case analysis and strategy', async () => {
    mockPost
      .mockResolvedValueOnce({ data: { summary: 'analysis' } })
      .mockResolvedValueOnce({ data: { strategy: 'settle' } });

    await expect(analyzeCase('7')).resolves.toEqual({ summary: 'analysis' });
    await expect(getCaseStrategy('7')).resolves.toEqual({ strategy: 'settle' });

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/cases/7/analyze');
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/cases/7/strategy');
  });

  it('loads case structure', async () => {
    const structure = { claims: [], evidence: [] };
    mockGet.mockResolvedValueOnce({ data: structure });

    await expect(getCaseStructure('7')).resolves.toEqual(structure);
    expect(mockGet).toHaveBeenCalledWith('/api/cases/7/structure');
  });
});
