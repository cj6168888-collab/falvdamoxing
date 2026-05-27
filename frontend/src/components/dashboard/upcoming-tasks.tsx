import { EmptyState } from '@/components/common/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import { UrgencyBadge } from '@/components/ui/urgency-badge';
import { formatChineseDate } from '@/lib/date';
import type { UpcomingTask } from '@/types/dashboard.types';
import { motion } from 'framer-motion';
import { ArrowRight, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TEXT = {
  sectionTitle: '近期待办',
  sectionHint: '30 天内',
  itemLabel: '待办',
  error: '加载近期待办失败',
  retry: '点击重试',
  emptyTitle: '暂无近期待办',
  emptyDescription: '30 天内没有待办事项，好好休息或处理其他工作',
};

function UpcomingTaskItem({ task }: { task: UpcomingTask }) {
  const navigate = useNavigate();
  const caseTitle = task.caseTitle || task.case_title || '';
  const dueDate = task.dueDate || task.due_date || '';

  return (
    <motion.button
      type="button"
      onClick={() => navigate(task.redirectPath || (task.case_id ? `/cases/${task.case_id}` : '/dashboard'))}
      className="group flex w-full items-center justify-between gap-3 rounded-lg border border-gray-200 bg-white p-4 transition-all duration-200 hover:border-gray-300 hover:shadow-sm dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600"
      whileHover={{ x: 4 }}
      transition={{ duration: 0.15 }}
      aria-label={`${TEXT.itemLabel}: ${task.title}, ${caseTitle}`}
    >
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400">
          <Clock className="h-4 w-4" />
        </div>
        <div className="min-w-0 text-left">
          <div className="flex flex-wrap items-center gap-2">
            <span className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">
              {task.title}
            </span>
            <UrgencyBadge daysRemaining={task.daysRemaining ?? task.days_until ?? 0} />
          </div>
          <div className="mt-0.5 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            <span className="truncate">{caseTitle}</span>
            <span className="shrink-0">·</span>
            <span className="shrink-0">{formatChineseDate(dueDate)}</span>
          </div>
        </div>
      </div>
      <ArrowRight className="h-4 w-4 shrink-0 text-gray-400 transition-colors group-hover:text-blue-500 dark:text-gray-500 dark:group-hover:text-blue-400" />
    </motion.button>
  );
}

function UpcomingTaskSkeleton() {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-gray-200 p-4 dark:border-gray-700">
      <Skeleton className="h-9 w-9 shrink-0 rounded-full" />
      <div className="min-w-0 flex-1 space-y-2">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-3 w-56" />
      </div>
    </div>
  );
}

export function UpcomingTasks({
  tasks,
  isLoading,
  isError,
  onRetry,
}: {
  tasks: UpcomingTask[];
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
}) {
  return (
    <section aria-label={TEXT.sectionTitle}>
      <div className="mb-4 flex items-center gap-2">
        <Clock className="h-5 w-5 text-amber-500" />
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{TEXT.sectionTitle}</h2>
        <span className="ml-auto text-xs text-gray-500 dark:text-gray-400">{TEXT.sectionHint}</span>
      </div>

      {isError ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center dark:border-red-800 dark:bg-red-950/30">
          <p className="text-sm text-red-600 dark:text-red-400">{TEXT.error}</p>
          <button
            type="button"
            onClick={onRetry}
            className="mt-1 text-sm font-medium text-red-700 underline dark:text-red-300"
          >
            {TEXT.retry}
          </button>
        </div>
      ) : isLoading ? (
        <div className="space-y-3">
          <UpcomingTaskSkeleton />
          <UpcomingTaskSkeleton />
          <UpcomingTaskSkeleton />
        </div>
      ) : tasks.length === 0 ? (
        <EmptyState
          icon={Clock}
          title={TEXT.emptyTitle}
          description={TEXT.emptyDescription}
        />
      ) : (
        <div className="space-y-2">
          {tasks.map((task) => (
            <UpcomingTaskItem key={task.id} task={task} />
          ))}
        </div>
      )}
    </section>
  );
}
