import axiosInstance from '@/api/client';
import {
  createAnalysisTask,
  createAnalysisStream,
  getAnalysisResult,
  getAnalysisStatus,
  startAnalysisTask,
  streamAnalysis,
} from './streaming-analysis.api';
import type { Mock } from 'vitest';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock('@/lib/api-config', () => ({
  API_BASE_URL: '',
  STREAMING_CONFIG: {},
  TOKEN_STORAGE_KEY: 'auth_token',
}));

const mockGet = axiosInstance.get as Mock;
const mockPost = axiosInstance.post as Mock;

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
});

afterEach(() => {
  localStorage.clear();
  vi.unstubAllGlobals();
});

function createSseResponse(chunks: string[]) {
  const encoder = new TextEncoder();

  return {
    ok: true,
    body: new ReadableStream({
      start(controller) {
        chunks.forEach((chunk) => controller.enqueue(encoder.encode(chunk)));
        controller.close();
      },
    }),
  };
}

describe('streaming analysis api', () => {
  it('creates and starts analysis tasks', async () => {
    mockPost
      .mockResolvedValueOnce({ data: { task_id: 'task-1' } })
      .mockResolvedValueOnce({ data: undefined });

    await expect(createAnalysisTask({
      caseId: '12',
      analysisType: 'full',
      customPrompt: 'focus on evidence',
      options: { depth: 'deep' },
    })).resolves.toEqual({ task_id: 'task-1' });
    await expect(startAnalysisTask('task-1')).resolves.toBeUndefined();

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/streaming-analysis/create', {
      case_id: 12,
      analysis_type: 'full',
      custom_prompt: 'focus on evidence',
      options: { depth: 'deep' },
    });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/streaming-analysis/task-1/start');
  });

  it('loads analysis status and result', async () => {
    mockGet
      .mockResolvedValueOnce({ data: { status: 'running' } })
      .mockResolvedValueOnce({ data: { report: 'done' } });

    await expect(getAnalysisStatus('task-1')).resolves.toEqual({ status: 'running' });
    await expect(getAnalysisResult('task-1')).resolves.toEqual({ report: 'done' });

    expect(mockGet).toHaveBeenNthCalledWith(1, '/api/streaming-analysis/task-1/status');
    expect(mockGet).toHaveBeenNthCalledWith(2, '/api/streaming-analysis/task-1/result');
  });

  it('parses SSE chunks from the analysis stream', async () => {
    const fetchMock = vi.fn().mockResolvedValue(createSseResponse([
      'data: {"type":"progress","progress":50}\n\n',
      'data: {"type":"complete","taskId":"task-1"}\n\n',
    ]));
    vi.stubGlobal('fetch', fetchMock);

    const reader = createAnalysisStream('task-1').getReader();

    await expect(reader.read()).resolves.toEqual({
      done: false,
      value: { type: 'progress', progress: 50 },
    });
    await expect(reader.read()).resolves.toEqual({
      done: false,
      value: { type: 'complete', taskId: 'task-1' },
    });
    await expect(reader.read()).resolves.toEqual({
      done: true,
      value: undefined,
    });
    expect(fetchMock).toHaveBeenCalledWith('/api/streaming-analysis/task-1/stream', {
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    });
  });

  it('passes the stored access token to the SSE request', async () => {
    localStorage.setItem('auth_token', 'token-1');
    const fetchMock = vi.fn().mockResolvedValue(createSseResponse([
      'data: {"type":"complete","taskId":"task-1"}\n\n',
    ]));
    vi.stubGlobal('fetch', fetchMock);

    const reader = createAnalysisStream('task-1').getReader();
    await reader.read();

    expect(fetchMock).toHaveBeenCalledWith('/api/streaming-analysis/task-1/stream', {
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Authorization: 'Bearer token-1',
      },
    });
  });

  it('yields analysis chunks with the async iterator helper', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(createSseResponse([
      'data: {"type":"content","content":"part 1"}\n\n',
      'data: {"type":"complete","taskId":"task-1"}\n\n',
    ])));

    const chunks = [];
    for await (const chunk of streamAnalysis('task-1')) {
      chunks.push(chunk);
    }

    expect(chunks).toEqual([
      { type: 'content', content: 'part 1' },
      { type: 'complete', taskId: 'task-1' },
    ]);
  });

  it('surfaces SSE connection failures', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }));

    await expect(createAnalysisStream('task-1').getReader().read()).rejects.toThrow('SSE 连接失败: 503');
  });
});
