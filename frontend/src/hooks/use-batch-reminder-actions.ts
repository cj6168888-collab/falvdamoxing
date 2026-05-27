import { useCallback, useState } from 'react';
import type { Reminder } from '@/types/reminder.types';

interface UseBatchReminderActionsProps {
  onSuccess?: (message: string) => void;
  onError?: (error: string) => void;
}

export function useBatchReminderActions({
  onSuccess,
  onError,
}: UseBatchReminderActionsProps = {}) {
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const selectAll = useCallback((items: Reminder[]) => {
    setSelectedIds(new Set(items.map((item) => String(item.id))));
  }, []);

  const deselectAll = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const toggleSelect = useCallback((id: string, selected: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }, []);

  const handleBatchMarkRead = useCallback(
    async (updateReminder: (id: string, data: { is_read: boolean }) => Promise<void>) => {
      setIsLoading(true);
      try {
        await Promise.all(Array.from(selectedIds).map((id) => updateReminder(id, { is_read: true })));
        onSuccess?.('已标记为已读');
        deselectAll();
      } catch {
        onError?.('操作失败');
      } finally {
        setIsLoading(false);
      }
    },
    [selectedIds, deselectAll, onSuccess, onError]
  );

  const handleBatchMarkUnread = useCallback(
    async (updateReminder: (id: string, data: { is_read: boolean }) => Promise<void>) => {
      setIsLoading(true);
      try {
        await Promise.all(Array.from(selectedIds).map((id) => updateReminder(id, { is_read: false })));
        onSuccess?.('已标记为未读');
        deselectAll();
      } catch {
        onError?.('操作失败');
      } finally {
        setIsLoading(false);
      }
    },
    [selectedIds, deselectAll, onSuccess, onError]
  );

  const handleBatchComplete = useCallback(
    async (updateReminder: (id: string, data: { is_completed: boolean }) => Promise<void>) => {
      setIsLoading(true);
      try {
        await Promise.all(Array.from(selectedIds).map((id) => updateReminder(id, { is_completed: true })));
        onSuccess?.('已标记为完成');
        deselectAll();
      } catch {
        onError?.('操作失败');
      } finally {
        setIsLoading(false);
      }
    },
    [selectedIds, deselectAll, onSuccess, onError]
  );

  const handleBatchUncomplete = useCallback(
    async (updateReminder: (id: string, data: { is_completed: boolean }) => Promise<void>) => {
      setIsLoading(true);
      try {
        await Promise.all(Array.from(selectedIds).map((id) => updateReminder(id, { is_completed: false })));
        onSuccess?.('已取消完成状态');
        deselectAll();
      } catch {
        onError?.('操作失败');
      } finally {
        setIsLoading(false);
      }
    },
    [selectedIds, deselectAll, onSuccess, onError]
  );

  const handleBatchSnooze = useCallback(
    async (days: number, snoozeReminder: (id: string, days: number) => Promise<void>) => {
      setIsLoading(true);
      try {
        await Promise.all(Array.from(selectedIds).map((id) => snoozeReminder(id, days)));
        onSuccess?.(`已延后 ${days} 天`);
        deselectAll();
      } catch {
        onError?.('操作失败');
      } finally {
        setIsLoading(false);
      }
    },
    [selectedIds, deselectAll, onSuccess, onError]
  );

  const handleBatchDelete = useCallback(
    async (deleteReminder: (id: string) => Promise<void>) => {
      setIsLoading(true);
      try {
        await Promise.all(Array.from(selectedIds).map((id) => deleteReminder(id)));
        onSuccess?.('已删除');
        deselectAll();
      } catch {
        onError?.('删除失败');
      } finally {
        setIsLoading(false);
      }
    },
    [selectedIds, deselectAll, onSuccess, onError]
  );

  return {
    selectedIds,
    isLoading,
    selectAll,
    deselectAll,
    toggleSelect,
    handleBatchMarkRead,
    handleBatchMarkUnread,
    handleBatchComplete,
    handleBatchUncomplete,
    handleBatchSnooze,
    handleBatchDelete,
  };
}
