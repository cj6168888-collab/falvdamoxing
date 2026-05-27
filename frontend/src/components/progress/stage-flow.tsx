import { useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, CalendarClock, CheckCircle2, Flag, Loader2, RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { formatChineseDate, daysUntil } from '@/lib/date';
import { generateMilestones, getMilestones, useDeadlines, type TimelineMilestone } from '@/api/timeline.api';
import type { Deadline } from '@/types/deadline.types';

interface Props {
  caseId: string;
}

const STAGES = [
  { key: 'pre_litigation', label: '诉前准备', aliases: ['pre_litigation', '诉前准备', 'milestone'] },
  { key: 'filing', label: '立案', aliases: ['filing', '立案'] },
  { key: 'evidence', label: '举证', aliases: ['evidence', '举证'] },
  { key: 'defense', label: '答辩', aliases: ['defense', '答辩'] },
  { key: 'trial', label: '庭审', aliases: ['trial', 'hearing', '庭审', '审理'] },
  { key: 'judgment', label: '判决', aliases: ['judgment', '判决'] },
  { key: 'execution', label: '执行', aliases: ['execution', '执行'] },
  { key: 'closed', label: '结案', aliases: ['closed', '结案'] },
];

const STATUS_LABELS: Record<string, string> = {
  pending: '待处理',
  active: '临近',
  expired: '已过期',
  completed: '已完成',
  suspended: '已中止',
  extended: '已展期',
};

function safeFormatDate(date?: string) {
  if (!date) return '未设置';
  try {
    return formatChineseDate(date);
  } catch {
    return date;
  }
}

function getDeadlineTone(deadline: Deadline) {
  if (deadline.status === 'completed') return 'bg-green-50 text-green-700 border-green-200';
  if (deadline.status === 'expired') return 'bg-red-50 text-red-700 border-red-200';
  if (!deadline.dueDate) return 'bg-slate-50 text-slate-600 border-slate-200';

  try {
    const remaining = daysUntil(deadline.dueDate);
    if (remaining < 0) return 'bg-red-50 text-red-700 border-red-200';
    if (remaining <= 7) return 'bg-amber-50 text-amber-700 border-amber-200';
  } catch {
    return 'bg-slate-50 text-slate-600 border-slate-200';
  }

  return 'bg-blue-50 text-blue-700 border-blue-200';
}

function calculateStageIndex(milestones: TimelineMilestone[], deadlines: Deadline[]) {
  const latestType = [...milestones]
    .reverse()
    .map((item) => item.type)
    .find(Boolean);

  if (latestType) {
    const normalized = latestType.toLowerCase();
    const stageIndex = STAGES.findIndex((stage) => stage.aliases.some((alias) => normalized.includes(alias.toLowerCase())));
    if (stageIndex >= 0) return stageIndex;
  }

  if (deadlines.length > 0) return 2;
  return 0;
}

function MilestoneCard({ milestone }: { milestone: TimelineMilestone }) {
  return (
    <Card className="border-slate-200">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Flag className="h-4 w-4 text-teal-700" />
              <p className="truncate font-medium text-slate-950 dark:text-slate-100">{milestone.title}</p>
            </div>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{milestone.description || '无说明'}</p>
            {milestone.aiSummary && <p className="mt-2 text-xs text-slate-500">{milestone.aiSummary}</p>}
          </div>
          <div className="shrink-0 text-right">
            <Badge variant="outline">{milestone.importance === 'important' ? '重要' : '普通'}</Badge>
            <p className="mt-2 text-xs text-slate-500">{safeFormatDate(milestone.date)}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function DeadlineCard({ deadline }: { deadline: Deadline }) {
  let remainingLabel = '未设置截止日';
  if (deadline.dueDate) {
    try {
      const remaining = daysUntil(deadline.dueDate);
      remainingLabel = remaining < 0 ? `已逾期 ${Math.abs(remaining)} 天` : `剩余 ${remaining} 天`;
    } catch {
      remainingLabel = '日期待核验';
    }
  }

  return (
    <Card className="border-slate-200">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <CalendarClock className="h-4 w-4 text-amber-700" />
              <p className="truncate font-medium text-slate-950 dark:text-slate-100">{deadline.title}</p>
            </div>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{deadline.legalBasis || deadline.type}</p>
            {deadline.relatedTasks?.length ? (
              <p className="mt-2 text-xs text-slate-500">{deadline.relatedTasks.join('、')}</p>
            ) : null}
          </div>
          <div className="shrink-0 text-right">
            <Badge variant="outline" className={getDeadlineTone(deadline)}>
              {STATUS_LABELS[deadline.status] || deadline.status}
            </Badge>
            <p className="mt-2 text-xs text-slate-500">{safeFormatDate(deadline.dueDate)}</p>
            <p className="mt-1 text-xs font-medium text-slate-700 dark:text-slate-200">{remainingLabel}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function StageFlow({ caseId }: Props) {
  const queryClient = useQueryClient();
  const deadlinesQuery = useDeadlines(caseId);
  const milestonesQuery = useQuery({
    queryKey: ['milestones', caseId],
    queryFn: () => getMilestones(caseId),
    enabled: !!caseId,
  });
  const generateMutation = useMutation({
    mutationFn: () => generateMilestones(caseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['milestones', caseId] });
    },
  });

  const deadlines = deadlinesQuery.data || [];
  const milestones = milestonesQuery.data || [];
  const currentStage = useMemo(() => calculateStageIndex(milestones, deadlines), [deadlines, milestones]);
  const progressValue = Math.round(((currentStage + 1) / STAGES.length) * 100);
  const isLoading = deadlinesQuery.isLoading || milestonesQuery.isLoading;
  const hasError = deadlinesQuery.isError || milestonesQuery.isError;

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-950 dark:text-slate-100">进度追踪</h2>
          <p className="mt-1 text-sm text-slate-500">当前阶段：{STAGES[currentStage].label}</p>
        </div>
        <Button
          variant="outline"
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending || !caseId}
        >
          {generateMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
          生成里程碑
        </Button>
      </div>

      {hasError && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="flex items-center gap-2 py-3 text-sm text-red-700">
            <AlertCircle className="h-4 w-4" />
            进度数据加载失败
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">阶段流转</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-3 md:grid-cols-8">
            {STAGES.map((stage, index) => {
              const done = index < currentStage;
              const active = index === currentStage;
              return (
                <div key={stage.key} className="flex min-w-0 flex-col items-center text-center">
                  <div
                    className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-medium ${
                      done
                        ? 'bg-green-600 text-white'
                        : active
                          ? 'bg-teal-700 text-white'
                          : 'bg-slate-100 text-slate-500 dark:bg-slate-800'
                    }`}
                  >
                    {done ? <CheckCircle2 className="h-4 w-4" /> : index + 1}
                  </div>
                  <span className="mt-2 text-xs text-slate-600 dark:text-slate-300">{stage.label}</span>
                </div>
              );
            })}
          </div>
          <div className="mt-5">
            <div className="mb-2 flex justify-between text-xs text-slate-500">
              <span>{STAGES[currentStage].label}</span>
              <span>{progressValue}%</span>
            </div>
            <Progress value={progressValue} />
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">关键里程碑</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {milestones.length ? (
              milestones.map((milestone) => <MilestoneCard key={milestone.id} milestone={milestone} />)
            ) : (
              <div className="rounded-md border border-dashed p-6 text-center text-sm text-slate-500">暂无里程碑</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">期限节点</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {deadlines.length ? (
              deadlines.map((deadline) => <DeadlineCard key={deadline.id} deadline={deadline} />)
            ) : (
              <div className="rounded-md border border-dashed p-6 text-center text-sm text-slate-500">暂无期限</div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
