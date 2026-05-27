import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  generateAppealPetition,
  useAppeal,
  useAppealArguments,
  useAppealCountdown,
  useAppealDeadlines,
  useAppealDocuments,
  useAppeals,
  useAppealStatistics,
  useAppealStrategy,
  useCreateAppeal,
  useCreateAppealArgument,
  useCreateAppealDeadline,
  useCreateAppealDocument,
  useCreateAppealStrategy,
  useDeleteAppeal,
  useDeleteAppealArgument,
  useUpdateAppeal,
  useUpdateAppealArgument,
} from './appeal.api';
import type { ReactNode } from 'react';
import type {
  Appeal,
  AppealArgument,
  AppealDeadline,
  AppealDocument,
  SecondTrialStrategy,
} from '@/types/appeal.types';
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

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPut.mockReset();
  mockDelete.mockReset();
});

describe('appeal api queries', () => {
  it('loads appeal resources', async () => {
    const responses: Record<string, unknown> = {
      '/api/appeal/case/case-1/appeals': { appeals: [{ id: 'appeal-1' }], total: 1 },
      '/api/appeal/appeals/appeal-1': { appeal: { id: 'appeal-1', status: 'draft' } },
      '/api/appeal/case/case-1/arguments': { arguments: [{ id: 1 }], total: 1 },
      '/api/appeal/appeal/appeal-1/deadlines': { deadlines: [{ id: 1 }], total: 1 },
      '/api/appeal/appeal/appeal-1/documents': { documents: [{ id: 1 }], total: 1 },
      '/api/appeal/appeal/appeal-1/strategy': { strategy: { id: 1, title: 'strategy' } },
      '/api/appeal/appeal/appeal-1/countdown': { days_left: 3 },
      '/api/appeal/case/case-1/statistics': { total: 1 },
    };

    mockGet.mockImplementation((url: string) => Promise.resolve({ data: responses[url] }));

    const appealsHook = renderHook(() => useAppeals('case-1'), { wrapper: createWrapper() });
    const appealHook = renderHook(() => useAppeal('appeal-1'), { wrapper: createWrapper() });
    const argumentsHook = renderHook(() => useAppealArguments('case-1'), { wrapper: createWrapper() });
    const deadlinesHook = renderHook(() => useAppealDeadlines('appeal-1'), { wrapper: createWrapper() });
    const documentsHook = renderHook(() => useAppealDocuments('appeal-1'), { wrapper: createWrapper() });
    const strategyHook = renderHook(() => useAppealStrategy('appeal-1'), { wrapper: createWrapper() });
    const countdownHook = renderHook(() => useAppealCountdown('appeal-1'), { wrapper: createWrapper() });
    const statisticsHook = renderHook(() => useAppealStatistics('case-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(appealsHook.result.current.data).toEqual({ appeals: [{ id: 'appeal-1' }], total: 1 }));
    await waitFor(() => expect(appealHook.result.current.data).toEqual({ id: 'appeal-1', status: 'draft' }));
    await waitFor(() => expect(argumentsHook.result.current.data).toEqual({ arguments: [{ id: 1 }], total: 1 }));
    await waitFor(() => expect(deadlinesHook.result.current.data).toEqual({ deadlines: [{ id: 1 }], total: 1 }));
    await waitFor(() => expect(documentsHook.result.current.data).toEqual({ documents: [{ id: 1 }], total: 1 }));
    await waitFor(() => expect(strategyHook.result.current.data).toEqual({ id: 1, title: 'strategy' }));
    await waitFor(() => expect(countdownHook.result.current.data).toEqual({ days_left: 3 }));
    await waitFor(() => expect(statisticsHook.result.current.data).toEqual({ total: 1 }));

    Object.keys(responses).forEach((url) => {
      expect(mockGet).toHaveBeenCalledWith(url);
    });
  });

  it('does not request appeal resources without ids', () => {
    renderHook(() => useAppeals(''), { wrapper: createWrapper() });
    renderHook(() => useAppeal(''), { wrapper: createWrapper() });
    renderHook(() => useAppealArguments(''), { wrapper: createWrapper() });
    renderHook(() => useAppealDeadlines(''), { wrapper: createWrapper() });
    renderHook(() => useAppealDocuments(''), { wrapper: createWrapper() });
    renderHook(() => useAppealStrategy(''), { wrapper: createWrapper() });
    renderHook(() => useAppealStatistics(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('appeal api mutations', () => {
  it('creates, updates, and deletes appeal resources', async () => {
    mockPost.mockResolvedValue({ data: { ok: true } });
    mockPut.mockResolvedValue({ data: { updated: true } });
    mockDelete.mockResolvedValue({ data: { deleted: true } });

    const createAppeal = renderHook(() => useCreateAppeal('case-1'), { wrapper: createWrapper() });
    const updateAppeal = renderHook(() => useUpdateAppeal('appeal-1'), { wrapper: createWrapper() });
    const deleteAppeal = renderHook(() => useDeleteAppeal('case-1'), { wrapper: createWrapper() });
    const createArgument = renderHook(() => useCreateAppealArgument('case-1'), { wrapper: createWrapper() });
    const updateArgument = renderHook(() => useUpdateAppealArgument(), { wrapper: createWrapper() });
    const deleteArgument = renderHook(() => useDeleteAppealArgument('case-1'), { wrapper: createWrapper() });
    const createDeadline = renderHook(() => useCreateAppealDeadline('appeal-1'), { wrapper: createWrapper() });
    const createDocument = renderHook(() => useCreateAppealDocument('appeal-1'), { wrapper: createWrapper() });
    const createStrategy = renderHook(() => useCreateAppealStrategy('appeal-1'), { wrapper: createWrapper() });

    const newAppeal: Partial<Appeal> = { appellant_name: 'appeal' };
    const appealUpdate: Partial<Appeal> = { status: 'submitted' };
    const newArgument: Partial<AppealArgument> = { title: 'argument' };
    const argumentUpdate: Partial<AppealArgument> = { success_probability: 80 };
    const newDeadline: Partial<AppealDeadline> = { deadline_name: 'deadline' };
    const newDocument: Partial<AppealDocument> = { document_name: 'document' };
    const newStrategy: Partial<SecondTrialStrategy> = { title: 'strategy' };

    await createAppeal.result.current.mutateAsync(newAppeal);
    await updateAppeal.result.current.mutateAsync(appealUpdate);
    await deleteAppeal.result.current.mutateAsync(1);
    await createArgument.result.current.mutateAsync(newArgument);
    await updateArgument.result.current.mutateAsync({ argumentId: 2, data: argumentUpdate });
    await deleteArgument.result.current.mutateAsync(2);
    await createDeadline.result.current.mutateAsync(newDeadline);
    await createDocument.result.current.mutateAsync(newDocument);
    await createStrategy.result.current.mutateAsync(newStrategy);

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/appeal/case/case-1/appeals', newAppeal);
    expect(mockPut).toHaveBeenNthCalledWith(1, '/api/appeal/appeals/appeal-1', appealUpdate);
    expect(mockDelete).toHaveBeenNthCalledWith(1, '/api/appeal/appeals/1');
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/appeal/case/case-1/arguments', newArgument);
    expect(mockPut).toHaveBeenNthCalledWith(2, '/api/appeal/argument/2', argumentUpdate);
    expect(mockDelete).toHaveBeenNthCalledWith(2, '/api/appeal/argument/2');
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/appeal/appeal/appeal-1/deadlines', newDeadline);
    expect(mockPost).toHaveBeenNthCalledWith(4, '/api/appeal/appeal/appeal-1/documents', newDocument);
    expect(mockPost).toHaveBeenNthCalledWith(5, '/api/appeal/appeal/appeal-1/strategy', newStrategy);
  });

  it('generates an appeal petition', async () => {
    mockPost.mockResolvedValueOnce({ data: { document_id: 'doc-1' } });

    await expect(generateAppealPetition('appeal-1')).resolves.toEqual({ document_id: 'doc-1' });
    expect(mockPost).toHaveBeenCalledWith('/api/appeal/appeal/appeal-1/generate-petition');
  });
});
