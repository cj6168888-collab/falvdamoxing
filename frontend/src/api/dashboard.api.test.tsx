import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import type { DashboardData } from '@/types/dashboard.types';
import {
  useActivityLog,
  useAiSuggestions,
  useDashboard,
  useDashboardStats,
  useRecentCases,
  useUpcomingTasks,
  useUrgentItems,
} from './dashboard.api';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
  },
}));

const mockGet = axiosInstance.get as Mock;

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

const dashboardData: DashboardData = {
  stats: {
    total_cases: 3,
    active_cases: 2,
    closed_cases: 1,
    execution_cases: 1,
    by_type: { contract: 2 },
    by_status: { active: 2 },
    total_documents: 4,
    total_evidence: 5,
    total_reminders: 6,
    unread_reminders: 1,
    uncompleted_reminders: 2,
    high_priority_reminders: 1,
  },
  urgent_items: [],
  upcoming_tasks: [],
  recent_cases: [],
  activity_log: [],
  generated_at: '2026-05-11T00:00:00.000Z',
};

beforeEach(() => {
  mockGet.mockReset();
});

describe('dashboard api hooks', () => {
  it('loads dashboard aggregate data', async () => {
    mockGet.mockResolvedValueOnce({ data: dashboardData });

    const { result } = renderHook(() => useDashboard(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(dashboardData));
    expect(mockGet).toHaveBeenCalledWith('/api/dashboard');
  });

  it('normalizes legacy dashboard aggregate data', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        caseStats: { total: 9, inProgress: 4, newThisMonth: 3, inExecution: 2 },
        urgentTasks: [
          {
            id: 'appeal-1',
            caseId: '1',
            caseTitle: 'Legacy case',
            type: 'appeal',
            title: 'Legacy urgent',
            daysRemaining: 2,
            dueDate: '2026-05-13T00:00:00.000Z',
            redirectPath: '/cases/1/overview',
          },
        ],
        upcomingTasks: [
          {
            id: 'deadline-1',
            caseId: '1',
            caseTitle: 'Legacy case',
            type: 'deadline',
            title: 'Legacy deadline',
            daysRemaining: 8,
            dueDate: '2026-05-20T00:00:00.000Z',
            redirectPath: '/cases/1/overview',
          },
        ],
      },
    });

    const { result } = renderHook(() => useDashboard(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data?.stats.total_cases).toBe(9));
    expect(result.current.data?.urgent_items[0]).toMatchObject({
      id: 'appeal-1',
      case_id: 1,
      case_title: 'Legacy case',
      title: 'Legacy urgent',
    });
    expect(result.current.data?.upcoming_tasks[0]).toMatchObject({
      id: 'deadline-1',
      case_id: 1,
      case_title: 'Legacy case',
      days_until: 8,
    });
  });

  it('loads dashboard stats', async () => {
    const stats = { total_cases: 8 };
    mockGet.mockResolvedValueOnce({ data: stats });

    const { result } = renderHook(() => useDashboardStats(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(stats));
    expect(mockGet).toHaveBeenCalledWith('/api/dashboard/stats');
  });

  it('loads urgent items', async () => {
    const response = { urgent_items: [{ id: 'urgent-1', title: '提交证据' }], total: 1 };
    mockGet.mockResolvedValueOnce({ data: response });

    const { result } = renderHook(() => useUrgentItems(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(response));
    expect(mockGet).toHaveBeenCalledWith('/api/dashboard/urgent');
  });

  it('loads upcoming tasks with day filter', async () => {
    const response = { upcoming_tasks: [{ id: 'task-1', title: '开庭' }], total: 1 };
    mockGet.mockResolvedValueOnce({ data: response });

    const { result } = renderHook(() => useUpcomingTasks(30), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(response));
    expect(mockGet).toHaveBeenCalledWith('/api/dashboard/upcoming', { params: { days: 30 } });
  });

  it('loads recent cases with limit filter', async () => {
    const response = { recent_cases: [{ id: 1, title: '合同纠纷' }], total: 1 };
    mockGet.mockResolvedValueOnce({ data: response });

    const { result } = renderHook(() => useRecentCases(3), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(response));
    expect(mockGet).toHaveBeenCalledWith('/api/dashboard/recent-cases', { params: { limit: 3 } });
  });

  it('loads AI suggestions', async () => {
    const response = {
      suggestions: '今日优先处理证据补强',
      generated_at: '2026-05-11T00:00:00.000Z',
      based_on: { urgent: 1 },
    };
    mockGet.mockResolvedValueOnce({ data: response });

    const { result } = renderHook(() => useAiSuggestions(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(response));
    expect(mockGet).toHaveBeenCalledWith('/api/dashboard/ai-suggestions');
  });

  it('loads activity log with limit filter', async () => {
    const response = { activity_log: [{ type: 'case', title: '更新案件', description: '已更新' }], total: 1 };
    mockGet.mockResolvedValueOnce({ data: response });

    const { result } = renderHook(() => useActivityLog(5), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(response));
    expect(mockGet).toHaveBeenCalledWith('/api/dashboard/activity', { params: { limit: 5 } });
  });
});
