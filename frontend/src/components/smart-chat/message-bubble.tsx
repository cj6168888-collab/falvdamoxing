import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { MarkdownContent } from '@/components/common/markdown-content';
import { SuggestionCards } from './suggestion-cards';
import { DocumentRecommendations } from './document-recommendations';
import { AmountCalculator } from './amount-calculator';
import { EvidenceWarning } from './evidence-warning';
import { extractEvidenceGaps } from './evidence-warning-utils';
import { ActionBar, type ActionButton } from './action-bar';
import { PRESET_ACTIONS } from './action-presets';
import { toast } from 'sonner';
import {
  Bot, User, Loader2, Calculator, FileDown, Edit,
  Check, Download, FileText
} from 'lucide-react';

export interface SuggestionData {
  rights_suggestions?: {
    can_claim_rights: string[];
    legal_basis?: string[];
    rights_analysis?: string;
  };
  amount_suggestions?: {
    recommended_amount: number | null;
    amount_breakdown?: Record<string, string>;
    amount_analysis?: string;
    max_possible?: string;
    realistic_expectation?: string;
  };
  defense_strategy?: {
    if_defendant: string;
    minimum_acceptable?: string;
    defense_points?: string[];
  };
  risk_assessment?: {
    win_probability: string;
    key_risks: string[];
    evidence_gaps?: string[];
    risk_mitigation?: string[];
  };
  summary_for_user?: string;
}

interface GeneratedDocument {
  id: number;
  type: string;
  content: string;
  download_url: string;
  evidence_count: number;
}

export interface SmartChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  analysis_id?: number;
  suggestions?: SuggestionData;
  recommended_documents?: { type: string; reason: string; priority: string }[];
  generated_document?: GeneratedDocument;
  timestamp: string;
  is_approved?: boolean;
}

interface MessageBubbleProps {
  msg: SmartChatMessage;
  caseId?: number;
  isExpanded: boolean;
  isExporting: boolean;
  showExportMenu: boolean;
  onToggleExpand: () => void;
  onApprove: (analysisId: number) => void;
  onDelete: (analysisId: number) => void;
  onRetry: (msg: SmartChatMessage) => void;
  onExport: (analysisId: number, format: 'pdf' | 'docx') => void;
  onToggleExportMenu: () => void;
  onGenerateDoc: (docType: string) => void;
  onGenerateAllDocs: (docs: { type: string }[]) => void;
  onEvidenceUploaded?: () => void;
}

export function MessageBubble({
  msg,
  caseId,
  isExpanded,
  isExporting,
  onToggleExpand,
  onApprove,
  onDelete,
  onRetry,
  onExport,
  onToggleExportMenu,
  onGenerateDoc,
  onGenerateAllDocs,
}: MessageBubbleProps) {
  const [showCalculator, setShowCalculator] = useState(false);
  const [isGeneratingDoc, setIsGeneratingDoc] = useState(false);
  const suggestions = msg.suggestions;

  // 提取证据缺口
  const evidenceGaps = extractEvidenceGaps(suggestions?.risk_assessment);

  // 生成文档
  const handleGenerateDoc = async (docType: string) => {
    setIsGeneratingDoc(true);
    try {
      await onGenerateDoc(docType);
    } finally {
      setIsGeneratingDoc(false);
    }
  };

  // 金额确认后的回调
  const handleAmountConfirmed = (amount: number) => {
    toast.success(`已确认诉讼金额：¥${amount.toLocaleString()}`);
    setShowCalculator(false);
  };

  // 用户消息
  if (msg.role === 'user') {
    return (
      <Card className="bg-blue-50 dark:bg-blue-950 max-w-2xl ml-auto">
        <CardContent className="p-3">
          <div className="flex items-start gap-2">
            <User className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // 构建操作按钮
  const analysisId = msg.analysis_id;
  const primaryActions: ActionButton[] = [
    PRESET_ACTIONS.expand(onToggleExpand),
    analysisId !== undefined ? PRESET_ACTIONS.approve(() => onApprove(analysisId)) : null,
    PRESET_ACTIONS.retry(() => onRetry(msg)),
    analysisId !== undefined ? PRESET_ACTIONS.delete(() => onDelete(analysisId)) : null,
    {
      id: 'export',
      icon: isExporting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileDown className="h-3.5 w-3.5" />,
      label: '导出',
      onClick: onToggleExportMenu,
    },
  ].filter(Boolean) as ActionButton[];

  // 次要操作按钮
  const secondaryActions: ActionButton[] = [
    analysisId !== undefined ? PRESET_ACTIONS.exportPdf(() => onExport(analysisId, 'pdf')) : null,
    analysisId !== undefined ? PRESET_ACTIONS.exportWord(() => onExport(analysisId, 'docx')) : null,
    suggestions?.amount_suggestions ? {
      id: 'calculator',
      icon: <Calculator className="h-3.5 w-3.5" />,
      label: '金额计算器',
      onClick: () => setShowCalculator(!showCalculator),
    } : null,
  ].filter(Boolean) as ActionButton[];

  // AI 消息
  return (
    <Card className={`max-w-3xl ${msg.is_approved ? 'border-green-300 bg-green-50/30 dark:bg-green-950/10' : ''}`}>
      <CardContent className="p-3">
        <div className="flex items-start gap-2">
          <Bot className="h-4 w-4 mt-0.5 flex-shrink-0 text-primary" />
          <div className="flex-1 min-w-0">
              {msg.analysis_id ? (
                <div>
                  {/* 顶部操作栏 */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1">
                      <Badge variant="outline" className="text-xs">AI 分析</Badge>
                      {msg.is_approved && (
                        <Badge className="text-xs bg-green-500">已认可</Badge>
                      )}
                      {msg.is_approved && (
                        <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                          主要脉络
                        </Badge>
                      )}
                    </div>
                    <ActionBar
                      primaryActions={primaryActions}
                      secondaryActions={secondaryActions}
                    />
                  </div>

                  {/* 证据缺失警告 */}
                  {evidenceGaps.length > 0 && isExpanded && (
                    <EvidenceWarning
                      gaps={evidenceGaps}
                      onUploadEvidence={() => {
                        // 滚动到上传区域或触发上传
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                    />
                  )}

                  {/* 结构化建议卡片 - 使用独立组件 */}
                  {suggestions && isExpanded && (
                    <SuggestionCards suggestions={suggestions} />
                  )}

                  {/* 金额计算器 - 可折叠 */}
                  {showCalculator && suggestions?.amount_suggestions && (
                    <div className="mt-3 mb-3">
                      <AmountCalculator
                        caseId={caseId || 0}
                        analysisId={msg.analysis_id}
                        recommendedAmount={suggestions.amount_suggestions.recommended_amount}
                        breakdown={suggestions.amount_suggestions.amount_breakdown}
                        maxPossible={suggestions.amount_suggestions.max_possible}
                        onConfirmed={handleAmountConfirmed}
                      />
                    </div>
                  )}

                  {/* 推荐文书 - 使用独立组件 */}
                  {msg.recommended_documents && msg.recommended_documents.length > 0 && (
                    <DocumentRecommendations
                      documents={msg.recommended_documents}
                      onGenerateDoc={handleGenerateDoc}
                      onGenerateAllDocs={onGenerateAllDocs}
                      isGenerating={isGeneratingDoc}
                    />
                  )}

                  {/* 生成的文书 - 带下载链接 */}
                  {msg.generated_document && (
                    <Card className="mt-3 mb-3 border-green-200 bg-green-50/30">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <Check className="h-4 w-4 text-green-600" />
                            <p className="text-sm font-medium text-green-700">
                              《{msg.generated_document.type}》已生成
                            </p>
                            <Badge variant="outline" className="text-xs">
                              基于 {msg.generated_document.evidence_count} 份证据
                            </Badge>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => {
                              const url = `/api/documents/${msg.generated_document!.id}/download`;
                              window.open(url, '_blank');
                            }}
                          >
                            <Download className="mr-1 h-3.5 w-3.5" />
                            下载文书
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              const url = `/api/evidence/export-book-for-document/${caseId}?document_type=${encodeURIComponent(msg.generated_document!.type)}&format=pdf`;
                              window.open(url, '_blank');
                              toast.success('正在生成对应证据册...');
                            }}
                          >
                            <FileText className="mr-1 h-3.5 w-3.5" />
                            下载证据册
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              // 展开查看完整文书内容
                              onToggleExpand();
                            }}
                          >
                            查看内容
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              // 触发编辑功能 - 通过props回调
                              const editEvent = new CustomEvent('edit-document', { 
                                detail: { 
                                  docId: msg.generated_document!.id,
                                  content: msg.generated_document!.content,
                                  type: msg.generated_document!.type
                                } 
                              });
                              window.dispatchEvent(editEvent);
                            }}
                          >
                            <Edit className="mr-1 h-3.5 w-3.5" />
                            编辑
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* 完整分析 */}
                  {isExpanded && (
                    <div className="border-t pt-3">
                      <MarkdownContent content={msg.content} />
                    </div>
                  )}
                  {!isExpanded && (
                    <p className="text-sm text-muted-foreground truncate">{msg.content.substring(0, 100)}...</p>
                  )}
                </div>
              ) : (
                <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
  );
}

export default MessageBubble;
