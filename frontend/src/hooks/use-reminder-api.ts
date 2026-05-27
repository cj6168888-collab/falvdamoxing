import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Reminder, ReminderCreate, ReminderUpdate, ReminderBatchAction } from '@/types/reminder.types';

// 获取提醒列表
export function useReminders(filters?: {
  status?: string;
  priority?: string;
  caseId?: string;
  page?: number;
  pageSize?: number;
}) {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.priority) params.append('priority', filters.priority);
  if (filters?.caseId) params.append('case_id', filters.caseId);
  if (filters?.page) params.append('page', String(filters.page));
  if (filters?.pageSize) params.append('page_size', String(filters.pageSize));

  return useQuery({
    queryKey: ['reminders', filters],
    queryFn: async (): Promise<{ items: Reminder[]; total: number }> => {
      const response = await fetch(`/api/reminders?${params}`);
      if (!response.ok) throw new Error('获取提醒列表失败');
      return response.json();
    },
  });
}

// 获取单个提醒
export function useReminder(id: string) {
  return useQuery({
    queryKey: ['reminder', id],
    queryFn: async (): Promise<Reminder> => {
      const response = await fetch(`/api/reminders/${id}`);
      if (!response.ok) throw new Error('获取提醒失败');
      return response.json();
    },
    enabled: !!id,
  });
}

// 创建提醒
export function useCreateReminder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ReminderCreate): Promise<Reminder> => {
      const response = await fetch('/api/reminders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('创建提醒失败');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      queryClient.invalidateQueries({ queryKey: ['reminder-stats'] });
    },
  });
}

// 更新提醒
export function useUpdateReminder(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ReminderUpdate): Promise<Reminder> => {
      const response = await fetch(`/api/reminders/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('更新提醒失败');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      queryClient.invalidateQueries({ queryKey: ['reminder', id] });
    },
  });
}

// 删除提醒
export function useDeleteReminder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      const response = await fetch(`/api/reminders/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('删除提醒失败');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      queryClient.invalidateQueries({ queryKey: ['reminder-stats'] });
    },
  });
}

// 批量操作提醒
export function useBatchReminderAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (action: ReminderBatchAction): Promise<{ success: boolean; processed: number }> => {
      const response = await fetch('/api/reminders/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(action),
      });
      if (!response.ok) throw new Error('批量操作失败');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      queryClient.invalidateQueries({ queryKey: ['reminder-stats'] });
    },
  });
}

// 获取提醒统计
export function useReminderStats() {
  return useQuery({
    queryKey: ['reminder-stats'],
    queryFn: async () => {
      const response = await fetch('/api/reminders/stats');
      if (!response.ok) throw new Error('获取统计失败');
      return response.json();
    },
    refetchInterval: 60000, // 每分钟刷新
  });
}

// 获取案件的提醒
export function useCaseReminders(caseId: string) {
  return useQuery({
    queryKey: ['case-reminders', caseId],
    queryFn: async (): Promise<Reminder[]> => {
      const response = await fetch(`/api/reminders?case_id=${caseId}`);
      if (!response.ok) throw new Error('获取案件提醒失败');
      const data = await response.json();
      return data.items || [];
    },
    enabled: !!caseId,
  });
}

// 获取今日提醒
export function useTodayReminders() {
  return useQuery({
    queryKey: ['today-reminders'],
    queryFn: async (): Promise<Reminder[]> => {
      const today = new Date().toISOString().split('T')[0];
      const response = await fetch(`/api/reminders?due_date=${today}`);
      if (!response.ok) throw new Error('获取今日提醒失败');
      const data = await response.json();
      return data.items || [];
    },
    refetchInterval: 300000, // 每5分钟刷新
  });
}

// 获取紧急提醒（即将到期）
export function useUrgentReminders(hoursThreshold = 24) {
  return useQuery({
    queryKey: ['urgent-reminders', hoursThreshold],
    queryFn: async (): Promise<Reminder[]> => {
      const response = await fetch(`/api/reminders/urgent?hours=${hoursThreshold}`);
      if (!response.ok) throw new Error('获取紧急提醒失败');
      const data = await response.json();
      return data.items || [];
    },
    refetchInterval: 60000, // 每分钟刷新
  });
}
