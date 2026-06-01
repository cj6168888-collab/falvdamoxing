import { useState, useRef, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import axiosInstance from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { MessageBubble, type SuggestionData } from '@/components/smart-chat/message-bubble';
import { EvidencePanel } from '@/components/smart-chat/evidence-panel';
import { LegalDisclaimer } from '@/components/common/legal-disclaimer';
import {
  Loader2, Sparkles, FileText,
  Send, Download, FileDown,
  Check, Upload, Eye,
  Shield, AlertCircle, MessageSquare, Clock, X, File,
  Briefcase, Gavel, ListChecks, Scale
} from 'lucide-react';
import { toast } from 'sonner';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  analysis_id?: number;
  suggestions?: SuggestionData;
  recommended_documents?: { type: string; reason: string; priority: string }[];
  timestamp: string;
  is_approved?: boolean;
  generated_document?: {
    id: number;
    type: string;
    content: string;
    download_url: string;
    evidence_count: number;
  };
}

interface EvidenceItem {
  id: number | string;
  display_name?: string;
  original_filename?: string;
  evidence_type?: string;
  summary?: string;
  extracted_content?: string;
  raw_content?: string;
  credibility_score?: number;
  proves_facts?: string[];
  keywords?: string[];
  evidence_review?: {
    proof_purpose?: string;
    original_status?: string;
    formed_at?: string;
    authenticity_risk?: string;
    legality_risk?: string;
    relevance_risk?: string;
    strengthening_actions?: string[];
    review_notes?: string;
    reviewed_at?: string;
  } | null;
}

interface SmartChatAnalysisRecord {
  id: number;
  content: string;
  result_data?: unknown;
  recommended_documents?: ChatMessage['recommended_documents'];
  created_at: string;
  is_approved?: boolean;
  is_deleted?: boolean;
}

interface CaseInfo {
  title: string;
  plaintiff: string;
  defendant: string;
  cause: string;
  claim_amount: string;
  evidence_count: number;
}

const ANALYSIS_STEPS = [
  '正在读取案件完整档案...',
  '正在逐一分析全部证据...',
  '正在建立证据关联网络...',
  '正在分析可主张的权利...',
  '正在计算建议金额...',
  '正在评估风险与底线...',
  '正在生成分析报告...',
];

const FOLLOWUP_STEPS = [
  '正在理解您的补充...',
  '正在结合已有分析...',
  '正在更新建议...',
  '正在生成回复...',
];

const LAWYER_PROMPT_TEMPLATES = [
  '请按律师办案口径审查本案：先列争议焦点，再逐项匹配证据，最后给出下一步取证和诉讼策略。',
  '请站在对方律师角度反驳我方主张，并指出最容易被攻击的证据和事实缺口。',
  '请基于现有证据生成一份可提交法院的证据目录草案，标明证明目的和风险提示。',
  '请判断本案是否适合先发律师函、申请财产保全或直接起诉，并说明触发条件。',
];

const ROLE_OPTIONS = [
  { value: 'plaintiff', label: '我是原告', helper: '主张权利' },
  { value: 'defendant', label: '我是被告', helper: '抗辩减损' },
  { value: 'third_party', label: '我是第三方', helper: '厘清责任' },
];

export default function SmartChatPage() {
  const params = useParams<{ caseId: string; id: string }>();
  const currentCaseId = params.caseId || params.id || '';

  // Core state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState(0);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [hasStarted, setHasStarted] = useState(false);
  const [currentSteps, setCurrentSteps] = useState<string[]>(ANALYSIS_STEPS);

  // Countdown timer state (for better UX)
  const [countdownSeconds, setCountdownSeconds] = useState(0);

  // Guide page inputs
  const [factDescription, setFactDescription] = useState('');
  const [userExpectation, setUserExpectation] = useState('');
  const [userRole, setUserRole] = useState('');

  // Chat input
  const [followUpInput, setFollowUpInput] = useState('');

  // File upload in chat
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // UI state
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(new Set());
  const [exportingId, setExportingId] = useState<number | null>(null);
  const [showExportMenu, setShowExportMenu] = useState<number | null>(null);
  const [showEvidenceDrawer, setShowEvidenceDrawer] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Case info
  const [caseInfo, setCaseInfo] = useState<CaseInfo | null>(null);
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const analysisTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const countdownTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load case info on mount
  useEffect(() => {
    if (!currentCaseId) return;
    const loadCaseInfo = async () => {
      try {
        const [caseRes, evidenceRes] = await Promise.all([
          axiosInstance.get(`/api/cases/${currentCaseId}`),
          axiosInstance.get(`/api/v2/evidence-graph/evidence/list`, { params: { case_id: parseInt(currentCaseId) } }),
        ]);
        const c = caseRes.data;
        setCaseInfo({
          title: c.title || `案件 #${currentCaseId}`,
          plaintiff: c.plaintiff || '未填写',
          defendant: c.defendant || '未填写',
          cause: c.cause || '待分析',
          claim_amount: c.claim_amount || '未填写',
          evidence_count: evidenceRes.data?.evidence_list?.length || 0,
        });
        setEvidenceList(evidenceRes.data?.evidence_list || []);

        // Load analysis history
        try {
          const historyRes = await axiosInstance.get(`/api/smart-chat/analyses/${currentCaseId}`);
          if (historyRes.data?.analyses?.length > 0) {
            const chatMsgs = historyRes.data.analyses
              .filter((a: SmartChatAnalysisRecord) => !a.is_deleted)
              .map((a: SmartChatAnalysisRecord) => ({
                id: `analysis-${a.id}`,
                role: 'assistant' as const,
                content: a.content,
                analysis_id: a.id,
                suggestions: a.result_data || undefined,
                recommended_documents: a.recommended_documents || [],
                timestamp: a.created_at,
                is_approved: a.is_approved,
              }));
            setMessages(chatMsgs);
            setHasStarted(true);
            if (chatMsgs.length > 0) {
              setExpandedMessages(new Set([chatMsgs[chatMsgs.length - 1].id]));
            }
          }
        } catch {
          // No history, normal
        }
      } catch (err) {
        console.error('[SmartChat] Failed to load case info:', err);
        setApiError('无法加载案件信息，请检查后端服务是否运行');
      }
    };
    loadCaseInfo();
  }, [currentCaseId]);

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isAnalyzing]);

  // Cleanup timers
  useEffect(() => {
    return () => {
      if (analysisTimerRef.current) clearInterval(analysisTimerRef.current);
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current);
    };
  }, []);

  // Format time helper
  const formatTime = useCallback((seconds: number) => {
    if (seconds < 60) return `${seconds}秒`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}分${secs}秒`;
  }, []);

  // Start progress simulation with countdown
  const startProgress = useCallback((steps: string[]) => {
    setCurrentSteps(steps);
    setAnalysisStep(0);
    setAnalysisProgress(0);
    setApiError(null);

    // 5 minutes countdown
    const MAX_WAIT_TIME = 300;
    setCountdownSeconds(MAX_WAIT_TIME);
    const startTs = Date.now();

    let currentStep = 0;
    const stepDuration = steps === ANALYSIS_STEPS ? 4000 : 3000;

    // Countdown timer
    countdownTimerRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTs) / 1000);
      const remaining = Math.max(0, MAX_WAIT_TIME - elapsed);
      setCountdownSeconds(remaining);
    }, 1000);

    // Progress update
    analysisTimerRef.current = setInterval(() => {
      currentStep = Math.min(currentStep + 1, steps.length - 1);
      setAnalysisStep(currentStep);
      setAnalysisProgress(Math.min(((currentStep + 1) / steps.length) * 95, 95));
    }, stepDuration);
  }, []);

  const stopProgress = useCallback(() => {
    if (analysisTimerRef.current) {
      clearInterval(analysisTimerRef.current);
      analysisTimerRef.current = null;
    }
    if (countdownTimerRef.current) {
      clearInterval(countdownTimerRef.current);
      countdownTimerRef.current = null;
    }
    setAnalysisProgress(100);
  }, []);

  // Start analysis
  const handleStartAnalysis = async () => {
    if (!factDescription.trim()) {
      toast.error('请先描述案情经过');
      return;
    }
    if (!currentCaseId) {
      toast.error('无法获取案件ID');
      return;
    }

    console.log('[SmartChat] Starting analysis for case:', currentCaseId);
    setIsAnalyzing(true);
    setHasStarted(true); // 确保进入聊天界面
    setApiError(null);
    startProgress(ANALYSIS_STEPS);

    // 设置 5 分钟超时
    const timeoutId = setTimeout(() => {
      console.error('[SmartChat] Analysis timeout after 5 minutes');
      stopProgress();
      setIsAnalyzing(false);
      setApiError('分析超时，请检查后端 LLM 服务是否正常运行');
      toast.error('分析超时，请重试');
    }, 5 * 60 * 1000);

    try {
      console.log('[SmartChat] Calling API with:', {
        case_id: parseInt(currentCaseId),
        fact_description: factDescription.substring(0, 100),
        user_expectation: userExpectation,
        user_role: userRole,
      });

      const res = await axiosInstance.post('/api/smart-chat/global-analysis', {
        case_id: parseInt(currentCaseId),
        fact_description: factDescription,
        user_expectation: userExpectation || undefined,
        user_role: userRole || undefined,
      }, {
        timeout: 300000, // 5 分钟超时
      });

      console.log('[SmartChat] API response:', res.data);

      // 清理超时
      clearTimeout(timeoutId);
      stopProgress();
      setIsAnalyzing(false);

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: factDescription,
        timestamp: new Date().toISOString(),
      };

      // 处理 API 返回的数据
      const analysisData = res.data;
      const aiMsg: ChatMessage = {
        id: `analysis-${analysisData.analysis_id || Date.now()}`,
        role: 'assistant',
        content: analysisData.full_analysis || analysisData.content || analysisData.result || '分析完成，请查看详细建议',
        analysis_id: analysisData.analysis_id,
        suggestions: analysisData.suggestions || analysisData.result_data,
        recommended_documents: analysisData.suggestions?.recommended_documents || analysisData.recommended_documents || [],
        timestamp: new Date().toISOString(),
      };

      setMessages(prev => [...prev, userMsg, aiMsg]);
      setExpandedMessages(new Set([aiMsg.id]));
      setFactDescription('');
      setUserExpectation('');
      toast.success('案情分析完成');

      // Refresh evidence
      try {
        const evRes = await axiosInstance.get(`/api/v2/evidence-graph/evidence/list`, { params: { case_id: parseInt(currentCaseId) } });
        setEvidenceList(evRes.data?.evidence_list || []);
        setCaseInfo(prev => prev ? { ...prev, evidence_count: evRes.data?.evidence_list?.length || 0 } : null);
      } catch {
        // ignore
      }
    } catch (err) {
      clearTimeout(timeoutId);
      stopProgress();
      setIsAnalyzing(false);
      const statusCode = getResponseStatus(err);
      let errorMsg = getRequestErrorMessage(err, '未知错误');
      if (statusCode === 404) {
        errorMsg = '后端 API 未找到，请检查后端服务是否运行';
      } else if (statusCode === 500) {
        errorMsg = '后端服务器错误，请检查 LLM 服务配置';
      } else if (statusCode === 503) {
        errorMsg = 'AI 服务暂时不可用，请稍后重试';
      }
      console.error('[SmartChat] Analysis failed:', err);
      setApiError('分析失败：' + errorMsg);
      toast.error(errorMsg);
    }
  };

  // Follow-up
  const handleFollowUp = async () => {
    console.log('[SmartChat] handleFollowUp called', { followUpInput: followUpInput.trim(), uploadedFilesCount: uploadedFiles.length, currentCaseId, isAnalyzing, isUploading });
    if (!followUpInput.trim() && uploadedFiles.length === 0) {
      toast.error('请输入文字或上传文件');
      return;
    }
    if (!currentCaseId) {
      console.log('[SmartChat] No case ID, returning');
      return;
    }
    
    // 如果有上传的文件，先处理文件
    if (uploadedFiles.length > 0) {
      console.log('[SmartChat] Has files, calling handleUploadFile');
      await handleUploadFile();
      return;
    }
    
    // 检查是否是要生成文书
    const input = followUpInput.trim();
    const docTypes = ['起诉状', '答辩状', '代理词', '申请书', '劳动仲裁申请书', '民事起诉状', '行政起诉状', '证据目录', '财产保全', '先予执行', '管辖异议', '反诉状', '上诉状', '再审申请书', '执行异议', '保全担保'];
    const matchedDocType = docTypes.find(dt => input.includes(dt));
    
    // 如果匹配到文书类型，直接生成
    if (matchedDocType) {
      setFollowUpInput('');  // 清空输入框
      await handleGenerateDoc(matchedDocType);
      return;
    }

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: followUpInput,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setFollowUpInput('');
    setIsAnalyzing(true);
    setApiError(null);
    startProgress(FOLLOWUP_STEPS);
    console.log('[SmartChat] Sending follow-up request:', { case_id: currentCaseId, message: followUpInput });

    try {
      const res = await axiosInstance.post('/api/smart-chat/follow-up', {
        case_id: parseInt(currentCaseId),
        message: followUpInput,
      });
      console.log('[SmartChat] Follow-up response:', res.data);
      stopProgress();
      const aiMsg: ChatMessage = {
        id: `analysis-${res.data.analysis_id}`,
        role: 'assistant',
        content: res.data.content,
        analysis_id: res.data.analysis_id,
        suggestions: res.data.suggestions,
        recommended_documents: res.data.suggestions?.recommended_documents || [],
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, aiMsg]);
      setExpandedMessages(prev => new Set(prev).add(aiMsg.id));
    } catch (err) {
      stopProgress();
      console.error('[SmartChat] Follow-up error:', err);
      const statusCode = getResponseStatus(err);
      let errorMsg = getRequestErrorMessage(err, '未知错误');
      if (statusCode === 404) errorMsg = '后端 API 未找到';
      else if (statusCode === 503) errorMsg = 'AI 服务暂时不可用，请稍后重试';
      setApiError('分析失败：' + errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Approve
  const handleApprove = async (analysisId: number) => {
    try {
      await axiosInstance.post(`/api/smart-chat/approve?analysis_id=${analysisId}&set_as_main_context=true`);
      setMessages(prev => prev.map(m => m.analysis_id === analysisId ? { ...m, is_approved: true } : m));
      toast.success('已认可该分析结果');
    } catch {
      toast.error('操作失败');
    }
  };

  // Delete
  const handleDelete = async (analysisId: number) => {
    try {
      await axiosInstance.post(`/api/smart-chat/delete?analysis_id=${analysisId}`);
      setMessages(prev => prev.filter(m => m.analysis_id !== analysisId));
      toast.success('已删除');
    } catch {
      toast.error('操作失败');
    }
  };

  // Handle file upload in chat
  const handleUploadFile = async () => {
    if (uploadedFiles.length === 0 || !currentCaseId) return;
    
    setIsUploading(true);
    
    try {
      // Upload each file
      for (const file of uploadedFiles) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('case_id', String(parseInt(currentCaseId)));
        formData.append('user_message', followUpInput.trim() || `请分析这份${file.name}文件的内容，结合案件已有证据判断其证明力和关联性`);
        
        console.log('[SmartChat] Uploading file:', file.name, 'case_id:', currentCaseId);
        const res = await axiosInstance.post('/api/smart-chat/upload-analysis', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        console.log('[SmartChat] Upload response:', res.data);
        
        const userMsg: ChatMessage = {
          id: `user-${Date.now()}-${file.name}`,
          role: 'user',
          content: followUpInput.trim() ? followUpInput : `[上传文件: ${file.name}]`,
          timestamp: new Date().toISOString(),
        };
        
        const aiMsg: ChatMessage = {
          id: `analysis-${res.data.analysis_id || Date.now()}-${file.name}`,
          role: 'assistant',
          content: res.data.content || res.data.full_analysis || '文件分析完成',
          analysis_id: res.data.analysis_id,
          suggestions: res.data.suggestions,
          timestamp: new Date().toISOString(),
        };
        
        setMessages(prev => [...prev, userMsg, aiMsg]);
        setExpandedMessages(prev => new Set(prev).add(aiMsg.id));
      }
      
      setFollowUpInput('');
      setUploadedFiles([]);
      toast.success(`已分析 ${uploadedFiles.length} 个文件并加入证据库`);
      
      // Refresh evidence list
      const evRes = await axiosInstance.get(`/api/v2/evidence-graph/evidence/list`, { params: { case_id: parseInt(currentCaseId) } });
      setEvidenceList(evRes.data?.evidence_list || []);
    } catch (err) {
      console.error('[SmartChat] File upload analysis failed:', err);
      console.error('[SmartChat] Error response:', getResponseData(err));
      console.error('[SmartChat] Error status:', getResponseStatus(err));
      setFollowUpInput('');
      setUploadedFiles([]);
      toast.error(getRequestErrorMessage(err, '文件分析失败，请重试'));
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const newFiles = Array.from(files);
      setUploadedFiles(prev => [...prev, ...newFiles]);
      e.target.value = '';
    }
  };

  const removeUploadedFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Retry
  const handleRetry = (msg: ChatMessage) => {
    const msgIndex = messages.findIndex(m => m.id === msg.id);
    const contextMessages = messages.slice(0, msgIndex);
    const userMsg = contextMessages.filter(m => m.role === 'user').pop();
    if (userMsg) {
      setFollowUpInput(`请重新分析：${userMsg.content}`);
      setTimeout(() => {
        const contextText = contextMessages
          .filter(m => m.role === 'assistant' && m.analysis_id)
          .map(m => `--- 分析 ${m.analysis_id} ---\n${m.content.substring(0, 2000)}`)
          .join('\n\n');
        handleFollowUpWithContext(`请基于以下已有分析，重新回答：\n\n用户问题：${userMsg.content}\n\n已有分析：\n${contextText}`);
      }, 100);
    }
  };

  const handleFollowUpWithContext = async (message: string) => {
    if (!currentCaseId) return;
    setIsAnalyzing(true);
    setApiError(null);
    startProgress(FOLLOWUP_STEPS);
    try {
      const res = await axiosInstance.post('/api/smart-chat/follow-up', {
        case_id: parseInt(currentCaseId),
        message,
      });
      stopProgress();
      const aiMsg: ChatMessage = {
        id: `analysis-${res.data.analysis_id}`,
        role: 'assistant',
        content: res.data.content,
        analysis_id: res.data.analysis_id,
        suggestions: res.data.suggestions,
        recommended_documents: res.data.suggestions?.recommended_documents || [],
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, aiMsg]);
      setExpandedMessages(prev => new Set(prev).add(aiMsg.id));
      setFollowUpInput('');
    } catch {
      stopProgress();
      toast.error('分析失败');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Export single analysis
  const handleExport = async (analysisId: number, format: 'pdf' | 'docx') => {
    setExportingId(analysisId);
    setShowExportMenu(null);
    try {
      const msg = messages.find(m => m.analysis_id === analysisId);
      if (!msg) return;
      const res = await axiosInstance.post('/api/exports', {
        content: msg.content,
        title: `案情分析_${new Date().toLocaleDateString('zh-CN')}`,
        format,
      }, { responseType: 'blob' });
      const blob = new Blob([res.data], {
        type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `案情分析_${new Date().toLocaleDateString('zh-CN')}.${format === 'pdf' ? 'pdf' : 'docx'}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`已导出为 ${format.toUpperCase()}`);
    } catch {
      toast.error('导出失败');
    } finally {
      setExportingId(null);
    }
  };

  // Export full conversation history
  const handleExportConversation = async (format: 'pdf' | 'docx') => {
    if (messages.length === 0) {
      toast.error('暂无对话记录可导出');
      return;
    }

    setExportingId(-1); // special id for conversation export
    try {
      // Build conversation content
      const conversationContent = messages.map(msg => {
        const role = msg.role === 'user' ? '【用户陈述】' : '【AI分析】';
        const time = new Date(msg.timestamp).toLocaleString('zh-CN');
        return `${role} ${time}\n${msg.content}\n${msg.is_approved ? '(已认可)\n' : ''}\n${'='.repeat(50)}\n`;
      }).join('\n');

      const res = await axiosInstance.post('/api/exports', {
        content: conversationContent,
        title: `完整对话记录_${caseInfo?.title || '案件'}_${new Date().toLocaleDateString('zh-CN')}`,
        format,
      }, { responseType: 'blob' });

      const blob = new Blob([res.data], {
        type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `完整对话记录_${new Date().toLocaleDateString('zh-CN')}.${format === 'pdf' ? 'pdf' : 'docx'}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`完整对话记录已导出为 ${format.toUpperCase()}`);
    } catch {
      toast.error('导出失败');
    } finally {
      setExportingId(null);
    }
  };

  // Generate document - call API directly, save to DB, show download link in chat
  const handleGenerateDoc = useCallback(async (docType: string) => {
    try {
      // Add a temporary message showing generation is in progress
      const tempMsgId = `doc-gen-${Date.now()}`;
      setMessages(prev => [...prev, {
        id: tempMsgId,
        role: 'assistant' as const,
        content: `正在为您生成《${docType}》...`,
        timestamp: new Date().toISOString(),
      }]);

      const res = await axiosInstance.post('/api/smart-chat/generate-document', {
        case_id: parseInt(currentCaseId),
        document_type: docType,
      });

      const docData = res.data;
      const docMsg: ChatMessage = {
        id: `doc-${docData.document_id}`,
        role: 'assistant' as const,
        content: `《${docType}》已生成完成！\n\n` +
          `**文书内容：**\n${docData.content.substring(0, 500)}...\n\n` +
          `**证据引用：** 基于 ${docData.evidence_count} 份证据生成，文书中已标注证据序号。`,
        timestamp: new Date().toISOString(),
        generated_document: {
          id: docData.document_id,
          type: docType,
          content: docData.content,
          download_url: docData.download_url,
          evidence_count: docData.evidence_count,
        },
      };

      // Replace the temp message with the actual document message
      setMessages(prev => prev.map(m => m.id === tempMsgId ? docMsg : m));
      toast.success(`《${docType}》已生成并保存`);
    } catch (err) {
      const errorMsg = getRequestErrorMessage(err, '文书草稿生成失败');
      toast.error(errorMsg);
      // Remove the temp message
      setMessages(prev => prev.filter(m => !m.id.startsWith('doc-gen-')));
    }
  }, [currentCaseId]);

  // Generate all recommended docs
  const handleGenerateAllDocs = useCallback(async (docs: { type: string }[]) => {
    for (const doc of docs) {
      await handleGenerateDoc(doc.type);
    }
  }, [handleGenerateDoc]);

  // 保存编辑后的文书
  const handleSaveDocument = useCallback(async (docId: number, newContent: string) => {
    try {
      await axiosInstance.put(`/api/document-management/generated/${docId}`, {
        content: newContent,
        status: 'draft'
      });
      toast.success('文书已保存');
    } catch (err) {
      toast.error('保存失败: ' + getRequestErrorMessage(err, '未知错误'));
    }
  }, []);

  // 监听编辑文书事件
  useEffect(() => {
    const handleEditEvent = (e: CustomEvent) => {
      const { docId, content } = e.detail;
      const newContent = prompt('编辑文书内容:', content);
      if (newContent && newContent !== content) {
        handleSaveDocument(docId, newContent);
      }
    };
    window.addEventListener('edit-document', handleEditEvent as EventListener);
    return () => window.removeEventListener('edit-document', handleEditEvent as EventListener);
  }, [handleSaveDocument]);

  const toggleExpand = (msgId: string) => {
    setExpandedMessages(prev => {
      const next = new Set(prev);
      if (next.has(msgId)) next.delete(msgId);
      else next.add(msgId);
      return next;
    });
  };

  // ==================== Guide Page ====================
  if (!hasStarted && !isAnalyzing) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-6 lg:py-8">
        {apiError && (
          <Card className="mb-4 border-red-200 bg-red-50">
            <CardContent className="py-3 flex items-center gap-2 text-red-600">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span className="text-sm">{apiError}</span>
            </CardContent>
          </Card>
        )}
        <div className="grid gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <div className="rounded-lg bg-slate-950 p-5 text-white shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-md bg-teal-500/15 text-teal-200">
                <Scale className="h-6 w-6" />
              </div>
              <div>
                <p className="text-xs font-medium text-teal-200">法律工作辅助台</p>
                <h1 className="text-xl font-bold">全案证据驱动分析</h1>
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-300">
              先让 AI 读取案件基础事实和证据链，再围绕争议焦点、举证责任、诉讼请求、反驳风险输出可复核的律师意见。
            </p>
            {caseInfo && (
              <div className="mt-5 rounded-md border border-white/10 bg-white/5 p-4">
                <h2 className="text-lg font-semibold">{caseInfo.title}</h2>
                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-slate-400">我方</p>
                    <p className="font-medium">{caseInfo.plaintiff}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">对方</p>
                    <p className="font-medium">{caseInfo.defendant}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">案由</p>
                    <p className="font-medium">{caseInfo.cause}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">诉讼金额</p>
                    <p className="font-medium">{caseInfo.claim_amount}</p>
                  </div>
                </div>
              </div>
            )}
            <div className="mt-5 grid grid-cols-3 gap-2">
              <div className="rounded-md border border-teal-400/20 bg-teal-400/10 p-3">
                <p className="text-xs text-teal-100">证据读取</p>
                <p className="mt-1 text-2xl font-bold">{caseInfo?.evidence_count ?? evidenceList.length}</p>
              </div>
              <div className="rounded-md border border-white/10 bg-white/5 p-3">
                <p className="text-xs text-slate-300">输出模式</p>
                <p className="mt-1 text-sm font-semibold">律师复核</p>
              </div>
              <div className="rounded-md border border-amber-300/20 bg-amber-300/10 p-3">
                <p className="text-xs text-amber-100">风险视角</p>
                <p className="mt-1 text-sm font-semibold">对抗审查</p>
              </div>
            </div>
            <div className="mt-5 space-y-3 text-sm text-slate-300">
              <div className="flex items-start gap-2">
                <ListChecks className="mt-0.5 h-4 w-4 text-teal-200" />
                <span>输出必须区分事实、证据、法律评价和下一步动作。</span>
              </div>
              <div className="flex items-start gap-2">
                <Gavel className="mt-0.5 h-4 w-4 text-teal-200" />
                <span>优先暴露证据缺口和对方可能抗辩，避免只给乐观结论。</span>
              </div>
            </div>
          </div>

          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Briefcase className="h-5 w-5 text-teal-700" />
                启动一次可复核的法律工作分析
              </CardTitle>
              <CardDescription>
                建议直接写明时间线、交易背景、对方行为、你想达成的结果。系统会结合全部证据链生成待核验分析。
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <LegalDisclaimer variant="analysis" />
              <div className="grid gap-2 sm:grid-cols-3">
                {ROLE_OPTIONS.map((option) => (
                  <Button
                    key={option.value}
                    variant={userRole === option.value ? 'default' : 'outline'}
                    onClick={() => setUserRole(option.value)}
                    className="h-auto justify-start px-3 py-2 text-left"
                  >
                    <span>
                      <span className="block text-sm">{option.label}</span>
                      <span className="block text-xs font-normal opacity-70">{option.helper}</span>
                    </span>
                  </Button>
                ))}
              </div>
              <Textarea
                value={factDescription}
                onChange={(e) => setFactDescription(e.target.value)}
                placeholder="例如：请基于博凯升华违背合作案，按时间线梳理我方已经掌握的事实，说明雷天乾/对方公司可能构成的违约或侵权点，并指出 177 份证据中还缺哪些关键材料。"
                rows={9}
                className="text-sm leading-6"
              />
              <div>
                <label className="mb-2 block text-sm font-medium">您的目标或底线（可选）</label>
                <Input
                  value={userExpectation}
                  onChange={(e) => setUserExpectation(e.target.value)}
                  placeholder="例如：优先固定主体责任，其次准备诉讼和保全，不接受只给泛泛建议"
                />
              </div>
              <div className="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
                <p className="mb-2 text-xs font-medium text-slate-600 dark:text-slate-300">可直接套用的问题</p>
                <div className="flex flex-wrap gap-2">
                  {LAWYER_PROMPT_TEMPLATES.map((template) => (
                    <button
                      key={template}
                      type="button"
                      onClick={() => setFactDescription(template)}
                      className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-left text-xs text-slate-700 transition-colors hover:border-teal-300 hover:text-teal-800 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300"
                    >
                      {template}
                    </button>
                  ))}
                </div>
              </div>
              <Button onClick={handleStartAnalysis} disabled={!factDescription.trim()} className="w-full bg-teal-700 hover:bg-teal-800">
                <Sparkles className="mr-2 h-4 w-4" />开始全案分析
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // ==================== Analysis In Progress ====================
  if (isAnalyzing) {
    const isLowTime = countdownSeconds < 60; // 少于1分钟时显示警告
    return (
      <div className="h-full flex flex-col">
        {/* 顶部状态栏 */}
        <div className="flex-1 flex items-center justify-center">
          <Card className="border-primary/30 bg-gradient-to-br from-primary/5 to-background w-full max-w-2xl mx-4">
            <CardContent className="py-8 px-6">
              {/* 标题和倒计时 */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <div className="absolute inset-0 h-8 w-8 rounded-full border-2 border-primary/30 animate-ping" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-primary">AI 正在分析案情</h2>
                    <p className="text-sm text-muted-foreground">基于案件全部证据进行深度分析</p>
                  </div>
                </div>
                {/* 倒计时显示 */}
                <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${isLowTime ? 'bg-red-100 text-red-600' : 'bg-primary/10 text-primary'}`}>
                  <Clock className="h-5 w-5" />
                  <span className="font-mono text-lg font-bold">{formatTime(countdownSeconds)}</span>
                </div>
              </div>

              {/* 进度条 */}
              <div className="mb-6">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-muted-foreground">分析进度</span>
                  <span className="font-medium text-primary">{Math.round(analysisProgress)}%</span>
                </div>
                <div className="h-3 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-primary/60 transition-all duration-500 ease-out"
                    style={{ width: `${analysisProgress}%` }}
                  />
                </div>
              </div>

              {/* 步骤列表 */}
              <div className="space-y-3 mb-6">
                {currentSteps.map((step, i) => (
                  <div
                    key={i}
                    className={`flex items-center gap-3 p-2 rounded-lg transition-all ${
                      i < analysisStep
                        ? 'bg-green-50 text-green-700'
                        : i === analysisStep
                        ? 'bg-primary/10 text-primary font-medium'
                        : 'text-muted-foreground/50'
                    }`}
                  >
                    {i < analysisStep ? (
                      <Check className="h-5 w-5 flex-shrink-0" />
                    ) : i === analysisStep ? (
                      <Loader2 className="h-5 w-5 flex-shrink-0 animate-spin" />
                    ) : (
                      <div className="h-5 w-5 rounded-full border-2 border-muted-foreground/20 flex-shrink-0" />
                    )}
                    <span className="text-sm">{step}</span>
                  </div>
                ))}
              </div>

              {/* 底部提示 */}
              <div className="flex items-center justify-between text-xs text-muted-foreground pt-4 border-t">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  <span>正在阅读全部 {evidenceList.length} 份证据</span>
                </div>
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  <span>分析完成后可继续追问</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // ==================== Chat Page ====================
  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Evidence Panel - Desktop sidebar */}
      <EvidencePanel evidenceList={evidenceList} variant="sidebar" />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="hidden items-center justify-between border-b bg-white/80 px-5 py-3 backdrop-blur dark:bg-slate-950/80 lg:flex">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <Scale className="h-3.5 w-3.5" />
              <span>法律 AI 助手 · 全案对话</span>
              <span>·</span>
              <span>{caseInfo?.cause || '待分析案由'}</span>
            </div>
            <h2 className="mt-1 truncate text-base font-semibold text-slate-950 dark:text-slate-100">
              {caseInfo?.title || `案件 #${currentCaseId}`}
            </h2>
          </div>
          <div className="grid grid-cols-3 gap-2 text-right">
            <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 dark:border-slate-800 dark:bg-slate-900">
              <p className="text-xs text-slate-500">证据</p>
              <p className="text-sm font-semibold">{evidenceList.length} 份</p>
            </div>
            <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 dark:border-slate-800 dark:bg-slate-900">
              <p className="text-xs text-slate-500">分析</p>
              <p className="text-sm font-semibold">{messages.filter(m => m.role === 'assistant').length} 次</p>
            </div>
            <div className="rounded-md border border-teal-200 bg-teal-50 px-3 py-1.5 text-teal-800 dark:border-teal-900 dark:bg-teal-950/40 dark:text-teal-200">
              <p className="text-xs">模式</p>
              <p className="text-sm font-semibold">律师复核</p>
            </div>
          </div>
        </div>

        {/* Top bar */}
        <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/20 lg:hidden">
          <div className="flex items-center gap-2 text-sm">
            <Shield className="h-4 w-4 text-primary" />
            <span className="truncate">{caseInfo?.title || '法律 AI 助手'} · {evidenceList.length} 份证据</span>
          </div>
          <Button variant="ghost" size="sm" onClick={() => setShowEvidenceDrawer(!showEvidenceDrawer)}>
            <Eye className="h-4 w-4 mr-1" />查看证据
          </Button>
        </div>

        {/* Evidence Drawer - Mobile */}
        {showEvidenceDrawer && (
          <EvidencePanel evidenceList={evidenceList} variant="drawer" onClose={() => setShowEvidenceDrawer(false)} />
        )}

        {/* Error display */}
        {apiError && (
          <div className="mx-4 mt-2">
            <Card className="border-red-200 bg-red-50">
              <CardContent className="py-2 flex items-center gap-2 text-red-600">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span className="text-sm">{apiError}</span>
                <Button variant="ghost" size="sm" className="ml-auto h-6 text-xs" onClick={() => setApiError(null)}>关闭</Button>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              msg={msg}
              caseId={parseInt(currentCaseId)}
              isExpanded={expandedMessages.has(msg.id)}
              isExporting={exportingId === msg.analysis_id}
              showExportMenu={showExportMenu === msg.analysis_id}
              onToggleExpand={() => toggleExpand(msg.id)}
              onApprove={handleApprove}
              onDelete={handleDelete}
              onRetry={handleRetry}
              onExport={handleExport}
              onToggleExportMenu={() => setShowExportMenu(showExportMenu === msg.analysis_id ? null : msg.analysis_id!)}
              onGenerateDoc={handleGenerateDoc}
              onGenerateAllDocs={handleGenerateAllDocs}
            />
          ))}

          {/* Follow-up progress */}
          {isAnalyzing && (
            <div className="mr-4">
              <Card className="border-primary/20 bg-primary/5">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2 text-sm">
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    <span className="text-primary font-medium">{currentSteps[analysisStep]}</span>
                  </div>
                  <Progress value={analysisProgress} className="mt-2 h-1" />
                </CardContent>
              </Card>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Bottom bar - Export + Input */}
        <div className="border-t bg-background">
          {/* Export bar */}
          {messages.length > 0 && (
            <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/20">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <MessageSquare className="h-3.5 w-3.5" />
                <span>共 {messages.filter(m => m.role === 'assistant').length} 次分析</span>
                {messages.filter(m => m.is_approved).length > 0 && (
                  <span className="text-green-600">· {messages.filter(m => m.is_approved).length} 次已认可</span>
                )}
              </div>
              <div className="relative">
                <Button variant="ghost" size="sm" className="h-7 text-xs"
                  onClick={() => setShowExportMenu(showExportMenu === -1 ? null : -1)}
                  disabled={exportingId === -1}>
                  {exportingId === -1 ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <Download className="h-3 w-3 mr-1" />}
                  导出对话记录
                </Button>
                {showExportMenu === -1 && (
                  <div className="absolute right-0 bottom-full mb-1 bg-popover border rounded-md shadow-lg p-1 z-50 min-w-[120px]">
                    <Button variant="ghost" size="sm" className="w-full justify-start h-7 text-xs" onClick={() => handleExportConversation('pdf')}>
                      <FileDown className="h-3 w-3 mr-1" />导出 PDF
                    </Button>
                    <Button variant="ghost" size="sm" className="w-full justify-start h-7 text-xs" onClick={() => handleExportConversation('docx')}>
                      <FileText className="h-3 w-3 mr-1" />导出 Word
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-3">
            <div className="mb-2 flex gap-2 overflow-x-auto pb-1">
              {LAWYER_PROMPT_TEMPLATES.map((template) => (
                <button
                  key={template}
                  type="button"
                  onClick={() => setFollowUpInput(template)}
                  className="shrink-0 rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-700 transition-colors hover:border-teal-300 hover:text-teal-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
                >
                  {template.length > 24 ? `${template.slice(0, 24)}...` : template}
                </button>
              ))}
            </div>
            {/* Uploaded files display */}
            {uploadedFiles.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-2">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="flex items-center gap-2 px-2 py-1 bg-muted/50 rounded-md">
                    <File className="h-4 w-4 text-primary" />
                    <span className="text-sm truncate max-w-[150px]">{file.name}</span>
                    <Button variant="ghost" size="sm" className="h-5 w-5 p-0" onClick={() => removeUploadedFile(index)}>
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".txt,.md,.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif"
              multiple
              onChange={handleFileSelect}
            />
            <div className="grid gap-2 lg:grid-cols-[auto_auto_minmax(0,1fr)_auto]">
              <Button
                variant="outline"
                size="sm"
                className="h-auto justify-center py-2"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
              >
                <Upload className="h-4 w-4 mr-1" />
                添加文件
              </Button>
              <select 
                className="rounded-md border bg-background px-2 py-2 text-sm"
                onChange={(e) => {
                  if (e.target.value) {
                    handleGenerateDoc(e.target.value);
                    e.target.value = '';
                  }
                }}
                value=""
              >
                <option value="">生成文书...</option>
                <option value="起诉状">民事起诉状</option>
                <option value="劳动仲裁申请书">劳动仲裁申请书</option>
                <option value="答辩状">答辩状</option>
                <option value="代理词">代理词</option>
                <option value="证据目录">证据目录</option>
                <option value="财产保全">财产保全申请书</option>
                <option value="先予执行">先予执行申请书</option>
                <option value="管辖异议">管辖异议申请书</option>
                <option value="反诉状">反诉状</option>
                <option value="上诉状">上诉状</option>
                <option value="再审申请书">再审申请书</option>
                <option value="执行异议">执行异议申请书</option>
              </select>
              <Textarea value={followUpInput} onChange={(e) => setFollowUpInput(e.target.value)}
                placeholder="追问法律 AI 助手：要求补充证据出处、重新按对方视角反驳、生成证据目录或文书草稿..." className="min-h-[72px] resize-none" rows={2}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleFollowUp(); } }} />
              <Button onClick={() => handleFollowUp()} disabled={isAnalyzing || isUploading || (!followUpInput.trim() && uploadedFiles.length === 0)} className="self-end bg-teal-700 hover:bg-teal-800">
                {isAnalyzing || isUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function getResponseStatus(error: unknown): number | undefined {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    return (error as { response?: { status?: number } }).response?.status;
  }
  return undefined;
}

function getResponseData(error: unknown): unknown {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    return (error as { response?: { data?: unknown } }).response?.data;
  }
  return undefined;
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
