import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  createDeadline,
  generateMilestones,
  getMilestones,
  getTimeline,
  getUrgencyReport,
  updateDeadline,
  useDeadlines,
} from './timeline.api';
import type { Deadline } from '@/types/deadline.types';
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

const deadline: Deadline = {
  id: '1',
  caseId: 'case-1',
  title: 'Submit evidence',
  type: 'evidence',
  dueDate: '2026-06-01',
  startDate: undefined,
  legalBasis: undefined,
  status: 'pending',
  createdAt: '',
  updatedAt: '',
  relatedTasks: [],
};

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPut.mockReset();
});

describe('timeline api hooks', () => {
  it('loads deadlines by case id', async () => {
    mockGet.mockResolvedValueOnce({
      data: [
        {
          id: 1,
          case_id: 'case-1',
          期限类型: 'evidence',
          期限名称: 'Submit evidence',
          截止日期: '2026-06-01',
          状态: 'pending',
        },
      ],
    });

    const { result } = renderHook(() => useDeadlines('case-1'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual([deadline]));
    expect(mockGet).toHaveBeenCalledWith('/api/time-control/case/case-1/deadlines');
  });

  it('does not request deadlines without a case id', () => {
    renderHook(() => useDeadlines(''), { wrapper: createWrapper() });

    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('timeline api commands', () => {
  it('creates and updates deadlines', async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        id: 1,
        case_id: 'case-1',
        期限类型: 'evidence',
        期限名称: 'Submit evidence',
        截止日期: '2026-06-01',
        状态: 'pending',
      },
    });
    mockPut.mockResolvedValueOnce({ data: { ...deadline, status: 'completed' } });

    await expect(
      createDeadline('case-1', {
        title: 'Submit evidence',
        type: 'evidence',
        dueDate: '2026-06-01',
      }),
    ).resolves.toEqual(deadline);
    await expect(updateDeadline('deadline-1', { status: 'completed' })).resolves.toEqual({
      ...deadline,
      status: 'completed',
    });

    expect(mockPost).toHaveBeenCalledWith('/api/time-control/case/case-1/deadlines', {
      期限类型: 'evidence',
      期限名称: 'Submit evidence',
      法律依据: undefined,
      起算日期: undefined,
      截止日期: '2026-06-01',
    });
    expect(mockPut).toHaveBeenCalledWith('/api/time-control/deadlines/deadline-1', null, {
      params: { status: 'completed' },
    });
  });

  it('generates milestones and loads timeline reports', async () => {
    mockPost.mockResolvedValueOnce({
      data: {
        milestones: [
          {
            id: 1,
            name: '立案材料',
            phase: 'filing',
            expected_date: '2026-06-03',
            description: '提交立案材料',
          },
        ],
      },
    });
    mockGet
      .mockResolvedValueOnce({
        data: [
          {
            id: 2,
            case_id: 'case-1',
            event_name: '举证期限',
            event_type: 'evidence',
            event_date: '2026-06-10',
            event_description: '完成举证',
            is_milestone: true,
          },
        ],
      })
      .mockResolvedValueOnce({ data: [{ id: 'event-1' }] })
      .mockResolvedValueOnce({ data: { level: 'normal' } });

    await expect(generateMilestones('case-1')).resolves.toMatchObject({
      milestones: [{ id: '1', title: '立案材料', type: 'filing' }],
    });
    await expect(getMilestones('case-1')).resolves.toEqual([
      {
        id: '2',
        caseId: 'case-1',
        title: '举证期限',
        type: 'evidence',
        date: '2026-06-10',
        description: '完成举证',
        importance: undefined,
        isMilestone: true,
        aiSummary: undefined,
      },
    ]);
    await expect(getTimeline('case-1')).resolves.toEqual([{ id: 'event-1' }]);
    await expect(getUrgencyReport('case-1')).resolves.toEqual({ level: 'normal' });

    expect(mockPost).toHaveBeenCalledWith('/api/time-control/case/case-1/generate-milestones');
    expect(mockGet).toHaveBeenNthCalledWith(1, '/api/time-control/case/case-1/milestones');
    expect(mockGet).toHaveBeenNthCalledWith(2, '/api/time-control/case/case-1/timeline');
    expect(mockGet).toHaveBeenNthCalledWith(3, '/api/time-control/case/case-1/urgency-report');
  });
});
