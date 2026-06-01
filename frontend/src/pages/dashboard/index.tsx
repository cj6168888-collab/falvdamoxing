import { useDashboard } from '@/api/dashboard.api';
import { EmptyState } from '@/components/common/empty-state';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { CaseOverview } from '@/components/dashboard/case-overview';
import { QuickActions } from '@/components/dashboard/quick-actions';
import { UpcomingTasks } from '@/components/dashboard/upcoming-tasks';
import { UrgentTasks } from '@/components/dashboard/urgent-tasks';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { formatChineseDate, formatChineseWeekday } from '@/lib/date';
import type { UrgentTask } from '@/types/dashboard.types';
import { useAuthStore } from '@/stores/auth.store';
import { RefreshCw } from 'lucide-react';
import { EnterpriseDashboard, PersonalDashboard } from './audience-dashboards';

const FALLBACK_URGENT_TYPE: UrgentTask['type'] = 'other';

function normalizeUrgentTaskType(type: string): UrgentTask['type'] {
  switch (type) {
    case 'appeal':
    case 'evidence':
    case 'hearing':
    case 'filing':
    case 'response':
    case 'other':
      return type;
    default:
      return FALLBACK_URGENT_TYPE;
  }
}

function LawFirmDashboard() {
  const { data, isLoading, isError, refetch } = useDashboard();
  const today = new Date();

  if (isLoading) return <PageSkeleton />;

  if (isError || !data) {
    return (
      <EmptyState
        title="无法加载工作台数据"
        description="请检查网络连接后重试"
        actionLabel="重试"
        onAction={() => refetch()}
      />
    );
  }

  const stats = data.stats;
  const urgentItems = data.urgent_items ?? [];
  const upcomingTasks = data.upcoming_tasks ?? [];

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">工作台</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {formatChineseDate(today)} {formatChineseWeekday(today)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-red-600 dark:text-red-400">
            <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-red-500" />
            {urgentItems.length} 项紧急
          </Badge>
          <Badge variant="outline" className="text-amber-600 dark:text-amber-400">
            <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-amber-500" />
            {upcomingTasks.length} 项待办
          </Badge>
          <Button variant="ghost" size="sm" onClick={() => refetch()} aria-label="刷新工作台">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.total_cases}</div>
            <p className="text-xs text-muted-foreground">总案件</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-blue-600">{stats.active_cases}</div>
            <p className="text-xs text-muted-foreground">进行中</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-600">{stats.closed_cases}</div>
            <p className="text-xs text-muted-foreground">已结案</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-amber-600">{stats.execution_cases}</div>
            <p className="text-xs text-muted-foreground">执行中</p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-8">
        {urgentItems.length > 0 && (
          <UrgentTasks
            tasks={urgentItems.map((item) => ({
              id: item.id,
              caseId: item.case_id ? String(item.case_id) : '',
              caseTitle: item.case_title ?? '',
              type: normalizeUrgentTaskType(item.type),
              title: item.title,
              description: item.description,
              daysRemaining: item.trigger_date
                ? Math.ceil((new Date(item.trigger_date).getTime() - Date.now()) / 86400000)
                : 0,
              dueDate: item.trigger_date ?? '',
              redirectPath: item.case_id ? `/cases/${item.case_id}` : '/dashboard',
            }))}
            isLoading={false}
            isError={false}
            onRetry={() => refetch()}
          />
        )}

        <CaseOverview />

        <UpcomingTasks
          tasks={upcomingTasks.map((task) => ({
            id: task.id,
            caseId: task.case_id ? String(task.case_id) : '',
            caseTitle: task.case_title ?? '',
            type: task.type,
            title: task.title,
            daysRemaining: task.days_until ?? 0,
            dueDate: task.due_date ?? '',
            redirectPath: task.case_id ? `/cases/${task.case_id}` : '/dashboard',
          }))}
          isLoading={false}
          isError={false}
          onRetry={() => refetch()}
        />

        <QuickActions />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const tenantType = useAuthStore((s) => s.tenant?.tenant_type);

  if (tenantType === 'enterprise') {
    return <EnterpriseDashboard />;
  }

  if (tenantType === 'personal') {
    return <PersonalDashboard />;
  }

  return <LawFirmDashboard />;
}
