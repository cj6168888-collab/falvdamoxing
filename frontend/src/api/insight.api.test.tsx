import axiosInstance from '@/api/client';
import {
  answerInsightClarification,
  askInsightQuestion,
  buildInsightEvidenceGraph,
  clearInsightCache,
  generateInsightReport,
  getInsightEvidenceCredibility,
  getInsightReportStatus,
  queryInsightEvidence,
} from './insight.api';
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

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
});

describe('insight api', () => {
  it('calls question and clarification endpoints', async () => {
    mockPost.mockResolvedValue({ data: { needs_clarification: false, answer: 'ok' } });

    await expect(askInsightQuestion('12', '下一步策略')).resolves.toEqual({
      needs_clarification: false,
      answer: 'ok',
    });
    await expect(answerInsightClarification(12, '下一步策略', { 补充: '已付款' })).resolves.toEqual({
      needs_clarification: false,
      answer: 'ok',
    });

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/v2/question', {
      case_id: 12,
      question: '下一步策略',
    });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/v2/question/answer', {
      case_id: 12,
      question: '下一步策略',
      answers: { 补充: '已付款' },
    });
  });

  it('calls report and cache endpoints', async () => {
    mockPost.mockResolvedValue({ data: { ok: true } });
    mockGet.mockResolvedValue({ data: { status: '已完成' } });

    await expect(generateInsightReport(12, 'strategy', true)).resolves.toEqual({ ok: true });
    await expect(getInsightReportStatus(12, 'strategy')).resolves.toEqual({ status: '已完成' });
    await expect(clearInsightCache(12)).resolves.toEqual({ ok: true });

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/v2/report/generate', {
      case_id: 12,
      report_type: 'strategy',
      force_regenerate: true,
    });
    expect(mockGet).toHaveBeenCalledWith('/api/v2/report/status/12', {
      params: { report_type: 'strategy' },
    });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/v2/cache/clear/12');
  });

  it('calls evidence graph, query, and credibility endpoints', async () => {
    mockPost.mockResolvedValue({ data: { nodes: [] } });
    mockGet.mockResolvedValue({ data: { count: 0 } });

    await expect(buildInsightEvidenceGraph(12, true)).resolves.toEqual({ nodes: [] });
    await expect(queryInsightEvidence(12, '付款', 'keywords')).resolves.toEqual({ count: 0 });
    await expect(getInsightEvidenceCredibility(34)).resolves.toEqual({ count: 0 });

    expect(mockPost).toHaveBeenCalledWith('/api/v2/evidence/graph', {
      case_id: 12,
      force_refresh: true,
    });
    expect(mockGet).toHaveBeenNthCalledWith(1, '/api/v2/evidence/query/12', {
      params: { query: '付款', search_type: 'keywords' },
    });
    expect(mockGet).toHaveBeenNthCalledWith(2, '/api/v2/evidence/credibility/34');
  });
});
