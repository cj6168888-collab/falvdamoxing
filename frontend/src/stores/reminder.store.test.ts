import { renderHook, act } from '@testing-library/react';
import { useReminderStore } from './reminder.store';
import type { Reminder } from '@/types/reminder.types';

describe('useReminderStore', () => {
  beforeEach(() => {
    useReminderStore.setState({ reminders: [], unreadCount: 0 });
  });

  it('initializes with empty reminders', () => {
    const { result } = renderHook(() => useReminderStore());
    expect(result.current.reminders).toEqual([]);
    expect(result.current.unreadCount).toBe(0);
  });

  it('sets reminders and calculates unread count', () => {
    const { result } = renderHook(() => useReminderStore());
    const mockReminders: Reminder[] = [
      createReminder({ id: 1, title: 'Test 1', is_read: false, priority: 'high' }),
      createReminder({ id: 2, title: 'Test 2', is_read: true, priority: 'medium' }),
    ];
    act(() => {
      result.current.setReminders(mockReminders);
    });
    expect(result.current.reminders).toHaveLength(2);
    expect(result.current.unreadCount).toBe(1);
  });

  it('marks a reminder as read', () => {
    const { result } = renderHook(() => useReminderStore());
    const mockReminders: Reminder[] = [
      createReminder({ id: 1, title: 'Test', is_read: false, priority: 'high' }),
    ];
    act(() => {
      result.current.setReminders(mockReminders);
    });
    expect(result.current.unreadCount).toBe(1);
    act(() => {
      result.current.markAsRead('1');
    });
    expect(result.current.unreadCount).toBe(0);
  });

  it('marks all reminders as read', () => {
    const { result } = renderHook(() => useReminderStore());
    const mockReminders: Reminder[] = [
      createReminder({ id: 1, title: 'Test 1', is_read: false, priority: 'high' }),
      createReminder({ id: 2, title: 'Test 2', is_read: false, priority: 'medium' }),
    ];
    act(() => {
      result.current.setReminders(mockReminders);
    });
    expect(result.current.unreadCount).toBe(2);
    act(() => {
      result.current.markAllAsRead();
    });
    expect(result.current.unreadCount).toBe(0);
  });
});

function createReminder(overrides: Partial<Reminder>): Reminder {
  return {
    id: 1,
    reminder_type: 'deadline',
    priority: 'medium',
    title: 'Test',
    content: 'Reminder content',
    is_triggered: false,
    is_read: false,
    is_completed: false,
    created_at: '2024-01-01',
    ...overrides,
  };
}
