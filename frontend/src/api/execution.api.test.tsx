import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  generateExecutionApplication,
  useCreateExecutionAsset,
  useCreateExecutionRecord,
  useCreateExecutionTask,
  useDeleteExecutionAsset,
  useDeleteExecutionRecord,
  useDeleteExecutionTask,
  useExecutionAssets,
  useExecutionOverview,
  useExecutionRecords,
  useExecutionStatistics,
  useExecutionTasks,
  useUpdateExecutionOverview,
  useUpdateExecutionTask,
} from './execution.api';
import type { ExecutionOverview } from '@/types/execution.types';
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

const overview: ExecutionOverview = {
  case_id: 12,
  case_title: 'Execution case',
  status: 'pending',
  progress: 30,
  total_records: 1,
  total_tasks: 2,
  todo_tasks: 1,
  in_progress_tasks: 1,
  completed_tasks: 0,
  total_assets: 1,
  controlled_assets: 0,
  disposed_assets: 0,
  stages: [],
};

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPut.mockReset();
  mockDelete.mockReset();
});

describe('execution api queries', () => {
  it('loads overview, records, tasks, assets, and statistics', async () => {
    mockGet
      .mockResolvedValueOnce({ data: overview })
      .mockResolvedValueOnce({ data: { records: [{ id: 1 }], total: 1 } })
      .mockResolvedValueOnce({ data: { tasks: [{ id: 1 }], total: 1 } })
      .mockResolvedValueOnce({ data: { assets: [{ id: 1 }], total: 1 } })
      .mockResolvedValueOnce({ data: { progress: 30 } });

    const overviewHook = renderHook(() => useExecutionOverview('12'), { wrapper: createWrapper() });
    const recordsHook = renderHook(() => useExecutionRecords('12'), { wrapper: createWrapper() });
    const tasksHook = renderHook(() => useExecutionTasks('12'), { wrapper: createWrapper() });
    const assetsHook = renderHook(() => useExecutionAssets('12'), { wrapper: createWrapper() });
    const statsHook = renderHook(() => useExecutionStatistics('12'), { wrapper: createWrapper() });

    await waitFor(() => expect(overviewHook.result.current.data).toEqual(overview));
    await waitFor(() => expect(recordsHook.result.current.data).toEqual({ records: [{ id: 1 }], total: 1 }));
    await waitFor(() => expect(tasksHook.result.current.data).toEqual({ tasks: [{ id: 1 }], total: 1 }));
    await waitFor(() => expect(assetsHook.result.current.data).toEqual({ assets: [{ id: 1 }], total: 1 }));
    await waitFor(() => expect(statsHook.result.current.data).toEqual({ progress: 30 }));

    expect(mockGet).toHaveBeenNthCalledWith(1, '/api/execution/case/12');
    expect(mockGet).toHaveBeenNthCalledWith(2, '/api/execution/case/12/records');
    expect(mockGet).toHaveBeenNthCalledWith(3, '/api/execution/case/12/tasks');
    expect(mockGet).toHaveBeenNthCalledWith(4, '/api/execution/case/12/assets');
    expect(mockGet).toHaveBeenNthCalledWith(5, '/api/execution/case/12/statistics');
  });

  it('does not request overview without a case id', () => {
    renderHook(() => useExecutionOverview(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('execution api mutations', () => {
  it('updates overview and manages records, tasks, and assets', async () => {
    mockPut.mockResolvedValue({ data: { ok: true } });
    mockPost.mockResolvedValue({ data: { id: 1 } });
    mockDelete.mockResolvedValue({ data: { deleted: true } });

    const updateOverview = renderHook(() => useUpdateExecutionOverview('12'), { wrapper: createWrapper() });
    const createRecord = renderHook(() => useCreateExecutionRecord('12'), { wrapper: createWrapper() });
    const deleteRecord = renderHook(() => useDeleteExecutionRecord('12'), { wrapper: createWrapper() });
    const createTask = renderHook(() => useCreateExecutionTask('12'), { wrapper: createWrapper() });
    const updateTask = renderHook(() => useUpdateExecutionTask('12'), { wrapper: createWrapper() });
    const deleteTask = renderHook(() => useDeleteExecutionTask('12'), { wrapper: createWrapper() });
    const createAsset = renderHook(() => useCreateExecutionAsset('12'), { wrapper: createWrapper() });
    const deleteAsset = renderHook(() => useDeleteExecutionAsset('12'), { wrapper: createWrapper() });

    await updateOverview.result.current.mutateAsync({ progress: 40 });
    await createRecord.result.current.mutateAsync({ title: 'Record', progress: 40 });
    await deleteRecord.result.current.mutateAsync(1);
    await createTask.result.current.mutateAsync({ title: 'Task', priority: 'high', status: 'todo' });
    await updateTask.result.current.mutateAsync({ taskId: 1, data: { status: 'completed' } });
    await deleteTask.result.current.mutateAsync(1);
    await createAsset.result.current.mutateAsync({ asset_name: 'Bank account', status: 'controlled' });
    await deleteAsset.result.current.mutateAsync(1);

    expect(mockPut).toHaveBeenNthCalledWith(1, '/api/execution/case/12', { progress: 40 });
    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/execution/case/12/records', { title: 'Record', progress: 40 });
    expect(mockDelete).toHaveBeenNthCalledWith(1, '/api/execution/records/1');
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/execution/case/12/tasks', { title: 'Task', priority: 'high', status: 'todo' });
    expect(mockPut).toHaveBeenNthCalledWith(2, '/api/execution/tasks/1', { status: 'completed' });
    expect(mockDelete).toHaveBeenNthCalledWith(2, '/api/execution/tasks/1');
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/execution/case/12/assets', { asset_name: 'Bank account', status: 'controlled' });
    expect(mockDelete).toHaveBeenNthCalledWith(3, '/api/execution/assets/1');
  });

  it('generates execution application', async () => {
    mockPost.mockResolvedValueOnce({ data: { document_id: 'doc-1' } });

    await expect(generateExecutionApplication('12')).resolves.toEqual({ document_id: 'doc-1' });
    expect(mockPost).toHaveBeenCalledWith('/api/execution/case/12/generate-application');
  });
});
