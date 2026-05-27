import { EmptyState } from '@/components/common/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import type { TodaySuggestion } from '@/types/dashboard.types';
import { AlertTriangle, CheckCircle, Info, Lightbulb } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TEXT = {
  sectionTitle: '今日建议',
  aiGenerated: 'AI 生成',
  itemLabel: 'AI 建议',
  error: '加载 AI 建议失败',
  retry: '点击重试',
  emptyTitle: '暂无建议',
  emptyDescription: 'AI 正在分析您的案件，稍后将生成个性化建议',
};

const priorityConfig: Record<
  TodaySuggestion['priority'],
  { icon: typeof Lightbulb; color: string; bgColor: string; label: string }
> = {
  high: {
    icon: AlertTriangle,
    color: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-100 dark:bg-red-900/50',
    label: '高优先',
  },
  medium: {
    icon: Lightbulb,
    color: 'text-amber-600 dark:text-amber-400',
    bgColor: 'bg-amber-100 dark:bg-amber-900/50',
    label: '中优先',
  },
  low: {
    icon: CheckCircle,
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-900/50',
    label: '低优先',
  },
};

function SuggestionItem({
  suggestion,
}: {
  suggestion: TodaySuggestion;
}) {
  const navigate = useNavigate();
  const config = priorityConfig[suggestion.priority];
  const Icon = config.icon;
  const content = suggestion.suggestion || suggestion.description;

  return (
    <button
      type="button"
      onClick={() => navigate(`/cases/${suggestion.caseId}`)}
      className="group w-full rounded-lg border border-gray-200 bg-white p-4 text-left transition-all duration-200 hover:border-gray-300 hover:shadow-sm dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600"
      aria-label={`${TEXT.itemLabel}: ${content}`}
    >
      <div className="flex items-start gap-3">
        <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${config.bgColor}`}>
          <Icon className={`h-4 w-4 ${config.color}`} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
              {suggestion.caseTitle || suggestion.title}
            </span>
            <span
              className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ${config.bgColor} ${config.color}`}
            >
              {config.label}
            </span>
          </div>
          <p className="mt-1.5 text-sm leading-relaxed text-gray-700 dark:text-gray-300">
            {content}
          </p>
        </div>
      </div>
    </button>
  );
}

function SuggestionSkeleton() {
  return (
    <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
      <div className="flex items-start gap-3">
        <Skeleton className="h-8 w-8 shrink-0 rounded-full" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </div>
    </div>
  );
}

export function TodaySuggestions({
  suggestions,
  isLoading,
  isError,
  onRetry,
}: {
  suggestions: TodaySuggestion[];
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
}) {
  return (
    <section aria-label={TEXT.sectionTitle}>
      <div className="mb-4 flex items-center gap-2">
        <Lightbulb className="h-5 w-5 text-yellow-500" />
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{TEXT.sectionTitle}</h2>
        <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
          <Info className="h-3 w-3" />
          {TEXT.aiGenerated}
        </span>
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
          <SuggestionSkeleton />
          <SuggestionSkeleton />
          <SuggestionSkeleton />
        </div>
      ) : suggestions.length === 0 ? (
        <EmptyState
          icon={Lightbulb}
          title={TEXT.emptyTitle}
          description={TEXT.emptyDescription}
        />
      ) : (
        <div className="space-y-2">
          {suggestions.map((suggestion) => (
            <SuggestionItem key={suggestion.id} suggestion={suggestion} />
          ))}
        </div>
      )}
    </section>
  );
}
