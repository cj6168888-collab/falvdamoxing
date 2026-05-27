import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import {
  createAnalysisTask,
  startAnalysisTask,
  streamAnalysis,
  type AnalysisChunk,
  type AnalysisRequest,
} from '@/api/streaming-analysis.api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Clock, Eye, FileText, History, PlayCircle, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

interface AnalysisRecord {
  id: number;
  case_id: number;
  analysis_type: string;
  depth: string;
  status: string;
  summary: string | null;
  full_report: string | null;
  evidence_count: number;
  total_stages: number;
  completed_stages: number;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

interface StreamLine {
  id: string;
  stage: string;
  content: string;
}

const TYPE_LABELS: Record<AnalysisRequest['analysisType'], string> = {
  full: '全量分析',
  evidence: '证据分析',
  strategy: '策略分析',
  risk: '风险评估',
  custom: '自定义分析',
};

const DEPTH_LABELS: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
  exhaustive: '穷尽',
};

const DEFAULT_PROMPT = '请用一段话概括本案当前最关键的争议焦点、证据缺口和下一步行动。';

export default function AnalysisHistoryPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const queryClient = useQueryClient();
  const [selectedRecord, setSelectedRecord] = useState<AnalysisRecord | null>(null);
  const [analysisType, setAnalysisType] = useState<AnalysisRequest['analysisType']>('custom');
  const [depth, setDepth] = useState<'quick' | 'standard' | 'deep'>('standard');
  const [customPrompt, setCustomPrompt] = useState(DEFAULT_PROMPT);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState('');
  const [streamLines, setStreamLines] = useState<StreamLine[]>([]);
  const [streamError, setStreamError] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['analysis-history', caseId],
    queryFn: () => axiosInstance.get(`/api/streaming-analysis/case/${caseId}/history`).then(res => res.data),
    enabled: !!caseId,
  });

  const deleteMutation = useMutation({
    mutationFn: (recordId: number) => axiosInstance.delete(`/api/streaming-analysis/record/${recordId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analysis-history', caseId] });
      toast.success('分析记录已删除');
    },
    onError: () => toast.error('删除失败'),
  });

  const viewMutation = useMutation({
    mutationFn: (recordId: number) => axiosInstance.get(`/api/streaming-analysis/record/${recordId}`).then(res => res.data),
    onSuccess: (data) => setSelectedRecord(data),
  });

  const analyses: AnalysisRecord[] = data?.analyses || [];

  const handleStart = async () => {
    if (!caseId || isRunning) return;

    setSelectedRecord(null);
    setIsRunning(true);
    setProgress(0);
    setCurrentStage('准备分析');
    setStreamLines([]);
    setStreamError('');

    try {
      const task = await createAnalysisTask({
        caseId,
        analysisType,
        customPrompt: analysisType === 'custom' ? customPrompt : undefined,
        options: { depth },
      });

      await startAnalysisTask(task.task_id);

      for await (const chunk of streamAnalysis(task.task_id)) {
        handleStreamChunk(chunk);
      }

      await queryClient.invalidateQueries({ queryKey: ['analysis-history', caseId] });
      toast.success('流式分析已完成');
    } catch (error) {
      const message = error instanceof Error ? error.message : '流式分析失败';
      setStreamError(message);
      toast.error(message);
    } finally {
      setIsRunning(false);
    }
  };

  const handleStreamChunk = (chunk: AnalysisChunk) => {
    if (chunk.progress !== undefined) {
      setProgress(Math.round(chunk.progress * 100));
    }
    if (chunk.stage) {
      setCurrentStage(chunk.stage);
    }
    if (chunk.type === 'content' && chunk.content) {
      const content = chunk.content;
      setStreamLines((current) => [
        ...current,
        {
          id: `${Date.now()}-${current.length}`,
          stage: chunk.stage || currentStage || '分析输出',
          content,
        },
      ]);
    }
    if (chunk.type === 'error' && chunk.error) {
      setStreamError(chunk.error);
    }
    if (chunk.type === 'complete') {
      setProgress(100);
      setCurrentStage('分析完成');
    }
  };

  if (isLoading) return <PageSkeleton />;

  if (selectedRecord) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => setSelectedRecord(null)}>
            <History className="mr-1 h-4 w-4" />
            返回列表
          </Button>
          <h2 className="text-xl font-bold">{TYPE_LABELS[selectedRecord.analysis_type as AnalysisRequest['analysisType']] || selectedRecord.analysis_type}</h2>
          <Badge>{DEPTH_LABELS[selectedRecord.depth] || selectedRecord.depth}</Badge>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>分析摘要</CardTitle>
            <CardDescription>
              {selectedRecord.evidence_count} 条证据 · {selectedRecord.completed_stages}/{selectedRecord.total_stages} 阶段 · {new Date(selectedRecord.created_at).toLocaleString('zh-CN')}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {selectedRecord.full_report || selectedRecord.summary || '暂无内容'}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold">流式分析</h2>
          <p className="text-sm text-muted-foreground">共 {analyses.length} 次分析记录</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PlayCircle className="h-5 w-5" />
            发起分析
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {(Object.keys(TYPE_LABELS) as AnalysisRequest['analysisType'][]).map((item) => (
              <Button
                key={item}
                type="button"
                variant={analysisType === item ? 'default' : 'outline'}
                size="sm"
                disabled={isRunning}
                onClick={() => setAnalysisType(item)}
              >
                {TYPE_LABELS[item]}
              </Button>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            {(['quick', 'standard', 'deep'] as const).map((item) => (
              <Button
                key={item}
                type="button"
                variant={depth === item ? 'secondary' : 'outline'}
                size="sm"
                disabled={isRunning}
                onClick={() => setDepth(item)}
              >
                {DEPTH_LABELS[item]}
              </Button>
            ))}
          </div>

          {analysisType === 'custom' && (
            <Textarea
              value={customPrompt}
              disabled={isRunning}
              onChange={(event) => setCustomPrompt(event.target.value)}
              className="min-h-[96px]"
            />
          )}

          <Button onClick={handleStart} disabled={isRunning || !caseId || (analysisType === 'custom' && customPrompt.trim().length === 0)}>
            <PlayCircle className="mr-2 h-4 w-4" />
            {isRunning ? '分析中...' : '启动流式分析'}
          </Button>
        </CardContent>
      </Card>

      {(isRunning || streamLines.length > 0 || streamError) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>实时输出</span>
              <Badge variant={streamError ? 'destructive' : progress >= 100 ? 'default' : 'secondary'}>
                {streamError ? '失败' : progress >= 100 ? '已完成' : currentStage || '进行中'}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{currentStage || '准备分析'}</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>

            {streamError && (
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/20 dark:text-red-300">
                {streamError}
              </div>
            )}

            <div className="max-h-[520px] space-y-3 overflow-auto rounded-md border bg-muted/20 p-3">
              {streamLines.length === 0 ? (
                <p className="text-sm text-muted-foreground">等待后端输出...</p>
              ) : (
                streamLines.map((line) => (
                  <div key={line.id} className="rounded-md bg-background p-3">
                    <div className="mb-2 text-xs font-medium text-muted-foreground">{line.stage}</div>
                    <div className="whitespace-pre-wrap text-sm leading-6">{line.content}</div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>分析历史</CardTitle>
          <CardDescription>{analyses.length === 0 ? '暂无分析记录' : `共 ${analyses.length} 条记录`}</CardDescription>
        </CardHeader>
        <CardContent>
          {analyses.length === 0 ? (
            <div className="py-10 text-center text-sm text-muted-foreground">暂无分析记录</div>
          ) : (
            <div className="space-y-3">
              {analyses.map((record) => (
                <div key={record.id} className="flex items-start justify-between gap-4 rounded-md border p-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <FileText className="h-4 w-4 text-primary" />
                      <span className="font-medium">{TYPE_LABELS[record.analysis_type as AnalysisRequest['analysisType']] || record.analysis_type}</span>
                      <Badge variant="outline">{DEPTH_LABELS[record.depth] || record.depth}</Badge>
                      {record.status === 'completed' ? (
                        <Badge variant="default" className="bg-green-500">已完成</Badge>
                      ) : record.status === 'failed' ? (
                        <Badge variant="destructive">失败</Badge>
                      ) : (
                        <Badge variant="secondary">进行中</Badge>
                      )}
                    </div>
                    <p className="mt-1 truncate text-sm text-muted-foreground">
                      {record.summary?.substring(0, 120) || record.error_message || '暂无摘要'}
                    </p>
                    <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(record.created_at).toLocaleString('zh-CN')}
                      </span>
                      <span>{record.evidence_count} 条证据</span>
                      <span>{record.completed_stages}/{record.total_stages} 阶段</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={record.status !== 'completed'}
                      onClick={() => viewMutation.mutate(record.id)}
                      aria-label="查看分析记录"
                    >
                      <Eye className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (confirm('确定删除此分析记录？')) {
                          deleteMutation.mutate(record.id);
                        }
                      }}
                      aria-label="删除分析记录"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
