import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  cancelReport,
  compareReports,
  deleteReport,
  exportReport,
  generateReport,
  getDocumentsReport,
  getReportStatus,
  invalidateReportCache,
  quickAnalysis,
  regenerateReport,
  subscribeToReportProgress,
  useReportDetail,
  useReportList,
  useReports,
} from './report.api';
import type { ReactNode } from 'react';
import type { Mock } from 'vitest';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockGet = axiosInstance.get as Mock;
const mockPost = axiosInstance.post as Mock;
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
  mockDelete.mockReset();
  localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('report api hooks', () => {
  it('loads report list and detail', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url === '/api/reports/list/case-1') {
        return Promise.resolve({ data: { reports: [{ id: 'report-1' }], total: 1 } });
      }

      if (url === '/api/reports/detail/report-1') {
        return Promise.resolve({ data: { id: 'report-1', sections: [] } });
      }

      return Promise.reject(new Error(`Unexpected report request: ${url}`));
    });

    const listHook = renderHook(() => useReports('case-1'), { wrapper: createWrapper() });
    const aliasHook = renderHook(() => useReportList('case-1'), { wrapper: createWrapper() });
    const detailHook = renderHook(() => useReportDetail('report-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(listHook.result.current.data).toEqual({ reports: [{ id: 'report-1' }], total: 1 }));
    await waitFor(() => expect(aliasHook.result.current.isSuccess || aliasHook.result.current.isFetching).toBeTruthy());
    await waitFor(() => expect(detailHook.result.current.data).toEqual({ id: 'report-1', sections: [] }));

    expect(mockGet).toHaveBeenCalledWith('/api/reports/list/case-1');
    expect(mockGet).toHaveBeenCalledWith('/api/reports/detail/report-1');
  });

  it('does not request reports without ids', () => {
    renderHook(() => useReports(''), { wrapper: createWrapper() });
    renderHook(() => useReportDetail(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('report browser APIs', () => {
  it('exports and downloads a report with the server filename', async () => {
    localStorage.setItem('auth_token', 'access-token');
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    const createObjectURL = vi.fn(() => 'blob:report');
    const revokeObjectURL = vi.fn();
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      blob: vi.fn().mockResolvedValue(new Blob(['report'])),
      headers: {
        get: vi.fn(() => 'attachment; filename="case-report.md"'),
      },
    });

    Object.defineProperty(window.URL, 'createObjectURL', {
      configurable: true,
      value: createObjectURL,
    });
    Object.defineProperty(window.URL, 'revokeObjectURL', {
      configurable: true,
      value: revokeObjectURL,
    });
    vi.stubGlobal('fetch', fetchMock);

    await exportReport('report-1', 'markdown');

    expect(fetchMock).toHaveBeenCalledWith('/api/reports/export/report-1?format=markdown', {
      headers: { Authorization: 'Bearer access-token' },
    });
    expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
    expect(clickSpy).toHaveBeenCalled();
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:report');
    expect(document.querySelector('a[download="case-report.md"]')).toBeNull();

    clickSpy.mockRestore();
  });

  it('throws when report export fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }));

    await expect(exportReport('report-1')).rejects.toThrow('导出失败');
  });

  it('subscribes to report progress events and closes the stream', () => {
    localStorage.setItem('auth_token', 'access-token');

    class FakeEventSource {
      static instances: FakeEventSource[] = [];

      listeners: Record<string, Array<(event: MessageEvent) => void>> = {};
      close = vi.fn();

      constructor(
        public url: string,
        public options?: unknown,
      ) {
        FakeEventSource.instances.push(this);
      }

      addEventListener(type: string, listener: (event: MessageEvent) => void) {
        this.listeners[type] = [...(this.listeners[type] || []), listener];
      }

      emit(type: string, data: unknown) {
        this.listeners[type]?.forEach((listener) => {
          listener({ data: JSON.stringify(data) } as MessageEvent);
        });
      }
    }

    vi.stubGlobal('EventSource', FakeEventSource as unknown as typeof EventSource);

    const callbacks = {
      onProgress: vi.fn(),
      onSectionStart: vi.fn(),
      onSectionContent: vi.fn(),
      onSectionError: vi.fn(),
      onComplete: vi.fn(),
      onError: vi.fn(),
    };

    const cleanup = subscribeToReportProgress('case-1', 'analysis', callbacks);
    const source = FakeEventSource.instances[0];

    expect(source.url).toBe('/api/reports/generate-stream/case-1?report_type=analysis');
    expect(source.options).toEqual({ headers: { Authorization: 'Bearer access-token' } });

    source.emit('progress', { progress: 25, message: 'quarter' });
    source.emit('section_start', { section_index: 1, title: 'Facts', content: '' });
    source.emit('section_content', { section_index: 1, title: 'Facts', content: 'content' });
    source.emit('section_error', { section_index: 1, title: 'Facts', error: 'failed' });
    source.emit('complete', { report_id: 'report-1' });

    expect(callbacks.onProgress).toHaveBeenCalledWith({ progress: 25, message: 'quarter' });
    expect(callbacks.onSectionStart).toHaveBeenCalledWith({ section_index: 1, title: 'Facts', content: '' });
    expect(callbacks.onSectionContent).toHaveBeenCalledWith({ section_index: 1, title: 'Facts', content: 'content' });
    expect(callbacks.onSectionError).toHaveBeenCalledWith({ section_index: 1, title: 'Facts', error: 'failed' });
    expect(callbacks.onComplete).toHaveBeenCalledWith({ report_id: 'report-1' });
    expect(source.close).toHaveBeenCalledTimes(1);

    cleanup();
    expect(source.close).toHaveBeenCalledTimes(2);
  });

  it('reports SSE connection errors', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    class FakeEventSource {
      static instances: FakeEventSource[] = [];

      listeners: Record<string, Array<(event: Event) => void>> = {};
      close = vi.fn();

      constructor() {
        FakeEventSource.instances.push(this);
      }

      addEventListener(type: string, listener: (event: Event) => void) {
        this.listeners[type] = [...(this.listeners[type] || []), listener];
      }

      emit(type: string) {
        this.listeners[type]?.forEach((listener) => listener(new Event(type)));
      }
    }

    vi.stubGlobal('EventSource', FakeEventSource as unknown as typeof EventSource);
    const onError = vi.fn();

    subscribeToReportProgress('case-1', 'analysis', { onError });
    const source = FakeEventSource.instances[0];
    source.emit('error');

    expect(onError).toHaveBeenCalledWith('连接错误');
    expect(source.close).toHaveBeenCalled();

    consoleError.mockRestore();
  });
});

describe('report api commands', () => {
  it('generates, cancels, and runs quick analysis', async () => {
    mockPost
      .mockResolvedValueOnce({ data: { id: 'report-new' } })
      .mockResolvedValueOnce({ status: 202 })
      .mockResolvedValueOnce({ data: { summary: 'ok' } });

    await expect(generateReport('case-1', 'analysis')).resolves.toEqual({ id: 'report-new' });
    await expect(cancelReport('case-1')).resolves.toEqual({ status: 202 });
    await expect(quickAnalysis('case-1')).resolves.toEqual({ summary: 'ok' });

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/reports/generate/case-1', { report_type: 'analysis' });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/reports/cancel/case-1');
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/reports/quick-analysis/case-1');
  });

  it('deletes, regenerates, and invalidates report data', async () => {
    mockDelete.mockResolvedValueOnce({ data: { deleted: true } });
    mockPost
      .mockResolvedValueOnce({ data: { regenerated: true } })
      .mockResolvedValueOnce({ data: { invalidated: true } })
      .mockResolvedValueOnce({ data: { report: 'documents' } });

    await expect(deleteReport('report-1')).resolves.toEqual({ deleted: true });
    await expect(regenerateReport('report-1')).resolves.toEqual({ regenerated: true });
    await expect(invalidateReportCache('case-1')).resolves.toEqual({ invalidated: true });
    await expect(getDocumentsReport('case-1')).resolves.toEqual({ report: 'documents' });

    expect(mockDelete).toHaveBeenCalledWith('/api/reports/report-1');
    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/reports/regenerate/report-1');
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/reports/invalidate-cache/case-1');
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/reports/generate-documents/case-1');
  });

  it('loads report status and compares reports', async () => {
    mockGet
      .mockResolvedValueOnce({ data: { status: 'COMPLETED' } })
      .mockResolvedValueOnce({
        data: {
          report_1: { id: 'r1' },
          report_2: { id: 'r2' },
          section_comparison: [],
          summary: { total_sections: 0 },
        },
      });

    await expect(getReportStatus('case-1', 'strategy')).resolves.toEqual({ status: 'COMPLETED' });
    await expect(compareReports('r1', 'r2')).resolves.toMatchObject({
      report_1: { id: 'r1' },
      report_2: { id: 'r2' },
    });

    expect(mockGet).toHaveBeenNthCalledWith(1, '/api/reports/status/case-1', {
      params: { report_type: 'strategy' },
    });
    expect(mockGet).toHaveBeenNthCalledWith(2, '/api/reports/compare/r1/r2');
  });
});
