import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axiosInstance from '@/api/client';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { PageSkeleton } from '@/components/common/loading-skeleton';
import { MarkdownContent } from '@/components/common/markdown-content';
import { CaseClaims, type CaseClaim } from '@/components/case/CaseClaims';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import {
  FileText, Download, FileDown, CheckCircle, ArrowLeft,
  Edit3, Save, X, Sparkles
} from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  message_type?: 'greeting' | 'inquiry' | 'document' | 'case_analysis';
  generated_document?: {
    id: number;
    type: string;
    content: string;
    download_url: string;
    evidence_count: number;
    is_confirmed?: boolean;
  };
  suggested_claims?: Array<{
    title: string;
    description: string;
    claim_type: string;
    amount: string;
  }>;
}

interface SuggestedClaim {
  title: string;
  description?: string;
  claim_type?: string;
  amount?: string;
  priority?: number;
}

interface GeneratedDocumentRecord {
  id: number;
  title?: string;
  document_type?: string;
  type?: string;
  content?: string;
  evidence_count?: number;
  created_at?: string;
}

export default function DocumentChatPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [selectedClaimId] = useState<string | null>(null);
  const [editingDocId, setEditingDocId] = useState<number | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [showClaimDialog, setShowClaimDialog] = useState(false);
  const [pendingClaims, setPendingClaims] = useState<SuggestedClaim[]>([]);
  const [hasAnalyzedCase, setHasAnalyzedCase] = useState(false);

  const id = caseId;

  // 获取案件信息
  const { data: caseInfo } = useQuery({
    queryKey: ['case', id],
    queryFn: async () => {
      if (!id) return null;
      const res = await axiosInstance.get(`/api/cases/${id}`);
      return res.data;
    },
    enabled: !!id,
  });

  // 加载历史对话（从smart-chat的analysis结果中获取）
  const { data: conversationHistory } = useQuery({
    queryKey: ['smart-chat-analyses', id],
    queryFn: async () => {
      if (!id) return [];
      const res = await axiosInstance.get(`/api/smart-chat/analyses/${id}`);
      return res.data || [];
    },
    enabled: !!id,
  });

  // 历史对话转为聊天消息
  useEffect(() => {
    if (conversationHistory && conversationHistory.length > 0) {
      const historyMessages: ChatMessage[] = [];
      for (const analysis of conversationHistory) {
        // 添加用户输入（fact_description 或 content的前半部分）
        const userContent = analysis.fact_description || '';
        if (userContent) {
          historyMessages.push({
            role: 'user',
            content: userContent,
            timestamp: analysis.created_at || new Date().toISOString(),
            message_type: 'inquiry',
          });
        }
        // 添加AI回复（content 是完整分析结果）
        const aiContent = analysis.content || '';
        if (aiContent) {
          historyMessages.push({
            role: 'assistant',
            content: aiContent,
            timestamp: analysis.created_at || new Date().toISOString(),
            message_type: 'case_analysis',
          });
        }
      }
      if (historyMessages.length > 0) {
        setChatMessages(prev => {
          if (prev.length <= 1) {
            return [...historyMessages, ...prev];
          }
          return prev;
        });
      }
    }
  }, [conversationHistory]);

  // 获取战役列表
  const { data: claims, refetch: refetchClaims } = useQuery({
    queryKey: ['claims', id],
    queryFn: async () => {
      if (!id) return [];
      const res = await axiosInstance.get<CaseClaim[]>(`/api/claims/case/${id}`);
      return res.data || [];
    },
    enabled: !!id,
  });

  // 获取已生成文书
  const { refetch: refetchDocs } = useQuery({
    queryKey: ['documents', id],
    queryFn: async () => {
      if (!id) return [];
      const res = await axiosInstance.get<GeneratedDocumentRecord[]>(`/api/document-management/case/${id}/generated`);
      return (res.data || []).map((d) => ({
        id: d.id,
        title: d.title || '',
        type: d.document_type || d.type || '',
        content: d.content || '',
        evidence_count: d.evidence_count || 0,
        created_at: d.created_at || '',
      }));
    },
    enabled: !!id,
  });

  // 欢迎消息（仅在无历史对话时显示）
  useEffect(() => {
    if (id && caseInfo && chatMessages.length === 0 && (!conversationHistory || conversationHistory.length === 0)) {
      const caseTitle = caseInfo.title || '案件';
      const plaintiff = (typeof caseInfo.plaintiff === 'object' && caseInfo.plaintiff !== null) 
        ? JSON.stringify(caseInfo.plaintiff) 
        : (caseInfo.plaintiff || '我方');
      const defendant = (typeof caseInfo.defendant === 'object' && caseInfo.defendant !== null)
        ? JSON.stringify(caseInfo.defendant)
        : (caseInfo.defendant || '对方');
      const claimAmount = caseInfo.claim_amount || '未明确';
      
      setChatMessages([{
        role: 'assistant',
        content: `您好！我是您的法律文书助手。\n\n我现在为您分析的是【${caseTitle}】案件：\n- 原告：${plaintiff}\n- 被告：${defendant}\n- 诉讼金额：${claimAmount}\n\n在生成文书之前，我需要先深入了解案情。请您告诉我：\n1. 案件的详细情况\n2. 您的诉求是什么（如：要求对方还款、支付违约金、赔偿损失等）\n3. 是否有关键证据需要特别说明\n\n请畅所欲言，我会认真分析并为您规划诉讼策略。`,
        timestamp: new Date().toISOString(),
        message_type: 'greeting',
      }]);
    }
  }, [id, caseInfo, conversationHistory, chatMessages.length]);

  // 发送消息
  const handleSendMessage = async () => {
    if (!chatInput.trim() || !id) return;

    const userMsg: ChatMessage = {
      role: 'user',
      content: chatInput,
      timestamp: new Date().toISOString(),
    };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setIsChatLoading(true);

    const inputText = chatInput;

    try {
      // 调用AI分析
      const res = await axiosInstance.post('/api/smart-chat/case-analysis', {
        case_id: parseInt(id),
        user_message: inputText,
        chat_history: chatMessages.map(m => ({ role: m.role, content: m.content })),
      });

      const analysisData = res.data;

      if (analysisData.analysis_type === 'case_analysis' && analysisData.suggested_claims) {
        // 首次分析案情，返回战役建议
        setHasAnalyzedCase(true);
        setPendingClaims(analysisData.suggested_claims || []);
        setShowClaimDialog(true);

        const aiMsg: ChatMessage = {
          role: 'assistant',
          content: analysisData.response || '我已经分析了您的案情，以下是我为您识别出的诉讼战役（诉求）：',
          timestamp: new Date().toISOString(),
          message_type: 'case_analysis',
          suggested_claims: analysisData.suggested_claims,
        };
        setChatMessages(prev => [...prev, aiMsg]);
      } else if (analysisData.analysis_type === 'document_request') {
        // 用户要求生成文书
        const docType = analysisData.document_type || '法律文书';
        
        // 如果还没有战役，先分析
        if (!claims || claims.length === 0) {
          setChatMessages(prev => [...prev, {
            role: 'assistant',
            content: '在生成文书之前，我需要先了解您的案情。请先告诉我您的诉求和案件情况。',
            timestamp: new Date().toISOString(),
          }]);
          setIsChatLoading(false);
          return;
        }

        const docRes = await axiosInstance.post('/api/smart-chat/generate-document', {
          case_id: parseInt(id),
          document_type: docType,
          claim_id: selectedClaimId ? parseInt(selectedClaimId) : null,
          custom_requirements: inputText,
        });

        const docData = docRes.data;
        const aiMsg: ChatMessage = {
          role: 'assistant',
          content: `《${docType}》已生成完成！\n\n基于 ${docData.claim_title ? `战役【${docData.claim_title}】相关` : '案件全部'} ${docData.evidence_count || 0} 份证据生成。\n\n您可以编辑内容后保存，或直接下载使用。`,
          timestamp: new Date().toISOString(),
          message_type: 'document',
          generated_document: {
            id: docData.document_id,
            type: docType,
            content: docData.content,
            download_url: docData.download_url,
            evidence_count: docData.evidence_count,
            is_confirmed: false,
          },
        };
        setChatMessages(prev => [...prev, aiMsg]);
        refetchDocs();
      } else {
        // 普通对话回复
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: analysisData.response || '收到您的信息。',
          timestamp: new Date().toISOString(),
        }]);
      }
    } catch (error) {
      const message = getRequestErrorMessage(error, '请求失败');
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: `抱歉，${message}，请重试。`,
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // 确认战役
  const handleConfirmClaims = async () => {
    try {
      for (const claim of pendingClaims) {
        await axiosInstance.post('/api/claims', {
          case_id: parseInt(id!),
          title: claim.title,
          description: claim.description,
          claim_type: claim.claim_type,
          amount: claim.amount,
          priority: claim.priority || 3,
        });
      }
      toast.success(`已创建 ${pendingClaims.length} 个战役`);
      refetchClaims();
      setShowClaimDialog(false);
      setPendingClaims([]);
    } catch {
      toast.error('创建战役失败');
    }
  };

  // 保存文书编辑
  const handleSaveEdit = async () => {
    if (!editingDocId || !editingContent) return;
    try {
      await axiosInstance.put(`/api/document-management/generated/${editingDocId}`, {
        content: editingContent,
      });
      toast.success('文书内容已保存');
      setEditingDocId(null);
      refetchDocs();
    } catch (error) {
      toast.error(getRequestErrorMessage(error, '保存失败'));
    }
  };

  // 开始编辑文书
  const handleStartEdit = (doc: { id: number; content: string }) => {
    setEditingDocId(doc.id);
    setEditingContent(doc.content);
  };

  // 下载文书
  const handleDownloadDoc = async (docId: number, format: string, filename: string) => {
    if (!id) return;
    try {
      toast.loading('正在下载...', { id: 'doc-download' });
      const response = await axiosInstance.get(
        `/api/documents/${docId}/download?doc_type=generated&format=${format}`,
        { responseType: 'blob' }
      );
      const blob = new Blob([response.data], { 
        type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success(`${format.toUpperCase()} 下载成功`, { id: 'doc-download' });
    } catch (error) {
      toast.error(getRequestErrorMessage(error, '下载失败'), { id: 'doc-download' });
    }
  };

  // 下载证据册
  const handleDownloadEvidenceBook = async (docType: string) => {
    if (!id) return;
    try {
      toast.loading('正在生成证据册...', { id: 'evidence-book' });
      const response = await axiosInstance.get(
        `/api/evidence/export-book-for-document/${id}?document_type=${encodeURIComponent(docType)}&format=pdf`,
        { responseType: 'blob' }
      );
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${docType}_证据册.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success('证据册下载成功', { id: 'evidence-book' });
    } catch (error) {
      toast.error(getRequestErrorMessage(error, '生成失败'), { id: 'evidence-book' });
    }
  };

  if (!id) return <PageSkeleton />;

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* 主内容区 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 左侧：战役列表 */}
        <div className="w-80 border-r p-4 overflow-y-auto">
          <Button variant="ghost" className="mb-4" onClick={() => navigate(`/cases/${id}`)}>
            <ArrowLeft className="mr-2 h-4 w-4" />返回案件
          </Button>
          <CaseClaims caseId={parseInt(id)} />
        </div>

        {/* 右侧：文书对话 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* 聊天消息 */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.map((msg, idx) => (
              <Card key={idx} className={msg.role === 'user' ? 'bg-blue-50 dark:bg-blue-950' : ''}>
                <CardContent className="p-3">
                  <div className="flex items-start gap-2">
                    {msg.role === 'assistant' ? (
                      msg.message_type === 'case_analysis' ? (
                        <Sparkles className="h-4 w-4 mt-0.5 flex-shrink-0 text-purple-500" />
                      ) : (
                        <FileText className="h-4 w-4 mt-0.5 flex-shrink-0 text-primary" />
                      )
                    ) : (
                      <div className="h-4 w-4 mt-0.5 flex-shrink-0 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs">我</div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm whitespace-pre-wrap">
                        {msg.generated_document ? (
                          <div>
                            <p className="mb-2">{msg.content}</p>
                            <Card className="mt-3 border-green-200 bg-green-50/30">
                              <CardContent className="p-4">
                                <div className="flex items-center gap-2 mb-3">
                                  <CheckCircle className="h-4 w-4 text-green-600" />
                                  <p className="text-sm font-medium text-green-700">
                                    《{msg.generated_document.type}》
                                  </p>
                                  <Badge variant="outline" className="text-xs">
                                    基于 {msg.generated_document.evidence_count} 份证据
                                  </Badge>
                                </div>

                                {editingDocId === msg.generated_document?.id ? (
                                  <div className="space-y-2">
                                    <Textarea
                                      value={editingContent}
                                      onChange={(e) => setEditingContent(e.target.value)}
                                      className="min-h-[300px] font-mono text-sm"
                                      rows={20}
                                    />
                                    <div className="flex gap-2">
                                      <Button size="sm" onClick={handleSaveEdit}>
                                        <Save className="mr-1 h-4 w-4" />保存修改
                                      </Button>
                                      <Button size="sm" variant="outline" onClick={() => setEditingDocId(null)}>
                                        <X className="mr-1 h-4 w-4" />取消
                                      </Button>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="mb-3 p-3 bg-white dark:bg-slate-900 rounded border border-green-100 dark:border-green-900 max-h-96 overflow-y-auto">
                                    <MarkdownContent content={msg.generated_document.content} />
                                  </div>
                                )}

                                <div className="flex flex-wrap gap-2 mt-3">
                                  <Button size="sm" variant="outline" onClick={() => handleStartEdit(msg.generated_document!)}>
                                    <Edit3 className="mr-1 h-3.5 w-3.5" />编辑
                                  </Button>
                                  <Button size="sm" onClick={() => handleDownloadDoc(msg.generated_document!.id, 'docx', `${msg.generated_document!.type}.docx`)}>
                                    <Download className="mr-1 h-3.5 w-3.5" />Word
                                  </Button>
                                  <Button size="sm" variant="outline" onClick={() => handleDownloadDoc(msg.generated_document!.id, 'pdf', `${msg.generated_document!.type}.pdf`)}>
                                    <FileDown className="mr-1 h-3.5 w-3.5" />PDF
                                  </Button>
                                  <Button size="sm" variant="ghost" onClick={() => handleDownloadEvidenceBook(msg.generated_document!.type)}>
                                    <FileText className="mr-1 h-3.5 w-3.5" />证据册
                                  </Button>
                                </div>
                              </CardContent>
                            </Card>
                          </div>
                        ) : (
                          <MarkdownContent content={msg.content} />
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            {isChatLoading && (
              <div className="flex justify-start">
                <Card className="border-primary/20 bg-primary/5">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="animate-pulse text-primary">AI 正在分析...</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* 输入框 */}
          <div className="border-t p-4 bg-background">
            <div className="flex gap-2 max-w-4xl mx-auto">
              <Textarea
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder={hasAnalyzedCase ? "请告诉我需要生成什么文书..." : "请描述案件情况、您的诉求..."}
                className="flex-1"
                rows={2}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
              <Button onClick={handleSendMessage} disabled={isChatLoading || !chatInput.trim()} className="self-end">
                发送
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* 战役确认对话框 */}
      <Dialog open={showClaimDialog} onOpenChange={setShowClaimDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-500" />
              战役规划确认
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-sm text-muted-foreground">
              根据您描述的案情，AI 为您识别出以下战役（诉讼请求）：
            </p>
            {pendingClaims.map((claim, idx) => (
              <Card key={idx} className="border-purple-200">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="flex-1">
                      <h4 className="font-medium">{claim.title}</h4>
                      {claim.description && (
                        <p className="text-sm text-muted-foreground mt-1">{claim.description}</p>
                      )}
                      <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                        {claim.claim_type && <span>类型: {claim.claim_type}</span>}
                        {claim.amount && <span>金额: {claim.amount}</span>}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowClaimDialog(false)}>
              取消
            </Button>
            <Button onClick={handleConfirmClaims}>
              确认创建战役
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function getRequestErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { detail?: string } } }).response;
    if (response?.data?.detail) {
      return response.data.detail;
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}
