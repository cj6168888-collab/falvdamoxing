import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import type { Reminder, ReminderStats } from '@/types/reminder.types';

type LegacyReminder = Partial<Reminder> & {
  due_date?: string | null;
  status?: string | null;
  countdown_hours?: number | null;
  related_type?: string | null;
};

type ReminderListPayload = { reminders: LegacyReminder[]; total: number } | LegacyReminder[];

type ReminderStatsPayload = Partial<ReminderStats> & {
  pending?: number;
  by_priority?: Record<string, number>;
  today_reminders?: LegacyReminder[];
  upcoming_reminders?: LegacyReminder[];
};

export type NormalizedReminderStats = ReminderStats & {
  pending?: number;
  today_reminders?: Reminder[];
  upcoming_reminders?: Reminder[];
};

function normalizeReminder(raw: LegacyReminder): Reminder {
  const status = raw.status ?? '';
  const reminderType = raw.reminder_type ?? raw.related_type ?? 'deadline';
  const triggerDate = raw.trigger_date ?? (raw.due_date ? `${raw.due_date}T00:00:00` : undefined);
  const isCompleted = raw.is_completed ?? status === 'completed';
  const isRead = raw.is_read ?? isCompleted;

  const reminder: Reminder = {
    ...raw,
    id: Number(raw.id),
    case_id: raw.case_id !== undefined && raw.case_id !== null ? Number(raw.case_id) : undefined,
    reminder_type: reminderType as Reminder['reminder_type'],
    priority: (raw.priority ?? 'medium') as Reminder['priority'],
    title: raw.title ?? '',
    content: raw.content ?? '',
    is_triggered: raw.is_triggered ?? false,
    is_read: isRead,
    is_completed: isCompleted,
  };

  if (triggerDate) {
    reminder.trigger_date = triggerDate;
  }
  if (raw.is_overdue !== undefined || status === 'overdue') {
    reminder.is_overdue = raw.is_overdue ?? status === 'overdue';
  }
  if (raw.days_until_trigger !== undefined) {
    reminder.days_until_trigger = raw.days_until_trigger;
  } else if (raw.countdown_hours !== undefined && raw.countdown_hours !== null) {
    reminder.days_until_trigger = Math.ceil(raw.countdown_hours / 24);
  }

  return reminder;
}

export function normalizeReminderList(payload: ReminderListPayload): { reminders: Reminder[]; total: number } {
  if (Array.isArray(payload)) {
    return {
      reminders: payload.map(normalizeReminder),
      total: payload.length,
    };
  }

  const reminders = (payload.reminders ?? []).map(normalizeReminder);
  return {
    reminders,
    total: payload.total ?? reminders.length,
  };
}

export function normalizeReminderStats(data: ReminderStatsPayload): NormalizedReminderStats {
  const uncompleted = data.uncompleted ?? data.pending ?? 0;
  const upcomingReminders = data.upcoming_reminders?.map(normalizeReminder) ?? [];

  return {
    total: data.total ?? 0,
    unread: data.unread ?? uncompleted,
    uncompleted,
    pending: data.pending,
    completed: data.completed ?? 0,
    high_priority: data.high_priority ?? data.by_priority?.high ?? 0,
    overdue: data.overdue ?? 0,
    upcoming_7d: data.upcoming_7d ?? upcomingReminders.length,
    by_type: data.by_type ?? {},
    today_reminders: data.today_reminders?.map(normalizeReminder) ?? [],
    upcoming_reminders: upcomingReminders,
  };
}

function cleanReminderPayload(data: Partial<Reminder>) {
  return Object.fromEntries(
    Object.entries(data).filter(([, value]) => value !== undefined && value !== ''),
  );
}

// ============ Queries ============

export function useReminders(caseId?: string) {
  return useQuery({
    queryKey: ['reminders', caseId],
    queryFn: () => axiosInstance.get<ReminderListPayload>('/api/reminders', { params: caseId ? { case_id: caseId } : undefined }).then(res => normalizeReminderList(res.data)),
  });
}

export function useReminderStats(caseId?: string) {
  return useQuery({
    queryKey: ['reminder-stats', caseId],
    queryFn: () => axiosInstance.get<ReminderStatsPayload>('/api/reminders/stats', { params: caseId ? { case_id: caseId } : undefined }).then(res => normalizeReminderStats(res.data)),
  });
}

export function useOverdueReminders() {
  return useQuery({
    queryKey: ['overdue-reminders'],
    queryFn: () => axiosInstance.get<ReminderListPayload>('/api/reminders/overdue').then(res => normalizeReminderList(res.data)),
  });
}

// ============ Mutations ============

export function useCreateReminder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Reminder>) => axiosInstance.post('/api/reminders', cleanReminderPayload(data)).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      queryClient.invalidateQueries({ queryKey: ['reminder-stats'] });
    },
  });
}

export function useUpdateReminder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ reminderId, data }: { reminderId: number; data: Partial<Reminder> }) =>
      axiosInstance.put(`/api/reminders/${reminderId}`, cleanReminderPayload(data)).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
    },
  });
}

export function useDeleteReminder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reminderId: number) => axiosInstance.delete(`/api/reminders/${reminderId}`).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      queryClient.invalidateQueries({ queryKey: ['reminder-stats'] });
    },
  });
}

export function useMarkReminderRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reminderId: number) => axiosInstance.put(`/api/reminders/${reminderId}`, { is_read: true }).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      queryClient.invalidateQueries({ queryKey: ['reminder-stats'] });
    },
  });
}

export function useMarkAllRemindersRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (caseId?: string) => axiosInstance.put('/api/reminders/mark-all-read', null, { params: caseId ? { case_id: caseId } : undefined }).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      queryClient.invalidateQueries({ queryKey: ['reminder-stats'] });
    },
  });
}

export function useMarkReminderComplete() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reminderId: number) => axiosInstance.put(`/api/reminders/${reminderId}/complete`).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      queryClient.invalidateQueries({ queryKey: ['reminder-stats'] });
    },
  });
}

export function useSnoozeReminder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ reminderId, days }: { reminderId: number; days: number }) =>
      axiosInstance.put(`/api/reminders/${reminderId}/snooze`, { days }).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
    },
  });
}

export function useBatchUpdateReminders() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { reminder_ids: number[]; is_read?: boolean; is_completed?: boolean; priority?: string }) =>
      axiosInstance.put('/api/reminders/batch', data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'] });
      queryClient.invalidateQueries({ queryKey: ['reminder-stats'] });
    },
  });
}

export function useAutoGenerateReminders() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (caseId: number) => axiosInstance.post('/api/reminders/auto-generate', null, { params: { case_id: caseId } }).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'], refetchType: 'all' });
      queryClient.invalidateQueries({ queryKey: ['reminder-stats'], refetchType: 'all' });
    },
  });
}

export function useAutoGenerateAllReminders() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => axiosInstance.post('/api/reminders/auto-generate-all').then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reminders'], refetchType: 'all' });
      queryClient.invalidateQueries({ queryKey: ['reminder-stats'], refetchType: 'all' });
    },
  });
}
