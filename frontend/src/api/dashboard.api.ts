import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { DashboardData, UrgentItem, UpcomingTask, RecentCase, ActivityLog } from '@/types/dashboard.types';

type LegacyDashboardStats = {
  total?: number;
  inProgress?: number;
  newThisMonth?: number;
  inExecution?: number;
};

type LegacyDashboardTask = {
  id?: string | number;
  caseId?: string | number;
  caseTitle?: string;
  type?: string;
  title?: string;
  description?: string;
  daysRemaining?: number;
  dueDate?: string | null;
  redirectPath?: string;
  priority?: string;
};

type LegacyDashboardData = Partial<DashboardData> & {
  caseStats?: LegacyDashboardStats | null;
  urgentTasks?: LegacyDashboardTask[];
  upcomingTasks?: LegacyDashboardTask[];
};

const EMPTY_STATS: DashboardData['stats'] = {
  total_cases: 0,
  active_cases: 0,
  closed_cases: 0,
  execution_cases: 0,
  by_type: {},
  by_status: {},
  total_documents: 0,
  total_evidence: 0,
  total_reminders: 0,
  unread_reminders: 0,
  uncompleted_reminders: 0,
  high_priority_reminders: 0,
};

function toNumericCaseId(value: string | number | undefined): number | undefined {
  if (value === undefined || value === '') return undefined;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : undefined;
}

function normalizeLegacyUrgentTask(task: LegacyDashboardTask, index: number): UrgentItem {
  const priority = task.priority ?? 'high';
  return {
    id: String(task.id ?? `legacy-urgent-${index}`),
    type: task.type ?? 'other',
    title: task.title ?? '',
    description: task.description,
    case_id: toNumericCaseId(task.caseId),
    case_title: task.caseTitle,
    priority,
    trigger_date: task.dueDate ?? undefined,
    severity: priority === 'critical' ? 'critical' : 'high',
  };
}

function normalizeLegacyUpcomingTask(task: LegacyDashboardTask, index: number): UpcomingTask {
  const caseId = task.caseId !== undefined ? String(task.caseId) : undefined;
  return {
    id: String(task.id ?? `legacy-upcoming-${index}`),
    type: task.type ?? 'deadline',
    title: task.title ?? '',
    description: task.description,
    case_id: toNumericCaseId(task.caseId),
    case_title: task.caseTitle,
    due_date: task.dueDate ?? undefined,
    days_until: task.daysRemaining,
    priority: task.priority,
    caseId,
    caseTitle: task.caseTitle,
    dueDate: task.dueDate ?? undefined,
    daysRemaining: task.daysRemaining,
    redirectPath: task.redirectPath,
  };
}

export function normalizeDashboardData(data: DashboardData | LegacyDashboardData): DashboardData {
  const dashboard = data as LegacyDashboardData;
  const legacyStats = dashboard.caseStats;
  const stats = dashboard.stats ?? (
    legacyStats
      ? {
          ...EMPTY_STATS,
          total_cases: legacyStats.total ?? 0,
          active_cases: legacyStats.inProgress ?? 0,
          closed_cases: legacyStats.newThisMonth ?? 0,
          execution_cases: legacyStats.inExecution ?? 0,
        }
      : EMPTY_STATS
  );

  return {
    stats: { ...EMPTY_STATS, ...stats },
    urgent_items: dashboard.urgent_items ?? dashboard.urgentTasks?.map(normalizeLegacyUrgentTask) ?? [],
    upcoming_tasks: dashboard.upcoming_tasks ?? dashboard.upcomingTasks?.map(normalizeLegacyUpcomingTask) ?? [],
    recent_cases: dashboard.recent_cases ?? [],
    activity_log: dashboard.activity_log ?? [],
    generated_at: dashboard.generated_at ?? new Date().toISOString(),
  };
}

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: () => axiosInstance.get<DashboardData | LegacyDashboardData>('/api/dashboard').then(res => normalizeDashboardData(res.data)),
    staleTime: 5 * 60 * 1000,
    refetchInterval: 60 * 1000,
  });
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => axiosInstance.get('/api/dashboard/stats').then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useUrgentItems() {
  return useQuery({
    queryKey: ['dashboard-urgent'],
    queryFn: () => axiosInstance.get<{ urgent_items: UrgentItem[]; total: number }>('/api/dashboard/urgent').then(res => res.data),
    staleTime: 2 * 60 * 1000,
  });
}

export function useUpcomingTasks(days: number = 7) {
  return useQuery({
    queryKey: ['dashboard-upcoming', days],
    queryFn: () => axiosInstance.get<{ upcoming_tasks: UpcomingTask[]; total: number }>('/api/dashboard/upcoming', { params: { days } }).then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useRecentCases(limit: number = 10) {
  return useQuery({
    queryKey: ['dashboard-recent-cases', limit],
    queryFn: () => axiosInstance.get<{ recent_cases: RecentCase[]; total: number }>('/api/dashboard/recent-cases', { params: { limit } }).then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useAiSuggestions() {
  return useQuery({
    queryKey: ['dashboard-ai-suggestions'],
    queryFn: () => axiosInstance.get<{ suggestions: string; generated_at: string; based_on: Record<string, unknown> }>('/api/dashboard/ai-suggestions').then(res => res.data),
    staleTime: 30 * 60 * 1000,
  });
}

export function useActivityLog(limit: number = 20) {
  return useQuery({
    queryKey: ['dashboard-activity', limit],
    queryFn: () => axiosInstance.get<{ activity_log: ActivityLog[]; total: number }>('/api/dashboard/activity', { params: { limit } }).then(res => res.data),
    staleTime: 2 * 60 * 1000,
  });
}
