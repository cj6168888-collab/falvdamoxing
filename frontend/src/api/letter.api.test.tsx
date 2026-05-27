import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  analyzeReply,
  confirmDelivered,
  createLetter,
  deleteLetter,
  discoverLetters,
  generateReply,
  getDiscoveryStatus,
  getMailTracking,
  getUrgencyReport,
  updateLetter,
  updateMailing,
  updateReply,
  useLetters,
} from './letter.api';
import type { ReactNode } from 'react';
import type { Letter } from '@/types/letter.types';
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

describe('letter api', () => {
  it('loads letters for a case', async () => {
    mockGet.mockResolvedValueOnce({ data: [{ id: 'letter-1' }] });

    const { result } = renderHook(() => useLetters('case-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual([{ id: 'letter-1' }]));
    expect(mockGet).toHaveBeenCalledWith('/api/time-control/case/case-1/letters');
  });

  it('does not request letters without a case id', () => {
    renderHook(() => useLetters(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });

  it('creates, updates, and deletes letters', async () => {
    mockPost.mockResolvedValue({ data: { ok: true }, status: 200 });
    mockPut.mockResolvedValue({ data: { updated: true } });
    mockDelete.mockResolvedValue({ data: { deleted: true } });

    const newLetter: Partial<Letter> = {
      title: 'notice',
      direction: 'outgoing',
      letter_type: 'lawyer_letter',
      reference_number: 'REF-1',
      sender: 'sender',
      recipient: 'recipient',
      letter_date: '2026-05-17',
      deadline: '2026-05-24',
      content_summary: 'summary',
      key_demands: 'demands',
    };
    const expectedCreatePayload = {
      标题: 'notice',
      方向: 'outgoing',
      类型: 'lawyer_letter',
      文号: 'REF-1',
      发送方: 'sender',
      接收方: 'recipient',
      函件日期: '2026-05-17',
      收到日期: undefined,
      截止日期: '2026-05-24',
      内容摘要: 'summary',
      核心诉求: 'demands',
    };
    const letterUpdate: Partial<Letter> = { title: 'updated' };

    await expect(createLetter('case-1', newLetter)).resolves.toEqual({ ok: true });
    await expect(updateLetter('case-1', 'letter-1', letterUpdate)).resolves.toEqual({ updated: true });
    await expect(deleteLetter('case-1', 'letter-1')).resolves.toEqual({ deleted: true });
    await expect(updateMailing('letter-1', { tracking_no: 'SF1' })).resolves.toMatchObject({ status: 200 });
    await expect(confirmDelivered('letter-1')).resolves.toMatchObject({ status: 200 });
    await expect(generateReply('letter-1')).resolves.toEqual({ ok: true });
    await expect(updateReply('letter-1', { content: 'reply' })).resolves.toMatchObject({ status: 200 });
    await expect(analyzeReply('letter-1')).resolves.toEqual({ ok: true });

    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/time-control/case/case-1/letters', expectedCreatePayload);
    expect(mockPut).toHaveBeenCalledWith('/api/time-control/letters/letter-1', letterUpdate);
    expect(mockDelete).toHaveBeenCalledWith('/api/time-control/letters/letter-1');
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/time-control/letters/letter-1/mailing', { tracking_no: 'SF1' });
    expect(mockPost).toHaveBeenNthCalledWith(3, '/api/time-control/letters/letter-1/delivered');
    expect(mockPost).toHaveBeenNthCalledWith(4, '/api/time-control/letters/letter-1/generate-reply');
    expect(mockPost).toHaveBeenNthCalledWith(5, '/api/time-control/letters/letter-1/reply', { content: 'reply' });
    expect(mockPost).toHaveBeenNthCalledWith(6, '/api/time-control/letters/letter-1/ai-analyze-reply');
  });

  it('loads tracking, urgency, and discovery data', async () => {
    mockGet
      .mockResolvedValueOnce({ data: { tracking: [] } })
      .mockResolvedValueOnce({ data: { urgent: 2 } })
      .mockResolvedValueOnce({ data: { status: 'done' } });
    mockPost.mockResolvedValueOnce({ data: { discovered: 1 } });

    await expect(getMailTracking('case-1')).resolves.toEqual({ tracking: [] });
    await expect(getUrgencyReport('case-1')).resolves.toEqual({ urgent: 2 });
    await expect(discoverLetters('case-1')).resolves.toEqual({ discovered: 1 });
    await expect(getDiscoveryStatus('case-1')).resolves.toEqual({ status: 'done' });

    expect(mockGet).toHaveBeenNthCalledWith(1, '/api/time-control/case/case-1/mail-tracking');
    expect(mockGet).toHaveBeenNthCalledWith(2, '/api/time-control/case/case-1/urgency-report');
    expect(mockPost).toHaveBeenCalledWith('/api/time-control/case/case-1/letters/discover');
    expect(mockGet).toHaveBeenNthCalledWith(3, '/api/time-control/case/case-1/letters/discovery-status');
  });
});
