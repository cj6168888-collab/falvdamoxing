import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, ArrowLeft, GitCompare, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { compareReports, type ReportCompareResult } from '@/api/report.api';
import { REPORT_TYPE_CONFIG, type ReportOutline } from '@/types/report.types';

interface Props {
  reports: ReportOutline[];
  onBack: () => void;
}

/**
 * 报告对比组件
 * 允许用户选择两个报告进行对比
 */
export function ReportCompare({ reports, onBack }: Props) {
  const [report1Id, setReport1Id] = useState<string>('');
  const [report2Id, setReport2Id] = useState<string>('');
  const [compareResult, setCompareResult] = useState<ReportCompareResult | null>(null);
  const [isComparing, setIsComparing] = useState(false);
  const [selectedSection, setSelectedSection] = useState<number>(0);

  const handleCompare = async () => {
    if (!report1Id || !report2Id) {
      toast.error('请选择要对比的两个报告');
      return;
    }
    if (report1Id === report2Id) {
      toast.error('请选择不同的报告进行对比');
      return;
    }

    setIsComparing(true);
    try {
      const result = await compareReports(report1Id, report2Id);
      setCompareResult(result);
      toast.success('对比完成');
    } catch (error) {
      toast.error('对比失败');
      console.error('Compare error:', error);
    } finally {
      setIsComparing(false);
    }
  };

  const getReportById = (id: string) => reports.find(r => r.id === id);

  // 重置对比结果
  const handleReset = () => {
    setCompareResult(null);
    setReport1Id('');
    setReport2Id('');
    setSelectedSection(0);
  };

  // 获取相似度颜色
  const getSimilarityColor = (similarity: number | null) => {
    if (similarity === null) return 'text-muted-foreground';
    if (similarity >= 80) return 'text-green-600';
    if (similarity >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  // 获取相似度图标
  const getSimilarityIcon = (similarity: number | null) => {
    if (similarity === null) return <AlertCircle className="h-4 w-4" />;
    if (similarity >= 80) return <CheckCircle className="h-4 w-4 text-green-500" />;
    if (similarity >= 50) return <AlertCircle className="h-4 w-4 text-yellow-500" />;
    return <XCircle className="h-4 w-4 text-red-500" />;
  };

  return (
    <div className="space-y-4">
      {/* 头部导航 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={onBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回
          </Button>
          <h2 className="text-lg font-bold">报告对比</h2>
        </div>
      </div>

      {/* 选择报告 */}
      {!compareResult && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitCompare className="h-5 w-5" />
              选择要对比的报告
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {/* 报告1 */}
              <div className="space-y-2">
                <label className="text-sm font-medium">报告 1</label>
                <Select value={report1Id} onValueChange={setReport1Id}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择第一个报告" />
                  </SelectTrigger>
                  <SelectContent>
                    {reports
                      .filter(r => r.id !== report2Id)
                      .map(report => (
                        <SelectItem key={report.id} value={report.id}>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{REPORT_TYPE_CONFIG[report.report_type]?.label || report.report_type}</Badge>
                            <span className="truncate">{report.title}</span>
                          </div>
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
                {report1Id && (
                  <div className="text-sm text-muted-foreground">
                    {getReportById(report1Id)?.created_at &&
                      new Date(getReportById(report1Id)!.created_at!).toLocaleDateString('zh-CN')}
                  </div>
                )}
              </div>

              {/* 报告2 */}
              <div className="space-y-2">
                <label className="text-sm font-medium">报告 2</label>
                <Select value={report2Id} onValueChange={setReport2Id}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择第二个报告" />
                  </SelectTrigger>
                  <SelectContent>
                    {reports
                      .filter(r => r.id !== report1Id)
                      .map(report => (
                        <SelectItem key={report.id} value={report.id}>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{REPORT_TYPE_CONFIG[report.report_type]?.label || report.report_type}</Badge>
                            <span className="truncate">{report.title}</span>
                          </div>
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
                {report2Id && (
                  <div className="text-sm text-muted-foreground">
                    {getReportById(report2Id)?.created_at &&
                      new Date(getReportById(report2Id)!.created_at!).toLocaleDateString('zh-CN')}
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleCompare}
                disabled={!report1Id || !report2Id || isComparing}
                className="flex-1"
              >
                {isComparing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    对比中...
                  </>
                ) : (
                  <>
                    <GitCompare className="mr-2 h-4 w-4" />
                    开始对比
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 对比结果 */}
      {compareResult && (
        <>
          {/* 对比概览 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>对比结果</CardTitle>
                <Button variant="outline" size="sm" onClick={handleReset}>
                  重新选择
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* 报告信息 */}
              <div className="grid gap-4 md:grid-cols-2 mb-6">
                <div className="p-4 border rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge>{REPORT_TYPE_CONFIG[compareResult.report_1.report_type]?.label || compareResult.report_1.report_type}</Badge>
                    <span className="text-sm text-muted-foreground">V{compareResult.report_1.version}</span>
                  </div>
                  <p className="font-medium truncate">{compareResult.report_1.title}</p>
                  <p className="text-sm text-muted-foreground">
                    {compareResult.report_1.created_at &&
                      new Date(compareResult.report_1.created_at).toLocaleString('zh-CN')}
                  </p>
                  <p className="text-sm mt-2">{compareResult.report_1.sections_count} 个章节</p>
                </div>
                <div className="p-4 border rounded-lg bg-muted/50">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge>{REPORT_TYPE_CONFIG[compareResult.report_2.report_type]?.label || compareResult.report_2.report_type}</Badge>
                    <span className="text-sm text-muted-foreground">V{compareResult.report_2.version}</span>
                  </div>
                  <p className="font-medium truncate">{compareResult.report_2.title}</p>
                  <p className="text-sm text-muted-foreground">
                    {compareResult.report_2.created_at &&
                      new Date(compareResult.report_2.created_at).toLocaleString('zh-CN')}
                  </p>
                  <p className="text-sm mt-2">{compareResult.report_2.sections_count} 个章节</p>
                </div>
              </div>

              {/* 统计摘要 */}
              <div className="grid gap-4 md:grid-cols-4">
                <div className="text-center p-3 border rounded-lg">
                  <p className="text-2xl font-bold">{compareResult.summary.total_sections}</p>
                  <p className="text-sm text-muted-foreground">总章节数</p>
                </div>
                <div className="text-center p-3 border rounded-lg">
                  <p className="text-2xl font-bold text-green-600">{compareResult.summary.common_sections}</p>
                  <p className="text-sm text-muted-foreground">共同章节</p>
                </div>
                <div className="text-center p-3 border rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">{compareResult.summary.only_in_first}</p>
                  <p className="text-sm text-muted-foreground">仅在报告1</p>
                </div>
                <div className="text-center p-3 border rounded-lg">
                  <p className="text-2xl font-bold text-purple-600">{compareResult.summary.only_in_second}</p>
                  <p className="text-sm text-muted-foreground">仅在报告2</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 章节对比 */}
          <Card>
            <CardHeader>
              <CardTitle>章节对比</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {compareResult.section_comparison.map((section, index) => {
                  const isBoth = section.status === 'both';
                  const similarity = section.similarity;

                  return (
                    <div
                      key={index}
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        selectedSection === index ? 'border-primary bg-primary/5' : 'hover:border-primary/50'
                      }`}
                      onClick={() => setSelectedSection(index)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-muted flex items-center justify-center text-sm font-medium">
                            {index + 1}
                          </span>
                          <span className="font-medium">
                            {section.section_1?.title || section.section_2?.title || `章节 ${index + 1}`}
                          </span>
                        </div>
                        <div className="flex items-center gap-3">
                          {isBoth && (
                            <div className={`flex items-center gap-1 ${getSimilarityColor(similarity)}`}>
                              {getSimilarityIcon(similarity)}
                              <span className="text-sm font-medium">
                                {similarity !== null ? `${similarity}%` : 'N/A'}
                              </span>
                            </div>
                          )}
                          <Badge
                            variant={
                              section.status === 'both' ? 'default' :
                              section.status === 'only_first' ? 'outline' : 'secondary'
                            }
                          >
                            {section.status === 'both' ? '共同' :
                             section.status === 'only_first' ? '报告1' : '报告2'}
                          </Badge>
                        </div>
                      </div>

                      {/* 详细信息 */}
                      {selectedSection === index && (
                        <div className="mt-4 pt-4 border-t space-y-2">
                          {section.section_1 && (
                            <div className="text-sm">
                              <span className="text-muted-foreground">报告1: </span>
                              <span>{section.section_1.content_length} 字符</span>
                              {section.section_1.completed_at && (
                                <span className="text-muted-foreground ml-2">
                                  ({new Date(section.section_1.completed_at).toLocaleDateString('zh-CN')})
                                </span>
                              )}
                            </div>
                          )}
                          {section.section_2 && (
                            <div className="text-sm">
                              <span className="text-muted-foreground">报告2: </span>
                              <span>{section.section_2.content_length} 字符</span>
                              {section.section_2.completed_at && (
                                <span className="text-muted-foreground ml-2">
                                  ({new Date(section.section_2.completed_at).toLocaleDateString('zh-CN')})
                                </span>
                              )}
                            </div>
                          )}
                          {isBoth && similarity !== null && (
                            <div className="flex items-center gap-2 mt-2">
                              <span className="text-sm text-muted-foreground">相似度:</span>
                              <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${
                                    similarity >= 80 ? 'bg-green-500' :
                                    similarity >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`}
                                  style={{ width: `${similarity}%` }}
                                />
                              </div>
                              <span className={`text-sm font-medium ${getSimilarityColor(similarity)}`}>
                                {similarity}%
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

export default ReportCompare;
