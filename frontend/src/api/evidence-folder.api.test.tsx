import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  deleteFileRecord,
  disableMonitoring,
  enableMonitoring,
  getFolderConfig,
  getFolderFiles,
  getFolderStatus,
  getScanHistory,
  reprocessFile,
  triggerIncrementalScan,
  triggerScan,
  updateFolderConfig,
  useDeleteFileRecord,
  useDisableMonitoring,
  useEnableMonitoring,
  useFolderConfig,
  useFolderFiles,
  useFolderStatus,
  useReprocessFile,
  useScanHistory,
  useTriggerScan,
  useUpdateFolderConfig,
} from './evidence-folder.api';
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

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPut.mockReset();
  mockDelete.mockReset();
});

describe('evidence folder api queries', () => {
  it('loads folder resources through hooks', async () => {
    const responses: Record<string, unknown> = {
      '/api/evidence-folder/cases/12/config': { case_id: 12, enabled: true },
      '/api/evidence-folder/cases/12/status': { case_id: 12, is_monitoring: false },
      '/api/evidence-folder/cases/12/files': { records: [], total: 0 },
      '/api/evidence-folder/cases/12/scans': { scans: [], total: 0 },
    };
    mockGet.mockImplementation((url: string) => Promise.resolve({ data: responses[url] }));

    const configHook = renderHook(() => useFolderConfig(12), { wrapper: createWrapper() });
    const statusHook = renderHook(() => useFolderStatus(12), { wrapper: createWrapper() });
    const filesHook = renderHook(() => useFolderFiles(12, { status: 'pending', page: 2 }), { wrapper: createWrapper() });
    const scansHook = renderHook(() => useScanHistory(12, { page: 3 }), { wrapper: createWrapper() });

    await waitFor(() => expect(configHook.result.current.data).toEqual({ case_id: 12, enabled: true }));
    await waitFor(() => expect(statusHook.result.current.data).toEqual({ case_id: 12, is_monitoring: false }));
    await waitFor(() => expect(filesHook.result.current.data).toEqual({ records: [], total: 0 }));
    await waitFor(() => expect(scansHook.result.current.data).toEqual({ scans: [], total: 0 }));

    expect(mockGet).toHaveBeenCalledWith('/api/evidence-folder/cases/12/config');
    expect(mockGet).toHaveBeenCalledWith('/api/evidence-folder/cases/12/status');
    expect(mockGet).toHaveBeenCalledWith('/api/evidence-folder/cases/12/files', { params: { status: 'pending', page: 2 } });
    expect(mockGet).toHaveBeenCalledWith('/api/evidence-folder/cases/12/scans', { params: { page: 3 } });
  });

  it('does not request folder hooks without a case id', () => {
    renderHook(() => useFolderConfig(0), { wrapper: createWrapper() });
    renderHook(() => useFolderStatus(0), { wrapper: createWrapper() });
    renderHook(() => useFolderFiles(0), { wrapper: createWrapper() });
    renderHook(() => useScanHistory(0), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('evidence folder api commands', () => {
  it('calls direct evidence folder endpoints', async () => {
    mockGet.mockResolvedValue({ data: { ok: true } });
    mockPut.mockResolvedValue({ data: { updated: true } });
    mockPost.mockResolvedValue({ data: { posted: true } });
    mockDelete.mockResolvedValue({ data: { deleted: true } });

    await expect(getFolderConfig(12)).resolves.toEqual({ ok: true });
    await expect(updateFolderConfig(12, { folder_path: 'D:/case', enabled: true })).resolves.toEqual({ updated: true });
    await expect(getFolderStatus(12)).resolves.toEqual({ ok: true });
    await expect(getFolderFiles(12, { status: 'pending' })).resolves.toEqual({ ok: true });
    await expect(getScanHistory(12, { page: 2 })).resolves.toEqual({ ok: true });
    await expect(triggerScan(12, 'incremental')).resolves.toEqual({ posted: true });
    await expect(triggerIncrementalScan(12)).resolves.toEqual({ posted: true });
    await expect(enableMonitoring(12)).resolves.toEqual({ posted: true });
    await expect(disableMonitoring(12)).resolves.toEqual({ posted: true });
    await expect(deleteFileRecord(12, 5)).resolves.toEqual({ deleted: true });
    await expect(reprocessFile(12, 5)).resolves.toEqual({ posted: true });

    expect(mockGet).toHaveBeenNthCalledWith(1, '/api/evidence-folder/cases/12/config');
    expect(mockPut).toHaveBeenCalledWith('/api/evidence-folder/cases/12/config', { folder_path: 'D:/case', enabled: true });
    expect(mockGet).toHaveBeenNthCalledWith(2, '/api/evidence-folder/cases/12/status');
    expect(mockGet).toHaveBeenNthCalledWith(3, '/api/evidence-folder/cases/12/files', { params: { status: 'pending' } });
    expect(mockGet).toHaveBeenNthCalledWith(4, '/api/evidence-folder/cases/12/scans', { params: { page: 2 } });
    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/evidence-folder/cases/12/scan', { scan_type: 'incremental' });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/evidence-folder/cases/12/scan-incremental');
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/evidence-folder/cases/12/enable-monitor');
    expect(mockPost).toHaveBeenNthCalledWith(4, '/api/evidence-folder/cases/12/disable-monitor');
    expect(mockDelete).toHaveBeenCalledWith('/api/evidence-folder/cases/12/files/5');
    expect(mockPost).toHaveBeenNthCalledWith(5, '/api/evidence-folder/cases/12/files/5/reprocess');
  });

  it('calls mutation hook endpoints', async () => {
    mockPut.mockResolvedValue({ data: { updated: true } });
    mockPost.mockResolvedValue({ data: { posted: true } });
    mockDelete.mockResolvedValue({ data: { deleted: true } });

    const updateConfig = renderHook(() => useUpdateFolderConfig(12), { wrapper: createWrapper() });
    const scan = renderHook(() => useTriggerScan(12), { wrapper: createWrapper() });
    const enable = renderHook(() => useEnableMonitoring(12), { wrapper: createWrapper() });
    const disable = renderHook(() => useDisableMonitoring(12), { wrapper: createWrapper() });
    const deleteRecord = renderHook(() => useDeleteFileRecord(12), { wrapper: createWrapper() });
    const reprocess = renderHook(() => useReprocessFile(12), { wrapper: createWrapper() });

    await updateConfig.result.current.mutateAsync({ folder_path: 'D:/case', enabled: true });
    await scan.result.current.mutateAsync('full');
    await enable.result.current.mutateAsync();
    await disable.result.current.mutateAsync();
    await deleteRecord.result.current.mutateAsync(5);
    await reprocess.result.current.mutateAsync(5);

    expect(mockPut).toHaveBeenCalledWith('/api/evidence-folder/cases/12/config', { folder_path: 'D:/case', enabled: true });
    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/evidence-folder/cases/12/scan', { scan_type: 'full' });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/evidence-folder/cases/12/enable-monitor');
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/evidence-folder/cases/12/disable-monitor');
    expect(mockDelete).toHaveBeenCalledWith('/api/evidence-folder/cases/12/files/5');
    expect(mockPost).toHaveBeenNthCalledWith(4, '/api/evidence-folder/cases/12/files/5/reprocess');
  });
});
