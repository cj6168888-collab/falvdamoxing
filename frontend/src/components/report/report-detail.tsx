import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useReportDetail, useRegenerateReport } from '@/hooks/use-report';
import { useReportPrint } from '@/hooks/use-report-print';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { ArrowLeft, RefreshCw, FileText, Clock, CheckCircle, Download, Loader2, Sparkles, Printer } from 'lucide-react';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { exportReport, quickAnalysis } from '@/api/report.api';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Progress } from '@/components/ui/progress';

interface Props {
  reportId: string;
  onBack: () => void;
  onRegenerate?: () => void;
}

export function ReportDetail({ reportId, onBack, onRegenerate }: Props) {
  const { data, isLoading, error, refetch } = useReportDetail(reportId);
  const regenerateReport = useRegenerateReport();
  const { printReport } = useReportPrint();
  const [isExporting, setIsExporting] = useState(false);
  const [isQuickAnalyzing, setIsQuickAnalyzing] = useState(false);

  const handlePrint = () => {
    if (data) {
      printReport(data);
    }
  };

  const handleRegenerate = async () => {
    try {
      await regenerateReport.mutateAsync(reportId);
      toast.success('报告重新生成完成');
      refetch();
      onRegenerate?.();
    } catch {
      toast.error('重新生成失败');
    }
  };

  const handleQuickAnalysis = async () => {
    if (!data?.case_id) return;
    setIsQuickAnalyzing(true);
    try {
      const result = await quickAnalysis(data.case_id.toString());
      toast.success('快速分析完成');
      // 显示分析结果
      console.log('Quick analysis result:', result);
      // 可以在这里添加一个对话框显示分析结果
      alert(result.analysis || '分析完成');
    } catch {
      toast.error('快速分析失败');
    } finally {
      setIsQuickAnalyzing(false);
    }
  };

  const handleExport = async (format: 'markdown' | 'text' | 'pdf' | 'word') => {
    setIsExporting(true);
    try {
      await exportReport(reportId, format);
      toast.success(`${format.toUpperCase()} 导出成功`);
    } catch {
      toast.error('导出失败');
    } finally {
      setIsExporting(false);
    }
  };

  if (isLoading) return <PageSkeleton />;

  if (error || !data) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <p className="text-destructive mb-4">加载报告失败</p>
          <Button variant="outline" onClick={onBack}>
            返回列表
          </Button>
        </CardContent>
      </Card>
    );
  }

  const sections = data.sections || [];
  const completedSections = sections.filter(s => s.status === 'completed').length;
  const progressPercent = data.total_sections > 0
    ? Math.round((completedSections / data.total_sections) * 100)
    : 0;
  const isGenerating = data.status === 'GENERATING';

  return (
    <div className="space-y-4">
      {/* 头部工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回
          </Button>
          <h2 className="text-lg font-bold">报告详情</h2>
        </div>
        <div className="flex items-center gap-2">
          {/* 快速分析按钮 */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleQuickAnalysis}
            disabled={isQuickAnalyzing || isGenerating}
          >
            {isQuickAnalyzing ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            快速分析
          </Button>

          {/* 导出按钮 */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" disabled={isExporting || isGenerating}>
                {isExporting ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Download className="mr-2 h-4 w-4" />
                )}
                导出
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => handleExport('markdown')}>
                Markdown 格式 (.md)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport('text')}>
                纯文本格式 (.txt)
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => handleExport('pdf')}>
                PDF 文档 (.pdf)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport('word')}>
                Word 文档 (.docx)
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* 打印按钮 */}
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrint}
            disabled={isGenerating || sections.length === 0}
            className="no-print"
          >
            <Printer className="mr-2 h-4 w-4" />
            打印
          </Button>

          {/* 重新生成按钮 */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleRegenerate}
            disabled={regenerateReport.isPending}
          >
            {regenerateReport.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" />
            )}
            重新生成
          </Button>
        </div>
      </div>

      {/* 生成进度条 */}
      {isGenerating && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="py-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                <span className="text-sm font-medium">报告生成中...</span>
              </div>
              <span className="text-sm text-muted-foreground">{progressPercent}%</span>
            </div>
            <Progress value={progressPercent} className="h-2" />
          </CardContent>
        </Card>
      )}

      {/* 报告基本信息 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              <CardTitle>{data.title}</CardTitle>
            </div>
            <Badge
              variant={
                data.status === 'COMPLETED' ? 'default' :
                data.status === 'GENERATING' ? 'secondary' : 'outline'
              }
            >
              {data.status === 'COMPLETED' ? '已完成' :
               data.status === 'GENERATING' ? '生成中' : data.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-sm text-muted-foreground">报告类型</p>
              <p className="font-medium">{data.report_type_name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">版本</p>
              <p className="font-medium">V{data.version}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">章节进度</p>
              <p className="font-medium">{completedSections}/{data.total_sections}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">生成时间</p>
              <p className="font-medium">
                {data.created_at ? new Date(data.created_at).toLocaleDateString('zh-CN') : '-'}
              </p>
            </div>
          </div>

          {data.description && (
            <div className="mt-4">
              <p className="text-sm text-muted-foreground">描述</p>
              <p className="text-sm">{data.description}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 报告内容 */}
      <Card>
        <CardHeader>
          <CardTitle>报告内容</CardTitle>
        </CardHeader>
        <CardContent>
          {sections.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              {isGenerating ? (
                <>
                  <Loader2 className="h-8 w-8 animate-spin mb-2" />
                  <p>报告正在生成中，请稍候...</p>
                </>
              ) : (
                <p>暂无章节内容</p>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {sections.map((section, index) => {
                const isCompleted = section.status === 'completed';
                return (
                  <div key={section.id} className="border-b pb-6 last:border-b-0 last:pb-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`flex items-center justify-center w-6 h-6 rounded-full text-sm font-medium ${
                        isCompleted
                          ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                          : 'bg-muted text-muted-foreground'
                      }`}>
                        {isCompleted ? (
                          <CheckCircle className="h-4 w-4" />
                        ) : (
                          index + 1
                        )}
                      </span>
                      <h3 className="font-medium">{section.title}</h3>
                    </div>

                    {section.content ? (
                      <div className="pl-8">
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {section.content}
                          </ReactMarkdown>
                        </div>
                      </div>
                    ) : (
                      <div className="pl-8">
                        <div className="flex items-center gap-2 text-muted-foreground text-sm">
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>内容生成中...</span>
                        </div>
                      </div>
                    )}

                    <div className="pl-8 mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                      {section.completed_at && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {new Date(section.completed_at).toLocaleString('zh-CN')}
                        </span>
                      )}
                      {section.key_points?.length > 0 && (
                        <span>{section.key_points.length} 个要点</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
