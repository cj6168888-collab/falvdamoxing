import { useState, useRef, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { MarkdownContent } from '@/components/common/markdown-content';
import { HistoryDocumentList, type HistoryDocument } from '@/components/document/history-document-list';
import { DocumentExportReviewDialog } from '@/components/document/document-export-review-dialog';
import { DocumentExportAuditHistory } from '@/components/document/document-export-audit-history';
import { downloadExportFile, exportCaseDocument } from '@/api/export.api';
import {
  FileText, Sparkles, Send, Loader2, Download, FileDown,
  CheckCircle, RotateCcw, MessageSquare, ArrowLeft, Check,
  Eye, X, Edit3
} from 'lucide-react';
import { toast } from 'sonner';

interface DocTemplate {
  type: string;
  name: string;
  description: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface GeneratedDocumentRecord {
  id: string | number;
  title?: string;
  document_type?: string;
  type?: string;
  content?: string;
  version?: number;
  status?: string;
  created_at?: string | Date;
  updated_at?: string | Date;
  based_on_adversarial?: boolean;
  based_on_ai_analysis?: boolean;
  generation_context?: string;
  referenced_evidence?: unknown;
  modification_history?: unknown[];
}

type PendingDocumentExport =
  | { kind: 'download'; docId: string | number; format: 'docx' | 'pdf'; documentTitle?: string }
  | { kind: 'markdown'; documentTitle?: string }
  | { kind: 'evidence-book'; documentTitle?: string };

export default function CaseDocumentsPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 状态
  const [viewMode, setViewMode] = useState<'select' | 'generate' | 'chat' | 'result'>('select');
  const [selectedTemplate, setSelectedTemplate] = useState<DocTemplate | null>(null);
  const [userRequirements, setUserRequirements] = useState('');
  const [generatedContent, setGeneratedContent] = useState('');
  const [currentDocId, setCurrentDocId] = useState<number | null>(null);
  const [currentDocTitle, setCurrentDocTitle] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isAutoFormatting, setIsAutoFormatting] = useState(false);
  const [isExportingMarkdown, setIsExportingMarkdown] = useState(false);
  const [isReviewExporting, setIsReviewExporting] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [pendingExport, setPendingExport] = useState<PendingDocumentExport | null>(null);

  // 对话修改
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  // 历史文书预览
  const [previewDocument, setPreviewDocument] = useState<HistoryDocument | null>(null);

  // 获取模板列表
  const { data: templates, isLoading: loadingTemplates } = useQuery({
    queryKey: ['document-templates'],
    queryFn: () => axiosInstance.get<DocTemplate[]>('/api/documents/templates').then(res => res.data),
  });

  // 获取已生成文书列表
  const { data: documents, isLoading: isLoadingDocs } = useQuery({
    queryKey: ['documents', id],
    queryFn: async () => {
      try {
        const res = await axiosInstance.get<GeneratedDocumentRecord[]>(`/api/document-management/case/${id}/generated`);
        return (res.data || []).map((d) => ({
          id: String(d.id),
          title: d.title || '',
          document_type: d.document_type || d.type || '',
          content: d.content || '',
          version: d.version || 1,
          status: d.status || 'draft',
          // 处理日期字段，确保是字符串格式
          created_at: d.created_at instanceof Date 
            ? d.created_at.toISOString() 
            : (typeof d.created_at === 'string' ? d.created_at : ''),
          updated_at: d.updated_at instanceof Date 
            ? d.updated_at.toISOString() 
            : (typeof d.updated_at === 'string' ? d.updated_at : ''),
          based_on_adversarial: d.based_on_adversarial || false,
          based_on_ai_analysis: d.based_on_ai_analysis || false,
          generation_context: d.generation_context || '',
          referenced_evidence: d.referenced_evidence || null,
          modification_history: d.modification_history || [],
        }));
      } catch (error) {
        console.error('获取文书列表失败:', error);
        return [];
      }
    },
    enabled: !!id,
  });

  // 自动滚动
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // ========== 历史文书处理函数 ==========
  
  // 查看历史文书
  const handleViewDocument = useCallback((doc: HistoryDocument) => {
    setPreviewDocument(doc);
  }, []);

  const requestDocumentDownload = useCallback((
    docId: string | number,
    format: 'docx' | 'pdf',
    documentTitle?: string,
  ) => {
    setPendingExport({ kind: 'download', docId, format, documentTitle });
  }, []);

  // 下载 Word
  const handleDownloadDocx = useCallback((docId: string) => {
    const documentTitle = documents?.find((doc) => doc.id === docId)?.title;
    requestDocumentDownload(docId, 'docx', documentTitle);
  }, [documents, requestDocumentDownload]);

  // 下载 PDF
  const handleDownloadPdf = useCallback((docId: string) => {
    const documentTitle = documents?.find((doc) => doc.id === docId)?.title;
    requestDocumentDownload(docId, 'pdf', documentTitle);
  }, [documents, requestDocumentDownload]);

  // 删除历史文书
  const deleteMutation = useMutation({
    mutationFn: async (docId: string) => {
      return axiosInstance.delete(`/api/document-management/generated/${docId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', id] });
      toast.success('文书已删除');
    },
    onError: () => {
      toast.error('删除失败');
    },
  });

  const handleDeleteDocument = useCallback((docId: string) => {
    if (confirm('确定要删除这份文书吗？')) {
      deleteMutation.mutate(docId);
    }
  }, [deleteMutation]);

  // 选择模板
  const handleSelectTemplate = (template: DocTemplate) => {
    setSelectedTemplate(template);
    setViewMode('generate');
  };

  // 开始起草
  const handleStartGenerate = async () => {
    if (!selectedTemplate || !id) return;

    setIsGenerating(true);
    try {
      const res = await axiosInstance.post('/api/smart-chat/generate-document', {
        case_id: parseInt(id),
        document_type: selectedTemplate.type,
        custom_requirements: userRequirements || undefined,
      });

      const docData = res.data;
      setGeneratedContent(docData.content);
      setCurrentDocId(docData.document_id);
      setCurrentDocTitle(`${selectedTemplate.name}`);
      setIsConfirmed(false);

      // 初始化对话
      setChatMessages([
        {
          role: 'assistant',
          content: `《${selectedTemplate.name}》已生成完成！\n\n` +
            `基于案件全部 ${docData.evidence_count || 0} 份证据生成，文书中已标注证据序号。\n\n` +
            `您可以告诉我需要修改或补充的内容，我会帮您完善文书。`,
          timestamp: new Date().toISOString(),
        },
      ]);

      setViewMode('chat');
      toast.success(`《${selectedTemplate.name}》已生成`);
    } catch (err) {
      toast.error(getRequestErrorMessage(err, '文书草稿生成失败'));
    } finally {
      setIsGenerating(false);
    }
  };

  // 发送对话消息
  const handleSendMessage = async () => {
    if (!chatInput.trim() || !currentDocId) return;

    const userMsg: ChatMessage = {
      role: 'user',
      content: chatInput,
      timestamp: new Date().toISOString(),
    };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      // 调用 AI 修改文书
      const res = await axiosInstance.post('/api/documents/modify', {
        document_id: currentDocId,
        message: chatInput,
        current_content: generatedContent,
      });

      const updatedContent = res.data.content || res.data.updated_content;
      if (updatedContent) {
        setGeneratedContent(updatedContent);
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: res.data.message || '已根据您的要求修改文书，请查看更新后的内容。',
          timestamp: new Date().toISOString(),
        }]);
      }
    } catch {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: '抱歉，修改文书时遇到错误，请稍后重试。',
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // 确认并自动排版
  const handleConfirmAndFormat = async () => {
    if (!currentDocId || !generatedContent) return;

    setIsAutoFormatting(true);
    try {
      // 调用自动排版
      const res = await axiosInstance.post('/api/documents/format', {
        document_id: currentDocId,
        content: generatedContent,
      });

      const formattedContent = res.data.formatted_content || res.data.content;
      if (formattedContent) {
        setGeneratedContent(formattedContent);
      }

      setIsConfirmed(true);
      toast.success('文书已自动排版并确认');
    } catch {
      // 即使排版失败也确认
      setIsConfirmed(true);
      toast.success('文书已确认');
    } finally {
      setIsAutoFormatting(false);
    }
  };

  // 下载文书
  const handleDownloadDoc = async (format: 'pdf' | 'docx' = 'docx') => {
    if (!currentDocId) return;
    requestDocumentDownload(currentDocId, format, currentDocTitle);
  };

  // 下载证据册
  const handleDownloadEvidenceBook = () => {
    if (!id || !currentDocTitle) return;
    setPendingExport({ kind: 'evidence-book', documentTitle: currentDocTitle });
  };

  const handleExportDocumentMarkdown = async () => {
    if (!id || !generatedContent) return;
    setPendingExport({ kind: 'markdown', documentTitle: currentDocTitle || selectedTemplate?.name });
  };

  const executeExportDocumentMarkdown = async () => {
    if (!id || !generatedContent) return;

    setIsExportingMarkdown(true);
    try {
      const result = await exportCaseDocument(id, {
        document_type: currentDocTitle || selectedTemplate?.name || '法律文书',
        format: 'markdown',
        custom_content: generatedContent,
      });
      await downloadExportFile(result);
      toast.success('文书 Markdown 已导出');
    } catch (err) {
      toast.error(getRequestErrorMessage(err, '文书导出失败'));
    } finally {
      setIsExportingMarkdown(false);
    }
  };

  const recordExportReviewAudit = async (checkedItems: string[]) => {
    if (!pendingExport) return;

    const exportFormat =
      pendingExport.kind === 'download'
        ? pendingExport.format
        : pendingExport.kind === 'markdown'
          ? 'markdown'
          : 'pdf';
    const generatedDocumentId =
      pendingExport.kind === 'download'
        ? Number(pendingExport.docId)
        : currentDocId || undefined;

    await axiosInstance.post('/api/documents/export-review-audits', {
      generated_document_id: typeof generatedDocumentId === 'number' && Number.isFinite(generatedDocumentId) ? generatedDocumentId : undefined,
      case_id: id ? parseInt(id) : undefined,
      document_title: pendingExport.documentTitle || currentDocTitle || selectedTemplate?.name,
      document_type: currentDocTitle || selectedTemplate?.name,
      export_action: pendingExport.kind,
      export_format: exportFormat,
      checked_items: checkedItems,
    });
  };

  const executePendingExport = async (checkedItems: string[]) => {
    if (!pendingExport) return;

    setIsReviewExporting(true);
    try {
      await recordExportReviewAudit(checkedItems);
      const auditDocumentId = pendingExport.kind === 'download' ? pendingExport.docId : currentDocId;
      if (auditDocumentId) {
        queryClient.invalidateQueries({ queryKey: ['document-export-review-audits', auditDocumentId] });
      }

      if (pendingExport.kind === 'download') {
        const url = `/api/documents/${pendingExport.docId}/download?format=${pendingExport.format}&doc_type=generated`;
        window.open(url, '_blank');
        toast.success(`正在下载 ${pendingExport.format.toUpperCase()} 格式`);
      } else if (pendingExport.kind === 'evidence-book') {
        if (!id || !pendingExport.documentTitle) return;
        const url = `/api/evidence/export-book-for-document/${id}?document_type=${encodeURIComponent(pendingExport.documentTitle)}&format=pdf`;
        window.open(url, '_blank');
        toast.success('正在生成对应证据册...');
      } else {
        await executeExportDocumentMarkdown();
      }

      setPendingExport(null);
    } catch {
      toast.error('导出失败');
    } finally {
      setIsReviewExporting(false);
    }
  };

  // 重新起草（基于当前文书，保留历史修改）
  const handleRegenerate = async () => {
    if (!currentDocId || !id) {
      // 无当前文书，直接新建
      setGeneratedContent('');
      setCurrentDocId(null);
      setChatMessages([]);
      setIsConfirmed(false);
      setViewMode('generate');
      return;
    }

    // 基于当前文书重新起草，保留历史修改
    setIsGenerating(true);
    try {
      const res = await axiosInstance.post('/api/smart-chat/generate-document', {
        case_id: parseInt(id),
        document_type: documentTypeFromTitle(currentDocTitle) || '起诉状',
        custom_requirements: '请在原文书基础上修改，不要改变原有的正确内容',
        based_on_document_id: currentDocId,
      });

      const docData = res.data;
      setGeneratedContent(docData.content);
      setCurrentDocId(docData.document_id);
      setCurrentDocTitle(currentDocTitle);
      setIsConfirmed(false);

      setChatMessages([
        {
          role: 'assistant',
          content: `已基于历史修改重新起草文书草稿！\n\n之前的修改意见已被保留，请在当前基础上继续核验修改。`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      toast.error('重新起草失败');
    } finally {
      setIsGenerating(false);
    }
  };

  // 从标题提取文书类型
  const documentTypeFromTitle = (title: string): string => {
    const types = ['起诉状', '答辩状', '律师函', '催告函', '上诉状', '代理词', '证据清单'];
    for (const t of types) {
      if (title.includes(t)) return t;
    }
    return '起诉状';
  };

  const getPendingExportLabel = () => {
    if (!pendingExport) return '导出文书';
    if (pendingExport.kind === 'markdown') return '导出 Markdown';
    if (pendingExport.kind === 'evidence-book') return '下载证据册';
    return pendingExport.format === 'pdf' ? '下载 PDF' : '下载 Word';
  };

  const renderExportReviewDialog = () => (
    <DocumentExportReviewDialog
      open={!!pendingExport}
      documentTitle={pendingExport?.documentTitle || currentDocTitle || selectedTemplate?.name}
      exportLabel={getPendingExportLabel()}
      isLoading={isReviewExporting || isExportingMarkdown}
      onOpenChange={(open) => {
        if (!open && !isReviewExporting && !isExportingMarkdown) {
          setPendingExport(null);
        }
      }}
      onConfirm={executePendingExport}
    />
  );

  if (loadingTemplates) return <PageSkeleton />;

  // ==================== 模板选择视图 ====================
  if (viewMode === 'select') {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-bold">文书草稿</h2>
          <p className="text-sm text-muted-foreground">选择文书类型，系统将基于案件信息起草待核验文书草稿</p>
        </div>

        <Tabs defaultValue="templates" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="templates" className="flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              新建文书
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              历史文书 ({documents?.length || 0})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="templates" className="space-y-6 mt-6">
            {/* 快捷入口 */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {(templates || []).slice(0, 4).map((t) => (
                <Card
                  key={t.type}
                  className="cursor-pointer transition-all hover:shadow-md hover:border-primary"
                  onClick={() => handleSelectTemplate(t)}
                >
                  <CardContent className="pt-6">
                    <FileText className="mb-2 h-8 w-8 text-primary" />
                    <h3 className="font-medium">{t.name}</h3>
                    <p className="mt-1 text-xs text-muted-foreground">{t.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* 全部模板 */}
            <div>
              <h3 className="mb-3 text-sm font-medium text-muted-foreground">全部文书类型 ({(templates || []).length})</h3>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {(templates || []).map((t) => (
                  <Card
                    key={t.type}
                    className="cursor-pointer transition-all hover:shadow-md hover:border-primary"
                    onClick={() => handleSelectTemplate(t)}
                  >
                    <CardContent className="flex items-start gap-3 p-4">
                      <div className="mt-0.5 rounded bg-primary/10 p-1.5">
                        <FileText className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium">{t.name}</h4>
                          <Badge variant="outline" className="text-xs">{t.type}</Badge>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">{t.description}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="history" className="mt-6">
            <HistoryDocumentList
              documents={(documents || []) as HistoryDocument[]}
              onViewDocument={handleViewDocument}
              onDownloadDocx={handleDownloadDocx}
              onDownloadPdf={handleDownloadPdf}
              onDeleteDocument={handleDeleteDocument}
              isLoading={isLoadingDocs}
            />
          </TabsContent>
        </Tabs>

        {/* 历史文书预览弹窗 */}
        {previewDocument && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-background rounded-lg shadow-lg w-full max-w-4xl max-h-[90vh] flex flex-col">
              <div className="flex items-center justify-between p-4 border-b">
                <div>
                  <h3 className="text-lg font-bold">{previewDocument.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {previewDocument.document_type} · v{previewDocument.version}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleDownloadDocx(previewDocument.id)}>
                    <Download className="h-4 w-4 mr-1" />
                    Word
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => handleDownloadPdf(previewDocument.id)}>
                    <FileDown className="h-4 w-4 mr-1" />
                    PDF
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => setPreviewDocument(null)}>
                    <X className="h-5 w-5" />
                  </Button>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  <MarkdownContent content={previewDocument.content} />
                </div>
                <div className="mt-4">
                  <DocumentExportAuditHistory documentId={previewDocument.id} compact />
                </div>
              </div>
              <div className="p-4 border-t flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setGeneratedContent(previewDocument.content);
                    setCurrentDocId(parseInt(previewDocument.id));
                    setCurrentDocTitle(previewDocument.title);
                    setViewMode('chat');
                    setChatMessages([{
                      role: 'assistant',
                      content: `已打开《${previewDocument.title}》。您可以告诉我需要修改或补充的内容。`,
                      timestamp: new Date().toISOString(),
                    }]);
                    setPreviewDocument(null);
                  }}
                >
                  <Edit3 className="h-4 w-4 mr-1" />
                  继续编辑
                </Button>
                <Button onClick={() => {
                  setGeneratedContent(previewDocument.content);
                  setCurrentDocId(parseInt(previewDocument.id));
                  setCurrentDocTitle(previewDocument.title);
                  setIsConfirmed(true);
                  setViewMode('result');
                  setPreviewDocument(null);
                }}>
                  <Eye className="h-4 w-4 mr-1" />
                  查看/下载
                </Button>
              </div>
            </div>
          </div>
        )}
        {renderExportReviewDialog()}
      </div>
    );
  }

  // ==================== 要求填写视图 ====================
  if (viewMode === 'generate' && selectedTemplate) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => setViewMode('select')}>
            <ArrowLeft className="mr-1 h-4 w-4" />
            返回选择
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              生成 {selectedTemplate.name}
            </CardTitle>
            <CardDescription>{selectedTemplate.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium">您的要求（可选）</label>
              <Textarea
                value={userRequirements}
                onChange={(e) => setUserRequirements(e.target.value)}
                placeholder={`例如：\n- 强调对方违约事实，引用民法典第577条\n- 要求赔偿损失及利息\n- 重点说明证据1、3、5的关联性\n- 语气要强硬/温和`}
                rows={6}
                className="font-mono text-sm"
              />
            </div>
            <Button
              onClick={handleStartGenerate}
              disabled={isGenerating}
              className="w-full"
            >
              {isGenerating ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />正在起草文书草稿...</>
              ) : (
                <><Sparkles className="mr-2 h-4 w-4" />开始起草草稿</>
              )}
            </Button>
            <p className="text-xs text-muted-foreground">
              系统将基于案件全部证据起草文书草稿，并在草稿中标注证据序号；提交或对外发送前请逐项核验。
            </p>
          </CardContent>
        </Card>
        {renderExportReviewDialog()}
      </div>
    );
  }

  // ==================== 对话修改视图 ====================
  if (viewMode === 'chat') {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => setViewMode('select')}>
              <ArrowLeft className="mr-1 h-4 w-4" />
              返回列表
            </Button>
            <div>
              <h2 className="text-lg font-bold">{currentDocTitle}</h2>
              <p className="text-sm text-muted-foreground">与 AI 对话修改文书内容</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRegenerate}>
              <RotateCcw className="mr-1 h-4 w-4" />
              重新起草草稿
            </Button>
            {!isConfirmed ? (
              <Button
                size="sm"
                onClick={handleConfirmAndFormat}
                disabled={isAutoFormatting}
              >
                {isAutoFormatting ? (
                  <><Loader2 className="mr-1 h-4 w-4 animate-spin" />排版中...</>
                ) : (
                  <><Check className="mr-1 h-4 w-4" />确认并排版</>
                )}
              </Button>
            ) : (
              <div className="flex items-center gap-2">
                <Badge className="bg-green-500">已确认</Badge>
                <Button size="sm" onClick={() => handleDownloadDoc('docx')}>
                  <Download className="mr-1 h-4 w-4" />Word
                </Button>
                <Button size="sm" onClick={() => handleDownloadDoc('pdf')}>
                  <FileDown className="mr-1 h-4 w-4" />PDF
                </Button>
                <Button size="sm" variant="outline" onClick={handleDownloadEvidenceBook}>
                  <FileText className="mr-1 h-4 w-4" />证据册
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleExportDocumentMarkdown}
                  disabled={isExportingMarkdown}
                >
                  {isExportingMarkdown ? (
                    <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="mr-1 h-4 w-4" />
                  )}
                  Markdown
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          {/* 文书内容 */}
          <div className="lg:col-span-2">
            <Card className="h-[calc(100vh-200px)] flex flex-col">
              <CardHeader className="pb-3 flex-shrink-0">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <FileText className="h-5 w-5 text-primary" />
                  文书内容
                  {isConfirmed && (
                    <Badge className="bg-green-500">已确认</Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto p-6">
                {generatedContent ? (
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    <MarkdownContent content={generatedContent} />
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    <Loader2 className="h-6 w-6 animate-spin mr-2" />
                    正在起草文书草稿...
                  </div>
                )}
              </CardContent>
            </Card>
            <div className="mt-4">
              <DocumentExportAuditHistory documentId={currentDocId} compact />
            </div>
          </div>

          {/* AI 对话 */}
          <div className="lg:col-span-1">
            <Card className="h-[calc(100vh-200px)] flex flex-col">
              <CardHeader className="pb-3 flex-shrink-0">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <MessageSquare className="h-5 w-5 text-primary" />
                  AI 修改文书
                </CardTitle>
                <CardDescription>告诉 AI 需要修改或补充的内容</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 overflow-hidden flex flex-col p-0">
                {/* 聊天消息列表 */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {chatMessages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[90%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                        msg.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'
                      }`}>
                        {msg.content}
                      </div>
                    </div>
                  ))}
                  {isChatLoading && (
                    <div className="flex justify-start">
                      <div className="bg-muted rounded-lg px-3 py-2 text-sm flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        AI 正在修改...
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* 输入框 */}
                <div className="border-t p-3">
                  <div className="flex gap-2">
                    <Input
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder="例如：强调对方违约事实、补充利息计算..."
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      disabled={isChatLoading}
                      className="flex-1"
                    />
                    <Button
                      size="sm"
                      onClick={handleSendMessage}
                      disabled={isChatLoading || !chatInput.trim()}
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
        {renderExportReviewDialog()}
      </div>
    );
  }

  // ==================== 确认下载视图 ====================
  if (viewMode === 'result') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={() => setViewMode('select')}>
              <ArrowLeft className="mr-1 h-4 w-4" />
              返回列表
            </Button>
            <div>
              <h2 className="text-xl font-bold">{currentDocTitle}</h2>
              <p className="text-sm text-muted-foreground">文书已确认，可下载</p>
            </div>
          </div>
        </div>

        {/* 下载卡片 */}
        <Card className="border-green-200 bg-green-50/30">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="h-6 w-6 text-green-600" />
              <div>
                <h3 className="font-bold text-lg">《{currentDocTitle}》已准备就绪</h3>
                <p className="text-sm text-muted-foreground">文书已自动排版，可随时下载</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button onClick={() => handleDownloadDoc('docx')}>
                <Download className="mr-2 h-4 w-4" />
                下载 Word
              </Button>
              <Button onClick={() => handleDownloadDoc('pdf')}>
                <FileDown className="mr-2 h-4 w-4" />
                下载 PDF
              </Button>
              <Button variant="outline" onClick={handleDownloadEvidenceBook}>
                <FileText className="mr-2 h-4 w-4" />
                下载对应证据册
              </Button>
              <Button
                variant="outline"
                onClick={handleExportDocumentMarkdown}
                disabled={isExportingMarkdown}
              >
                {isExportingMarkdown ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Download className="mr-2 h-4 w-4" />
                )}
                导出 Markdown
              </Button>
              <Button variant="outline" onClick={() => {
                setViewMode('chat');
                setIsConfirmed(false);
              }}>
                <RotateCcw className="mr-2 h-4 w-4" />
                继续修改
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 文书预览 */}
        <Card>
          <CardHeader>
            <CardTitle>文书预览</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="whitespace-pre-wrap text-sm leading-relaxed max-h-[60vh] overflow-y-auto">
              <MarkdownContent content={generatedContent} />
            </div>
          </CardContent>
        </Card>
        <DocumentExportAuditHistory documentId={currentDocId} />
        {renderExportReviewDialog()}
      </div>
    );
  }

  return null;
}

function getRequestErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    return response?.data?.detail || fallback;
  }
  return fallback;
}
