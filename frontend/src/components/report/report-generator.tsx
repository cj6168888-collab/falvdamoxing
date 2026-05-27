import { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Sparkles, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { useGenerateReport, useReportList } from '@/hooks/use-report';
import { subscribeToReportProgress } from '@/api/report.api';

// 报告类型配置 - 与后端一致
const REPORT_TYPES = [
  { value: 'analysis', label: '案件分析', description: '全面分析案件事实和法律问题', sections: 7 },
  { value: 'strategy', label: '策略建议', description: '诉讼策略和行动建议', sections: 5 },
  { value: 'full_analysis', label: '完整对抗性分析', description: '双方视角的完整对抗性分析', sections: 8 },
  { value: 'evidence', label: '证据报告', description: '证据梳理和分析报告', sections: 5 },
  { value: 'milestone', label: '里程碑报告', description: '案件进度和待办事项', sections: 1 },
  { value: 'summary', label: '案件总结', description: '案件概要总结', sections: 1 },
];

interface SectionProgress {
  index: number;
  title: string;
  status: 'pending' | 'generating' | 'completed' | 'error';
  content?: string;
}

interface Props {
  caseId: string;
  onReportGenerated?: (reportId: string) => void;
}

/**
 * 报告生成器组件
 * 支持选择报告类型、实时显示生成进度
 */
export function ReportGenerator({ caseId, onReportGenerated }: Props) {
  const [selectedType, setSelectedType] = useState<string>('analysis');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generationMessage, setGenerationMessage] = useState('');
  const [sections, setSections] = useState<SectionProgress[]>([]);
  const [error, setError] = useState<string | null>(null);

  const generateReport = useGenerateReport();
  const { refetch } = useReportList(caseId);

  // 处理报告生成
  const handleGenerate = useCallback(async () => {
    if (!caseId) return;

    const typeConfig = REPORT_TYPES.find(t => t.value === selectedType);
    if (!typeConfig) return;

    setIsGenerating(true);
    setGenerationProgress(0);
    setGenerationMessage('正在初始化...');
    setError(null);

    // 初始化章节进度
    const initialSections: SectionProgress[] = REPORT_TYPES
      .find(t => t.value === selectedType)
      ?.value === selectedType
      ? Array.from({ length: typeConfig.sections }, (_, i) => ({
          index: i,
          title: `章节 ${i + 1}`,
          status: 'pending' as const,
        }))
      : [];
    setSections(initialSections);

    try {
      // 调用生成 API
      await generateReport.mutateAsync({ caseId, type: selectedType });

      // 订阅 SSE 流式进度
      const unsubscribe = subscribeToReportProgress(
        caseId,
        selectedType,
        {
          onProgress: (data) => {
            setGenerationProgress(data.progress);
            setGenerationMessage(data.message);
          },
          onSectionStart: (data) => {
            setSections(prev => prev.map((s, i) =>
              i === data.section_index
                ? { ...s, status: 'generating', title: data.title }
                : s
            ));
          },
          onSectionContent: (data) => {
            setSections(prev => prev.map((s, i) =>
              i === data.section_index
                ? { ...s, status: 'completed', content: data.content }
                : s
            ));
          },
          onSectionError: (data) => {
            setSections(prev => prev.map((s, i) =>
              i === data.section_index
                ? { ...s, status: 'error' }
                : s
            ));
          },
          onComplete: (data) => {
            setGenerationProgress(100);
            setGenerationMessage('报告生成完成');
            setIsGenerating(false);
            toast.success('报告生成完成');
            refetch();
            if (data?.report_id && onReportGenerated) {
              onReportGenerated(data.report_id);
            }
            unsubscribe();
          },
          onError: (errMsg) => {
            setError(errMsg);
            setIsGenerating(false);
            toast.error(`报告生成失败: ${errMsg}`);
            unsubscribe();
          },
        }
      );

      toast.success(`${typeConfig.label} 开始生成`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '未知错误';
      setError(message || '生成失败');
      setIsGenerating(false);
      toast.error(`生成失败: ${message}`);
    }
  }, [caseId, selectedType, generateReport, refetch, onReportGenerated]);

  // 取消生成
  const handleCancel = useCallback(() => {
    setIsGenerating(false);
    setGenerationProgress(0);
    setGenerationMessage('');
    setSections([]);
    setError(null);
    toast.info('已取消报告生成');
  }, []);

  const selectedTypeConfig = REPORT_TYPES.find(t => t.value === selectedType);

  return (
    <div className="space-y-4">
      {/* 生成进度显示 */}
      {isGenerating && (
        <Card className="border-primary/50 bg-primary/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                <CardTitle className="text-base">正在生成报告</CardTitle>
              </div>
              <Badge variant="secondary">{selectedTypeConfig?.label}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* 总体进度 */}
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">{generationMessage}</span>
                <span className="font-medium">{generationProgress}%</span>
              </div>
              <Progress value={generationProgress} className="h-2" />
            </div>

            {/* 章节进度 */}
            {sections.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground font-medium">章节进度</p>
                <div className="grid gap-2">
                  {sections.map((section) => (
                    <div
                      key={section.index}
                      className="flex items-center gap-2 text-sm"
                    >
                      {section.status === 'completed' ? (
                        <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                      ) : section.status === 'error' ? (
                        <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
                      ) : section.status === 'generating' ? (
                        <Loader2 className="h-4 w-4 animate-spin text-primary flex-shrink-0" />
                      ) : (
                        <Clock className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      )}
                      <span className={section.status === 'pending' ? 'text-muted-foreground' : ''}>
                        {section.title || `章节 ${section.index + 1}`}
                      </span>
                      <Badge
                        variant="outline"
                        className="ml-auto text-xs"
                      >
                        {section.status === 'completed' ? '已完成' :
                         section.status === 'generating' ? '生成中' :
                         section.status === 'error' ? '失败' : '等待'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 取消按钮 */}
            <div className="flex justify-end pt-2">
              <Button variant="outline" size="sm" onClick={handleCancel}>
                取消生成
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 错误显示 */}
      {error && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="flex items-center gap-2 py-3 text-destructive">
            <XCircle className="h-5 w-5" />
            <span>{error}</span>
          </CardContent>
        </Card>
      )}

      {/* 报告类型选择 */}
      {!isGenerating && (
        <Card>
          <CardHeader>
            <CardTitle>选择报告类型</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3">
              {REPORT_TYPES.map((type) => (
                <div
                  key={type.value}
                  className={`p-4 border rounded-lg cursor-pointer transition-all ${
                    selectedType === type.value
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                  onClick={() => setSelectedType(type.value)}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{type.label}</span>
                    {selectedType === type.value && (
                      <CheckCircle className="h-5 w-5 text-primary" />
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{type.description}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    预计 {type.sections} 个章节
                  </p>
                </div>
              ))}
            </div>

            <Button
              onClick={handleGenerate}
              disabled={generateReport.isPending}
              className="w-full"
              size="lg"
            >
              {generateReport.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  正在提交...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  生成 {selectedTypeConfig?.label}
                </>
              )}
            </Button>

            <p className="text-xs text-muted-foreground text-center">
              报告将在后台生成，生成完成后可在报告列表中查看
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default ReportGenerator;
