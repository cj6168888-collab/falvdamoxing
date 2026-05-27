import { create } from 'zustand';
import type { Reminder } from '@/types/reminder.types';

interface ReminderStore {
  reminders: Reminder[];
  setReminders: (reminders: Reminder[]) => void;
  markAsRead: (id: number | string) => void;
  markAllAsRead: () => void;
  unreadCount: number;
}

function isUnread(reminder: Reminder | { is_read?: boolean; isRead?: boolean }) {
  if ('is_read' in reminder && reminder.is_read !== undefined) {
    return !reminder.is_read;
  }
  return !(reminder as { isRead?: boolean }).isRead;
}

export const useReminderStore = create<ReminderStore>((set) => ({
  reminders: [],
  setReminders: (reminders) => set({ reminders, unreadCount: reminders.filter(isUnread).length }),
  markAsRead: (id) =>
    set((state) => {
      const updated = state.reminders.map((r) =>
        String(r.id) === String(id) ? { ...r, is_read: true, isRead: true } : r
      );
      return { reminders: updated, unreadCount: updated.filter(isUnread).length };
    }),
  markAllAsRead: () =>
    set((state) => ({
      reminders: state.reminders.map((r) => ({ ...r, is_read: true, isRead: true })),
      unreadCount: 0,
    })),
  unreadCount: 0,
}));
