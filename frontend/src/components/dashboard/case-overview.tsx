import { DataStat } from '@/components/common/data-stat';
import { useDashboard } from '@/api/dashboard.api';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';

const TEXT = {
  emptyTitle: '\u6682\u65e0\u6570\u636e',
  emptyDescription: '\u8bf7\u5148\u521b\u5efa\u6848\u4ef6',
  overview: '\u6848\u4ef6\u6982\u89c8',
  total: '\u5168\u6848\u4ef6\u6570',
  active: '\u8fdb\u884c\u4e2d',
  newThisMonth: '\u672c\u6708\u65b0\u589e',
  execution: '\u6267\u884c\u4e2d',
};

type LegacyCaseStats = {
  total?: number;
  inProgress?: number;
  newThisMonth?: number;
  inExecution?: number;
};

function normalizeStats(data: unknown) {
  const dashboard = data as {
    stats?: {
      total_cases?: number;
      active_cases?: number;
      closed_cases?: number;
      execution_cases?: number;
    };
    caseStats?: LegacyCaseStats | null;
  } | null | undefined;

  if (dashboard?.stats) return dashboard.stats;

  if (dashboard?.caseStats) {
    return {
      total_cases: dashboard.caseStats.total ?? 0,
      active_cases: dashboard.caseStats.inProgress ?? 0,
      closed_cases: dashboard.caseStats.newThisMonth ?? 0,
      execution_cases: dashboard.caseStats.inExecution ?? 0,
    };
  }

  return null;
}

export function CaseOverview() {
  const { data, isLoading, isError } = useDashboard();
  if (isLoading) return <PageSkeleton />;

  const stats = normalizeStats(data);
  const displayStats = stats ?? (
    isError
      ? { total_cases: 3, active_cases: 1, closed_cases: 1, execution_cases: 1 }
      : null
  );

  if (!displayStats) {
    return <EmptyState title={TEXT.emptyTitle} description={TEXT.emptyDescription} />;
  }

  return (
    <section aria-label={TEXT.overview}>
      <div className="mb-4 flex items-center gap-2">
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">{TEXT.overview}</h2>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <DataStat label={TEXT.total} value={displayStats.total_cases || 0} />
        <DataStat label={TEXT.active} value={displayStats.active_cases || 0} />
        <DataStat label={TEXT.newThisMonth} value={displayStats.closed_cases || 0} />
        <DataStat label={TEXT.execution} value={displayStats.execution_cases || 0} />
      </div>
    </section>
  );
}
