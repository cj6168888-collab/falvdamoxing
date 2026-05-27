import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useReportList, useGenerateReport, useDeleteReport } from '@/hooks/use-report';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { Plus, FileText, Trash2, RefreshCw, Eye, BarChart3, Target, Shield, Calendar, User, GitCompare } from 'lucide-react';
import { ReportDetail } from './report-detail';
import { ReportCompare } from './report-compare';
import { toast } from 'sonner';
import type { ReportOutline } from '@/types/report.types';
import type { LucideIcon } from 'lucide-react';

// 报告类型配置 - 与后端 report.py 的 TYPE_INFO 对应
const REPORT_TYPES: Record<string, {
  value: string;
  label: string;
  icon: LucideIcon;
  color: string;
  description: string;
}> = {
  'ANALYSIS': { value: 'analysis', label: '案件分析', icon: BarChart3, color: 'bg-blue-500', description: '全面分析案件事实和法律问题' },
  'STRATEGY': { value: 'strategy', label: '策略建议', icon: Target, color: 'bg-green-500', description: '制定诉讼策略和行动建议' },
  'FULL_ANALYSIS': { value: 'full_analysis', label: '完整对抗性分析', icon: Shield, color: 'bg-purple-500', description: '双方视角的完整对抗性分析' },
  'EVIDENCE_REPORT': { value: 'evidence', label: '证据报告', icon: FileText, color: 'bg-orange-500', description: '证据梳理和分析报告' },
  'MILESTONE_REPORT': { value: 'milestone', label: '里程碑报告', icon: Calendar, color: 'bg-teal-500', description: '案件进度和待办事项' },
  'SUMMARY_REPORT': { value: 'summary', label: '案件总结', icon: User, color: 'bg-gray-500', description: '案件概要总结' },
};

// 状态配置 - 与后端 ReportStatus 对应
const STATUS_CONFIG: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' | null }> = {
  PLANNING: { label: '规划中', variant: 'secondary' },
  GENERATING: { label: '生成中', variant: 'secondary' },
  VALIDATING: { label: '校验中', variant: 'secondary' },
  COMPLETED: { label: '已完成', variant: 'default' },
  PARTIAL: { label: '部分完成', variant: 'outline' },
  FAILED: { label: '失败', variant: 'destructive' },
};

interface Props {
  caseId: string;
}

export function ReportList({ caseId }: Props) {
  const { data, isLoading, refetch } = useReportList(caseId);
  const generateReport = useGenerateReport();
  const deleteReport = useDeleteReport();

  const [showGenerator, setShowGenerator] = useState(false);
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [showCompare, setShowCompare] = useState(false);

  const reports: ReportOutline[] = data?.reports || [];

  // 处理删除报告
  const handleDelete = async (reportId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('确定要删除这份报告吗？')) return;

    try {
      await deleteReport.mutateAsync(reportId);
      toast.success('报告已删除');
      refetch();
    } catch {
      toast.error('删除失败');
    }
  };

  // 处理查看报告
  const handleViewReport = (reportId: string) => {
    setSelectedReportId(reportId);
  };

  // 处理报告生成
  const handleGenerate = async (type: string) => {
    try {
      await generateReport.mutateAsync({ caseId, type });
      toast.success('报告生成任务已创建');
      setShowGenerator(false);
      refetch();
    } catch (error: unknown) {
      const message =
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        typeof (error as { response?: { data?: { detail?: unknown } } }).response?.data?.detail ===
          'string'
          ? (error as { response: { data: { detail: string } } }).response.data.detail
          : error instanceof Error
            ? error.message
            : '未知错误';
      toast.error(`生成失败: ${message}`);
    }
  };

  if (isLoading) return <PageSkeleton />;

  // 显示报告对比视图
  if (showCompare) {
    return (
      <ReportCompare
        reports={reports}
        onBack={() => setShowCompare(false)}
      />
    );
  }

  // 显示报告详情
  if (selectedReportId) {
    return (
      <ReportDetail
        reportId={selectedReportId}
        onBack={() => setSelectedReportId(null)}
        onRegenerate={() => {
          setSelectedReportId(null);
          setShowGenerator(true);
        }}
      />
    );
  }

  // 显示报告生成器
  if (showGenerator) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">生成报告</h2>
          <Button variant="ghost" onClick={() => setShowGenerator(false)}>
            返回列表
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Object.values(REPORT_TYPES).map((type) => {
            const Icon = type.icon;
            const isGenerating = generateReport.isPending && generateReport.variables?.type === type.value;

            return (
              <Card
                key={type.value}
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => !generateReport.isPending && handleGenerate(type.value)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <div className={`p-2 rounded-lg ${type.color}`}>
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    <CardTitle className="text-base">{type.label}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">{type.description}</p>
                  {isGenerating && (
                    <div className="mt-2 flex items-center gap-2">
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      <span className="text-sm">生成中...</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    );
  }

  const isEmpty = reports.length === 0;
  const hasMultipleReports = reports.length >= 2;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">报告中心</h2>
        <div className="flex items-center gap-2">
          {hasMultipleReports && (
            <Button variant="outline" onClick={() => setShowCompare(true)}>
              <GitCompare className="mr-2 h-4 w-4" />
              对比报告
            </Button>
          )}
          <Button onClick={() => setShowGenerator(true)}>
            <Plus className="mr-2 h-4 w-4" />
            生成报告
          </Button>
        </div>
      </div>

      {isEmpty ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FileText className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">暂无报告</p>
            <Button onClick={() => setShowGenerator(true)}>
              <Plus className="mr-2 h-4 w-4" />
              生成第一份报告
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {reports.map((report) => {
            const statusConfig = STATUS_CONFIG[report.status] || STATUS_CONFIG.PLANNING;
            // 根据 report_type 查找对应的类型配置
            const typeConfig = REPORT_TYPES[report.report_type] || REPORT_TYPES['ANALYSIS'];
            const Icon = typeConfig.icon;
            // 进度百分比
            const progress = report.progress?.progress || 0;

            return (
              <Card
                key={report.id}
                className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => handleViewReport(report.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${typeConfig.color}`}>
                        <Icon className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{report.title}</p>
                          <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>
                          {report.version > 1 && (
                            <Badge variant="outline">V{report.version}</Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                          <span>{typeConfig.label}</span>
                          <span>·</span>
                          <span>{report.created_at ? new Date(report.created_at).toLocaleDateString('zh-CN') : ''}</span>
                          {report.progress && report.progress.total > 0 && (
                            <>
                              <span>·</span>
                              <span>{report.progress.completed}/{report.progress.total} 章节</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewReport(report.id)}
                        title="查看详情"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => handleDelete(report.id, e)}
                        title="删除报告"
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {/* 进度条 - 仅在生成中状态显示 */}
                  {report.status === 'GENERATING' && progress > 0 && (
                    <div className="mt-3">
                      <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">{Math.round(progress)}% 完成</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
