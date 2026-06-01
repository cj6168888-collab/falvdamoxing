import { useState, useCallback, useEffect, useMemo } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import { EvidenceList } from '@/components/evidence/evidence-list';
import { EvidenceUploader } from '@/components/evidence/evidence-uploader';
import { EvidenceReviewFields } from '@/components/evidence/evidence-review-fields';
import { uploadEvidence } from '@/api/evidence.api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { EmptyState } from '@/components/common/empty-state';
import { MarkdownContent } from '@/components/common/markdown-content';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  List, Eye, Printer, Sparkles, X, FileText, Image,
  ChevronLeft, RotateCw, Loader2, CheckCircle,
  MessageSquare, Download, Search, ShieldCheck, AlertTriangle,
  FolderOpen, Filter,
  type LucideIcon
} from 'lucide-react';
import { toast } from 'sonner';

interface EvidenceItem {
  id: string;
  case_id: number;
  display_name: string;
  original_filename: string;
  evidence_type: string;
  summary: string;
  extracted_content: string;
  raw_content: string;
  proves_facts: EvidenceFact[];
  credibility_score: number | null;
  status: string;
  source_party: string;
  created_at: string;
  file_path: string;
  entity_tags: unknown[];
  evidence_review?: {
    review_status?: string;
    reviewed_by?: string;
    reviewed_at?: string;
    source?: string | null;
    formed_at?: string | null;
    original_status?: string | null;
    proof_purpose?: string | null;
    authenticity_risk?: string | null;
    legality_risk?: string | null;
    relevance_risk?: string | null;
    strengthening_actions?: string[];
    review_notes?: string | null;
  } | null;
}

type EvidenceFact = string | { fact?: string };
type EvidenceBookFormat = 'markdown' | 'pdf' | 'docx';

export default function CaseEvidencePage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const highlightId = searchParams.get('highlight');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem | null>(null);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [userGuidance, setUserGuidance] = useState('');
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [imageZoom, setImageZoom] = useState(false);
  const [showUploader, setShowUploader] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isExportingBook, setIsExportingBook] = useState(false);

  const handleUploadFiles = async (files: File[]) => {
    if (!id) return;
    setIsUploading(true);
    const toastId = toast.loading(`正在上传并分析 ${files.length} 个本地证据文件...这可能需要三十秒到数分钟`);
    try {
      const formData = new FormData();
      files.forEach((f) => formData.append('files', f));
      await uploadEvidence(id, formData);
      toast.success('上传并解析成功', { id: toastId });
      setShowUploader(false);
      refetch();
    } catch (e) {
      toast.error(getRequestErrorMessage(e, '上传失败'), { id: toastId });
    } finally {
      setIsUploading(false);
    }
  };

  // 获取证据列表
  const { data: evidenceList, isLoading, refetch } = useQuery<EvidenceItem[]>({
    queryKey: ['evidence-list', id],
    queryFn: () => axiosInstance.get(`/api/v2/evidence-graph/evidence/list`, { params: { case_id: parseInt(id || '0') } })
      .then(res => (res.data?.evidence_list || []) as EvidenceItem[]),
    enabled: !!id,
  });

  // Auto-select highlighted evidence
  useEffect(() => {
    if (highlightId && evidenceList) {
      const found = evidenceList.find((e: EvidenceItem) => String(e.id) === highlightId);
      if (found) {
        setSelectedEvidence(found);
      }
    }
  }, [highlightId, evidenceList]);

  // AI 分析证据
  const analyzeEvidence = useMutation({
    mutationFn: async ({ evidenceId, guidance }: { evidenceId: string; guidance: string }) => {
      const evidence = evidenceList?.find((e: EvidenceItem) => e.id === evidenceId);
      if (!evidence) throw new Error('证据不存在');

      const prompt = `你是一位资深律师，请分析以下证据：

【证据信息】
- 名称：${evidence.display_name || evidence.original_filename}
- 类型：${evidence.evidence_type || '未分类'}
- 摘要：${evidence.summary || '无'}
- 内容：${(evidence.extracted_content || evidence.raw_content || '').substring(0, 3000)}
${evidence.proves_facts && evidence.proves_facts.length > 0 ? `- 证明事实：${JSON.stringify(evidence.proves_facts)}` : ''}

${guidance ? `【用户指导意见】\n用户认为该证据可以证明：${guidance}\n\n请评估用户的判断是否准确，并给出专业意见。` : '请全面分析该证据的证明力、法律效力、可能的弱点，以及需要与其他哪些证据关联才能形成完整证据链。'}

请从以下方面分析：
1. 证据的证明力评估
2. 证据的法律效力
3. 证据的证明力参考
4. 需要关联的其他证据
5. 是否需要补充扫描或补充证据
6. 对用户指导意见的专业评价`;

      const res = await axiosInstance.post('/api/smart-chat/follow-up', {
        case_id: parseInt(id || '0'),
        message: prompt,
      });
      return res.data.content;
    },
    onMutate: () => {
      setIsAnalyzing(true);
      setAnalysisProgress(0);
      let progress = 0;
      const interval = setInterval(() => {
        progress = Math.min(progress + 5, 95);
        setAnalysisProgress(progress);
      }, 500);
      return { interval };
    },
    onSuccess: (content, _, ctx) => {
      if (ctx?.interval) clearInterval(ctx.interval);
      setAnalysisProgress(100);
      setAnalysisResult(content);
      setIsAnalyzing(false);
      toast.success('AI 分析完成');
    },
    onError: (err, _, ctx) => {
      if (ctx?.interval) clearInterval(ctx.interval);
      setIsAnalyzing(false);
      toast.error('AI 分析失败：' + getRequestErrorMessage(err, '未知错误'));
    },
  });

  const handleAnalyze = useCallback(() => {
    if (!selectedEvidence) return;
    setAnalysisResult(null);
    analyzeEvidence.mutate({ evidenceId: selectedEvidence.id, guidance: userGuidance });
  }, [selectedEvidence, userGuidance, analyzeEvidence]);

  const handlePrint = useCallback(() => {
    if (!selectedEvidence) return;
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;
    const content = selectedEvidence.extracted_content || selectedEvidence.raw_content || selectedEvidence.summary || '无内容';
    printWindow.document.write(`
      <html><head><title>${selectedEvidence.display_name || selectedEvidence.original_filename}</title>
      <style>body{font-family:SimSun,serif;padding:40px;line-height:1.8;}h1{font-size:18px;border-bottom:2px solid #333;padding-bottom:10px;}.meta{color:#666;margin-bottom:20px;}.content{white-space:pre-wrap;}</style>
      </head><body>
      <h1>${selectedEvidence.display_name || selectedEvidence.original_filename}</h1>
      <div class="meta">
        <p>证据类型：${selectedEvidence.evidence_type || '未分类'}</p>
        <p>证明力参考：${selectedEvidence.credibility_score || '未评估'}（仅作工作底稿参考）</p>
        <p>来源方：${selectedEvidence.source_party || '未知'}</p>
        <p>创建时间：${selectedEvidence.created_at ? new Date(selectedEvidence.created_at).toLocaleString('zh-CN') : '-'}</p>
      </div>
      <div class="content">${content}</div>
      </body></html>
    `);
    printWindow.document.close();
    printWindow.print();
  }, [selectedEvidence]);

  const handleDownload = useCallback(() => {
    if (!selectedEvidence) return;
    const content = selectedEvidence.extracted_content || selectedEvidence.raw_content || selectedEvidence.summary || '无内容';
    const blob = new Blob([`证据名称：${selectedEvidence.display_name || selectedEvidence.original_filename}\n证据类型：${selectedEvidence.evidence_type || '未分类'}\n证明力参考：${selectedEvidence.credibility_score || '未评估'}（仅作工作底稿参考）\n\n${content}`], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedEvidence.display_name || selectedEvidence.original_filename || '证据'}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [selectedEvidence]);

  const handleExportBook = useCallback(async (format: EvidenceBookFormat) => {
    if (!id) return;
    setIsExportingBook(true);
    const toastId = toast.loading('正在生成证据册...');
    try {
      const res = await axiosInstance.get(`/api/evidence/export-book/${id}`, {
        params: { format },
      });
      const data = res.data as {
        success?: boolean;
        message?: string;
        error?: string;
        content?: string;
        download_url?: string;
        filename?: string;
        format_used?: string;
      };

      if (data.success === false) {
        throw new Error(data.message || data.error || '导出失败');
      }

      const anchor = document.createElement('a');
      if (data.download_url) {
        anchor.href = data.download_url;
        anchor.download = data.filename || `evidence-book.${data.format_used || format}`;
      } else if (typeof data.content === 'string') {
        const ext = format === 'markdown' ? 'md' : format;
        const blob = new Blob([data.content], {
          type: format === 'markdown' ? 'text/markdown;charset=utf-8' : 'text/plain;charset=utf-8',
        });
        anchor.href = URL.createObjectURL(blob);
        anchor.download = `evidence-book-${id}.${ext}`;
      } else {
        throw new Error('导出结果缺少下载内容');
      }

      document.body.appendChild(anchor);
      anchor.click();
      if (anchor.href.startsWith('blob:')) {
        URL.revokeObjectURL(anchor.href);
      }
      document.body.removeChild(anchor);
      toast.success('证据册导出成功', { id: toastId });
    } catch (e) {
      toast.error(getRequestErrorMessage(e, '证据册导出失败'), { id: toastId });
    } finally {
      setIsExportingBook(false);
    }
  }, [id]);

  const isImageFile = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp'].includes(ext || '');
  };

  const evidences = evidenceList || [];
  const evidenceStats = useMemo(() => buildEvidenceStats(evidences), [evidences]);
  const evidenceTypes = useMemo(() => {
    const types = Array.from(new Set(evidences.map((ev: EvidenceItem) => ev.evidence_type || '未分类')));
    return types.sort((a, b) => a.localeCompare(b, 'zh-CN'));
  }, [evidences]);
  const filteredEvidences = useMemo(() => {
    const keyword = searchText.trim().toLowerCase();
    return evidences.filter((ev: EvidenceItem) => {
      const matchesKeyword = !keyword || [
        ev.display_name,
        ev.original_filename,
        ev.evidence_type,
        ev.summary,
        ev.extracted_content,
        ev.raw_content,
        ev.source_party,
      ].some((value) => String(value || '').toLowerCase().includes(keyword));
      const matchesType = typeFilter === 'all' || (ev.evidence_type || '未分类') === typeFilter;
      const matchesStatus = statusFilter === 'all' || ev.status === statusFilter;
      return matchesKeyword && matchesType && matchesStatus;
    });
  }, [evidences, searchText, statusFilter, typeFilter]);
  const exportBookDisabled = isExportingBook || evidences.length === 0;
  const exportBookMenu = (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" disabled={exportBookDisabled}>
          {isExportingBook ? (
            <Loader2 className="h-4 w-4 mr-1 animate-spin" />
          ) : (
            <Download className="h-4 w-4 mr-1" />
          )}
          导出证据册
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleExportBook('markdown')}>
          Markdown 格式 (.md)
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => handleExportBook('pdf')}>
          PDF 文档 (.pdf)
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExportBook('docx')}>
          Word 文档 (.docx)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );

  if (isLoading) return <PageSkeleton />;

  if (evidences.length === 0) {
    if (showUploader) {
      return (
        <div className="space-y-4 max-w-2xl mx-auto">
          <Button variant="ghost" onClick={() => setShowUploader(false)}><ChevronLeft className="h-4 w-4 mr-1"/> 返回</Button>
          <div className={isUploading ? 'opacity-50 pointer-events-none' : ''}>
            <EvidenceUploader caseId={id || ''} onUpload={handleUploadFiles} />
          </div>
        </div>
      );
    }

    return (
      <EmptyState
        title="暂无证据"
        description="请先上传证据或配置证据文件夹"
        actionLabel="上传本地证据"
        onAction={() => setShowUploader(true)}
      />
    );
  }

  if (showUploader) {
    return (
      <div className="space-y-4 max-w-2xl mx-auto">
        <Button variant="ghost" onClick={() => setShowUploader(false)}><ChevronLeft className="h-4 w-4 mr-1"/> 返回</Button>
        <div className={isUploading ? 'opacity-50 pointer-events-none' : ''}>
          <EvidenceUploader caseId={id || ''} onUpload={handleUploadFiles} />
        </div>
      </div>
    );
  }

  // 证据详情弹窗
  if (selectedEvidence) {
    const isImage = isImageFile(selectedEvidence.original_filename || '');
    const content = selectedEvidence.extracted_content || selectedEvidence.raw_content || '';

    return (
      <div className="space-y-4">
        {/* 顶部导航 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => { setSelectedEvidence(null); setShowAnalysis(false); setAnalysisResult(null); setUserGuidance(''); }}>
              <ChevronLeft className="mr-1 h-4 w-4" />返回列表
            </Button>
            <div>
              <h2 className="text-lg font-bold">{selectedEvidence.display_name || selectedEvidence.original_filename}</h2>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline">{selectedEvidence.evidence_type || '未分类'}</Badge>
                {selectedEvidence.credibility_score != null && (
                  <Badge variant="outline">证明力参考 {selectedEvidence.credibility_score}%</Badge>
                )}
                <StatusBadge status={selectedEvidence.status} />
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handlePrint}>
              <Printer className="mr-1 h-4 w-4" />打印
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="mr-1 h-4 w-4" />下载
            </Button>
            <Button variant={showAnalysis ? 'default' : 'outline'} size="sm" onClick={() => setShowAnalysis(!showAnalysis)}>
              <Sparkles className="mr-1 h-4 w-4" />AI 分析
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* 左侧：证据内容 */}
          <div className={`${showAnalysis ? 'lg:col-span-2' : 'lg:col-span-3'} space-y-4`}>
            {/* 图片预览 */}
            {isImage && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">证据图片</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="relative">
                    <img
                      src={`/api/files/${selectedEvidence.case_id}/${selectedEvidence.original_filename}`}
                      alt={selectedEvidence.display_name}
                      className="w-full max-h-96 object-contain rounded-lg cursor-pointer bg-muted"
                      onClick={() => setImageZoom(!imageZoom)}
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                    {imageZoom && (
                      <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center" onClick={() => setImageZoom(false)}>
                        <img
                          src={`/api/files/${selectedEvidence.case_id}/${selectedEvidence.original_filename}`}
                          alt={selectedEvidence.display_name}
                          className="max-w-[90vw] max-h-[90vh] object-contain"
                        />
                        <Button variant="ghost" size="icon" className="absolute top-4 right-4 text-white" onClick={() => setImageZoom(false)}>
                          <X className="h-6 w-6" />
                        </Button>
                      </div>
                    )}
                    <p className="text-center text-xs text-muted-foreground mt-2">点击图片放大查看</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 证据内容 */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">证据内容</CardTitle>
              </CardHeader>
              <CardContent>
                {content ? (
                  <div className="max-h-[60vh] overflow-y-auto">
                    <MarkdownContent content={content} />
                  </div>
                ) : (
                  <div className="py-8 text-center text-sm text-muted-foreground">
                    <FileText className="mx-auto h-8 w-8 opacity-50 mb-2" />
                    <p>暂无内容</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <EvidenceReviewFields
              evidence={selectedEvidence}
              onSaved={(updatedEvidence) => {
                setSelectedEvidence(updatedEvidence as EvidenceItem);
                refetch();
              }}
            />

            {/* 证明事实 */}
            {selectedEvidence.proves_facts && selectedEvidence.proves_facts.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">证明事实</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="list-disc pl-5 space-y-1">
                    {selectedEvidence.proves_facts.map((fact, i) => (
                      <li key={i} className="text-sm text-muted-foreground">
                        {typeof fact === 'string' ? fact : fact.fact || JSON.stringify(fact)}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>

          {/* 右侧：AI 分析 */}
          {showAnalysis && (
            <div className="space-y-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    AI 证据分析
                  </CardTitle>
                  <CardDescription>
                    告诉 AI 你认为该证据可以证明什么，AI 会给出专业意见
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Textarea
                    value={userGuidance}
                    onChange={(e) => setUserGuidance(e.target.value)}
                    placeholder="例如：我认为这份合同可以证明双方存在买卖关系，对方未按约交货构成违约..."
                    rows={4}
                    className="text-sm"
                  />
                  <Button
                    onClick={handleAnalyze}
                    disabled={isAnalyzing}
                    className="w-full"
                  >
                    {isAnalyzing ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" />AI 分析中...</>
                    ) : (
                      <><Sparkles className="mr-2 h-4 w-4" />开始分析</>
                    )}
                  </Button>
                  {isAnalyzing && <Progress value={analysisProgress} className="h-1" />}
                </CardContent>
              </Card>

              {/* 分析结果 */}
              {analysisResult && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      AI 分析结果
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="max-h-[50vh] overflow-y-auto">
                      <MarkdownContent content={analysisResult} />
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // 证据列表 - 缩略图网格视图
  if (viewMode === 'grid') {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-950">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                <FolderOpen className="h-4 w-4" />
                <span>证据链审查</span>
              </div>
              <h2 className="mt-1 text-xl font-semibold text-slate-950 dark:text-slate-100">
                证据列表 ({filteredEvidences.length}/{evidences.length})
              </h2>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                按证明力参考、证据类型和处理状态快速定位材料，先处理低证明力参考、失败解析和关键主体材料。
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {exportBookMenu}
              <Button variant="default" size="sm" onClick={() => setShowUploader(true)} disabled={isUploading} className="bg-teal-700 hover:bg-teal-800">
                <Sparkles className="h-4 w-4 mr-1" />{isUploading ? '处理中...' : '上传证据'}
              </Button>
              <Button variant="outline" size="sm" onClick={() => setViewMode('list')}>
                <List className="h-4 w-4 mr-1" />列表
              </Button>
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RotateCw className="h-4 w-4 mr-1" />刷新
              </Button>
            </div>
          </div>

          <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
            <EvidenceStatCard icon={ShieldCheck} label="已完成解析" value={evidenceStats.processed} suffix="份" tone="teal" />
            <EvidenceStatCard icon={AlertTriangle} label="低证明力参考/待核验" value={evidenceStats.lowCredibility} suffix="份" tone="amber" />
            <EvidenceStatCard icon={FileText} label="有证明事实" value={evidenceStats.withFacts} suffix="份" tone="slate" />
            <EvidenceStatCard icon={X} label="失败或无内容" value={evidenceStats.problematic} suffix="份" tone="red" />
          </div>

          <div className="mt-4 grid gap-2 lg:grid-cols-[minmax(0,1fr)_180px_160px_auto]">
            <label className="relative block">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={searchText}
                onChange={(event) => setSearchText(event.target.value)}
                placeholder="搜索文件名、摘要、正文、来源方..."
                className="h-10 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-sm outline-none transition-colors focus:border-teal-400 dark:border-slate-800 dark:bg-slate-950"
              />
            </label>
            <select
              value={typeFilter}
              onChange={(event) => setTypeFilter(event.target.value)}
              className="h-10 rounded-md border border-slate-200 bg-white px-3 text-sm dark:border-slate-800 dark:bg-slate-950"
            >
              <option value="all">全部类型</option>
              {evidenceTypes.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              className="h-10 rounded-md border border-slate-200 bg-white px-3 text-sm dark:border-slate-800 dark:bg-slate-950"
            >
              <option value="all">全部状态</option>
              <option value="processed">已完成</option>
              <option value="processing">处理中</option>
              <option value="pending">待处理</option>
              <option value="failed">失败</option>
            </select>
            <Button
              variant="outline"
              size="sm"
              onClick={() => { setSearchText(''); setTypeFilter('all'); setStatusFilter('all'); }}
              className="h-10"
            >
              <Filter className="mr-1 h-4 w-4" />
              重置
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
          {filteredEvidences.map((ev: EvidenceItem) => {
            const isImg = isImageFile(ev.original_filename || '');
            return (
              <Card
                key={ev.id}
                data-testid="evidence-item"
                className="group cursor-pointer overflow-hidden border-slate-200 transition-shadow hover:shadow-md dark:border-slate-800"
                onClick={() => setSelectedEvidence(ev)}
              >
                {/* 缩略图区域 */}
                <div className="relative flex aspect-[4/3] items-center justify-center overflow-hidden bg-slate-100 dark:bg-slate-900">
                  {isImg ? (
                    <div className="w-full h-full flex items-center justify-center bg-muted">
                      <Image className="h-12 w-12 text-muted-foreground/50" />
                    </div>
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-muted">
                      <FileText className="h-12 w-12 text-muted-foreground/50" />
                    </div>
                  )}
                  {/* 悬浮操作 */}
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                    <Button size="sm" variant="secondary" className="h-8 px-2 text-xs"
                      onClick={(e) => { e.stopPropagation(); setSelectedEvidence(ev); }}>
                      <Eye className="h-3 w-3 mr-1" />查看
                    </Button>
                  </div>
                  {/* 状态标记 */}
                  <div className="absolute right-2 top-2">
                    <StatusBadge status={ev.status} />
                  </div>
                  <div className="absolute bottom-2 left-2 rounded bg-white/90 px-2 py-1 text-[10px] font-medium text-slate-700 shadow-sm dark:bg-slate-950/90 dark:text-slate-300">
                    {ev.evidence_type || '未分类'}
                  </div>
                </div>
                {/* 信息区域 */}
                <CardContent className="p-3">
                  <p className="line-clamp-2 min-h-[40px] text-sm font-medium leading-5" title={ev.display_name || ev.original_filename}>
                    {ev.display_name || ev.original_filename || '未命名'}
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    {ev.credibility_score != null && (
                      <CredibilityPill score={ev.credibility_score} />
                    )}
                    {ev.proves_facts?.length > 0 && (
                      <Badge variant="outline" className="h-5 text-[10px]">证明 {ev.proves_facts.length}</Badge>
                    )}
                  </div>
                  {ev.summary && (
                    <p className="mt-2 line-clamp-3 text-xs leading-5 text-slate-500 dark:text-slate-400" title={ev.summary}>
                      {ev.summary}
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
        {filteredEvidences.length === 0 && (
          <Card className="border-dashed">
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              没有匹配当前筛选条件的证据。
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // 列表视图
  return (
    <div className="space-y-4">
      <div className="flex justify-end gap-2 mb-4">
        {exportBookMenu}
        <Button variant="default" size="sm" onClick={() => setShowUploader(true)} disabled={isUploading}>
          <Sparkles className="h-4 w-4 mr-1" />{isUploading ? '处理中...' : '上传证据'}
        </Button>
      </div>
      <EvidenceList caseId={id || ''} />
    </div>
  );
}

function getRequestErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    return response?.data?.detail || fallback;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

function buildEvidenceStats(evidences: EvidenceItem[]) {
  return evidences.reduce(
    (stats, ev) => {
      const content = ev.extracted_content || ev.raw_content || ev.summary || '';
      if (ev.status === 'processed') stats.processed += 1;
      if (ev.credibility_score != null && ev.credibility_score < 60) stats.lowCredibility += 1;
      if (ev.proves_facts?.length > 0) stats.withFacts += 1;
      if (ev.status === 'failed' || !content.trim()) stats.problematic += 1;
      return stats;
    },
    { processed: 0, lowCredibility: 0, withFacts: 0, problematic: 0 }
  );
}

function EvidenceStatCard({
  icon: Icon,
  label,
  value,
  suffix,
  tone,
}: {
  icon: LucideIcon;
  label: string;
  value: number;
  suffix: string;
  tone: 'teal' | 'amber' | 'slate' | 'red';
}) {
  const toneClass = {
    teal: 'border-teal-200 bg-teal-50 text-teal-800 dark:border-teal-900 dark:bg-teal-950/40 dark:text-teal-200',
    amber: 'border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200',
    slate: 'border-slate-200 bg-slate-50 text-slate-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200',
    red: 'border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200',
  }[tone];

  return (
    <div className={`rounded-md border p-3 ${toneClass}`}>
      <div className="flex items-center gap-2 text-xs font-medium opacity-80">
        <Icon className="h-4 w-4" />
        {label}
      </div>
      <div className="mt-2 flex items-end gap-1">
        <span className="text-2xl font-semibold leading-none">{value}</span>
        <span className="text-xs opacity-70">{suffix}</span>
      </div>
    </div>
  );
}

function CredibilityPill({ score }: { score: number }) {
  const colorClass = score >= 80
    ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-300'
    : score >= 60
      ? 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-300'
      : 'border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300';

  return (
    <span className={`inline-flex h-5 items-center rounded border px-1.5 text-[10px] font-medium ${colorClass}`}>
      证明力参考 {score}%
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
    processed: { label: '已完成', variant: 'default' },
    processing: { label: '处理中', variant: 'secondary' },
    pending: { label: '待处理', variant: 'outline' },
    failed: { label: '失败', variant: 'destructive' },
  };
  const c = config[status] || { label: status, variant: 'secondary' };
  return <Badge variant={c.variant} className="text-xs">{c.label}</Badge>;
}
