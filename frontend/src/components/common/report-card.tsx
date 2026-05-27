import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Eye, Download, BarChart3, Target, Shield, Calendar, User } from 'lucide-react';
import { REPORT_TYPE_CONFIG, REPORT_STATUS_CONFIG, type ReportOutline } from '@/types/report.types';

interface Props {
  report: ReportOutline;
  onView: (reportId: string) => void;
  onExport?: (reportId: string) => void;
}

/**
 * 报告卡片组件
 * 用于在报告列表中展示单个报告
 */
export function ReportCard({ report, onView, onExport }: Props) {
  // 获取类型配置
  const typeConfig = REPORT_TYPE_CONFIG[report.report_type] || REPORT_TYPE_CONFIG['ANALYSIS'];
  const statusConfig = REPORT_STATUS_CONFIG[report.status] || REPORT_STATUS_CONFIG['PLANNING'];

  // 获取类型图标
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'ANALYSIS': return BarChart3;
      case 'STRATEGY': return Target;
      case 'FULL_ANALYSIS': return Shield;
      case 'MILESTONE_REPORT': return Calendar;
      case 'OPPONENT_ANALYSIS': return User;
      default: return BarChart3;
    }
  };

  const TypeIcon = getTypeIcon(report.report_type);
  const isGenerating = report.status === 'GENERATING';
  const isCompleted = report.status === 'COMPLETED';

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <div className={`p-2 rounded-lg ${typeConfig.color}`}>
            <TypeIcon className="h-4 w-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <CardTitle className="text-base truncate">{report.title}</CardTitle>
          </div>
          <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 text-sm text-muted-foreground mb-3">
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

        {/* 进度条 */}
        {isGenerating && report.progress && (
          <div className="mb-3">
            <div className="h-1.5 w-full bg-secondary rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${report.progress.progress}%` }}
              />
            </div>
            <p className="text-xs text-muted-foreground mt-1">{Math.round(report.progress.progress)}% 完成</p>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onView(report.id)}
          >
            <Eye className="mr-1 h-4 w-4" />
            查看
          </Button>
          {isCompleted && onExport && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onExport(report.id)}
            >
              <Download className="mr-1 h-4 w-4" />
              导出
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default ReportCard;
