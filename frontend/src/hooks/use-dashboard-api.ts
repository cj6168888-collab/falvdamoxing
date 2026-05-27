import { useQuery } from '@tanstack/react-query';

async function getJson<T>(url: string, errorMessage: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(errorMessage);
  return response.json() as Promise<T>;
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => getJson('/api/dashboard/stats', '获取统计数据失败'),
    refetchInterval: 300000,
  });
}

export function useUrgentItems() {
  return useQuery({
    queryKey: ['urgent-items'],
    queryFn: () => getJson('/api/dashboard/urgent', '获取紧急事项失败'),
    refetchInterval: 60000,
  });
}

export function useUpcomingDeadlines(days = 7) {
  return useQuery({
    queryKey: ['upcoming-deadlines', days],
    queryFn: () => getJson(`/api/dashboard/upcoming?days=${days}`, '获取即将到期事项失败'),
    refetchInterval: 300000,
  });
}

export function useCaseStatsByStatus() {
  return useQuery({
    queryKey: ['case-stats-by-status'],
    queryFn: () => getJson('/api/cases/stats/by-status', '获取案件统计失败'),
  });
}

export function useRecentCases(limit = 5) {
  return useQuery({
    queryKey: ['recent-cases', limit],
    queryFn: () => getJson(`/api/cases/recent?limit=${limit}`, '获取最近案件失败'),
  });
}

export function useActivityTimeline(days = 7) {
  return useQuery({
    queryKey: ['activity-timeline', days],
    queryFn: () => getJson(`/api/activity?days=${days}`, '获取活动时间线失败'),
  });
}
