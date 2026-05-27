import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  continueDebate,
  createAnalysis,
  generateFullAnalysis,
  generateEvidenceMatrix,
  getAdversarialAnalysisDetail,
  getDebateProgress,
  getRigorousAnalysisProgress,
  opponentAnalysis,
  predictScenarios,
  startDebateStream,
  startRigorousAnalysis,
  updateAdversarialAnalysis,
  useAdversarialAnalysis,
} from './adversarial.api';
import type { RigorousAnalysisRequest } from './adversarial.api';
import type { ReactNode } from 'react';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

const mockGet = axiosInstance.get as Mock;
const mockPost = axiosInstance.post as Mock;
const mockPut = axiosInstance.put as Mock;

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
});

describe('adversarial api', () => {
  it('loads adversarial analyses for a case', async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: 1 }] });

    const { result } = renderHook(() => useAdversarialAnalysis('case-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual([{ id: 1 }]));
    expect(mockGet).toHaveBeenCalledWith('/api/adversarial/case/case-1/analyses');
  });

  it('does not request analyses without a case id', () => {
    renderHook(() => useAdversarialAnalysis(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });

  it('calls adversarial command endpoints', async () => {
    mockPost.mockResolvedValue({ data: { ok: true } });
    mockGet.mockResolvedValue({ data: { status: 'completed' } });
    mockPut.mockResolvedValue({ data: { id: 9, title: 'updated' } });

    await expect(createAnalysis('case-1', { phase: 'trial' })).resolves.toEqual({ ok: true });
    await expect(generateEvidenceMatrix('case-1')).resolves.toEqual({ ok: true });
    await expect(predictScenarios('case-1')).resolves.toEqual({ ok: true });
    await expect(opponentAnalysis('case-1')).resolves.toEqual({ ok: true });
    await expect(startDebateStream('case-1', { user_input: 'start' })).resolves.toEqual({ ok: true });
    await expect(getDebateProgress('debate-1')).resolves.toEqual({ status: 'completed' });
    await expect(continueDebate('debate-1', 'continue')).resolves.toEqual({ ok: true });
    const rigorousRequest: RigorousAnalysisRequest = { 案件名称: 'analysis' };

    await expect(startRigorousAnalysis('case-1', rigorousRequest)).resolves.toEqual({ ok: true });
    await expect(getRigorousAnalysisProgress('analysis-1')).resolves.toEqual({ status: 'completed' });
    await expect(getAdversarialAnalysisDetail(9)).resolves.toEqual({ status: 'completed' });
    await expect(updateAdversarialAnalysis(9, { title: 'updated' })).resolves.toEqual({ id: 9, title: 'updated' });

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/adversarial/case/case-1/analysis', { phase: 'trial' });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/adversarial/case/case-1/evidence-matrix');
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/adversarial/case/case-1/scenario-prediction');
    expect(mockPost).toHaveBeenNthCalledWith(4, '/api/adversarial/case/case-1/opponent-analysis');
    expect(mockPost).toHaveBeenNthCalledWith(5, '/api/adversarial/case/case-1/debate-stream', { user_input: 'start' });
    expect(mockGet).toHaveBeenNthCalledWith(1, '/api/adversarial/debate/debate-1/progress');
    expect(mockPost).toHaveBeenNthCalledWith(6, '/api/adversarial/debate/debate-1/continue', { user_input: 'continue' });
    expect(mockPost).toHaveBeenNthCalledWith(7, '/api/adversarial/case/case-1/evidence-based-analysis', rigorousRequest);
    expect(mockGet).toHaveBeenNthCalledWith(2, '/api/adversarial/progress/analysis-1');
    expect(mockGet).toHaveBeenNthCalledWith(3, '/api/adversarial/9');
    expect(mockPut).toHaveBeenCalledWith('/api/adversarial/9', { title: 'updated' });
  });

  it('runs full analysis with an abort signal', async () => {
    mockPost.mockResolvedValueOnce({ data: { analysis_id: 1, full_report: 'done' } });

    await expect(generateFullAnalysis('case-1', { 分析阶段: '庭审' })).resolves.toEqual({
      analysis_id: 1,
      full_report: 'done',
    });
    expect(mockPost).toHaveBeenCalledWith(
      '/api/adversarial/case/case-1/full-analysis',
      { 分析阶段: '庭审' },
      { signal: expect.any(AbortSignal) },
    );
  });

  it('normalizes full analysis timeout errors', async () => {
    mockPost.mockRejectedValueOnce(new Error('canceled'));

    await expect(generateFullAnalysis('case-1')).rejects.toThrow('分析超时（超过5分钟），建议使用"后台分析"功能');
  });
});
