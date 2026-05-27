import { useReminders, useMarkReminderRead as useMarkReminderReadApi, useMarkAllRemindersRead as useMarkAllRemindersReadApi } from '@/api/reminder.api';
import { useReminderStore } from '@/stores/reminder.store';

export function useReminderList(caseId?: string) {
  return useReminders(caseId);
}

export function useMarkReminderRead() {
  const apiMutation = useMarkReminderReadApi();
  const markAsRead = useReminderStore((state) => state.markAsRead);

  return {
    ...apiMutation,
    mutate: (reminderId: number, options?: Parameters<typeof apiMutation.mutate>[1]) => {
      markAsRead(reminderId);
      apiMutation.mutate(reminderId, options);
    },
  };
}

export function useMarkAllRemindersRead() {
  const apiMutation = useMarkAllRemindersReadApi();
  const markAllAsRead = useReminderStore((state) => state.markAllAsRead);

  return {
    ...apiMutation,
    mutate: (caseId?: string, options?: Parameters<typeof apiMutation.mutate>[1]) => {
      markAllAsRead();
      apiMutation.mutate(caseId, options);
    },
  };
}
