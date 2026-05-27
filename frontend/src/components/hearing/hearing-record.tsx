import { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useHearingList, useHearingStatementList } from '@/hooks/use-hearing';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { CalendarDays, MapPin, Mic2, Plus } from 'lucide-react';
import type { Hearing } from '@/types/hearing.types';

interface Props { caseId: string; }

const HEARING_TYPE_LABELS: Record<string, string> = {
  first_trial: '一审',
  second_trial: '二审',
  retrial: '再审',
};

const STATUS_LABELS: Record<string, string> = {
  preparing: '准备中',
  in_progress: '进行中',
  completed: '已完成',
  cancelled: '已取消',
};

const PHASE_LABELS: Record<string, string> = {
  preparation: '庭前准备',
  court_investigation: '法庭调查',
  cross_examination: '法庭调查/质证',
  court_debate: '法庭辩论',
  final_statement: '最后陈述',
};

function formatLabel(value: string | undefined, labels: Record<string, string>, fallback = '未设置') {
  if (!value) return fallback;
  return labels[value] || value;
}

function formatDate(value: string | undefined) {
  if (!value) return '未设置日期';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('zh-CN');
}

export function HearingRecord({ caseId }: Props) {
  const { data, isLoading } = useHearingList(caseId);
  const hearings = useMemo(() => data || [], [data]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selectedHearing = hearings.find((hearing: Hearing) => hearing.id === selectedId) || hearings[0];
  const { data: statements, isLoading: statementsLoading } = useHearingStatementList(selectedHearing?.id || null);

  useEffect(() => {
    if (!selectedId && hearings.length > 0) {
      setSelectedId(hearings[0].id);
    }
  }, [hearings, selectedId]);

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold">出庭抗辩</h2>
        <Button size="sm" variant="outline"><Plus className="mr-2 h-4 w-4" />添加开庭记录</Button>
      </div>

      {!hearings.length ? (
        <p className="text-muted-foreground text-center py-8">暂无开庭记录</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(320px,420px)]">
          <div className="space-y-3">
            {hearings.map((hearing: Hearing) => {
              const isSelected = selectedHearing?.id === hearing.id;
              return (
                <Card
                  key={hearing.id}
                  className={`cursor-pointer transition-shadow hover:shadow-md ${isSelected ? 'border-primary' : ''}`}
                  onClick={() => setSelectedId(hearing.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="font-medium">{formatLabel(hearing.hearingType || hearing.type, HEARING_TYPE_LABELS)}</p>
                        <div className="mt-2 flex flex-wrap gap-3 text-sm text-muted-foreground">
                          <span className="inline-flex items-center gap-1">
                            <CalendarDays className="h-4 w-4" />
                            {formatDate(hearing.date)}
                          </span>
                          <span className="inline-flex items-center gap-1">
                            <MapPin className="h-4 w-4" />
                            {hearing.location || hearing.courtName || '未填写地点'}
                          </span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Badge>{formatLabel(hearing.status, STATUS_LABELS)}</Badge>
                        {hearing.currentPhase && (
                          <Badge variant="outline">{formatLabel(hearing.currentPhase, PHASE_LABELS)}</Badge>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Mic2 className="h-4 w-4" />
                庭审发言记录
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!selectedHearing ? (
                <p className="text-sm text-muted-foreground">请选择一条开庭记录</p>
              ) : statementsLoading ? (
                <p className="text-sm text-muted-foreground">正在加载发言记录...</p>
              ) : !statements?.length ? (
                <p className="text-sm text-muted-foreground">暂无发言记录</p>
              ) : (
                <div className="space-y-3">
                  {statements.map((statement) => (
                    <div key={statement.id} className="rounded-md border p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-2 text-sm">
                          <Badge variant="outline">{statement.speakerName || statement.speakerRole || '未知发言人'}</Badge>
                          {statement.statementType && <span className="text-muted-foreground">{statement.statementType}</span>}
                        </div>
                        {statement.isTrap && <Badge variant="destructive">陷阱提醒</Badge>}
                      </div>
                      <p className="mt-2 whitespace-pre-wrap text-sm">{statement.content}</p>
                      {statement.suggestion && (
                        <p className="mt-2 rounded bg-muted p-2 text-xs text-muted-foreground">{statement.suggestion}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
