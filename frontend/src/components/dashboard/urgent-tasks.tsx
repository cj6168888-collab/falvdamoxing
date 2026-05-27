import { EmptyState } from '@/components/common/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import { UrgencyBadge } from '@/components/ui/urgency-badge';
import { formatChineseDate } from '@/lib/date';
import type { UrgentTask } from '@/types/dashboard.types';
import { motion } from 'framer-motion';
import { AlertTriangle, ArrowRight, CalendarDays, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TEXT = {
  sectionTitle: '紧急待办',
  sectionHint: '需要立即行动',
  itemLabel: '紧急事项',
  deadlinePrefix: '截止',
  error: '加载紧急待办失败',
  retry: '点击重试',
  emptyTitle: '暂无紧急事项',
  emptyDescription: '当前没有需要立即处理的事项，继续保持关注',
};

const typeIconMap: Record<UrgentTask['type'], typeof AlertTriangle> = {
  appeal: AlertTriangle,
  evidence: Clock,
  hearing: CalendarDays,
  filing: CalendarDays,
  response: AlertTriangle,
  other: Clock,
};

function UrgentTaskItem({ task }: { task: UrgentTask }) {
  const navigate = useNavigate();
  const Icon = typeIconMap[task.type];

  const isExpired = task.daysRemaining < 0;
  const isUrgent = task.daysRemaining >= 0 && task.daysRemaining <= 3;

  return (
    <motion.button
      type="button"
      onClick={() => navigate(task.redirectPath || '/dashboard')}
      className={`group w-full rounded-lg border p-4 text-left transition-all duration-200 hover:shadow-md ${
        isExpired
          ? 'border-red-200 bg-red-50 hover:border-red-300 dark:border-red-800 dark:bg-red-950/30 dark:hover:border-red-700'
          : isUrgent
            ? 'border-amber-200 bg-amber-50 hover:border-amber-300 dark:border-amber-800 dark:bg-amber-950/30 dark:hover:border-amber-700'
            : 'border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600'
      }`}
      whileHover={{ x: 4 }}
      transition={{ duration: 0.15 }}
      aria-label={`${TEXT.itemLabel}: ${task.title}, ${task.caseTitle ?? ''}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <div
            className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
              isExpired
                ? 'bg-red-100 text-red-600 dark:bg-red-900/50 dark:text-red-400'
                : isUrgent
                  ? 'bg-amber-100 text-amber-600 dark:bg-amber-900/50 dark:text-amber-400'
                  : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
            }`}
          >
            <Icon className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                {task.title}
              </span>
              <UrgencyBadge daysRemaining={task.daysRemaining} />
            </div>
            <p className="mt-1 truncate text-sm text-gray-600 dark:text-gray-400">
              {task.caseTitle}
            </p>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-500">
              {TEXT.deadlinePrefix}: {formatChineseDate(task.dueDate || new Date())}
            </p>
          </div>
        </div>
        <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-gray-400 transition-colors group-hover:text-blue-500 dark:text-gray-500 dark:group-hover:text-blue-400" />
      </div>
    </motion.button>
  );
}

function UrgentTaskSkeleton() {
  return (
    <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
      <div className="flex items-start gap-3">
        <Skeleton className="h-8 w-8 shrink-0 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-48" />
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-3 w-24" />
        </div>
      </div>
    </div>
  );
}

export function UrgentTasks({
  tasks,
  isLoading,
  isError,
  onRetry,
}: {
  tasks: UrgentTask[];
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
}) {
  if (isLoading) {
    return (
      <section aria-label={TEXT.sectionTitle}>
        <div className="mb-4 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{TEXT.sectionTitle}</h2>
          <span className="ml-auto text-xs text-gray-500 dark:text-gray-400">{TEXT.sectionHint}</span>
        </div>
        <div className="space-y-3">
          <UrgentTaskSkeleton />
          <UrgentTaskSkeleton />
          <UrgentTaskSkeleton />
        </div>
      </section>
    );
  }

  if (isError) {
    return (
      <section aria-label={TEXT.sectionTitle}>
        <div className="mb-4 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{TEXT.sectionTitle}</h2>
        </div>
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-950/30">
          <p className="text-sm text-red-600 dark:text-red-400">{TEXT.error}</p>
          <button
            type="button"
            onClick={onRetry}
            className="mt-2 text-sm font-medium text-red-700 underline dark:text-red-300"
          >
            {TEXT.retry}
          </button>
        </div>
      </section>
    );
  }

  if (tasks.length === 0) {
    return (
      <section aria-label={TEXT.sectionTitle}>
        <div className="mb-4 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{TEXT.sectionTitle}</h2>
          <span className="ml-auto text-xs text-gray-500 dark:text-gray-400">{TEXT.sectionHint}</span>
        </div>
        <EmptyState
          icon={AlertTriangle}
          title={TEXT.emptyTitle}
          description={TEXT.emptyDescription}
        />
      </section>
    );
  }

  return (
    <section aria-label={TEXT.sectionTitle}>
      <div className="mb-4 flex items-center gap-2">
        <AlertTriangle className="h-5 w-5 text-red-500" />
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{TEXT.sectionTitle}</h2>
        <span className="ml-auto text-xs text-gray-500 dark:text-gray-400">{TEXT.sectionHint}</span>
      </div>
      <div className="space-y-3">
        {tasks.map((task) => (
          <UrgentTaskItem key={task.id} task={task} />
        ))}
      </div>
    </section>
  );
}
