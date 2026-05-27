import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  createHearing,
  detectTrap,
  generateOpeningStatement,
  realtimeAnalysis,
  recordStatement,
  useHearingStatements,
  useHearings,
} from './hearing.api';
import type { ReactNode } from 'react';
import type { Hearing } from '@/types/hearing.types';
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

describe('hearing api', () => {
  it('loads hearings for a case', async () => {
    mockGet.mockResolvedValueOnce({
      data: [{ id: 'hearing-1', case_id: 7, 庭审类型: 'first_trial', 庭审日期: '2026-06-01T09:30:00', 地点: '第一法庭', 状态: 'in_progress' }],
    });

    const { result } = renderHook(() => useHearings('case-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data?.[0]).toMatchObject({
      id: 'hearing-1',
      caseId: '7',
      hearingType: 'first_trial',
      courtName: '第一法庭',
      status: 'in_progress',
    }));
    expect(mockGet).toHaveBeenCalledWith('/api/hearings/case/case-1/hearings');
  });

  it('does not request hearings without a case id', () => {
    renderHook(() => useHearings(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });

  it('loads statements for a hearing', async () => {
    mockGet.mockResolvedValueOnce({
      data: [{ id: 3, 发言类型: 'question', 讲话方角色: 'plaintiff_lawyer', 讲话人: '代理律师', 内容: '请说明付款时间。', 是否陷阱: false }],
    });

    const { result } = renderHook(() => useHearingStatements('hearing-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data?.[0]).toMatchObject({
      id: '3',
      speakerName: '代理律师',
      content: '请说明付款时间。',
      isTrap: false,
    }));
    expect(mockGet).toHaveBeenCalledWith('/api/hearings/hearing/hearing-1/statements');
  });

  it('calls hearing command endpoints', async () => {
    mockPost.mockResolvedValue({ data: { ok: true } });

    const hearing: Partial<Hearing> = { courtName: '第一法庭', type: 'first_trial', date: '2026-06-01T09:30:00' };

    await expect(createHearing('case-1', hearing)).resolves.toMatchObject({ id: '' });
    await expect(generateOpeningStatement('case-1', { focus: 'facts' })).resolves.toEqual({ ok: true });
    await expect(detectTrap('question')).resolves.toEqual({ ok: true });
    await expect(realtimeAnalysis('statement')).resolves.toEqual({ ok: true });
    await expect(recordStatement('hearing-1', { speaker: 'judge' })).resolves.toEqual({ ok: true });

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/hearings/case/case-1/hearing', {
      庭审类型: 'first_trial',
      庭审日期: '2026-06-01T09:30:00',
      地点: '第一法庭',
      参会人员: undefined,
      案号: undefined,
    });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/hearings/case/case-1/opening-statement', { focus: 'facts' });
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/hearings/detect-trap', { statement: 'question', speaker_role: 'opponent' });
    expect(mockPost).toHaveBeenNthCalledWith(4, '/api/hearings/realtime-analysis', { 发言内容: 'statement', 讲话方角色: 'opponent' });
    expect(mockPost).toHaveBeenNthCalledWith(5, '/api/hearings/hearing/hearing-1/statement', { speaker: 'judge' });
  });
});
