import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Shield, Upload, FileText, ChevronDown, ChevronUp, Star, Info } from 'lucide-react';
import { EvidenceUploader } from './evidence-uploader';

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

interface EvidencePanelProps {
  evidenceList: EvidenceItem[];
  variant?: 'sidebar' | 'drawer';
  onClose?: () => void;
  caseId?: number;
  onEvidenceUploaded?: () => void;
}

export function EvidencePanel({
  evidenceList,
  variant = 'sidebar',
  onClose,
  caseId,
  onEvidenceUploaded,
}: EvidencePanelProps) {
  const [showAll, setShowAll] = useState(false);
  const [expandedIds, setExpandedIds] = useState<Set<number | string>>(new Set());

  const displayList = showAll ? evidenceList : evidenceList.slice(0, 20);

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      CONTRACT: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      contract: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      INVOICE: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      invoice: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      correspondence: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      CORRESPONDENCE: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      communication: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      COMMUNICATION: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      identification: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
      IDENTIFICATION: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
      witness: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      WITNESS: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      appraisal: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      video_audio: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
      other: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
    };
    return colors[type?.toUpperCase()] || colors.other;
  };

  const getCredibilityColor = (score?: number) => {
    if (!score) return 'text-muted-foreground';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-amber-600';
    return 'text-red-600';
  };

  const toggleExpand = (id: number | string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const getDisplayContent = (ev: EvidenceItem) => {
    // 优先显示提取的内容，其次原始内容
    return ev.extracted_content || ev.raw_content || ev.summary || '无内容';
  };

  const formatReviewActions = (actions?: string[]) => {
    if (!actions || actions.length === 0) return '待补充';
    return actions.filter(Boolean).join('；') || '待补充';
  };

  const content = (
    <div className="p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-sm flex items-center gap-2">
          <Shield className="h-4 w-4 text-primary" />
          已读取证据
          <span className="text-xs text-muted-foreground">({evidenceList.length})</span>
        </h3>
        <div className="flex items-center gap-1">
          {caseId && variant === 'sidebar' && (
            <EvidenceUploader
              caseId={caseId}
              onUploadSuccess={() => {
                onEvidenceUploaded?.();
              }}
              trigger={
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0" title="上传证据">
                  <Upload className="h-3.5 w-3.5" />
                </Button>
              }
            />
          )}
          {variant === 'drawer' && onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>关闭</Button>
          )}
        </div>
      </div>

      {/* 空状态提示 */}
      {evidenceList.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center py-8">
          <div className="rounded-full bg-muted p-3 mb-3">
            <FileText className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="text-sm text-muted-foreground mb-2">暂无证据</p>
          <p className="text-xs text-muted-foreground mb-4">请先上传证据材料</p>
          {caseId && (
            <EvidenceUploader
              caseId={caseId}
              onUploadSuccess={() => {
                onEvidenceUploaded?.();
              }}
              trigger={
                <Button variant="outline" size="sm" className="text-xs">
                  <Upload className="h-3 w-3 mr-1" />
                  上传证据
                </Button>
              }
            />
          )}
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-2">
          {displayList.map((ev) => {
            const isExpanded = expandedIds.has(ev.id);
            const displayContent = getDisplayContent(ev);
            const review = ev.evidence_review;
            const hasReview = Boolean(review);

            return (
              <Collapsible key={ev.id} open={isExpanded} onOpenChange={() => toggleExpand(ev.id)}>
                <div className="rounded border text-xs">
                  <CollapsibleTrigger asChild>
                    <div className="p-2 hover:bg-muted/50 transition-colors cursor-pointer">
                      <div className="flex items-start gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate" title={ev.display_name || ev.original_filename || '未命名'}>
                            {ev.display_name || ev.original_filename || '未命名'}
                          </p>
                          <div className="flex items-center gap-1 mt-1 flex-wrap">
                            <span className={`text-xs px-1.5 py-0.5 rounded ${getTypeColor(ev.evidence_type || '')}`}>
                              {ev.evidence_type || '未分类'}
                            </span>
                            <span
                              className={`text-xs px-1.5 py-0.5 rounded ${
                                hasReview
                                  ? 'bg-teal-50 text-teal-700 dark:bg-teal-950/30 dark:text-teal-300'
                                  : 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-300'
                              }`}
                            >
                              {hasReview ? '已人工复核' : '待人工复核'}
                            </span>
                            {ev.credibility_score && (
                              <span className={`text-xs flex items-center gap-0.5 ${getCredibilityColor(ev.credibility_score)}`}>
                                <Star className="h-2.5 w-2.5" />
                                {Math.round(ev.credibility_score)}%
                              </span>
                            )}
                          </div>
                          {/* AI 摘要 */}
                          {ev.summary && !isExpanded && (
                            <p className="text-muted-foreground mt-1 line-clamp-2 flex items-start gap-1">
                              <Info className="h-3 w-3 flex-shrink-0 mt-0.5 text-blue-500" />
                              <span className="line-clamp-2">{ev.summary}</span>
                            </p>
                          )}
                        </div>
                        <ChevronDown className={`h-4 w-4 flex-shrink-0 text-muted-foreground transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                      </div>
                    </div>
                  </CollapsibleTrigger>

                  <CollapsibleContent>
                    <div className="px-2 pb-2 pt-1 border-t space-y-2">
                      {/* AI 摘要 */}
                      {ev.summary && (
                        <div className="bg-blue-50 dark:bg-blue-950/20 rounded p-2">
                          <p className="text-xs font-medium text-blue-700 dark:text-blue-400 flex items-center gap-1">
                            <Info className="h-3 w-3" />
                            AI 理解摘要
                          </p>
                          <p className="text-xs mt-1 text-blue-800 dark:text-blue-300">{ev.summary}</p>
                        </div>
                      )}

                      {/* 证明的事实 */}
                      <div className="rounded border border-teal-200 bg-teal-50/70 p-2 dark:border-teal-900/60 dark:bg-teal-950/20">
                        <p className="text-xs font-medium text-teal-800 dark:text-teal-300 flex items-center gap-1">
                          <Shield className="h-3 w-3" />
                          人工复核工作底稿
                        </p>
                        <dl className="mt-2 grid gap-1 text-xs text-teal-900 dark:text-teal-100">
                          <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-2">
                            <dt className="text-teal-700 dark:text-teal-300">证明目的</dt>
                            <dd>{review?.proof_purpose || '待人工填写'}</dd>
                          </div>
                          <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-2">
                            <dt className="text-teal-700 dark:text-teal-300">原件状态</dt>
                            <dd>{review?.original_status || '待核验'}</dd>
                          </div>
                          <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-2">
                            <dt className="text-teal-700 dark:text-teal-300">形成时间</dt>
                            <dd>{review?.formed_at || '待核验'}</dd>
                          </div>
                          <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-2">
                            <dt className="text-teal-700 dark:text-teal-300">真实性</dt>
                            <dd>{review?.authenticity_risk || '待人工核验'}</dd>
                          </div>
                          <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-2">
                            <dt className="text-teal-700 dark:text-teal-300">合法性</dt>
                            <dd>{review?.legality_risk || '待人工核验'}</dd>
                          </div>
                          <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-2">
                            <dt className="text-teal-700 dark:text-teal-300">关联性</dt>
                            <dd>{review?.relevance_risk || '待人工核验'}</dd>
                          </div>
                          <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-2">
                            <dt className="text-teal-700 dark:text-teal-300">补强动作</dt>
                            <dd>{formatReviewActions(review?.strengthening_actions)}</dd>
                          </div>
                          {review?.review_notes && (
                            <div className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-2">
                              <dt className="text-teal-700 dark:text-teal-300">复核备注</dt>
                              <dd>{review.review_notes}</dd>
                            </div>
                          )}
                        </dl>
                      </div>

                      {ev.proves_facts && ev.proves_facts.length > 0 && (
                        <div className="bg-green-50 dark:bg-green-950/20 rounded p-2">
                          <p className="text-xs font-medium text-green-700 dark:text-green-400">证明事实</p>
                          <ul className="list-disc pl-4 mt-1 space-y-0.5">
                            {ev.proves_facts.map((fact, i) => (
                              <li key={i} className="text-xs text-green-800 dark:text-green-300">{fact}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* 关键词 */}
                      {ev.keywords && ev.keywords.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {ev.keywords.slice(0, 10).map((kw, i) => (
                            <span key={i} className="text-xs bg-muted px-1.5 py-0.5 rounded">
                              {kw}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* 完整内容预览 */}
                      {displayContent && displayContent !== ev.summary && (
                        <div className="bg-muted/50 rounded p-2">
                          <p className="text-xs font-medium text-muted-foreground mb-1">内容预览</p>
                          <p className="text-xs text-muted-foreground whitespace-pre-wrap line-clamp-6">
                            {displayContent.substring(0, 500)}
                            {displayContent.length > 500 && '...'}
                          </p>
                        </div>
                      )}
                    </div>
                  </CollapsibleContent>
                </div>
              </Collapsible>
            );
          })}
          {evidenceList.length > 20 && (
            <Button variant="ghost" size="sm" className="w-full text-xs" onClick={() => setShowAll(!showAll)}>
              {showAll ? (
                <>
                  <ChevronUp className="h-3 w-3 mr-1" />
                  收起
                </>
              ) : (
                <>
                  还有 {evidenceList.length - 20} 份证据
                  <ChevronDown className="h-3 w-3 ml-1" />
                </>
              )}
            </Button>
          )}
        </div>
      )}

      {/* 证据上传按钮 - 抽屉模式 */}
      {caseId && variant === 'drawer' && evidenceList.length > 0 && (
        <div className="pt-3 mt-auto border-t">
          <EvidenceUploader
            caseId={caseId}
            onUploadSuccess={() => {
              onEvidenceUploaded?.();
            }}
            trigger={
              <Button variant="outline" size="sm" className="w-full text-xs">
                <Upload className="h-3 w-3 mr-1" />
                上传新证据
              </Button>
            }
          />
        </div>
      )}
    </div>
  );

  // 桌面侧栏模式
  if (variant === 'sidebar') {
    return (
      <div className="hidden lg:flex w-64 border-r bg-muted/10 flex-shrink-0 flex-col">
        {content}
      </div>
    );
  }

  // 手机抽屉模式
  return (
    <div className="lg:hidden border-b bg-muted/10 max-h-80 overflow-y-auto">
      {content}
    </div>
  );
}
