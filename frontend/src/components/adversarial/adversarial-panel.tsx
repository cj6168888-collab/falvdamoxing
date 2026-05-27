import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Sparkles, ExternalLink, Plus, ChevronDown, ChevronUp, Scale, FileText, Download } from 'lucide-react';
import { toast } from 'sonner';
import { useTaskStore, pollTaskStatus } from '@/stores/task.store';
import axiosInstance from '@/api/client';
import { DebateStreamPanel } from './debate-stream';
import { generateFullAnalysis, useAdversarialAnalysis, type FullAnalysisResponse } from '@/api/adversarial.api';
import { downloadExportFile, exportAdversarialAnalysis } from '@/api/export.api';

interface Props { caseId: string; }

type AnalysisValue = string | number | boolean | null | undefined | AnalysisRecord | AnalysisValue[];
type AdversarialExportFormat = 'markdown' | 'docx' | 'pdf';

interface AnalysisRecord {
  [key: string]: AnalysisValue;
}

const adversarialExportFormats: Array<{ format: AdversarialExportFormat; label: string }> = [
  { format: 'markdown', label: 'Markdown' },
  { format: 'docx', label: 'Word' },
  { format: 'pdf', label: 'PDF' },
];

interface AdversarialAnalysisListItem extends AnalysisRecord {
  id: number;
  title?: string;
  analysis_phase?: string;
  opponent_name?: string;
  created_at?: string;
  is_current?: boolean;
}

function isAnalysisRecord(value: unknown): value is AnalysisRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (!isAnalysisRecord(error)) return fallback;

  const response = error.response;
  if (isAnalysisRecord(response)) {
    const data = response.data;
    if (isAnalysisRecord(data) && typeof data.detail === 'string') {
      return data.detail;
    }
  }

  return typeof error.message === 'string' ? error.message : fallback;
}

function getField(source: AnalysisRecord, keys: string[]): AnalysisValue {
  for (const key of keys) {
    const value = source[key];
    if (value !== undefined && value !== null && value !== '') return value;
  }
  return undefined;
}

function formatContent(content: AnalysisValue): string {
  if (content === undefined || content === null) return '';
  return typeof content === 'string' ? content : JSON.stringify(content, null, 2);
}

function normalizeAnalysisList(value: unknown): AdversarialAnalysisListItem[] {
  if (Array.isArray(value)) return value.filter((item): item is AdversarialAnalysisListItem => isAnalysisRecord(item) && typeof item.id === 'number');
  if (isAnalysisRecord(value) && Array.isArray(value.items)) {
    return value.items.filter((item): item is AdversarialAnalysisListItem => isAnalysisRecord(item) && typeof item.id === 'number');
  }
  return [];
}

function toNumericId(value: AnalysisValue): number | null {
  if (typeof value === 'number') return value;
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value);
    return Number.isNaN(parsed) ? null : parsed;
  }
  return null;
}

export function AdversarialPanel({ caseId }: Props) {
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisRecord | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const [fullReport, setFullReport] = useState<string | null>(null);
  const [currentAnalysisId, setCurrentAnalysisId] = useState<number | null>(null);
  const [exportingAnalysisId, setExportingAnalysisId] = useState<number | null>(null);
  const [isGeneratingFull, setIsGeneratingFull] = useState(false);
  const [activeTab, setActiveTab] = useState('analysis');

  const addTask = useTaskStore((s) => s.addTask);
  const updateTask = useTaskStore((s) => s.updateTask);
  const tasks = useTaskStore((s) => s.tasks);
  const { data: analysisListData, refetch: refetchAnalyses } = useAdversarialAnalysis(caseId);
  const existingAnalyses = normalizeAnalysisList(analysisListData);
  const currentExportId = currentAnalysisId || existingAnalyses[0]?.id || null;

  useEffect(() => {
    if (!activeTaskId) return;
    const task = tasks.find((t) => t.id === activeTaskId);
    if (task?.status === 'completed' && task.result) {
      const result = task.result;
      const analysis = isAnalysisRecord(result) && 'analysis' in result
        ? result.analysis
        : undefined;
      setAnalysisResult(isAnalysisRecord(analysis) ? analysis : isAnalysisRecord(result) ? result : null);
      const resultRecord = isAnalysisRecord(result) ? result : null;
      const analysisRecord = isAnalysisRecord(analysis) ? analysis : null;
      const completedAnalysisId = toNumericId(getField(resultRecord || {}, ['analysis_id', 'id']))
        || toNumericId(getField(analysisRecord || {}, ['analysis_id', 'id']));
      if (completedAnalysisId) {
        setCurrentAnalysisId(completedAnalysisId);
        void refetchAnalyses();
      }
      setActiveTaskId(null);
    }
  }, [tasks, activeTaskId, refetchAnalyses]);

  const activeAdversarialTask = tasks.find(
    (t) => t.type === 'adversarial' && t.caseId === caseId && (t.status === 'pending' || t.status === 'running')
  );

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  // 一键生成完整分析
  const handleGenerateFullAnalysis = async () => {
    if (!caseId || isGeneratingFull) return;

    setIsGeneratingFull(true);
    try {
      const result: FullAnalysisResponse = await generateFullAnalysis(caseId);
      setFullReport(result.full_report);
      setCurrentAnalysisId(result.analysis_id);
      setActiveTab('analysis'); // 显示在分析结果标签页
      await refetchAnalyses();
      toast.success('完整分析报告已生成');
    } catch (error: unknown) {
      toast.error(getErrorMessage(error, '生成失败'));
    } finally {
      setIsGeneratingFull(false);
    }
  };

  const handleAnalyze = async () => {
    if (!caseId) return;

    try {
      const createRes = await axiosInstance.post('/api/ai-tasks/create', {
        type: 'adversarial',
        case_id: parseInt(caseId),
        title: '对抗性分析',
        params: { phase: 'litigation' },
      });

      const backendTaskId = createRes.data.task_id;

      addTask({
        id: backendTaskId,
        type: 'adversarial',
        caseId,
        title: '对抗性分析',
      });

      await axiosInstance.post(`/api/ai-tasks/${backendTaskId}/execute`);

      setActiveTaskId(backendTaskId);
      pollTaskStatus(
        backendTaskId, 
        (data) => {
          updateTask(backendTaskId, {
            status: data.status,
            progress: data.progress,
            message: data.message,
            result: data.result,
            error: data.error,
            completedAt: data.status === 'completed' || data.status === 'failed' ? Date.now() : undefined,
          });

          if (data.status === 'completed') {
            toast.success('对抗性分析已完成');
          } else if (data.status === 'failed') {
            toast.error(`分析失败: ${data.error}`);
          }
        },
        (elapsedSeconds) => {
          // 任务卡住时的回调
          toast.warning(
            `AI分析时间较长（已运行${Math.floor(elapsedSeconds / 60)}分钟），请耐心等待...`,
            { duration: 10000 }
          );
        }
      );

      toast.info('对抗性分析正在后台运行，您可切换到其他页面');
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, '分析任务创建失败'));
    }
  };

  const handleDebateComplete = (report: string) => {
    setFullReport(report);
    toast.success('模拟庭审辩论已完成');
  };

  const handleExportAnalysis = async (analysisId: number, format: AdversarialExportFormat) => {
    setExportingAnalysisId(analysisId);
    try {
      const result = await exportAdversarialAnalysis(analysisId, format);
      await downloadExportFile(result);
      const actualFormat = result.format_used && result.format_used !== format ? `（实际 ${result.format_used}）` : '';
      toast.success(`对抗分析 ${adversarialExportFormats.find((item) => item.format === format)?.label || format} 已导出${actualFormat}`);
    } catch (error: unknown) {
      toast.error(getErrorMessage(error, '对抗分析导出失败'));
    } finally {
      setExportingAnalysisId(null);
    }
  };

  const renderExportMenu = (analysisId: number) => {
    const isExporting = exportingAnalysisId === analysisId;

    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button size="sm" variant="outline" disabled={isExporting}>
            <Download className="mr-2 h-4 w-4" />
            {isExporting ? '导出中...' : '导出'}
            <ChevronDown className="ml-1 h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {adversarialExportFormats.map((item) => (
            <DropdownMenuItem
              key={item.format}
              onClick={() => void handleExportAnalysis(analysisId, item.format)}
            >
              <Download className="mr-2 h-4 w-4" />
              导出 {item.label}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    );
  };

  const renderSection = (title: string, content: AnalysisValue, color: string) => {
    if (!content) return null;
    const isExpanded = expandedSections[title] || false;
    return (
      <div className="rounded-lg border overflow-hidden">
        <button
          className="w-full flex items-center justify-between p-4 hover:bg-muted/50"
          onClick={() => toggleSection(title)}
        >
          <h4 className={`font-medium ${color}`}>{title}</h4>
          {isExpanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </button>
        {isExpanded && (
          <div className="px-4 pb-4 text-sm text-muted-foreground whitespace-pre-wrap">
            {formatContent(content)}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* 顶部操作区 */}
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">对抗性分析</h2>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="default"
            onClick={handleGenerateFullAnalysis}
            disabled={isGeneratingFull}
          >
            {isGeneratingFull ? (
              <>
                <Sparkles className="mr-2 h-4 w-4 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                一键完整分析
              </>
            )}
          </Button>
          {!activeAdversarialTask && (
            <Button size="sm" variant="outline" onClick={handleAnalyze}>
              <Plus className="mr-2 h-4 w-4" />
              后台分析
            </Button>
          )}
          {currentExportId && renderExportMenu(currentExportId)}
        </div>
      </div>

      {/* 任务进度条 */}
      {activeAdversarialTask && (
        <Card className="border-primary/20 bg-primary/5">
          <CardContent className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <Sparkles className="h-5 w-5 animate-pulse text-primary" />
              <div>
                <p className="font-medium text-sm">{activeAdversarialTask.title}</p>
                <p className="text-xs text-muted-foreground">{activeAdversarialTask.message}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-24 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-500"
                  style={{ width: `${Math.round(activeAdversarialTask.progress * 100)}%` }}
                />
              </div>
              <span className="text-xs text-muted-foreground">{Math.round(activeAdversarialTask.progress * 100)}%</span>
              <ExternalLink className="h-4 w-4 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      )}

      {existingAnalyses.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">历史对抗分析</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {existingAnalyses.slice(0, 5).map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between gap-3 rounded-md border px-3 py-2"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-medium">{item.title || `分析 #${item.id}`}</p>
                    {item.is_current && <Badge variant="secondary">当前</Badge>}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {[item.analysis_phase, item.opponent_name].filter(Boolean).join(' · ') || '基础分析'}
                  </p>
                </div>
                {renderExportMenu(item.id)}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 标签页切换：分析结果 / 模拟庭审辩论 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="analysis" className="gap-1">
            <FileText className="h-4 w-4" />
            分析结果
          </TabsTrigger>
          <TabsTrigger value="debate" className="gap-1">
            <Scale className="h-4 w-4" />
            模拟庭审辩论
          </TabsTrigger>
          <TabsTrigger value="swot" className="gap-1">
            <Sparkles className="h-4 w-4" />
            SWOT分析
          </TabsTrigger>
        </TabsList>

        {/* 分析结果标签 */}
        <TabsContent value="analysis" className="mt-4">
          {analysisResult ? (
            <div className="space-y-3">
              {renderSection('我方优势', getField(analysisResult, ['我方优势', 'our_strengths']), 'text-green-600')}
              {renderSection('我方劣势', getField(analysisResult, ['我方劣势', 'our_weaknesses']), 'text-red-600')}
              {renderSection('对方劣势', getField(analysisResult, ['对方劣势', 'opponent_weaknesses']), 'text-amber-600')}
              {renderSection('对方优势', getField(analysisResult, ['对方优势', 'opponent_strengths']), 'text-blue-600')}
              {renderSection('核心策略', getField(analysisResult, ['核心策略', 'core_strategy']), 'text-primary')}
              {renderSection('态势评估', getField(analysisResult, ['态势评估', 'situation_assessment']), 'text-muted-foreground')}
              {renderSection('关键风险', getField(analysisResult, ['关键风险', 'key_risks']), 'text-red-500')}
            </div>
          ) : fullReport ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">完整分析报告</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                  {fullReport}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>四象限分析</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg border p-4">
                    <h4 className="font-medium text-green-600">我方优势</h4>
                    <p className="text-sm text-muted-foreground mt-2">暂无数据，请先生成分析</p>
                  </div>
                  <div className="rounded-lg border p-4">
                    <h4 className="font-medium text-red-600">我方劣势</h4>
                    <p className="text-sm text-muted-foreground mt-2">暂无数据</p>
                  </div>
                  <div className="rounded-lg border p-4">
                    <h4 className="font-medium text-amber-600">对方劣势</h4>
                    <p className="text-sm text-muted-foreground mt-2">暂无数据</p>
                  </div>
                  <div className="rounded-lg border p-4">
                    <h4 className="font-medium text-blue-600">对方优势</h4>
                    <p className="text-sm text-muted-foreground mt-2">暂无数据</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 模拟庭审辩论标签 */}
        <TabsContent value="debate" className="mt-4">
          <DebateStreamPanel
            caseId={caseId}
            onDebateComplete={handleDebateComplete}
          />
        </TabsContent>

        {/* SWOT分析标签 */}
        <TabsContent value="swot" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>SWOT 四象限分析</CardTitle>
            </CardHeader>
            <CardContent>
              {analysisResult ? (
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg border p-4 bg-green-50/50">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="default" className="bg-green-500">S</Badge>
                      <span className="font-medium text-green-700">优势 Strengths</span>
                    </div>
                    <p className="text-sm whitespace-pre-wrap">
                      {formatContent(getField(analysisResult, ['our_strengths', 'our_advantages', '_strengths'])) || '暂无数据'}
                    </p>
                  </div>
                  <div className="rounded-lg border p-4 bg-red-50/50">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="default" className="bg-red-500">W</Badge>
                      <span className="font-medium text-red-700">劣势 Weaknesses</span>
                    </div>
                    <p className="text-sm whitespace-pre-wrap">
                      {formatContent(getField(analysisResult, ['weaknesses', 'our_weaknesses'])) || '暂无数据'}
                    </p>
                  </div>
                  <div className="rounded-lg border p-4 bg-blue-50/50">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="default" className="bg-blue-500">O</Badge>
                      <span className="font-medium text-blue-700">机会 Opportunities</span>
                    </div>
                    <p className="text-sm whitespace-pre-wrap">
                      {formatContent(getField(analysisResult, ['opportunities', 'opponent_weaknesses'])) || '暂无数据'}
                    </p>
                  </div>
                  <div className="rounded-lg border p-4 bg-amber-50/50">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="default" className="bg-amber-500">T</Badge>
                      <span className="font-medium text-amber-700">威胁 Threats</span>
                    </div>
                    <p className="text-sm whitespace-pre-wrap">
                      {formatContent(getField(analysisResult, ['threats', 'opponent_strengths', 'key_risks'])) || '暂无数据'}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <p>暂无分析数据，请先生成完整分析或进行模拟庭审辩论</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
