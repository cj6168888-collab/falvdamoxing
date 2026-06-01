import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axiosInstance from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ClaimBasisMatrix } from '@/components/senior-analysis/claim-basis-matrix';
import { FactEvidenceInferenceColumns } from '@/components/senior-analysis/fact-evidence-inference-columns';
import { Sparkles, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import { useTaskStore, pollTaskStatus } from '@/stores/task.store';

const DEPTH_LABELS: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
};

interface SeniorAnalysisResult {
  status?: string;
  message?: string;
  summary?: unknown;
  case_understanding?: Record<string, unknown>;
  evidence_inventory?: Record<string, unknown>;
  evidence_review?: unknown;
  requirements_check?: {
    requirements?: Array<Record<string, unknown>>;
  };
  issues?: Record<string, unknown>;
  risk_assessment?: unknown;
  recommendations?: unknown;
  strategy_suggestions?: unknown;
  analysis_level?: string;
}

export default function SeniorAnalysisPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const [depth, setDepth] = useState<'quick' | 'standard' | 'deep'>('standard');
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<SeniorAnalysisResult | null>(null);

  const addTask = useTaskStore((s) => s.addTask);
  const updateTask = useTaskStore((s) => s.updateTask);
  const tasks = useTaskStore((s) => s.tasks);

  useEffect(() => {
    if (!activeTaskId) return;
    const task = tasks.find((t) => t.id === activeTaskId);
    if (task?.status === 'completed' && task.result) {
      setAnalysisResult(task.result as SeniorAnalysisResult);
      setActiveTaskId(null);
    }
  }, [tasks, activeTaskId]);

  const activeAnalysisTask = tasks.find(
    (t) => t.type === 'senior_analysis' && t.caseId === caseId && (t.status === 'pending' || t.status === 'running')
  );

  const handleAnalyze = async () => {
    if (!caseId) return;

    try {
      const createRes = await axiosInstance.post('/api/ai-tasks/create', {
        type: 'senior_analysis',
        case_id: parseInt(caseId),
        title: `资深律师分析（${DEPTH_LABELS[depth]}）`,
        params: { depth },
      });

      const backendTaskId = createRes.data.task_id;

      addTask({
        id: backendTaskId,
        type: 'senior_analysis',
        caseId,
        title: `资深律师分析（${DEPTH_LABELS[depth]}）`,
      });

      await axiosInstance.post(`/api/ai-tasks/${backendTaskId}/execute`);

      setActiveTaskId(backendTaskId);
      pollTaskStatus(backendTaskId, (data) => {
        updateTask(backendTaskId, {
          status: data.status,
          progress: data.progress,
          message: data.message,
          result: data.result,
          error: data.error,
          completedAt: data.status === 'completed' || data.status === 'failed' ? Date.now() : undefined,
        });

        if (data.status === 'completed') {
          toast.success('资深律师分析已完成');
        } else if (data.status === 'failed') {
          toast.error(`分析失败: ${data.error}`);
        }
      });

      toast.info('资深律师分析正在后台运行，您可切换到其他页面');
    } catch (err) {
      const errorMsg = getRequestErrorMessage(err, '分析任务创建失败');
      toast.error(errorMsg);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">资深律师分析</h2>
          <p className="text-sm text-muted-foreground">模拟资深律师视角，全面分析案件</p>
        </div>
      </div>

      <div className="flex gap-2">
        {(['quick', 'standard', 'deep'] as const).map((d) => (
          <Button
            key={d}
            variant={depth === d ? 'default' : 'outline'}
            onClick={() => setDepth(d)}
            disabled={!!activeAnalysisTask}
          >
            {DEPTH_LABELS[d]}
          </Button>
        ))}
      </div>

      {activeAnalysisTask && (
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <Sparkles className="h-5 w-5 animate-pulse text-primary" />
              <div>
                <p className="font-medium text-sm">{activeAnalysisTask.title}</p>
                <p className="text-xs text-muted-foreground">{activeAnalysisTask.message}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-24 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-500"
                  style={{ width: `${Math.round(activeAnalysisTask.progress * 100)}%` }}
                />
              </div>
              <span className="text-xs text-muted-foreground">{Math.round(activeAnalysisTask.progress * 100)}%</span>
              <ExternalLink className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      )}

      {!activeAnalysisTask && (
        <Button onClick={handleAnalyze}>
          <Sparkles className="mr-2 h-4 w-4" />
          开始分析
        </Button>
      )}

      {analysisResult && (
        <Card>
          <CardHeader>
            <CardTitle>分析结果</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <AnalysisSection title="分析摘要" value={analysisResult.summary} />
            <AnalysisSection title="案件理解" value={analysisResult.case_understanding} />
            <AnalysisSection title="证据盘点" value={analysisResult.evidence_inventory ?? analysisResult.evidence_review} />
            <FactEvidenceInferenceColumns
              caseUnderstanding={analysisResult.case_understanding}
              evidenceInventory={analysisResult.evidence_inventory}
              requirementsCheck={analysisResult.requirements_check}
              issues={analysisResult.issues}
              recommendations={analysisResult.recommendations ?? analysisResult.strategy_suggestions}
            />
            <ClaimBasisMatrix requirementsCheck={analysisResult.requirements_check} />
            <AnalysisSection title="要件核对" value={analysisResult.requirements_check} />
            <AnalysisSection title="问题发现" value={analysisResult.issues} />
            <AnalysisSection title="风险评估" value={analysisResult.risk_assessment} />
            <AnalysisSection title="策略建议" value={analysisResult.recommendations ?? analysisResult.strategy_suggestions} />
          </CardContent>
        </Card>
      )}

      {!activeAnalysisTask && !analysisResult && (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            选择分析深度后点击"开始分析"
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function AnalysisSection({ title, value }: { title: string; value: unknown }) {
  if (value === undefined || value === null || value === '') {
    return null;
  }

  return (
    <div>
      <h4 className="text-sm font-medium">{title}</h4>
      <pre className="mt-1 max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-muted/40 p-3 text-sm leading-6 text-muted-foreground">
        {formatAnalysisValue(value)}
      </pre>
    </div>
  );
}

const FIELD_LABELS: Record<string, string> = {
  action: '行动',
  analysis_level: '分析深度',
  avg_credibility: '平均可信度',
  by_credibility: '可信度分布',
  by_source: '来源分布',
  by_type: '类型分布',
  case_number: '案号',
  case_type: '案件类型',
  category_name: '分类',
  cause: '案由',
  content_excerpt: '内容摘录',
  core_disputes: '核心争议',
  coverage_level: '覆盖等级',
  defendant: '被告',
  description: '描述',
  evidence_mapping: '证据映射',
  evidence_required: '证据要求',
  evidence_summary: '证据摘要',
  fact: '事实',
  gaps: '缺口',
  issues: '问题',
  key_facts: '关键事实',
  mitigation: '应对',
  mitigation_strategies: '应对策略',
  missing_elements: '缺失要件',
  obtain_method: '获取方式',
  overall_assessment: '整体评估',
  overall_coverage: '整体覆盖率',
  overall_level: '整体风险',
  plaintiff: '原告',
  priority: '优先级',
  recommendation: '建议',
  recommendations: '建议',
  requirement: '要件',
  requirements: '要件',
  risk_items: '风险项',
  status: '状态',
  suggestion: '建议',
  summary: '摘要',
  title: '标题',
  total: '总数',
  total_gaps: '缺口总数',
  type: '类型',
};

function formatAnalysisValue(value: unknown, indent = ''): string {
  if (value === null || value === undefined) {
    return `${indent}暂无`;
  }

  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return `${indent}${String(value)}`;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return `${indent}暂无`;
    }
    return value
      .map((item, index) => `${indent}${index + 1}. ${formatAnalysisValue(item, '').trim().replace(/\n/g, `\n${indent}   `)}`)
      .join('\n');
  }

  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>).filter(([, item]) => !isEmptyValue(item));
    if (entries.length === 0) {
      return `${indent}暂无`;
    }

    return entries
      .map(([key, item]) => {
        const label = FIELD_LABELS[key] || key;
        if (isScalarValue(item)) {
          return `${indent}${label}: ${String(item)}`;
        }
        return `${indent}${label}:\n${formatAnalysisValue(item, `${indent}  `)}`;
      })
      .join('\n');
  }

  return `${indent}${String(value)}`;
}

function isScalarValue(value: unknown) {
  return value === null || ['string', 'number', 'boolean'].includes(typeof value);
}

function isEmptyValue(value: unknown) {
  return (
    value === undefined ||
    value === null ||
    value === '' ||
    (Array.isArray(value) && value.length === 0) ||
    (typeof value === 'object' && value !== null && !Array.isArray(value) && Object.keys(value).length === 0)
  );
}

function getRequestErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    return response?.data?.detail || fallback;
  }
  return fallback;
}
