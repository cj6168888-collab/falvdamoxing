import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, waitFor } from '@/test/test-utils';
import axiosInstance from '@/api/client';
import {
  useAutoGenerateAllReminders,
  useAutoGenerateReminders,
  useBatchUpdateReminders,
  useCreateReminder,
  useDeleteReminder,
  useMarkAllRemindersRead,
  useMarkReminderComplete,
  useMarkReminderRead,
  useOverdueReminders,
  useReminderStats,
  useReminders,
  useSnoozeReminder,
  useUpdateReminder,
} from './reminder.api';
import type { Reminder } from '@/types/reminder.types';
import type { ReactNode } from 'react';
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

const reminder: Reminder = {
  id: 1,
  case_id: 12,
  reminder_type: 'deadline',
  priority: 'high',
  title: 'Submit evidence',
  content: 'Prepare evidence list',
  is_triggered: false,
  is_read: false,
  is_completed: false,
};

beforeEach(() => {
  mockGet.mockReset();
  mockPost.mockReset();
  mockPut.mockReset();
  mockDelete.mockReset();
});

describe('reminder api queries', () => {
  it('loads reminders with optional case filter', async () => {
    const response = { reminders: [reminder], total: 1 };
    mockGet.mockResolvedValueOnce({ data: response });

    const { result } = renderHook(() => useReminders('12'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data).toEqual(response));
    expect(mockGet).toHaveBeenCalledWith('/api/reminders', { params: { case_id: '12' } });
  });

  it('normalizes the legacy reminder array response', async () => {
    mockGet.mockResolvedValueOnce({
      data: [{
        id: 2,
        case_id: 12,
        case_title: 'Case',
        title: 'Legacy reminder',
        content: 'Legacy content',
        due_date: '2026-05-20',
        priority: 'high',
        status: 'pending',
        related_type: 'evidence',
        countdown_hours: 49,
      }],
    });

    const { result } = renderHook(() => useReminders(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.data?.total).toBe(1));
    expect(result.current.data?.reminders[0]).toMatchObject({
      id: 2,
      reminder_type: 'evidence',
      trigger_date: '2026-05-20T00:00:00',
      is_read: false,
      is_completed: false,
      days_until_trigger: 3,
    });
  });

  it('loads reminder stats and overdue reminders', async () => {
    mockGet
      .mockResolvedValueOnce({ data: { total: 1, pending: 1, by_priority: { high: 1 }, by_type: {} } })
      .mockResolvedValueOnce({ data: { reminders: [reminder], total: 1 } });

    const stats = renderHook(() => useReminderStats(), { wrapper: createWrapper() });
    const overdue = renderHook(() => useOverdueReminders(), { wrapper: createWrapper() });

    await waitFor(() => expect(stats.result.current.data).toMatchObject({
      total: 1,
      unread: 1,
      uncompleted: 1,
      high_priority: 1,
    }));
    await waitFor(() => expect(overdue.result.current.data).toEqual({ reminders: [reminder], total: 1 }));
    expect(mockGet).toHaveBeenNthCalledWith(1, '/api/reminders/stats', { params: undefined });
    expect(mockGet).toHaveBeenNthCalledWith(2, '/api/reminders/overdue');
  });
});

describe('reminder api mutations', () => {
  it('creates, updates, and deletes reminders', async () => {
    mockPost.mockResolvedValueOnce({ data: reminder });
    mockPut.mockResolvedValueOnce({ data: { ...reminder, title: 'Updated' } });
    mockDelete.mockResolvedValueOnce({ data: { deleted: true } });

    const create = renderHook(() => useCreateReminder(), { wrapper: createWrapper() });
    const update = renderHook(() => useUpdateReminder(), { wrapper: createWrapper() });
    const remove = renderHook(() => useDeleteReminder(), { wrapper: createWrapper() });

    await expect(create.result.current.mutateAsync({ title: 'Submit evidence' })).resolves.toEqual(reminder);
    await expect(update.result.current.mutateAsync({ reminderId: 1, data: { title: 'Updated' } })).resolves.toEqual({
      ...reminder,
      title: 'Updated',
    });
    await expect(remove.result.current.mutateAsync(1)).resolves.toEqual({ deleted: true });

    expect(mockPost).toHaveBeenCalledWith('/api/reminders', { title: 'Submit evidence' });
    expect(mockPut).toHaveBeenCalledWith('/api/reminders/1', { title: 'Updated' });
    expect(mockDelete).toHaveBeenCalledWith('/api/reminders/1');
  });

  it('marks, snoozes, batches, and auto-generates reminders', async () => {
    mockPut.mockResolvedValue({ data: { ok: true } });
    mockPost.mockResolvedValue({ data: { generated: 1 } });

    const markRead = renderHook(() => useMarkReminderRead(), { wrapper: createWrapper() });
    const markAll = renderHook(() => useMarkAllRemindersRead(), { wrapper: createWrapper() });
    const complete = renderHook(() => useMarkReminderComplete(), { wrapper: createWrapper() });
    const snooze = renderHook(() => useSnoozeReminder(), { wrapper: createWrapper() });
    const batch = renderHook(() => useBatchUpdateReminders(), { wrapper: createWrapper() });
    const autoOne = renderHook(() => useAutoGenerateReminders(), { wrapper: createWrapper() });
    const autoAll = renderHook(() => useAutoGenerateAllReminders(), { wrapper: createWrapper() });

    await markRead.result.current.mutateAsync(1);
    await markAll.result.current.mutateAsync('12');
    await complete.result.current.mutateAsync(1);
    await snooze.result.current.mutateAsync({ reminderId: 1, days: 3 });
    await batch.result.current.mutateAsync({ reminder_ids: [1, 2], is_read: true });
    await autoOne.result.current.mutateAsync(12);
    await autoAll.result.current.mutateAsync();

    expect(mockPut).toHaveBeenNthCalledWith(1, '/api/reminders/1', { is_read: true });
    expect(mockPut).toHaveBeenNthCalledWith(2, '/api/reminders/mark-all-read', null, { params: { case_id: '12' } });
    expect(mockPut).toHaveBeenNthCalledWith(3, '/api/reminders/1/complete');
    expect(mockPut).toHaveBeenNthCalledWith(4, '/api/reminders/1/snooze', { days: 3 });
    expect(mockPut).toHaveBeenNthCalledWith(5, '/api/reminders/batch', { reminder_ids: [1, 2], is_read: true });
    expect(mockPost).toHaveBeenNthCalledWith(1, '/api/reminders/auto-generate', null, { params: { case_id: 12 } });
    expect(mockPost).toHaveBeenNthCalledWith(2, '/api/reminders/auto-generate-all');
  });
});
